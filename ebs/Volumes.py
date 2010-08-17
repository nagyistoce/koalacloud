#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os

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

from dateutil.parser import *

from error_messages import error_messages

from boto.ec2.connection import *

class Volumes(webapp.RequestHandler):
    def get(self):
        # Eventuell vorhande Fehlermeldung holen
        message = self.request.get('message')
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
          self.redirect('/')

        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if not results:
          self.redirect('/')
        else:
          # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache)
          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          #url = users.create_logout_url(self.request.uri)
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache)

          if sprache != "de":
            sprache = "en"

          input_error_message = error_messages.get(message, {}).get(sprache)

          # Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
          if input_error_message == None:
            input_error_message = ""

          # Wenn die Nachricht grün formatiert werden soll...
          if message in ("15", "22", "23", "24", "27"):
            # wird sie hier, in der Hilfsfunktion grün formatiert
            input_error_message = format_error_message_green(input_error_message)
          # Ansonsten wird die Nachricht rot formatiert
          elif message in ("8", "10", "16", "17", "18", "19", "20", "21", "25", "26"):
            input_error_message = format_error_message_red(input_error_message)
          else:
            input_error_message = ""

          #!!!!!!! (Anfang)
          try:
            # Liste mit den Zonen
            liste_zonen = conn_region.get_all_zones()
          except EC2ResponseError:
            # Wenn es nicht klappt...
            if sprache == "de":
              zonentabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
            else:
              zonentabelle = '<font color="red">An error occured</font>'
            laenge_liste_zonen = 0
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            if sprache == "de":
              zonentabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
            else:
              zonentabelle = '<font color="red">A timeout error occured</font>'
            laenge_liste_zonen = 0
          else:
            # Wenn es geklappt hat...
            # Anzahl der Elemente in der Liste
            laenge_liste_zonen = len(liste_zonen)
          #!!!!!!! (Ende) 
                      
#          # Liste mit den Zonen
#          liste_zonen = conn_region.get_all_zones()
#          # Anzahl der Elemente in der Liste
#          laenge_liste_zonen = len(liste_zonen)

          # Hier wird die Auswahlliste der Zonen erzeugt
          # Diese Auswahlliste ist zum Erzeugen neuer Volumes notwendig
          zonen_in_der_region = ''
          if laenge_liste_zonen == 0:
              zonen_in_der_region = zonen_in_der_region + "<option>&nbsp;</option>"
          else:
              for i in range(laenge_liste_zonen):
                  zonen_in_der_region = zonen_in_der_region + "<option>"
                  zonen_in_der_region = zonen_in_der_region + liste_zonen[i].name
                  zonen_in_der_region = zonen_in_der_region + "</option>"

          try:
            # Liste mit den Volumes
            liste_volumes = conn_region.get_all_volumes()
          except EC2ResponseError:
            # Wenn es nicht klappt...
            if sprache == "de":
              volumestabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
            else:
              volumestabelle = '<font color="red">An error occured</font>'
            # Wenn diese Zeile nicht da ist, kommt es später zu einem Fehler!
            laenge_liste_volumes = 0
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            if sprache == "de":
              volumestabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
            else:
              volumestabelle = '<font color="red">A timeout error occured</font>'
            # Wenn diese Zeile nicht da ist, kommt es später zu einem Fehler!
            laenge_liste_volumes = 0
          else:
            # Wenn es geklappt hat...
            # Anzahl der Volumes in der Liste
            laenge_liste_volumes = len(liste_volumes)


            if laenge_liste_volumes == 0:
              if sprache == "de":
                volumestabelle = 'Es sind keine Volumes in der Region vorhanden.'
              else:
                volumestabelle = 'No volumes exist inside this region.'
            else: 
              volumestabelle = ''
              volumestabelle = volumestabelle + '<table border="3" cellspacing="0" cellpadding="5">'
              volumestabelle = volumestabelle + '<tr>'
              volumestabelle = volumestabelle + '<th>&nbsp;&nbsp;</th>'
              volumestabelle = volumestabelle + '<th>&nbsp;&nbsp;</th>'
              volumestabelle = volumestabelle + '<th>&nbsp;</th>'
              volumestabelle = volumestabelle + '<th align="center">Volume ID</th>'
              volumestabelle = volumestabelle + '<th align="center">Snapshot ID</th>'
              if sprache == "de":
                volumestabelle = volumestabelle + '<th align="center">Gr&ouml;&szlig;e [GB]</th>'
                volumestabelle = volumestabelle + '<th align="center">Status</th>'
                volumestabelle = volumestabelle + '<th align="center">Zone</th>'
                volumestabelle = volumestabelle + '<th align="center">Datum der Erzeugung</th>'
                volumestabelle = volumestabelle + '<th align="center">Device</th>'
                volumestabelle = volumestabelle + '<th align="center">Datum des Verkn&uuml;pfung</th>'
                volumestabelle = volumestabelle + '<th align="center">Instanz ID</th>'
                volumestabelle = volumestabelle + '<th align="center">Status der Verkn&uuml;pfung</th>'
              else: # Wenn die Sprache Englisch ist...
                volumestabelle = volumestabelle + '<th align="center">Size [GB]</th>'
                volumestabelle = volumestabelle + '<th align="center">Status</th>'
                volumestabelle = volumestabelle + '<th align="center">Zone</th>'
                volumestabelle = volumestabelle + '<th align="center">Creation Date</th>'
                volumestabelle = volumestabelle + '<th align="center">Device</th>'
                volumestabelle = volumestabelle + '<th align="center">Attach Date</th>'
                volumestabelle = volumestabelle + '<th align="center">Instance ID</th>'
                volumestabelle = volumestabelle + '<th align="center">Attach Status</th>'
              volumestabelle = volumestabelle + '</tr>'
              for i in range(laenge_liste_volumes):
                  volumestabelle = volumestabelle + '<tr>'
                  volumestabelle = volumestabelle + '<td>'
                  # Nur wenn der Zustand des Volumes "available" ist, darf  man es löschen.
                  # Darum wird hier überprüft, ob der Wert von "attach_data.status" gesetzt ist.
                  # Wenn er nicht gesetzt ist, kann/darf das Volume gelöscht werden.
                  if liste_volumes[i].attach_data.status == None:
                    volumestabelle = volumestabelle + '<a href="/volumeentfernen?volume='
                    volumestabelle = volumestabelle + liste_volumes[i].id
                    if sprache == "de":
                      volumestabelle = volumestabelle + '" title="Volume l&ouml;schen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Volume l&ouml;schen"></a>'
                    else:
                      volumestabelle = volumestabelle + '" title="erase volume"><img src="bilder/delete.png" width="16" height="16" border="0" alt="erase volume"></a>'
                  # Das Volume kann/darf nicht gelöscht werden.
                  else:
                    volumestabelle = volumestabelle + '&nbsp;'
                  volumestabelle = volumestabelle + '</td>'

                  volumestabelle = volumestabelle + '<td>'
                  volumestabelle = volumestabelle + '<a href="/snapshoterzeugen?volume='
                  volumestabelle = volumestabelle + liste_volumes[i].id
                  if sprache == "de":
                    volumestabelle = volumestabelle + '" title="Snapshot erzeugen"><img src="bilder/plus.png" width="16" height="16" border="0" alt="Snapshot erzeugen"></a>'
                  else:
                    volumestabelle = volumestabelle + '" title="create snapshot"><img src="bilder/plus.png" width="16" height="16" border="0" alt="create snapshot"></a>'
                  volumestabelle = volumestabelle + '</td>'

                  if liste_volumes[i].attach_data.status == None:
                    volumestabelle = volumestabelle + '<td align="center">'
                    volumestabelle = volumestabelle + '<a href="/volumeanhaengen?volume='
                    volumestabelle = volumestabelle + liste_volumes[i].id
                    volumestabelle = volumestabelle + "&amp;zone="
                    volumestabelle = volumestabelle + str(liste_volumes[i].zone)
                    if sprache == "de":
                      volumestabelle = volumestabelle + '" title="Volume anh&auml;ngen">'
                      volumestabelle = volumestabelle + '<img src="bilder/attach.png" width="52" height="18" border="0" alt="Volume anh&auml;ngen"></a>'
                    else:
                      volumestabelle = volumestabelle + '" title="attach volume">'
                      volumestabelle = volumestabelle + '<img src="bilder/attach.png" width="52" height="18" border="0" alt="attach volume"></a>'
                  elif liste_volumes[i].attach_data.status == u'attaching':
                    volumestabelle = volumestabelle + '<td align="center">'
                    volumestabelle = volumestabelle + 'attaching'
                  elif liste_volumes[i].attach_data.status == u'deleting':
                    volumestabelle = volumestabelle + '<td align="center">'
                    volumestabelle = volumestabelle + 'deleting'
                  elif liste_volumes[i].attach_data.status == u'busy':
                    volumestabelle = volumestabelle + '<td align="center">'
                    volumestabelle = volumestabelle + 'busy'
                  elif liste_volumes[i].attach_data.status == u'attached':
                    volumestabelle = volumestabelle + '<td align="center">'
                    volumestabelle = volumestabelle + '<a href="/volumeloesen?volume='
                    volumestabelle = volumestabelle + liste_volumes[i].id
                    if sprache == "de":
                      volumestabelle = volumestabelle + '" title="Volume l&ouml;sen">'
                      volumestabelle = volumestabelle + '<img src="bilder/detach.png" width="52" height="18" border="0" alt="Detach Volume"></a>'
                    else:
                      volumestabelle = volumestabelle + '" title="detach volume">'
                      volumestabelle = volumestabelle + '<img src="bilder/detach.png" width="52" height="18" border="0" alt="detach volume"></a>'
                  else:
                    volumestabelle = volumestabelle + '<td align="center">'
                    volumestabelle = volumestabelle + '&nbsp;'
                  volumestabelle = volumestabelle + '</td>'
                  volumestabelle = volumestabelle + '<td>'
                  volumestabelle = volumestabelle + '<tt>'+str(liste_volumes[i].id)+'</tt>'
                  volumestabelle = volumestabelle + '</td>'
                  volumestabelle = volumestabelle + '<td>'
                  volumestabelle = volumestabelle + '<tt>'+str(liste_volumes[i].snapshot_id)+'</tt>'
                  volumestabelle = volumestabelle + '</td>'
                  volumestabelle = volumestabelle + '<td align="right">'
                  volumestabelle = volumestabelle + str(liste_volumes[i].size)
                  volumestabelle = volumestabelle + '</td>'
                  if liste_volumes[i].status == u'available':
                    volumestabelle = volumestabelle + '<td bgcolor="#c3ddc3" align="center">'
                    volumestabelle = volumestabelle + liste_volumes[i].status
                  elif liste_volumes[i].status == u'in-use':
                    volumestabelle = volumestabelle + '<td bgcolor="#ffffcc" align="center">'
                    volumestabelle = volumestabelle + liste_volumes[i].status
                  elif liste_volumes[i].status == u'deleting':
                    volumestabelle = volumestabelle + '<td bgcolor="#ffcc99" align="center">'
                    volumestabelle = volumestabelle + liste_volumes[i].status
                  else:
                    volumestabelle = volumestabelle + '<td align="center">'
                    volumestabelle = volumestabelle + liste_volumes[i].status
                  volumestabelle = volumestabelle + '</td>'
                  volumestabelle = volumestabelle + '<td align="center">'
                  volumestabelle = volumestabelle + str(liste_volumes[i].zone)
                  volumestabelle = volumestabelle + '</td>'
                  volumestabelle = volumestabelle + '<td>'
                  # Den ISO8601 Zeitstring umwandeln, damit es besser aussieht.
                  datum_der_erzeugung = parse(liste_volumes[i].create_time)
                  volumestabelle = volumestabelle + str(datum_der_erzeugung.strftime("%Y-%m-%d  %H:%M:%S"))
                  #volumestabelle = volumestabelle + str(datum_der_erzeugung)
                  #volumestabelle = volumestabelle + str(liste_volumes[i].create_time)
                  volumestabelle = volumestabelle + '</td>'
                  if liste_volumes[i].attach_data.device == None:
                    volumestabelle = volumestabelle + '<td>'
                    volumestabelle = volumestabelle + '&nbsp;'
                  else:
                    volumestabelle = volumestabelle + '<td align="center">'
                    volumestabelle = volumestabelle + '<tt>'+str(liste_volumes[i].attach_data.device)+'</tt>'
                  volumestabelle = volumestabelle + '</td>'
                  if liste_volumes[i].attach_data.attach_time == None:
                    volumestabelle = volumestabelle + '<td>'
                    volumestabelle = volumestabelle + '&nbsp;'
                  else:
                    volumestabelle = volumestabelle + '<td>'
                    # Den ISO8601 Zeitstring umwandeln, damit es besser aussieht.
                    datum_des_anhaengens = parse(liste_volumes[i].attach_data.attach_time)
                    volumestabelle = volumestabelle + str(datum_des_anhaengens.strftime("%Y-%m-%d  %H:%M:%S"))
                    #volumestabelle = volumestabelle + str(liste_volumes[i].attach_data.attach_time)
                  volumestabelle = volumestabelle + '</td>'
                  if liste_volumes[i].attach_data.instance_id == None:
                    volumestabelle = volumestabelle + '<td>'
                    volumestabelle = volumestabelle + '&nbsp;'
                  else:
                    volumestabelle = volumestabelle + '<td align="center">'
                    volumestabelle = volumestabelle + str(liste_volumes[i].attach_data.instance_id)
                  volumestabelle = volumestabelle + '</td>'
                  if liste_volumes[i].attach_data.status == None:
                    volumestabelle = volumestabelle + '<td>'
                    volumestabelle = volumestabelle + '&nbsp;'
                  elif liste_volumes[i].attach_data.status == u'attached':
                    volumestabelle = volumestabelle + '<td bgcolor="#c3ddc3" align="center">'
                    volumestabelle = volumestabelle + str(liste_volumes[i].attach_data.status)
                  elif liste_volumes[i].attach_data.status == u'busy':
                    volumestabelle = volumestabelle + '<td bgcolor="#ffcc99" align="center">'
                    volumestabelle = volumestabelle + str(liste_volumes[i].attach_data.status)
                  else:
                    volumestabelle = volumestabelle + '<td align="center">'
                    volumestabelle = volumestabelle + str(liste_volumes[i].attach_data.status)
                  volumestabelle = volumestabelle + '</td>'
                  volumestabelle = volumestabelle + '</tr>'
              volumestabelle = volumestabelle + '</table>'

          if laenge_liste_volumes >= 1:
            alle_volumes_loeschen_button = '<p>&nbsp;</p>\n'
            alle_volumes_loeschen_button = alle_volumes_loeschen_button + '<table border="0" cellspacing="5" cellpadding="5">\n'
            alle_volumes_loeschen_button = alle_volumes_loeschen_button + '<tr>\n'
            alle_volumes_loeschen_button = alle_volumes_loeschen_button + '<td align="center">\n'
            alle_volumes_loeschen_button = alle_volumes_loeschen_button + '<form action="/alle_volumes_loeschen" method="get">\n'
            if sprache == "de":
              alle_volumes_loeschen_button = alle_volumes_loeschen_button + '<input type="submit" value="Alle Volumes l&ouml;schen">\n'
            else:
              alle_volumes_loeschen_button = alle_volumes_loeschen_button + '<input type="submit" value="erase all volumes">\n'
            alle_volumes_loeschen_button = alle_volumes_loeschen_button + '</form>\n'
            alle_volumes_loeschen_button = alle_volumes_loeschen_button + '</td>\n'
            alle_volumes_loeschen_button = alle_volumes_loeschen_button + '</tr>\n'
            alle_volumes_loeschen_button = alle_volumes_loeschen_button + '</table>\n'
          else:
            alle_volumes_loeschen_button = '<p>&nbsp;</p>\n'

          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'volumestabelle': volumestabelle,
          'zonen_in_der_region': zonen_in_der_region,
          'input_error_message': input_error_message,
          'zonen_liste': zonen_liste,
          'alle_volumes_loeschen_button': alle_volumes_loeschen_button,
          }

          #if sprache == "de": naechse_seite = "volumes_de.html"
          #else:               naechse_seite = "volumes_en.html"
          #path = os.path.join(os.path.dirname(__file__), naechse_seite)
          path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "volumes.html")
          self.response.out.write(template.render(path,template_values))

          