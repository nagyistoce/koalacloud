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

class SecurityGroups(webapp.RequestHandler):
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
          if message in ("40", "48"):
            # wird sie hier, in der Hilfsfunktion grün formatiert
            input_error_message = format_error_message_green(input_error_message)
          # Ansonsten wird die Nachricht rot formatiert
          elif message in ("8", "41", "42", "43", "44", "45", "46", "47", "49"):
            input_error_message = format_error_message_red(input_error_message)
          else:
            input_error_message = ""

          try:
            # Liste mit den Security Groups
            liste_security_groups = conn_region.get_all_security_groups()
          except EC2ResponseError:
            # Wenn es nicht klappt...
            if sprache == "de":
              gruppentabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
            else:
              gruppentabelle = '<font color="red">An error occured</font>'
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            if sprache == "de":
              gruppentabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
            else:
              gruppentabelle = '<font color="red">A timeout error occured</font>'
          else:
            # Wenn es geklappt hat...
            # Anzahl der Elemente in der Liste
            laenge_liste_security_groups = len(liste_security_groups)

            if laenge_liste_security_groups == 0:
              gruppentabelle = 'Es sind keine Sicherheitsgruppen in der Zone vorhanden.'
            else:
              gruppentabelle = ''
              gruppentabelle = gruppentabelle + '<table border="3" cellspacing="0" cellpadding="5">'
              gruppentabelle = gruppentabelle + '<tr>'
              gruppentabelle = gruppentabelle + '<th>&nbsp;</th>'
              if sprache == "de":
                gruppentabelle = gruppentabelle + '<th align="center">Besitzer</th>'
              else:
                gruppentabelle = gruppentabelle + '<th align="center">Owner</th>'
              gruppentabelle = gruppentabelle + '<th align="center">Name</th>'
              if sprache == "de":
                gruppentabelle = gruppentabelle + '<th align="center">Beschreibung</th>'
              else:
                gruppentabelle = gruppentabelle + '<th align="center">Description</th>'
              gruppentabelle = gruppentabelle + '<th>&nbsp;</th>'
              gruppentabelle = gruppentabelle + '</tr>'
              for i in range(laenge_liste_security_groups):
                  gruppentabelle = gruppentabelle + '<tr>'
                  gruppentabelle = gruppentabelle + '<td>'
                  gruppentabelle = gruppentabelle + '<a href="/gruppenentfernen?gruppe='
                  gruppentabelle = gruppentabelle + liste_security_groups[i].name
                  if sprache == "de":
                    gruppentabelle = gruppentabelle + '" title=" Sicherheitsgruppe l&ouml;schen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Security Gruppe l&ouml;schen"></a>'
                  else:
                    gruppentabelle = gruppentabelle + '" title="erase security group"><img src="bilder/delete.png" width="16" height="16" border="0" alt="erase security group"></a>'
                  gruppentabelle = gruppentabelle + '</td>'
                  gruppentabelle = gruppentabelle + '<td>'
                  gruppentabelle = gruppentabelle + liste_security_groups[i].owner_id
                  gruppentabelle = gruppentabelle + '</td>'
                  gruppentabelle = gruppentabelle + '<td>'
                  gruppentabelle = gruppentabelle + liste_security_groups[i].name
                  gruppentabelle = gruppentabelle + '</td>'
                  gruppentabelle = gruppentabelle + '<td>'
                  gruppentabelle = gruppentabelle + liste_security_groups[i].description
                  gruppentabelle = gruppentabelle + '</td>'
                  gruppentabelle = gruppentabelle + '<td>'
                  gruppentabelle = gruppentabelle + '<a href="/gruppenaendern?gruppe='
                  gruppentabelle = gruppentabelle + liste_security_groups[i].name
                  if sprache == "de":
                    gruppentabelle = gruppentabelle + '" title="Regeln einsehen/&auml;ndern"><img src="bilder/einstellungen.png" width="58" height="18" border="0" alt="Regeln einsehen/&auml;ndern"></a>'
                  else:
                    gruppentabelle = gruppentabelle + '" title="check/alter rules"><img src="bilder/einstellungen.png" width="58" height="18" border="0" alt="check/alter rules"></a>'
                  gruppentabelle = gruppentabelle + '</td>'
                  gruppentabelle = gruppentabelle + '</tr>'
              gruppentabelle = gruppentabelle + '</table>'

          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'securitygroupsliste': gruppentabelle,
          'input_error_message': input_error_message,
          'zonen_liste': zonen_liste,
          }

          #if sprache == "de": naechse_seite = "securitygroups_de.html"
          #else:               naechse_seite = "securitygroups_en.html"
          #path = os.path.join(os.path.dirname(__file__), naechse_seite)
          path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "securitygroups.html")
          self.response.out.write(template.render(path,template_values))

          