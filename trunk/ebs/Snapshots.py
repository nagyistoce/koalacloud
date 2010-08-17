#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api.urlfetch import DownloadError

from library import login

from library import login
from library import aktuelle_sprache
from library import navigations_bar_funktion
from library import amazon_region
from library import zonen_liste_funktion
from library import format_error_message_green
from library import format_error_message_red

from error_messages import error_messages

from dateutil.parser import *

from boto.ec2.connection import *

class Snapshots(webapp.RequestHandler):
    def get(self):
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
          navigations_bar = navigations_bar_funktion(sprache)
          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
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
          if message in ("11", "13"):
            # wird sie hier, in der Hilfsfunktion grün formatiert
            input_error_message = format_error_message_green(input_error_message)
          # Ansonsten wird die Nachricht rot formatiert
          elif message in ("8", "12", "14"):
            input_error_message = format_error_message_red(input_error_message)
          else:
            input_error_message = ""

          try:
            # Liste mit den Snapshots
            #liste_snapshots = conn_region.get_all_snapshots(owner="amazon")
            #liste_snapshots = conn_region.get_all_snapshots(owner="self")
            liste_snapshots = conn_region.get_all_snapshots()
          except EC2ResponseError:
            # Wenn es nicht klappt...
            if sprache == "de":
              snapshotstabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
            else:
              snapshotstabelle = '<font color="red">An error occured</font>'
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            if sprache == "de":
              snapshotstabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
            else:
              snapshotstabelle = '<font color="red">A timeout error occured</font>'
          else:
            # Wenn es geklappt hat...
            # Anzahl der Snapshots in der Liste
            laenge_liste_snapshots = len(liste_snapshots)

            if laenge_liste_snapshots == 0:
              if sprache == "de":
                snapshotstabelle = 'Es sind keine Snapshots in der Region vorhanden.'
              else:
                snapshotstabelle = 'No snapshots exist inside this region.'
            else: 
              snapshotstabelle = ''
              snapshotstabelle = snapshotstabelle + '<table border="3" cellspacing="0" cellpadding="5">'
              snapshotstabelle = snapshotstabelle + '<tr>'
              snapshotstabelle = snapshotstabelle + '<th>&nbsp;&nbsp;</th>'
              snapshotstabelle = snapshotstabelle + '<th align="center">Snapshot ID</th>'
              snapshotstabelle = snapshotstabelle + '<th align="center">Volume ID</th>'
              if sprache == "de":
                snapshotstabelle = snapshotstabelle + '<th align="center">Gr&ouml;&szlig;e [GB]</th>'
                snapshotstabelle = snapshotstabelle + '<th align="center">Status</th>'
                snapshotstabelle = snapshotstabelle + '<th align="center">Besitzer</th>'
                snapshotstabelle = snapshotstabelle + '<th align="center">Beschreibung</th>'
                snapshotstabelle = snapshotstabelle + '<th align="center">Startzeitpunkt</th>'
                snapshotstabelle = snapshotstabelle + '<th align="center">Fortschritt</th>'
              else: # Wenn die Sprache Englisch ist...
                snapshotstabelle = snapshotstabelle + '<th align="center">Size [GB]</th>'
                snapshotstabelle = snapshotstabelle + '<th align="center">Status</th>'
                snapshotstabelle = snapshotstabelle + '<th align="center">Owner</th>'
                snapshotstabelle = snapshotstabelle + '<th align="center">Description</th>'
                snapshotstabelle = snapshotstabelle + '<th align="center">Start Time</th>'
                snapshotstabelle = snapshotstabelle + '<th align="center">Progress</th>'
              snapshotstabelle = snapshotstabelle + '</tr>'
              for i in range(laenge_liste_snapshots):
                  snapshotstabelle = snapshotstabelle + '<tr>'
                  snapshotstabelle = snapshotstabelle + '<td>'
                  snapshotstabelle = snapshotstabelle + '<a href="/snapshotsentfernen?snapshot='
                  snapshotstabelle = snapshotstabelle + liste_snapshots[i].id
                  if sprache == "de":
                    snapshotstabelle = snapshotstabelle + '" title="Snapshot l&ouml;schen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Snapshot l&ouml;schen"></a>'
                  else:
                    snapshotstabelle = snapshotstabelle + '" title="erase snapshot"><img src="bilder/delete.png" width="16" height="16" border="0" alt="snapshot volume"></a>'
                  snapshotstabelle = snapshotstabelle + '</td>'
                  snapshotstabelle = snapshotstabelle + '<td>'
                  snapshotstabelle = snapshotstabelle + '<tt>'
                  snapshotstabelle = snapshotstabelle + liste_snapshots[i].id
                  snapshotstabelle = snapshotstabelle + '</tt>'
                  snapshotstabelle = snapshotstabelle + '</td>'
                  snapshotstabelle = snapshotstabelle + '<td>'
                  snapshotstabelle = snapshotstabelle + '<tt>'
                  snapshotstabelle = snapshotstabelle + liste_snapshots[i].volume_id
                  snapshotstabelle = snapshotstabelle + '</tt>'
                  snapshotstabelle = snapshotstabelle + '</td>'
                  snapshotstabelle = snapshotstabelle + '<td align="right">'
                  snapshotstabelle = snapshotstabelle + str(liste_snapshots[i].volume_size)
                  snapshotstabelle = snapshotstabelle + '</td>'
                  if liste_snapshots[i].status == u'completed':
                    snapshotstabelle = snapshotstabelle + '<td bgcolor="#c3ddc3" align="center">'
                    snapshotstabelle = snapshotstabelle + liste_snapshots[i].status
                  elif liste_snapshots[i].status == u'pending':
                    snapshotstabelle = snapshotstabelle + '<td bgcolor="#ffffcc" align="center">'
                    snapshotstabelle = snapshotstabelle + liste_snapshots[i].status
                  elif liste_snapshots[i].status == u'deleting':
                    snapshotstabelle = snapshotstabelle + '<td bgcolor="#ffcc99" align="center">'
                    snapshotstabelle = snapshotstabelle + liste_snapshots[i].status
                  else:
                    snapshotstabelle = snapshotstabelle + '<td align="center">'
                    snapshotstabelle = snapshotstabelle + liste_snapshots[i].status
                  snapshotstabelle = snapshotstabelle + '</td>'
                  snapshotstabelle = snapshotstabelle + '<td align="left">'
                  snapshotstabelle = snapshotstabelle + str(liste_snapshots[i].owner_id)
                  snapshotstabelle = snapshotstabelle + '</td>'
                  snapshotstabelle = snapshotstabelle + '<td align="left">'
                  snapshotstabelle = snapshotstabelle + str(liste_snapshots[i].description)
                  snapshotstabelle = snapshotstabelle + '</td>'
                  snapshotstabelle = snapshotstabelle + '<td>'
                  # Den ISO8601 Zeitstring umwandeln, damit es besser aussieht.
                  datum_der_erzeugung = parse(liste_snapshots[i].start_time)
                  snapshotstabelle = snapshotstabelle + str(datum_der_erzeugung.strftime("%Y-%m-%d  %H:%M:%S"))
                  snapshotstabelle = snapshotstabelle + '</td>'
                  snapshotstabelle = snapshotstabelle + '<td align="right">'
                  snapshotstabelle = snapshotstabelle + str(liste_snapshots[i].progress)
                  snapshotstabelle = snapshotstabelle + '</td>'
                  snapshotstabelle = snapshotstabelle + '</tr>'
              snapshotstabelle = snapshotstabelle + '</table>'

          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'snapshotstabelle': snapshotstabelle,
          'zonen_liste': zonen_liste,
          'input_error_message': input_error_message,
          }

          #if sprache == "de": naechse_seite = "snapshots_de.html"
          #else:               naechse_seite = "snapshots_en.html"
          #path = os.path.join(os.path.dirname(__file__), naechse_seite)
          path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "snapshots.html")
          self.response.out.write(template.render(path,template_values))

          