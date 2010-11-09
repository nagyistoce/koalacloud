#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os
import re
import urllib

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api.urlfetch import DownloadError

from library import login
from library import aktuelle_sprache
from library import navigations_bar_funktion
from library import amazon_region
from library import zonen_liste_funktion
from library import format_error_message_green
from library import format_error_message_red
from library import logins3
from library import aws_access_key_erhalten
from library import aws_secret_access_key_erhalten
from library import endpointurl_erhalten
from library import zugangstyp_erhalten
from library import port_erhalten

from dateutil.parser import *

from error_messages import error_messages

# für die Verschlüsselung
# this is needed for the encyption
from itertools import izip, cycle
import hmac, sha
# für die Verschlüsselung
# this is needed for the encyption
import base64


class BucketInhaltPur(webapp.RequestHandler):
    def get(self):
        # self.response.out.write('posted!')
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
          self.redirect('/')
        # Eventuell vorhande Fehlermeldung holen
        message = self.request.get('message')
        # Namen des Buckets holen, dessen Inhalt angezeigt wird
        bucketname = self.request.get('bucket')

        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if not results:
          self.redirect('/')
        else:
          # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache)

          results = aktivezone.fetch(100)

          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          #url = users.create_logout_url(self.request.uri)
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)
          zugangstyp = zugangstyp_erhalten(username) 

          zonen_liste = zonen_liste_funktion(username,sprache)

          if sprache != "de":
            sprache = "en"

          input_error_message = error_messages.get(message, {}).get(sprache)

          # Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
          if input_error_message == None:
            input_error_message = ""

          # Wenn die Nachricht grün formatiert werden soll...
          if message in ("111", "118", "120"):
            # wird sie hier, in der Hilfsfunktion grün formatiert
            input_error_message = format_error_message_green(input_error_message)
          # Ansonsten wird die Nachricht rot formatiert
          elif message in ("112", "119", "121"):
            input_error_message = format_error_message_red(input_error_message)
          else:
            input_error_message = ""


          AWSAccessKeyId = aws_access_key_erhalten(username,regionname)
          AWSSecretAccessKeyId = aws_secret_access_key_erhalten(username,regionname)


          # Mit S3 verbinden
          conn_s3 = logins3(username)
          
          try:
            # Liste der Buckets
            bucket_instance = conn_s3.get_bucket(bucketname)
          except:
            # Wenn es nicht klappt...
            if sprache == "de":
              bucket_keys_tabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
            else:
              bucket_keys_tabelle = '<font color="red">An error occured</font>'
            laenge_liste_keys = 0
            # Wenn es geklappt hat...
          else:
            try:
              # Liste der Keys
              liste_keys = bucket_instance.get_all_keys()
            except:
              # Wenn es nicht klappt...
              if sprache == "de":
                bucket_keys_tabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
              else:
                bucket_keys_tabelle = '<font color="red">An error occured</font>'
              laenge_liste_keys = 0
            else:
              # Wenn es geklappt hat...
              # Anzahl der Keys in der Liste
              laenge_liste_keys = len(liste_keys)
  
            # Wenn wir in einer Eucalyputs-Infrastruktur sind, dann muss dieser
            # dämliche None-Eintrag weg
            if regionname != "Amazon":
              liste_keys2 = []
              for i in range(laenge_liste_keys):
                if str(liste_keys[i].name) != 'None':
                  liste_keys2.append(liste_keys[i])
              laenge_liste_keys2 = len(liste_keys2)
              laenge_liste_keys = laenge_liste_keys2
              liste_keys = liste_keys2
  
  
            if laenge_liste_keys == 0:
              if sprache == "de":
                bucket_keys_tabelle = 'Der Bucket <B>'+ bucketname+' </B>ist leer.'
              else:
                bucket_keys_tabelle = 'The bucket <B>'+ bucketname+' </B>is empty.'
            else:
              bucket_keys_tabelle = ''
              bucket_keys_tabelle = bucket_keys_tabelle + '<table border="3" cellspacing="0" cellpadding="5">'
              bucket_keys_tabelle = bucket_keys_tabelle + '<tr>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<th>&nbsp;&nbsp;&nbsp;</th>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<th>&nbsp;&nbsp;&nbsp;</th>'
              if sprache == "de":
                bucket_keys_tabelle = bucket_keys_tabelle + '<th align="left">Keys</th>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Dateigr&ouml;&szlig;e</th>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Letzte &Auml;nderung</th>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Zugriffsberechtigung</th>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Pr&uuml;fsumme (MD5)</th>'
              else:
                bucket_keys_tabelle = bucket_keys_tabelle + '<th align="left">Keys</th>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Filesize</th>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Last Modified</th>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Access Control List</th>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">MD5</th>'
              bucket_keys_tabelle = bucket_keys_tabelle + '</tr>'
  
              for i in range(laenge_liste_keys):
                  bucket_keys_tabelle = bucket_keys_tabelle + '<tr>'
                  if liste_keys[i].name == None and regionname != "Amazon":
                    bucket_keys_tabelle = bucket_keys_tabelle + '<td>&nbsp;</td>'
                  else:
                    bucket_keys_tabelle = bucket_keys_tabelle + '<td>'
                    bucket_keys_tabelle = bucket_keys_tabelle + '<a href="/bucketkeyentfernen?bucket='
                    bucket_keys_tabelle = bucket_keys_tabelle + str(bucketname)
                    bucket_keys_tabelle = bucket_keys_tabelle + '&amp;typ=pur'
                    bucket_keys_tabelle = bucket_keys_tabelle + '&amp;key='
                    bucket_keys_tabelle = bucket_keys_tabelle + str(liste_keys[i].name)
                    if sprache == "de":
                      bucket_keys_tabelle = bucket_keys_tabelle + '" title="Key l&ouml;schen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Key l&ouml;schen"></a>'
                    else:
                      bucket_keys_tabelle = bucket_keys_tabelle + '" title="erase key"><img src="bilder/delete.png" width="16" height="16" border="0" alt="erase key"></a>'
                    bucket_keys_tabelle = bucket_keys_tabelle + '</td>'
  
                  if liste_keys[i].name == None and regionname != "Amazon":
                    bucket_keys_tabelle = bucket_keys_tabelle + '<td>&nbsp;</td>'
                  else:
                    bucket_keys_tabelle = bucket_keys_tabelle + '<td>'
                    # In der reinen S3-Darstellung ist alles eine Datei
                    if sprache == "de":
                      bucket_keys_tabelle = bucket_keys_tabelle + '<img src="bilder/document.png" width="16" height="16" border="0" alt="Datei">'
                    else:
                      bucket_keys_tabelle = bucket_keys_tabelle + '<img src="bilder/document.png" width="16" height="16" border="0" alt="File">'
                    bucket_keys_tabelle = bucket_keys_tabelle + '</td>'
  
                  bucket_keys_tabelle = bucket_keys_tabelle + '<td>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '<a href="'
                  if regionname == "Amazon":
                    bucket_keys_tabelle = bucket_keys_tabelle + liste_keys[i].generate_url(600, method='GET', headers=None, query_auth=True, force_http=True).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
                  else:
                    port = port_erhalten(username,regionname) 
                    bucket_keys_tabelle = bucket_keys_tabelle + liste_keys[i].generate_url(600, method='GET', headers=None, query_auth=True, force_http=True).replace('&', '&amp;').replace('&amp;amp;', '&amp;').replace('/services/Walrus/', ':'+str(port)+'/services/Walrus/')
                  bucket_keys_tabelle = bucket_keys_tabelle + '">'
                  bucket_keys_tabelle = bucket_keys_tabelle + str(liste_keys[i].name)
                  bucket_keys_tabelle = bucket_keys_tabelle + '</a>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '</td>'
  
                  bucket_keys_tabelle = bucket_keys_tabelle + '<td align="right">'
                  if liste_keys[i].name == None and regionname != "Amazon":
                    bucket_keys_tabelle = bucket_keys_tabelle + '&nbsp;'
                  else:
                    bucket_keys_tabelle = bucket_keys_tabelle + str(liste_keys[i].size)
                  bucket_keys_tabelle = bucket_keys_tabelle + '</td>'
  
                  #bucket_keys_tabelle = bucket_keys_tabelle + '<td>'
                  #bucket_keys_tabelle = bucket_keys_tabelle + str(liste_keys[i].content_type)
                  #bucket_keys_tabelle = bucket_keys_tabelle + '</td>'
  
                  bucket_keys_tabelle = bucket_keys_tabelle + '<td>'
                  # Den ISO8601 Zeitstring umwandeln, damit es besser aussieht.
                  if liste_keys[i].name == None and regionname != "Amazon":
                    bucket_keys_tabelle = bucket_keys_tabelle + '&nbsp;'
                  else:
                    datum_der_letzten_aenderung = parse(liste_keys[i].last_modified)
                    bucket_keys_tabelle = bucket_keys_tabelle + str(datum_der_letzten_aenderung.strftime("%Y-%m-%d  %H:%M:%S"))
                  bucket_keys_tabelle = bucket_keys_tabelle + '</td>'
  
                  bucket_keys_tabelle = bucket_keys_tabelle + '<td align="center">'
                  bucket_keys_tabelle = bucket_keys_tabelle + '<a href="/acl_einsehen?bucket='
                  bucket_keys_tabelle = bucket_keys_tabelle + str(bucketname)
                  bucket_keys_tabelle = bucket_keys_tabelle + '&amp;typ=pur'
                  bucket_keys_tabelle = bucket_keys_tabelle + '&amp;key='
                  bucket_keys_tabelle = bucket_keys_tabelle + str(liste_keys[i].name)
                  if sprache == "de":
                    bucket_keys_tabelle = bucket_keys_tabelle + '" title="ACL einsehen/&auml;ndern">ACL einsehen/&auml;ndern</a>'
                  else:
                    bucket_keys_tabelle = bucket_keys_tabelle + '" title="view/edit ACL">view/edit ACL</a>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '</td>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '<td align="center">'
                  bucket_keys_tabelle = bucket_keys_tabelle + '<tt>'+str(liste_keys[i].etag)+'</tt>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '</td>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '</tr>'
              bucket_keys_tabelle = bucket_keys_tabelle + '</table>'

          # Wenn man sich NICHT unter Amazon befindet, funktioniert der Download von Keys nicht.
#          if regionname != "Amazon":
#            if sprache == "de":
#              eucalyptus_warnung = '<B>Achtung!</B> Unter Eucalyptus 1.6 und 1.6.1 funktioniert der Download von Keys nicht. Dabei handelt es sich um einen Fehler von Eucalyptus. Es kommt zu dieser Fehlermeldung: <B>Failure: 500 Internal Server Error</B>'
#            else:
#              eucalyptus_warnung = '<B>Attention!</B> With Eucalyptus 1.6 and 1.6.1 the download of Keys is broken. This is a bug of Eucalyptus. The result is this error message: <B>Failure: 500 Internal Server Error</B>'
#          else: 
#            eucalyptus_warnung = ''


          #Dokumentation zum Upload von Keys
          #http://docs.amazonwebservices.com/AmazonS3/latest/index.html?HTTPPOSTForms.html
          #http://doc.s3.amazonaws.com/proposals/post.html
          #http://developer.amazonwebservices.com/connect/entry.jspa?externalID=1434
          #http://s3.amazonaws.com/doc/s3-example-code/post/post_sample.html

          # Hier wird das Policy-Dokument erzeugt
          policy_document = ''
          policy_document = policy_document + '{'
          policy_document = policy_document + '"expiration": "2100-01-01T00:00:00Z",'
          policy_document = policy_document + '"conditions": ['
          policy_document = policy_document + '{"bucket": "'+bucketname+'"}, '
          policy_document = policy_document + '["starts-with", "$acl", ""],'
          policy_document = policy_document + '{"redirect": "http://koalacloud.appspot.com/bucket_inhalt_pure"},'
          policy_document = policy_document + '["starts-with", "$key", ""],'
          policy_document = policy_document + '["starts-with", "$Content-Type", ""]'
          policy_document = policy_document + ']'
          policy_document = policy_document + '}'

          policy = base64.b64encode(policy_document)

          signature = base64.b64encode(hmac.new(AWSSecretAccessKeyId, policy, sha).digest())

           
           

          keys_upload_formular = '<p>&nbsp;</p>\n'
          if zugangstyp == "Eucalyptus":
            endpointurl = endpointurl_erhalten(username,regionname)
            port = port_erhalten(username,regionname) 
            keys_upload_formular = keys_upload_formular + '<form action="http://'+str(endpointurl)+':'+str(port)+'/services/Walrus/'
          elif zugangstyp == "GoogleStorage":
            keys_upload_formular = keys_upload_formular + '<form action="http://commondatastorage.googleapis.com/'
          else:
            keys_upload_formular = keys_upload_formular + '<form action="http://s3.amazonaws.com/'
            
          keys_upload_formular = keys_upload_formular + bucketname
          keys_upload_formular = keys_upload_formular + '" method="post" enctype="multipart/form-data">\n'
          keys_upload_formular = keys_upload_formular + '<table border="0" cellspacing="0" cellpadding="5">'
          keys_upload_formular = keys_upload_formular + '<tr>'
          keys_upload_formular = keys_upload_formular + '<td>'
          keys_upload_formular = keys_upload_formular + '<input type="hidden" name="key" value="${filename}">\n'
          keys_upload_formular = keys_upload_formular + '<select name="acl" size="1">\n'
          keys_upload_formular = keys_upload_formular + '<option selected="selected">public-read</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>private</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>public-read-write</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>authenticated-read</option>\n'
          keys_upload_formular = keys_upload_formular + '</select>\n'
          keys_upload_formular = keys_upload_formular + '<select name="Content-Type" size="1">\n'
          keys_upload_formular = keys_upload_formular + '<option selected="selected">application/octet-stream</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>application/pdf</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>application/zip</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>audio/mp4</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>audio/mpeg</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>audio/ogg</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>audio/vorbis</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>image/gif</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>image/jpeg</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>image/png</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>image/tiff</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>text/html</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>text/plain</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>video/mp4</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>video/mpeg</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>video/ogg</option>\n'
          keys_upload_formular = keys_upload_formular + '</select>\n'
          keys_upload_formular = keys_upload_formular + '</td>'
          keys_upload_formular = keys_upload_formular + '</tr>'
          keys_upload_formular = keys_upload_formular + '<tr>'
          keys_upload_formular = keys_upload_formular + '<td>'
          keys_upload_formular = keys_upload_formular + '<input type="hidden" name="redirect" value="http://koalacloud.appspot.com/bucket_inhalt_pure">\n'        
          keys_upload_formular = keys_upload_formular + '<input type="hidden" name="AWSAccessKeyId" value="'+AWSAccessKeyId+'">\n'
          keys_upload_formular = keys_upload_formular + '<input type="hidden" name="policy" value="'+policy+'">\n'
          keys_upload_formular = keys_upload_formular + '<input type="hidden" name="signature" value="'+signature+'">\n'
          keys_upload_formular = keys_upload_formular + '<input type="file" name="file" size="80">\n'
          keys_upload_formular = keys_upload_formular + '</td>'
          keys_upload_formular = keys_upload_formular + '</tr>'
          keys_upload_formular = keys_upload_formular + '<tr>'
          keys_upload_formular = keys_upload_formular + '<td>'
          if sprache == "de":
            keys_upload_formular = keys_upload_formular + '<input type="submit" name="" value="Datei hochladen">\n'
          else:
            keys_upload_formular = keys_upload_formular + '<input type="submit" name="submit" value="upload file">\n'
          keys_upload_formular = keys_upload_formular + '</td>'
          keys_upload_formular = keys_upload_formular + '</tr>'
          keys_upload_formular = keys_upload_formular + '</table>'
          keys_upload_formular = keys_upload_formular + '</form>'
         
          # Unter Eucalyptus funktioniert das Hochladen von Keys nicht
          #else:
          #  if sprache == "de":
          #    keys_upload_formular = '<p>&nbsp;</p>\n Das Hochladen von Keys funktioniert unter Eucalyptus noch nicht'
          #  else:
          #    keys_upload_formular = '<p>&nbsp;</p>\n The key upload is still not working with Eucaplyptus'


          if laenge_liste_keys != 0:
            alle_keys_loeschen_button = '<p>&nbsp;</p>\n'
            alle_keys_loeschen_button = alle_keys_loeschen_button + '<form action="/alle_keys_loeschen" method="get">\n'
            alle_keys_loeschen_button = alle_keys_loeschen_button + '<input type="hidden" name="s3_ansicht" value="pur"> \n'
            alle_keys_loeschen_button = alle_keys_loeschen_button + '<input type="hidden" name="bucket_name" value="'+bucketname+'"> \n'
            if sprache == "de":
              alle_keys_loeschen_button = alle_keys_loeschen_button + '<input type="submit" value="Alle Keys l&ouml;schen">\n'
            else:
              alle_keys_loeschen_button = alle_keys_loeschen_button + '<input type="submit" value="Erase all keys">\n'
            alle_keys_loeschen_button = alle_keys_loeschen_button + '</form>\n'
          else:
            alle_keys_loeschen_button = ''

          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'zonen_liste': zonen_liste,
          'bucket_keys_tabelle': bucket_keys_tabelle,
          'input_error_message': input_error_message,
          'bucketname': bucketname,
          'keys_upload_formular': keys_upload_formular,
          #'eucalyptus_warnung': eucalyptus_warnung,
          'alle_keys_loeschen_button': alle_keys_loeschen_button,
          }

          #if sprache == "de": naechse_seite = "s3_keys_pur_de.html"
          #else:               naechse_seite = "s3_keys_pur_en.html"
          #path = os.path.join(os.path.dirname(__file__), naechse_seite)
          path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "s3_keys_pur.html")
          self.response.out.write(template.render(path,template_values))

