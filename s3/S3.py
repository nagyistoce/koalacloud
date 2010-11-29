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
from library import logins3
from library import aws_access_key_erhalten
from library import aws_secret_access_key_erhalten


from dateutil.parser import *

from error_messages import error_messages

class S3(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        # self.response.out.write('posted!')
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
          self.redirect('/')
        # Eventuell vorhande Fehlermeldung holen
        message = self.request.get('message')

        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if not results:
          self.redirect('/')
        else:
          # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache,mobile)

          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache,mobile)

          if sprache != "de":
            sprache = "en"

          input_error_message = error_messages.get(message, {}).get(sprache)

          # Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
          if input_error_message == None:
            input_error_message = ""

          # Wenn die Nachricht grün formatiert werden soll...
          if message in ("105", "110"):
            # wird sie hier, in der Hilfsfunktion grün formatiert
            input_error_message = format_error_message_green(input_error_message)
          # Ansonsten wird die Nachricht rot formatiert
          elif message in ("92", "106", "107", "108", "109"):
            input_error_message = format_error_message_red(input_error_message)
          else:
            input_error_message = ""

          # Mit S3 verbinden
          conn_s3 = logins3(username)

          try:
            # Liste der Buckets
            liste_buckets = conn_s3.get_all_buckets()
          except:
            # Wenn es nicht klappt...
            if sprache == "de":
              bucketstabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
            else:
              bucketstabelle = '<font color="red">An error occured</font>'
          else:
            # Wenn es geklappt hat...
            # Anzahl der Elemente in der Liste
            laenge_liste_buckets = len(liste_buckets)

            if laenge_liste_buckets == 0:
              if sprache == "de":
                bucketstabelle = 'Es sind keine Buckets in der Region vorhanden.'
              else:
                bucketstabelle = 'Still no buckets exist inside this region.'
            else:
              bucketstabelle = ''
              bucketstabelle = bucketstabelle + '<table border="3" cellspacing="0" cellpadding="5">'
              bucketstabelle = bucketstabelle + '<tr>'
              bucketstabelle = bucketstabelle + '<th>&nbsp;</th>'
              bucketstabelle = bucketstabelle + '<th>&nbsp;</th>'
              bucketstabelle = bucketstabelle + '<th align="left">Buckets</th>'
              if sprache == "de":
                bucketstabelle = bucketstabelle + '<th>Reine S3-Darstellung</th>'
                bucketstabelle = bucketstabelle + '<th>Komfort-Darstellung</th>'
              else:
                bucketstabelle = bucketstabelle + '<th>Pure S3</th>'
                bucketstabelle = bucketstabelle + '<th>S3 with more comfort</th>'
              bucketstabelle = bucketstabelle + '</tr>'
              for i in range(laenge_liste_buckets):
                  bucketstabelle = bucketstabelle + '<tr>'
                  bucketstabelle = bucketstabelle + '<td>'
                  bucketstabelle = bucketstabelle + '<a href="/bucketentfernen?bucket='
                  bucketstabelle = bucketstabelle + str(liste_buckets[i].name)
                  if sprache == "de":
                    bucketstabelle = bucketstabelle + '" title="Bucket l&ouml;schen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Bucket l&ouml;schen"></a>'
                  else:
                    bucketstabelle = bucketstabelle + '" title="erase bucket"><img src="bilder/delete.png" width="16" height="16" border="0" alt="erase bucket"></a>'
                  bucketstabelle = bucketstabelle + '</td>'
                  bucketstabelle = bucketstabelle + '<td>'
                  bucketstabelle = bucketstabelle + '<img src="bilder/folder.png" width="16" height="16" border="0" alt="Bucket">'
                  bucketstabelle = bucketstabelle + '</td>'
                  bucketstabelle = bucketstabelle + '<td>'
                  bucketstabelle = bucketstabelle + str(liste_buckets[i].name)
                  bucketstabelle = bucketstabelle + '</td>'
                  bucketstabelle = bucketstabelle + '<td align="center">'
                  bucketstabelle = bucketstabelle + '<a href="/bucket_inhalt_pure?bucket='
                  bucketstabelle = bucketstabelle + str(liste_buckets[i].name)
                  if sprache == "de":
                    bucketstabelle = bucketstabelle + '" title="Bucket einsehen (reine S3-Darstellung)"><img src="bilder/right.png" width="16" height="16" border="0" alt="Bucket"></a>'
                  else:
                    bucketstabelle = bucketstabelle + '" title="List content of this bucket (pure S3)"><img src="bilder/right.png" width="16" height="16" border="0" alt="Bucket"></a>'
                  bucketstabelle = bucketstabelle + '</td>'
                  bucketstabelle = bucketstabelle + '<td align="center">'
                  bucketstabelle = bucketstabelle + '<a href="/bucket_inhalt?bucket='
                  bucketstabelle = bucketstabelle + str(liste_buckets[i].name)
                  if sprache == "de":
                    bucketstabelle = bucketstabelle + '" title="Bucket einsehen (Komfort-Darstellung)"><img src="bilder/right.png" width="16" height="16" border="0" alt="Bucket"></a>'
                  else:
                    bucketstabelle = bucketstabelle + '" title="List content of this bucket (S3 with more comfort)"><img src="bilder/right.png" width="16" height="16" border="0" alt="Bucket"></a>'
                  bucketstabelle = bucketstabelle + '</td>'
                  bucketstabelle = bucketstabelle + '</tr>'
              bucketstabelle = bucketstabelle + '</table>'

          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'zonen_liste': zonen_liste,
          'bucketstabelle': bucketstabelle,
          'input_error_message': input_error_message,
          }

          #if sprache == "de": naechse_seite = "s3_de.html"
          #else:               naechse_seite = "s3_en.html"
          #path = os.path.join(os.path.dirname(__file__), naechse_seite)
          path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "s3.html")
          self.response.out.write(template.render(path,template_values))

