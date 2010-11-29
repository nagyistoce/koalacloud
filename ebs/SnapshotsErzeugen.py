#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template

from library import login

from library import login
from library import aktuelle_sprache
from library import navigations_bar_funktion
from library import amazon_region
from library import zonen_liste_funktion
from library import format_error_message_green
from library import format_error_message_red

class SnapshotsErzeugen(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Name des zu anzuhängenden Volumes holen
        volume = self.request.get('volume')
        # Name der Zone holen
        volume_zone  = self.request.get('zone')
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
          navigations_bar = navigations_bar_funktion(sprache,mobile)

          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache,mobile)

          if mobile == "true":
              tabelle_snapshot = ''
              tabelle_snapshot += '<form action="/snapshoterzeugendefinitiv" method="post" accept-charset="utf-8"> \n'
              tabelle_snapshot += '<input type="hidden" name="mobile" value="'+mobile+'">'
              tabelle_snapshot += '<input type="hidden" name="volume" value="'+volume+'"> \n'
              tabelle_snapshot += '<table border="0" cellspacing="0" cellpadding="5">'
              tabelle_snapshot += '<tr>'
              tabelle_snapshot += '<td align="left"><B>Volume: </B>'+volume+'</td>'
              tabelle_snapshot += '</tr>'
              tabelle_snapshot += '<tr>'
              if sprache == "de":
                tabelle_snapshot += '<td align="left"><B>Beschreibung:</B></td>'
              else:
                tabelle_snapshot += '<td align="left"><B>Description:</B></td>'
              tabelle_snapshot += '</tr>'
              tabelle_snapshot += '<tr>'
              tabelle_snapshot += '<td><input name="beschreibung" type="text" size="40" maxlength="40"></td>\n'              
              tabelle_snapshot += '</tr>'
              tabelle_snapshot += '<tr>'
              if sprache == "de":
                tabelle_snapshot += '<td><input type="submit" value="Snapshot erzeugen"></td> \n'
              else:
                tabelle_snapshot += '<td><input type="submit" value="create snapshot"></td> \n'
              tabelle_snapshot += '</tr>'
              tabelle_snapshot += '</table>'
              tabelle_snapshot += '</form>'
          else:
              tabelle_snapshot = ''
              tabelle_snapshot += '<form action="/snapshoterzeugendefinitiv" method="post" accept-charset="utf-8"> \n'
              tabelle_snapshot += '<input type="hidden" name="mobile" value="'+mobile+'">'
              tabelle_snapshot += '<input type="hidden" name="volume" value="'+volume+'"> \n'
              tabelle_snapshot += '<table border="0" cellspacing="0" cellpadding="5">'
              tabelle_snapshot += '<tr>'
              tabelle_snapshot += '<td align="right"><B>Volume:</B></td>'
              tabelle_snapshot += '<td>'+volume+'</td>'
              tabelle_snapshot += '</tr>'
              tabelle_snapshot += '<tr>'
              if sprache == "de":
                tabelle_snapshot += '<td align="right"><B>Beschreibung:</B></td>'
              else:
                tabelle_snapshot += '<td align="right"><B>Description:</B></td>'
              tabelle_snapshot += '<td><input name="beschreibung" type="text" size="80" maxlength="80"></td>\n'
              tabelle_snapshot += '</tr>'
              tabelle_snapshot += '</table>'
              tabelle_snapshot += '<p>&nbsp;</p> \n'
              if sprache == "de":
                tabelle_snapshot += '<input type="submit" value="Snapshot erzeugen"> \n'
              else:
                tabelle_snapshot += '<input type="submit" value="create snapshot"> \n'
              tabelle_snapshot += '</form>'


          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'zonen_liste': zonen_liste,
          'tabelle_snapshot': tabelle_snapshot,
          'mobile': mobile,
          }

          if mobile == "true":
              path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "snapshot_erzeugen.html")
          else:
              path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "snapshot_erzeugen.html")
          self.response.out.write(template.render(path,template_values))
