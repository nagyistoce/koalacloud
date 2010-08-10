#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

# Copyright 2009,2010 Christian Baun

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import decimal
import wsgiref.handlers
import os
import sys
import cgi
import time
import re

from ebs.VolumesLoesen import *
from ebs.VolumesEntfernen import *
from ebs.AlleVolumesLoeschenDefinitiv import *
from ebs.VolumeDefinitivAnhaengen import *
from ebs.VolumesErzeugen import *
from ebs.VolumesAnhaengen import *
from ebs.Volumes import *
from ebs.AlleVolumesLoeschenFrage import *
from ebs.Snapshots import *
from ebs.SnapshotsErzeugen import *
from ebs.SnapshotsEntfernen import *
from ebs.SnapshotsErzeugenDefinitiv import *

from ec2.AlleInstanzenBeenden import *
from ec2.Zonen import *
from ec2.Release_IP import *
from ec2.Allocate_IP import *
from ec2.Disassociate_IP import *
from ec2.IP_Definitiv_Anhaengen import *
from ec2.Associate_IP import *
from ec2.Elastic_IPs import *
from ec2.KeyEntfernen import *
from ec2.GruppeEntfernen import *
from ec2.InstanzAnlegen import *
from ec2.InstanzReboot import *
from ec2.InstanzBeenden import *

from elb.LoadBalancer import *
from elb.LoadBalancer_Instanz_Zuordnen import *
from elb.LoadBalancer_Instanz_Entfernen import *
from elb.LoadBalancer_Zone_Entfernen import *
from elb.LoadBalancer_Zone_Zuordnen import *
from elb.LoadBalancer_Aendern import *
from elb.DeleteLoadBalancer import *
from elb.CreateLoadBalancer import *
from elb.CreateLoadBalancerWirklich import *

from library import login
from library import xor_crypt_string
from library import aktuelle_sprache
from library import navigations_bar_funktion
from library import amazon_region
from library import zonen_liste_funktion
from library import format_error_message_green
from library import format_error_message_red
from library import loginelb

from error_messages import error_messages

from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api.urlfetch import DownloadError
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from boto.ec2.connection import *
from boto.ec2 import *
from boto.s3.connection import *
from boto.s3 import *
from boto.ec2.elb import ELBConnection
from dateutil.parser import *
from dateutil.tz import *
from datetime import *
# für die Verschlüsselung
# this is needed for the encyption
from itertools import izip, cycle
import hmac, sha
# für die Verschlüsselung
# this is needed for the encyption
import base64


class KoalaCloudDatenbank(db.Model):
    user = db.UserProperty(required=True)
    #input = db.IntegerProperty()
    regionname = db.StringProperty(required=True)
    endpointurl = db.StringProperty()
    port = db.StringProperty()
    eucalyptusname = db.StringProperty()
    zugangstyp = db.StringProperty()  # Amazon, Eucalyptus, Nimbus...
    accesskey = db.StringProperty(required=True)
    secretaccesskey = db.StringProperty(required=True)
    date = db.DateTimeProperty(auto_now_add=True)

class KoalaCloudDatenbankAktiveZone(db.Model):
    user = db.UserProperty(required=True)
    aktivezone = db.StringProperty()
    zugangstyp = db.StringProperty()  # Amazon, Eucalyptus, Nimbus...

class KoalaCloudDatenbankSprache(db.Model):
    user = db.UserProperty(required=True)
    sprache = db.StringProperty()

class KoalaCloudDatenbankFavouritenAMIs(db.Model):
    user = db.UserProperty(required=True)
    zone = db.StringProperty(required=True)
    ami = db.StringProperty(required=True)



class MainPage(webapp.RequestHandler):
    def get(self):
        # Den Usernamen erfahren
        username = users.get_current_user()

        if users.get_current_user():
            # Nachsehen, ob eine Region/Zone ausgewählte wurde
            # See if a region/zone has already been chosen
            aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
            results = aktivezone.fetch(100)

            if not results:
              regionname = 'keine'
              zone_amazon = ""
            else:
              conn_region, regionname = login(username)
              zone_amazon = amazon_region(username)

            # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
            # See if a language has already been chosen 
            sprache = aktuelle_sprache(username)
            navigations_bar = navigations_bar_funktion(sprache)

            url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
            url_linktext = 'Logout'

        else:
            sprache = "en"
            navigations_bar = navigations_bar_funktion(sprache)
            url = users.create_login_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
            url_linktext = 'Login'
            regionname = 'keine'
            zone_amazon = ""

        zonen_liste = zonen_liste_funktion(username,sprache)

        template_values = {
        'navigations_bar': navigations_bar,
        'zone': regionname,
        'zone_amazon': zone_amazon,
        'url': url,
        'url_linktext': url_linktext,
        'zonen_liste': zonen_liste,
        }

        #if sprache == "en":   naechse_seite = "start_en.html"
        #elif sprache == "de": naechse_seite = "start_de.html"
        #else:                 naechse_seite = "start_en.html"
        #path = os.path.join(os.path.dirname(__file__), naechse_seite)
        path = os.path.join(os.path.dirname(__file__), "templates", sprache, "start.html")
        self.response.out.write(template.render(path,template_values))


class Regionen(webapp.RequestHandler):
    def get(self):
        message = self.request.get('message')
        neuerzugang = self.request.get('neuerzugang')
        # Den Usernamen erfahren
        # Get the username
        username = users.get_current_user()
        # self.response.out.write('posted!')

        # Wir müssen das so machen, weil wir sonst nicht weiterkommen,
        # wenn ein Benutzer noch keinen Zugang eingerichtet hat.
        if users.get_current_user():
            sprache = aktuelle_sprache(username)
            navigations_bar = navigations_bar_funktion(sprache)
            # Nachsehen, ob eine Region/Zone ausgewählte wurde
            aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
            results = aktivezone.fetch(100)

            if not results:
              regionname = 'keine'
              zone_amazon = ""
            else:
              conn_region, regionname = login(username)
              zone_amazon = amazon_region(username)

            url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
            url_linktext = 'Logout'

            zonen_liste = zonen_liste_funktion(username,sprache)

            if sprache != "de":
              sprache = "en"

            input_error_message = error_messages.get(message, {}).get(sprache)

            # Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
            if input_error_message == None:
              input_error_message = ""

            # Wenn die Nachricht grün formatiert werden soll...
            if message in ("89", "90", "91", "92", "93", "94", "95", "96", "97", "98", "99"):
              # wird sie hier, in der Hilfsfunktion rot formatiert
              input_error_message = format_error_message_red(input_error_message)
            else:
              input_error_message = ""


            # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
            testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db", username_db=username)
            # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
            # Wie viele Einträge des Benutzers sind schon vorhanden?
            anzahl = testen.count()     
            # Alle Einträge des Benutzers holen?
            results = testen.fetch(100) 

            if anzahl:
              # wenn schon Einträge für den Benutzer vorhanden sind...
              tabelle_logins = ''
              tabelle_logins = tabelle_logins + '<table border="3" cellspacing="0" cellpadding="5">'
              tabelle_logins = tabelle_logins + '<tr>'
              tabelle_logins = tabelle_logins + '<th>&nbsp;</th>'
              if sprache == "de":
                tabelle_logins = tabelle_logins + '<th align="center">Art der Region</th>'
              else:
                tabelle_logins = tabelle_logins + '<th align="center">Sort of Region</th>'
              tabelle_logins = tabelle_logins + '<th align="center">Endpoint URL</th>'
              tabelle_logins = tabelle_logins + '<th align="center">Access Key</th>'
              if sprache == "de":
                tabelle_logins = tabelle_logins + '<th align="center">Name/Beschreibung</th>'
              else:
                tabelle_logins = tabelle_logins + '<th align="center">Name/Description</th>'
              tabelle_logins = tabelle_logins + '</tr>'
              for test in results:
                tabelle_logins = tabelle_logins + '<tr>'
                tabelle_logins = tabelle_logins + '<td>'
                tabelle_logins = tabelle_logins + '<a href="/zugangentfernen?region='
                tabelle_logins = tabelle_logins + str(test.regionname)
                tabelle_logins = tabelle_logins + '&amp;endpointurl='
                tabelle_logins = tabelle_logins + str(test.endpointurl)
                tabelle_logins = tabelle_logins + '&amp;accesskey='
                tabelle_logins = tabelle_logins + str(test.accesskey)
                tabelle_logins = tabelle_logins + '"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Zugang l&ouml;schen"></a>'
                tabelle_logins = tabelle_logins + '</td>'
                tabelle_logins = tabelle_logins + '<td align="center">'
                if test.eucalyptusname == "Amazon":
                  tabelle_logins = tabelle_logins + 'Amazon AWS'
                elif test.regionname == "nimbus":
                  tabelle_logins = tabelle_logins + 'Nimbus'
                elif test.regionname == "eucalyptus":
                  tabelle_logins = tabelle_logins + 'Eucalyptus'
                else:
                  tabelle_logins = tabelle_logins + '&nbsp;'
                tabelle_logins = tabelle_logins + '</td>'
                tabelle_logins = tabelle_logins + '<td align="center">'
                tabelle_logins = tabelle_logins + str(test.endpointurl)
                tabelle_logins = tabelle_logins + '</td>'
                tabelle_logins = tabelle_logins + '<td align="left">'
                tabelle_logins = tabelle_logins + str(test.accesskey)
                tabelle_logins = tabelle_logins + '</td>'
                tabelle_logins = tabelle_logins + '<td align="left">'
                tabelle_logins = tabelle_logins + test.eucalyptusname
                tabelle_logins = tabelle_logins + '</td>'
                tabelle_logins = tabelle_logins + '</tr>'
              tabelle_logins = tabelle_logins + '</table>'
            else:
              # wenn noch keine Einträge für den Benutzer vorhanden sind...
              if sprache == "de":
                tabelle_logins = 'Sie haben noch keine Login-Daten eingegeben'
              else:
                tabelle_logins = 'still no credentials exist'
              tabelle_logins = tabelle_logins + '<p>&nbsp;</p>'

            if neuerzugang == "eucalyptus":
              eingabefelder = '<p>&nbsp;</p>'
              eingabefelder = eingabefelder + '<form action="/zugangeinrichten" method="post" accept-charset="utf-8">'
              eingabefelder = eingabefelder + '<input type="hidden" name="typ" value="eucalyptus">'
              eingabefelder = eingabefelder + '<table border="0" cellspacing="5" cellpadding="5">'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '  <td></td>'
              if sprache == "de":
                eingabefelder = eingabefelder + '    <td><font color="green">Der Name ist nur zur Unterscheidung</font></td>'
              else:
                eingabefelder = eingabefelder + '    <td><font color="green">Choose one you like</font></td>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '    <td align="right">Name:</td>'
              eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="40" name="nameregion" value="">'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '  <td></td>'
              if sprache == "de":
                eingabefelder = eingabefelder + '    <td><font color="green">Nur die IP oder DNS ohne <tt>/services/Eucalyptus</tt></font></td>'
              else:
                eingabefelder = eingabefelder + '    <td><font color="green">Just the IP or DNS without <tt>/services/Eucalyptus</tt></font></td>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '    <td align="right">Endpoint URL:</td>'
              eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="40" name="endpointurl" value="">'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '  <td></td>'
              if sprache == "de":
                eingabefelder = eingabefelder + '    <td><font color="green">Google App Engine akzeptiert nur diese Ports</font></td>'
              else:
                eingabefelder = eingabefelder + '    <td><font color="green">Google App Engine accepts only these ports</font></td>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '    <td align="right">Port:</td>'
              #eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="5" maxlength="5" name="port" value=""></td>'
              eingabefelder = eingabefelder + '    <td colspan="2">'
              eingabefelder = eingabefelder + '      <select name="port" size="1">'
              eingabefelder = eingabefelder + '        <option>80</option>'
              eingabefelder = eingabefelder + '        <option>443</option>'
              eingabefelder = eingabefelder + '        <option>4443</option>'
              eingabefelder = eingabefelder + '        <option>8080</option>'
              eingabefelder = eingabefelder + '        <option>8081</option>'
              eingabefelder = eingabefelder + '        <option>8082</option>'
              eingabefelder = eingabefelder + '        <option>8083</option>'
              eingabefelder = eingabefelder + '        <option>8084</option>'
              eingabefelder = eingabefelder + '        <option>8085</option>'
              eingabefelder = eingabefelder + '        <option>8086</option>'
              eingabefelder = eingabefelder + '        <option>8087</option>'
              eingabefelder = eingabefelder + '        <option>8088</option>'
              eingabefelder = eingabefelder + '        <option>8089</option>'
              eingabefelder = eingabefelder + '        <option selected="selected">8188</option>'
#              eingabefelder = eingabefelder + '        <option>8442</option>' ####### weg damit!!! ###
              eingabefelder = eingabefelder + '        <option>8444</option>'
              eingabefelder = eingabefelder + '        <option>8990</option>'
              eingabefelder = eingabefelder + '      </select>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '    <td align="right">Access Key:</td>'
              eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="40" name="accesskey" value=""></td>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '    <td align="right">Secret Access Key:</td>'
              eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="40" name="secretaccesskey" value=""></td>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '    <td>&nbsp;</td>'
              if sprache == "de":
                eingabefelder = eingabefelder + '    <td align="center"><input type="submit" value="Zugang einrichten"></td>'
                eingabefelder = eingabefelder + '    <td align="center"><input type="reset" value="L&ouml;schen"></td>'
              else:
                eingabefelder = eingabefelder + '    <td align="center"><input type="submit" value="send"></td>'
                eingabefelder = eingabefelder + '    <td align="center"><input type="reset" value="erase"></td>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '</table>'
              eingabefelder = eingabefelder + '</form>'
            elif neuerzugang == "ec2":
              eingabefelder = '<p>&nbsp;</p>'
              eingabefelder = eingabefelder + '<form action="/zugangeinrichten" method="post" accept-charset="utf-8">'
              eingabefelder = eingabefelder + '<input type="hidden" name="typ" value="ec2">'
              eingabefelder = eingabefelder + '<table border="0" cellspacing="5" cellpadding="5">'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '    <td align="right">Access Key:</td>'
              eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="40" name="accesskey" value=""></td>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '    <td align="right">Secret Access Key:</td>'
              eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="40" name="secretaccesskey" value=""></td>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '    <td>&nbsp;</td>'
              if sprache == "de":
                eingabefelder = eingabefelder + '    <td align="center"><input type="submit" value="Zugang einrichten"></td>'
                eingabefelder = eingabefelder + '    <td align="center"><input type="reset" value="L&ouml;schen"></td>'
              else:
                eingabefelder = eingabefelder + '    <td align="center"><input type="submit" value="send"></td>'
                eingabefelder = eingabefelder + '    <td align="center"><input type="reset" value="erase"></td>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '</table>'
              eingabefelder = eingabefelder + '</form>'
            elif neuerzugang == "nimbus":
              eingabefelder = '<p>&nbsp;</p>'
              eingabefelder = eingabefelder + '<form action="/zugangeinrichten" method="post" accept-charset="utf-8">'
              eingabefelder = eingabefelder + '<input type="hidden" name="typ" value="nimbus">'
              eingabefelder = eingabefelder + '<table border="0" cellspacing="5" cellpadding="5">'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '  <td></td>'
              if sprache == "de":
                eingabefelder = eingabefelder + '    <td><font color="green">Der Name ist nur zur Unterscheidung</font></td>'
              else:
                eingabefelder = eingabefelder + '    <td><font color="green">Choose one you like</font></td>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '    <td align="right">Name:</td>'
              eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="40" name="nameregion" value=""></td>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '  <td></td>'
              if sprache == "de":
                eingabefelder = eingabefelder + '    <td><font color="green">Nur die IP oder DNS</font></td>'
              else:
                eingabefelder = eingabefelder + '    <td><font color="green">Just the IP or DNS</font></td>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '    <td align="right">Endpoint URL:</td>'
              eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="40" name="endpointurl" value=""></td>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '  <td></td>'
              if sprache == "de":
                eingabefelder = eingabefelder + '    <td><font color="green">Google App Engine akzeptiert nur diese Ports</font></td>'
              else:
                eingabefelder = eingabefelder + '    <td><font color="green">Google App Engine accepts only these ports</font></td>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '    <td align="right">Port:</td>'
              #eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="5" maxlength="5" name="port" value=""></td>'
              eingabefelder = eingabefelder + '    <td colspan="2">'
              eingabefelder = eingabefelder + '      <select name="port" size="1">'
              eingabefelder = eingabefelder + '        <option>80</option>'
              eingabefelder = eingabefelder + '        <option>443</option>'
              eingabefelder = eingabefelder + '        <option>4443</option>'
              eingabefelder = eingabefelder + '        <option>8080</option>'
              eingabefelder = eingabefelder + '        <option>8081</option>'
              eingabefelder = eingabefelder + '        <option>8082</option>'
              eingabefelder = eingabefelder + '        <option>8083</option>'
              eingabefelder = eingabefelder + '        <option>8084</option>'
              eingabefelder = eingabefelder + '        <option>8085</option>'
              eingabefelder = eingabefelder + '        <option>8086</option>'
              eingabefelder = eingabefelder + '        <option>8087</option>'
              eingabefelder = eingabefelder + '        <option>8088</option>'
              eingabefelder = eingabefelder + '        <option>8089</option>'
              eingabefelder = eingabefelder + '        <option selected="selected">8188</option>'
              #eingabefelder = eingabefelder + '        <option>8442</option>' ####### weg damit!!! ###
              eingabefelder = eingabefelder + '        <option>8444</option>'
              eingabefelder = eingabefelder + '        <option>8990</option>'
              eingabefelder = eingabefelder + '      </select>'
              eingabefelder = eingabefelder + '    </td>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '    <td align="right">Access Key:</td>'
              eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="40" name="accesskey" value=""></td>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '    <td align="right">Secret Access Key:</td>'
              eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="40" name="secretaccesskey" value=""></td>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '  <tr>'
              eingabefelder = eingabefelder + '    <td>&nbsp;</td>'
              if sprache == "de":
                eingabefelder = eingabefelder + '    <td align="center"><input type="submit" value="Zugang einrichten"></td>'
                eingabefelder = eingabefelder + '    <td align="center"><input type="reset" value="L&ouml;schen"></td>'
              else:
                eingabefelder = eingabefelder + '    <td align="center"><input type="submit" value="send"></td>'
                eingabefelder = eingabefelder + '    <td align="center"><input type="reset" value="erase"></td>'
              eingabefelder = eingabefelder + '  </tr>'
              eingabefelder = eingabefelder + '</table>'
              eingabefelder = eingabefelder + '</form>'
            elif neuerzugang == "opennebula":
              eingabefelder = '<p>&nbsp;</p>'
              if sprache == "de":
                eingabefelder = eingabefelder + '<font color="green">Unterst&uuml;tung f&uuml;r OpenNebula ist noch nicht implementiert</font>'
              else:
                eingabefelder = eingabefelder + '<font color="green">The support of OpenNebula is not yet finished</font>'
            elif neuerzugang == "tashi":
              eingabefelder = '<p>&nbsp;</p>'
              if sprache == "de":
                eingabefelder = eingabefelder + '<font color="green">Unterst&uuml;tung f&uuml;r Tashi ist noch nicht implementiert</font>'
              else:
                eingabefelder = eingabefelder + '<font color="green">The support of Tashi is not yet finished</font>'
            else:
              eingabefelder = ''

            if neuerzugang == "eucalyptus":
              version_warnung = '<p>&nbsp;</p>'
              if sprache == "de":
                version_warnung = version_warnung + '<p><font color="red">KOALA unterst&uuml;tzt ausschlie&szlig;lich Eucalyptus 1.6.2.<br> '
                version_warnung = version_warnung + 'Fr&uuml;here Versionen haben einige Bugs, die zu Problemen f&uuml;hren k&ouml;nnen.<br>'
                version_warnung = version_warnung + 'Ein Update von Eucalyptus auf die aktuelle Version wird daher empfohlen.</font></p>'
              else:
                version_warnung = version_warnung + '<p><font color="red">KOALA supports only Eucalyptus 1.6.2.<br> '
                version_warnung = version_warnung + 'Prior versions have some bugs that can cause some problems.<br>'
                version_warnung = version_warnung + 'Updating Eucalyptus to the latest version should be considered.</font></p>'
            else:
              version_warnung = ''

            if neuerzugang == "eucalyptus":
              port_warnung = '<p>&nbsp;</p>\n'
              if sprache == "de":
                port_warnung = port_warnung + 'Die Google App Engine akzeptiert nur wenige Ports. '
                port_warnung = port_warnung + 'Leider ist der Standard-Port von Eucalyputs (8773) nicht dabei. '
                port_warnung = port_warnung + 'Es empfiehlt sich darum, einen anderen Port auf den Eucalyptus-Port umzuleiten. '
                port_warnung = port_warnung + 'Ein Beispiel:<br> \n'
                port_warnung = port_warnung + '<tt>iptables -A INPUT -p tcp --dport 8188 -j ACCEPT</tt><br>\n '
                port_warnung = port_warnung + '<tt>iptables -A PREROUTING -t nat -i eth0 -p tcp --dport 8188 -j REDIRECT --to-port 8773</tt> '
              else:
                port_warnung = port_warnung + 'The Google App Engine accepts only few ports '
                port_warnung = port_warnung + 'and the default port of Eucalyptus (8773) is not included. '
                port_warnung = port_warnung + 'Because of this fact, you have to route another port to the Eucayptus port. '
                port_warnung = port_warnung + 'For example:<br> \n'
                port_warnung = port_warnung + '<tt>iptables -A INPUT -p tcp --dport 8188 -j ACCEPT</tt><br>\n '
                port_warnung = port_warnung + '<tt>iptables -A PREROUTING -t nat -i eth0 -p tcp --dport 8188 -j REDIRECT --to-port 8773</tt> '
            elif neuerzugang == "nimbus":
              port_warnung = '<p>&nbsp;</p>\n'
              if sprache == "de":
                port_warnung = port_warnung + 'Die Google App Engine akzeptiert nur wenige Ports. '
                port_warnung = port_warnung + 'Wenn die Nimbus-Infrastruktur, die Sie verwenden m&ouml;chten, einen keine unterst&uuml;tzten Port (z.B. 8442) verwendet, '
                port_warnung = port_warnung + 'empfiehlt es sich, einen unterst&uuml;tzten Port auf den Port der Nimbus-Infrastruktur umzuleiten. '
                port_warnung = port_warnung + 'Ein Beispiel:<br> \n'
                port_warnung = port_warnung + '<tt>iptables -A INPUT -p tcp --dport 8188 -j ACCEPT</tt><br>\n '
                port_warnung = port_warnung + '<tt>iptables -A PREROUTING -t nat -i eth0 -p tcp --dport 8188 -j REDIRECT --to-port 8442</tt> '
              else:
                port_warnung = port_warnung + 'The Google App Engine accepts only few ports. '
                port_warnung = port_warnung + 'If the Nimbus infrastructure you want to access, has a non accepted port (e.g. 8442), you have to route an accepted port to the port of the Nimbus infrastructure. '
                port_warnung = port_warnung + 'For example:<br> \n'
                port_warnung = port_warnung + '<tt>iptables -A INPUT -p tcp --dport 8188 -j ACCEPT</tt><br>\n '
                port_warnung = port_warnung + '<tt>iptables -A PREROUTING -t nat -i eth0 -p tcp --dport 8188 -j REDIRECT --to-port 8442</tt> '
            else:
              port_warnung = '<p>&nbsp;</p>'


            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'eingabefelder': eingabefelder,
            'input_error_message': input_error_message,
            'tabelle_logins': tabelle_logins,
            'zonen_liste': zonen_liste,
            'port_warnung': port_warnung,
            'version_warnung': version_warnung,
            }

            path = os.path.join(os.path.dirname(__file__), "templates", sprache, "index.html")
            self.response.out.write(template.render(path,template_values))
        else:
            self.redirect('/')


class ZugangEntfernen(webapp.RequestHandler):
    def get(self):
        region = self.request.get('region')
        endpointurl = self.request.get('endpointurl')
        accesskey = self.request.get('accesskey')
        # Den Usernamen erfahren
        username = users.get_current_user()

        #anfrage = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND regionname = :regionname_db AND endpointurl = :endpointurl_db AND accesskey = accesskey_db", username_db=username, regionname_db=region, endpointurl_db=endpointurl, accesskey_db=accesskey)
        testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND regionname = :regionname_db AND endpointurl = :endpointurl_db AND accesskey = :accesskey_db", username_db=username, regionname_db=region, endpointurl_db=endpointurl, accesskey_db=accesskey)
        # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
        results = testen.fetch(100)
        for result in results:
          result.delete()

        testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
        results = testen.fetch(100)
        for result in results:
          result.delete()

        self.redirect('/regionen')



class Login(webapp.RequestHandler):
    def post(self):
        cloud_region = self.request.get('cloud_region')
        endpointurl = self.request.get('endpointurl')
        accesskey = self.request.get('accesskey')
        secretaccesskey = self.request.get('secretaccesskey')
        if cloud_region == "Amazon EC2 EU West":
          regionname = "eu-west-1"
        if cloud_region == "Amazon EC2 US East":
          regionname = "us-east-1"
        if cloud_region == "Amazon EC2 US West":
          regionname = "us-west-1"
        if cloud_region == "Amazon EC2 Asia Pacific":
          regionname = "ap-southeast-1"
        if cloud_region == "Eucalyptus":
          regionname = "eucalyptus"

        if cloud_region == "Amazon EC2 EU West" or cloud_region == "Amazon EC2 US East" or cloud_region == "Amazon EC2 US West" or cloud_region == "Amazon EC2 Asia Pacific":
          conn_region = boto.ec2.connect_to_region(regionname,
                                                   aws_access_key_id=accesskey,
                                                   aws_secret_access_key=secretaccesskey,
                                                   is_secure = False)
        if cloud_region == "Eualyptus":
          conn_region = boto.connect_ec2(aws_access_key_id=accesskey,
                                         aws_secret_access_key=secretaccesskey,
                                         is_secure=False,
                                         region=RegionInfo(name="eucalyptus", endpoint=endpointurl),
                                         port=8773,
                                         path="/services/Eucalyptus")

        # Den Usernamen erfahren
        username = users.get_current_user()

        # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
        testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND regionname = :regionname_db ", username_db=username, regionname_db=regionname)
        # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
        results = testen.fetch(100)
        for result in results:
          result.delete()

        # Festlegen, was in den Datastore geschrieben werden soll
        logindaten = KoalaCloudDatenbank(regionname=regionname,
                                         accesskey=accesskey,
                                         endpointurl=endpointurl,
                                         secretaccesskey=secretaccesskey,
                                         user=username)
        # In den Datastore schreiben
        logindaten.put()   

        self.redirect('/')

class Instanzen(webapp.RequestHandler):
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

        if results:
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
          if message in ("73", "77", "79", "81"):
            # wird sie hier, in der Hilfsfunktion grün formatiert
            input_error_message = format_error_message_green(input_error_message)
          # Ansonsten wird die Nachricht rot formatiert
          elif message in ("8", "9", "10", "74", "75", "76", "78", "80", "82"):
            input_error_message = format_error_message_red(input_error_message)
          else:
            input_error_message = ""

          try:
            liste_reservations = conn_region.get_all_instances()
          except EC2ResponseError:
            # Wenn es nicht klappt...
            if sprache == "de":
              instanzentabelle = '<font color="red">Es ist zu einem Fehler gekommen</font> <p>&nbsp;</p>'
            else:
              instanzentabelle = '<font color="red">An error occured</font> <p>&nbsp;</p>'
            # Wenn diese Zeile nicht da ist, kommt es später zu einem Fehler!
            laenge_liste_reservations = 0
          except DownloadError:
            if sprache == "de":
              instanzentabelle = '<font color="red">Es ist zu einem Timeout gekommen</font> <p>&nbsp;</p>'
            else:
              instanzentabelle = '<font color="red">an timeout error occured</font> <p>&nbsp;</p>'
            # Wenn diese Zeile nicht da ist, kommt es später zu einem Fehler!
            laenge_liste_reservations = 0
          else:
            # Wenn es geklappt hat...
            laenge_liste_reservations = len(liste_reservations)     # Anzahl der Elemente in der Liste

            if laenge_liste_reservations == 0:
              if sprache == "de":
                instanzentabelle = 'Es sind keine Instanzen in der Region vorhanden.'
              else:
                instanzentabelle = 'Still no instances exist inside this region.'
            else:
              instanzentabelle = ''
              instanzentabelle = instanzentabelle + '<table border="3" cellspacing="0" cellpadding="5">'
              instanzentabelle = instanzentabelle + '<tr>'
              instanzentabelle = instanzentabelle + '<th>&nbsp;</th>'
              instanzentabelle = instanzentabelle + '<th>&nbsp;</th>'
              instanzentabelle = instanzentabelle + '<th align="center">Instance ID</th>'
              instanzentabelle = instanzentabelle + '<th>&nbsp;</th>'
              instanzentabelle = instanzentabelle + '<th>&nbsp;</th>'
              instanzentabelle = instanzentabelle + '<th align="center">&nbsp;&nbsp;&nbsp;</th>'
              instanzentabelle = instanzentabelle + '<th align="center">Status</th>'
              if sprache == "de":
                instanzentabelle = instanzentabelle + '<th align="center">Typ</th>'
              else:
                instanzentabelle = instanzentabelle + '<th align="center">Type</th>'
              instanzentabelle = instanzentabelle + '<th align="center">Reservation ID</th>'
              if sprache == "de":
                instanzentabelle = instanzentabelle + '<th align="center">Besitzer</th>'
              else:
                instanzentabelle = instanzentabelle + '<th align="center">Owner</th>'
              instanzentabelle = instanzentabelle + '<th align="center">Image</th>'
              instanzentabelle = instanzentabelle + '<th align="center">Kernel</th>'
              instanzentabelle = instanzentabelle + '<th align="center">Ramdisk</th>'
              instanzentabelle = instanzentabelle + '<th align="center">Zone</th>'
              if sprache == "de":
                instanzentabelle = instanzentabelle + '<th align="center">Gruppe</th>'
              else:
                instanzentabelle = instanzentabelle + '<th align="center">Group</th>'
              instanzentabelle = instanzentabelle + '<th align="center">Public DNS</th>'
              instanzentabelle = instanzentabelle + '<th align="center">Private DNS</th>'
              if sprache == "de":
                instanzentabelle = instanzentabelle + '<th align="center">Schl&uuml;ssel</th>'
                instanzentabelle = instanzentabelle + '<th align="center">Startzeitpunkt</th>'
              else:
                instanzentabelle = instanzentabelle + '<th align="center">Key</th>'
                instanzentabelle = instanzentabelle + '<th align="center">Launch Time</th>'
              instanzentabelle = instanzentabelle + '</tr>'
              for i in liste_reservations:
                for x in i.instances:
                  instanzentabelle = instanzentabelle + '<tr>'
                  instanzentabelle = instanzentabelle + '<td>'
                  if sprache == "de":
                    instanzentabelle = instanzentabelle + '<a href="/instanzbeenden?id='
                    instanzentabelle = instanzentabelle + x.id
                    instanzentabelle = instanzentabelle + '"title="Instanz beenden"><img src="bilder/stop.png" width="16" height="16" border="0" alt="Instanz beenden"></a>'
                  else:
                    instanzentabelle = instanzentabelle + '<a href="/instanzbeenden?id='
                    instanzentabelle = instanzentabelle + x.id
                    instanzentabelle = instanzentabelle + '"title="stop instance"><img src="bilder/stop.png" width="16" height="16" border="0" alt="stop instance"></a>'
                  instanzentabelle = instanzentabelle + '</td>'
                  instanzentabelle = instanzentabelle + '<td>'
                  if sprache == "de":
                    instanzentabelle = instanzentabelle + '<a href="/instanzreboot?id='
                    instanzentabelle = instanzentabelle + x.id
                    instanzentabelle = instanzentabelle + '"title="Instanz neustarten"><img src="bilder/gear.png" width="16" height="16" border="0" alt="Instanz neustarten"></a>'
                  else:
                    instanzentabelle = instanzentabelle + '<a href="/instanzreboot?id='
                    instanzentabelle = instanzentabelle + x.id
                    instanzentabelle = instanzentabelle + '"title="reboot instance"><img src="bilder/gear.png" width="16" height="16" border="0" alt="reboot instance"></a>'
                  instanzentabelle = instanzentabelle + '</td>'
                  instanzentabelle = instanzentabelle + '<td align="center">'
                  instanzentabelle = instanzentabelle + '<tt>'+str(x.id)+'</tt>'
                  instanzentabelle = instanzentabelle + '</td>'
                  instanzentabelle = instanzentabelle + '<td>'
                  if sprache == "de":
                    instanzentabelle = instanzentabelle + '<a href="/console_output?id='
                    instanzentabelle = instanzentabelle + x.id
                    instanzentabelle = instanzentabelle + '"title="Konsolenausgabe"><img src="bilder/terminal.png" width="22" height="16" border="0" alt="Konsolenausgabe"></a>'
                  else:
                    instanzentabelle = instanzentabelle + '<a href="/console_output?id='
                    instanzentabelle = instanzentabelle + x.id
                    instanzentabelle = instanzentabelle + '"title="console output"><img src="bilder/terminal.png" width="22" height="16" border="0" alt="console output"></a>'
                  instanzentabelle = instanzentabelle + '</td>'

                  # Launch more of these
                  instanzentabelle = instanzentabelle + '<td>'
                  if sprache == "de":
                    instanzentabelle = instanzentabelle + '<a href="/instanzanlegen?image='
                    instanzentabelle = instanzentabelle + str(x.image_id)
                    instanzentabelle = instanzentabelle + "&amp;zone="
                    instanzentabelle = instanzentabelle + str(x.placement)
                    instanzentabelle = instanzentabelle + "&amp;key="
                    instanzentabelle = instanzentabelle + str(x.key_name)
                    # Es ist denkbar, dass der Wert des Kernels "None" ist.
                    # Dann darf man hier nichts angeben!
                    if x.kernel != None:
                      instanzentabelle = instanzentabelle + "&amp;aki="
                      instanzentabelle = instanzentabelle + str(x.kernel)
                    # Manchmal ist die Angabe der Ramdisk "None".
                    # Dann darf man hier nichts angeben!
                    if x.ramdisk != None:
                      instanzentabelle = instanzentabelle + "&amp;ari="
                      instanzentabelle = instanzentabelle + str(x.ramdisk)
                    instanzentabelle = instanzentabelle + "&amp;type="
                    instanzentabelle = instanzentabelle + str(x.instance_type)
                    instanzentabelle = instanzentabelle + "&amp;gruppe="
                    instanzentabelle = instanzentabelle + i.groups[0].id
                    instanzentabelle = instanzentabelle + '"title="Weitere Instanzen starten"><img src="bilder/plus.png" width="16" height="16" border="0" alt="Weitere Instanzen starten"></a>'
                  else:
                    instanzentabelle = instanzentabelle + '<a href="/instanzanlegen?image='
                    instanzentabelle = instanzentabelle + str(x.image_id)
                    instanzentabelle = instanzentabelle + "&amp;zone="
                    instanzentabelle = instanzentabelle + str(x.placement)
                    instanzentabelle = instanzentabelle + "&amp;key="
                    instanzentabelle = instanzentabelle + str(x.key_name)
                    # Es ist denkbar, dass der Wert des Kernels "None" ist.
                    # Dann darf man hier nichts angeben!
                    if x.kernel != None:
                      instanzentabelle = instanzentabelle + "&amp;aki="
                      instanzentabelle = instanzentabelle + str(x.kernel)
                    # Manchmal ist die Angabe der Ramdisk "None".
                    # Dann darf man hier nichts angeben!
                    if x.ramdisk != None:
                      instanzentabelle = instanzentabelle + "&amp;ari="
                      instanzentabelle = instanzentabelle + str(x.ramdisk)
                    instanzentabelle = instanzentabelle + "&amp;type="
                    instanzentabelle = instanzentabelle + str(x.instance_type)
                    instanzentabelle = instanzentabelle + "&amp;gruppe="
                    instanzentabelle = instanzentabelle + i.groups[0].id
                    instanzentabelle = instanzentabelle + '"title="launch more of these"><img src="bilder/plus.png" width="16" height="16" border="0" alt="launch more of these"></a>'
                  instanzentabelle = instanzentabelle + '</td>'

                  # Die Icons der Betriebssysteme nur unter Amazon
                  #if regionname == "Amazon":
                  # Hier kommt die Spalte mit den Icons der Betriebssysteme
                  instanzentabelle = instanzentabelle + '<td align="center">'
                  image = conn_region.get_image(str(x.image_id))
                  if image == None:
                    # Das hier kommt, wenn das Image der laufenden Instanz nicht mehr existiert!
                    instanzentabelle = instanzentabelle + '<img src="bilder/linux_icon_48.gif" width="24" height="24" border="0" alt="Linux">'
                  else:
                    beschreibung_in_kleinbuchstaben = image.location.lower()
                    if beschreibung_in_kleinbuchstaben.find('fedora') != -1:
                      instanzentabelle = instanzentabelle + '<img src="bilder/fedora_icon_48.png" width="24" height="24" border="0" alt="Fedora">'
                    elif beschreibung_in_kleinbuchstaben.find('ubuntu') != -1:
                      instanzentabelle = instanzentabelle + '<img src="bilder/ubuntu_icon_48.png" width="24" height="24" border="0" alt="Ubuntu">'
                    elif beschreibung_in_kleinbuchstaben.find('debian') != -1:
                      instanzentabelle = instanzentabelle + '<img src="bilder/debian_icon_48.png" width="24" height="24" border="0" alt="Debian">'
                    elif beschreibung_in_kleinbuchstaben.find('gentoo') != -1:
                      instanzentabelle = instanzentabelle + '<img src="bilder/gentoo_icon_48.png" width="24" height="24" border="0" alt="Gentoo">'
                    elif beschreibung_in_kleinbuchstaben.find('suse') != -1:
                      instanzentabelle = instanzentabelle + '<img src="bilder/suse_icon_48.png" width="24" height="24" border="0" alt="SUSE">'
                    elif beschreibung_in_kleinbuchstaben.find('centos') != -1:
                      instanzentabelle = instanzentabelle + '<img src="bilder/centos_icon_48.png" width="24" height="24" border="0" alt="CentOS">'
                    elif beschreibung_in_kleinbuchstaben.find('redhat') != -1:
                      instanzentabelle = instanzentabelle + '<img src="bilder/redhat_icon_48.png" width="24" height="24" border="0" alt="RedHat">'
                    elif beschreibung_in_kleinbuchstaben.find('windows') != -1:
                      instanzentabelle = instanzentabelle + '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
                    elif beschreibung_in_kleinbuchstaben.find('opensolaris') != -1:
                      instanzentabelle = instanzentabelle + '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                    elif beschreibung_in_kleinbuchstaben.find('solaris') != -1:
                      instanzentabelle = instanzentabelle + '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                    elif beschreibung_in_kleinbuchstaben.find('osol') != -1:
                      instanzentabelle = instanzentabelle + '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                    else:
                      instanzentabelle = instanzentabelle + '<img src="bilder/linux_icon_48.gif" width="24" height="24" border="0" alt="Linux">'
                    instanzentabelle = instanzentabelle + '</td>'
                  #else:
                    ## Das hier wird bei Eucalyptus gemacht
                    #instanzentabelle = instanzentabelle + '<td><img src="bilder/linux_icon_48.gif" width="24" height="24" border="0" alt="Linux"></td>'

                  # Hier kommt die Spalte "Status"
                  if x.state == u'running':
                    instanzentabelle = instanzentabelle + '<td bgcolor="#c3ddc3">'
                    instanzentabelle = instanzentabelle + 'running'
                  if x.state == u'pending':
                    instanzentabelle = instanzentabelle + '<td bgcolor="#ffffcc">'
                    instanzentabelle = instanzentabelle + 'pending'
                  if x.state == u'shutting-down':
                    instanzentabelle = instanzentabelle + '<td bgcolor="#ffcc99">'
                    instanzentabelle = instanzentabelle + 'shutting-down'
                  if x.state == u'terminated':
                    instanzentabelle = instanzentabelle + '<td bgcolor="#ffcccc">'
                    instanzentabelle = instanzentabelle + 'terminated'
                  instanzentabelle = instanzentabelle + '</td><td>'
                  instanzentabelle = instanzentabelle + '<tt>'
                  instanzentabelle = instanzentabelle + str(x.instance_type)
                  instanzentabelle = instanzentabelle + '</tt>'
                  instanzentabelle = instanzentabelle + '</td><td align="center">'
                  instanzentabelle = instanzentabelle + '<tt>'
                  instanzentabelle = instanzentabelle + str(i.id)
                  #y = str(i)
                  #z = y.replace('Reservation:', '')
                  #instanzentabelle = instanzentabelle + z
                  instanzentabelle = instanzentabelle + '</tt>'
                  instanzentabelle = instanzentabelle + '</td><td align="center">'
                  instanzentabelle = instanzentabelle + '<tt>'
                  instanzentabelle = instanzentabelle + str(i.owner_id)
                  #y = str(i)
                  #z = y.replace('Reservation:', '')
                  #instanzentabelle = instanzentabelle + z
                  instanzentabelle = instanzentabelle + '</tt>'
                  instanzentabelle = instanzentabelle + '</td><td>'
                  instanzentabelle = instanzentabelle + '<tt>'+str(x.image_id)+'</tt>'
                  instanzentabelle = instanzentabelle + '</td><td>'
                  instanzentabelle = instanzentabelle + '<tt>'+str(x.kernel)+'</tt>'
                  instanzentabelle = instanzentabelle + '</td><td>'
                  instanzentabelle = instanzentabelle + '<tt>'+str(x.ramdisk)+'</tt>'
                  instanzentabelle = instanzentabelle + '</td><td>'
                  instanzentabelle = instanzentabelle + str(x.placement)
                  instanzentabelle = instanzentabelle + '</td><td>'
                  laenge_liste_guppen_reservations = len(i.groups)
                  if laenge_liste_guppen_reservations == 1:
                    # Wenn zu der Reservation nur eine Sicherheitsgruppe gehört
                    for z in range(laenge_liste_guppen_reservations):
                      instanzentabelle = instanzentabelle + i.groups[z].id
                  else:
                    # Wenn zu der Reservation mehrere Sicherheitsgruppen gehören
                    for z in range(laenge_liste_guppen_reservations):
                      instanzentabelle = instanzentabelle + i.groups[z].id+' '
                  #instanzentabelle = instanzentabelle + '</td><td align="center">'
                  instanzentabelle = instanzentabelle + '</td><td>'
                  instanzentabelle = instanzentabelle + str(x.public_dns_name)
                  #if x.public_dns_name != None:
                    #instanzentabelle = instanzentabelle + '<a href="http://'+x.public_dns_name+'" style="color:blue">Link</a>'
                  #else:
                    #instanzentabelle = instanzentabelle + x.private_dns_name
                  #instanzentabelle = instanzentabelle + '</td><td align="center">'
                  instanzentabelle = instanzentabelle + '</td><td>'
                  instanzentabelle = instanzentabelle + str(x.private_dns_name)
                  #if x.private_dns_name != None:
                    #instanzentabelle = instanzentabelle + '<a href="http://'+x.private_dns_name+'" style="color:blue">Link</a>'
                  #else:
                    #instanzentabelle = instanzentabelle + x.public_dns_name
                  instanzentabelle = instanzentabelle + '</td><td align="center">'
                  # Bei Eucalyptus kommt es manchmal vor, dass der Keyname nicht geholt werden kann. In diesem Fall kommt es zu einer HTML-Warnung, weil <tt></tt> leer ist. Darum lieber nur ein Leerzeichen, wenn der Keyname leer ist.
                  if x.key_name == "":
                    instanzentabelle = instanzentabelle + '&nbsp;'
                  else:
                    instanzentabelle = instanzentabelle + '<tt>'+str(x.key_name)+'</tt>'
                  instanzentabelle = instanzentabelle + '</td><td>'
                  #self.response.out.write(x.private_dns_name+" ")
                  #self.response.out.write(str(x.state_code)+" ") 
                  #self.response.out.write(x.key_name+" ")
                  #self.response.out.write(str(x.shutdown_state)+" ")
                  #self.response.out.write(str(x.previous_state)+" ")
                  #self.response.out.write(str(x.ami_launch_index)+" ")
                  #self.response.out.write(str(x.monitored)+" ")
                  #self.response.out.write('<BR>')
                  datum_des_starts = parse(x.launch_time)
                  #instanzentabelle = instanzentabelle + str(datum_des_starts)
                  instanzentabelle = instanzentabelle + str(datum_des_starts.strftime("%Y-%m-%d  %H:%M:%S"))
                  #instanzentabelle = instanzentabelle + x.launch_time
                  instanzentabelle = instanzentabelle + '</td>'
                  instanzentabelle = instanzentabelle + '</tr>'
              instanzentabelle = instanzentabelle + '</table>'


          if laenge_liste_reservations >= 1:
            alle_instanzen_loeschen_button = '<p>&nbsp;</p>\n'
            alle_instanzen_loeschen_button = alle_instanzen_loeschen_button + '<table border="0" cellspacing="5" cellpadding="5">\n'
            alle_instanzen_loeschen_button = alle_instanzen_loeschen_button + '<tr>\n'
            alle_instanzen_loeschen_button = alle_instanzen_loeschen_button + '<td align="center">\n'
            alle_instanzen_loeschen_button = alle_instanzen_loeschen_button + '<form action="/alle_instanzen_beenden" method="get">\n'
            if sprache == "de":
              alle_instanzen_loeschen_button = alle_instanzen_loeschen_button + '<input type="submit" value="Alle Instanzen beenden">\n'
            else:
              alle_instanzen_loeschen_button = alle_instanzen_loeschen_button + '<input type="submit" value="stop all instances">\n'
            alle_instanzen_loeschen_button = alle_instanzen_loeschen_button + '</form>\n'
            alle_instanzen_loeschen_button = alle_instanzen_loeschen_button + '</td>\n'
            alle_instanzen_loeschen_button = alle_instanzen_loeschen_button + '</tr>\n'
            alle_instanzen_loeschen_button = alle_instanzen_loeschen_button + '</table>\n'
          else:
            alle_instanzen_loeschen_button = '<p>&nbsp;</p>\n'


          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'reservationliste': instanzentabelle,
          'zonen_liste': zonen_liste,
          'input_error_message': input_error_message,
          'alle_instanzen_loeschen_button': alle_instanzen_loeschen_button,
          }

          #if sprache == "de": naechse_seite = "instanzen_de.html"
          #else:               naechse_seite = "instanzen_en.html"
          #path = os.path.join(os.path.dirname(__file__), naechse_seite)
          path = os.path.join(os.path.dirname(__file__), "templates", sprache, "instanzen.html")
          self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')


class AlleInstanzenBeendenFrage(webapp.RequestHandler):
    def get(self):
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')

        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if results:
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache)
          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache)

          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'zonen_liste': zonen_liste,
          }

          #if sprache == "de": naechse_seite = "alle_images_beenden_frage_de.html"
          #else:               naechse_seite = "alle_images_beenden_frage_en.html"
          #path = os.path.join(os.path.dirname(__file__), naechse_seite)
          path = os.path.join(os.path.dirname(__file__), "templates", sprache, "alle_images_beenden_frage.html")
          self.response.out.write(template.render(path,template_values))



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

        if results:
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
          path = os.path.join(os.path.dirname(__file__), "templates", sprache, "securitygroups.html")
          self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')

class GruppeAendern(webapp.RequestHandler):
    def get(self):
        # Eventuell vorhande Fehlermeldung holen
        message = self.request.get('message')
        # Den Namen der zu löschenden Gruppe holen
        gruppe = self.request.get('gruppe')
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')

        sprache = aktuelle_sprache(username)
        navigations_bar = navigations_bar_funktion(sprache)
        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if not results:
          regionname = 'keine'
          zone_amazon = ""
        else:
          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

        url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
        url_linktext = 'Logout'

        zonen_liste = zonen_liste_funktion(username,sprache)

        if sprache != "de":
          sprache = "en"

        input_error_message = error_messages.get(message, {}).get(sprache)

        # Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
        if input_error_message == None:
          input_error_message = ""

        # Wenn die Nachricht grün formatiert werden soll...
        if message in ("28", "37"):
          # wird sie hier, in der Hilfsfunktion grün formatiert
          input_error_message = format_error_message_green(input_error_message)
        # Ansonsten wird die Nachricht rot formatiert
        elif message in ("8", "29", "30", "31", "32", "33", "34", "35", "36", "38", "39"):
          input_error_message = format_error_message_red(input_error_message)
        else:
          input_error_message = ""

        try:
          # Liste mit den Security Groups
          # Man kann nicht direkt versuchen mit get_all_security_groups(gruppen_liste)
          # die anzulegende Gruppe zu erzeugen. Wenn die Gruppe noch nicht existiert,
          # gibt es eine Fehlermeldung
          liste_security_groups = conn_region.get_all_security_groups()
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "7"
          self.redirect('/securitygroups?message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "7"
          self.redirect('/securitygroups?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat und die Liste geholt wurde...

          # Anzahl der Elemente in der Liste
          laenge_liste_security_groups = len(liste_security_groups)


          for i in range(laenge_liste_security_groups):
            # Vergleichen
            if liste_security_groups[i].name == gruppe:
              # Liste mit den Regeln der Security Group holen
              liste_regeln = liste_security_groups[i].rules
              # Anzahl der Elemente in der Liste mit den Regeln
              laenge_liste_regeln = len(liste_regeln)
              if laenge_liste_regeln == 0:
                if sprache == "de":
                  regelntabelle = 'Es sind noch keine Regeln in der  Sicherheitsgruppe '+gruppe+' vorhanden'
                else:
                  regelntabelle = 'Still no rules exist inside the security group '+gruppe
              else:
                for i in range(laenge_liste_regeln):

                  regelntabelle = ''
                  regelntabelle = regelntabelle + '<table border="3" cellspacing="0" cellpadding="5">'
                  regelntabelle = regelntabelle + '<tr>'
                  regelntabelle = regelntabelle + '<th>&nbsp;</th>'
                  if sprache == "de":
                    regelntabelle = regelntabelle + '<th align="center">Protokoll</th>'
                  else:
                    regelntabelle = regelntabelle + '<th align="center">Protocol</th>'
                  regelntabelle = regelntabelle + '<th align="center">From Port</th>'
                  regelntabelle = regelntabelle + '<th align="center">To Port</th>'
                  regelntabelle = regelntabelle + '</tr>'
                  for i in range(laenge_liste_regeln):
                      regelntabelle = regelntabelle + '<tr>'
                      regelntabelle = regelntabelle + '<td>'
                      regelntabelle = regelntabelle + '<a href="/grupperegelentfernen?regel='
                      regelntabelle = regelntabelle + str(liste_regeln[i])
                      regelntabelle = regelntabelle + '&amp;gruppe='
                      regelntabelle = regelntabelle + gruppe
                      regelntabelle = regelntabelle + '" title="Regel l&ouml;schen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Regel l&ouml;schen"></a>'
                      regelntabelle = regelntabelle + '</td>'
                      regelntabelle = regelntabelle + '<td>'
                      if str(liste_regeln[i].ip_protocol) == "tcp":
                        regelntabelle = regelntabelle + 'TCP'
                      if str(liste_regeln[i].ip_protocol) == "udp":
                        regelntabelle = regelntabelle + 'UDP'
                      if str(liste_regeln[i].ip_protocol) == "icmp":
                        regelntabelle = regelntabelle + 'ICMP'
                      regelntabelle = regelntabelle + '</td>'
                      regelntabelle = regelntabelle + '<td>'
                      regelntabelle = regelntabelle + str(liste_regeln[i].from_port)
                      regelntabelle = regelntabelle + '</td>'
                      regelntabelle = regelntabelle + '<td>'
                      regelntabelle = regelntabelle + str(liste_regeln[i].to_port)
                      regelntabelle = regelntabelle + '</td>'
                      regelntabelle = regelntabelle + '</tr>'
                  regelntabelle = regelntabelle + '</table>'

          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'gruppe': gruppe,
          'regelntabelle': regelntabelle,
          'input_error_message': input_error_message,
          'zonen_liste': zonen_liste,
          }

          #if sprache == "de": naechse_seite = "securitygrouprules_de.html"
          #else:               naechse_seite = "securitygrouprules_en.html"
          #path = os.path.join(os.path.dirname(__file__), naechse_seite)
          path = os.path.join(os.path.dirname(__file__), "templates", sprache, "securitygrouprules.html")
          self.response.out.write(template.render(path,template_values))


class GruppeRegelErzeugen(webapp.RequestHandler):
    def post(self):
        #self.response.out.write('posted!')
        gruppe = self.request.get('gruppe')
        protokoll_input = self.request.get('protokoll')
        # Die Methode authorize will den Protokoll-Namen in Kleinbuchstaben
        if protokoll_input == 'TCP':  protokoll = 'tcp'
        if protokoll_input == 'UDP':  protokoll = 'udp'
        if protokoll_input == 'ICMP': protokoll = 'icmp'
        port_from = self.request.get('port_from')
        port_to = self.request.get('port_to')
        cidr_ip = '0.0.0.0/0'

        username = users.get_current_user()      # Den Usernamen erfahren

        conn_region, regionname = login(username)


        # Schauen, ob die Regel folgende ist: From -1 To -1 (ICMP) für Ping
        if port_from == '-1' and port_to == '-1':
          ausnahme = 1
        else:
          ausnahme = 0

        # Testen ob der Port FROM und der Port TO angegeben wurde
        if port_from == "" and port_to == "" and ausnahme == 0:
          # Wenn die Ports nicht angegeben wurden, kann keine Regel angelegt werden
          fehlermeldung = "29"
          self.redirect('/gruppenaendern?gruppe='+gruppe+'&message='+fehlermeldung)
        # Testen ob der Port FROM angegeben wurde
        elif port_from == "" and ausnahme == 0:
          # Wenn der Port nicht angegeben wurde, kann keine Regel angelegt werden
          fehlermeldung = "30"
          self.redirect('/gruppenaendern?gruppe='+gruppe+'&message='+fehlermeldung)
        elif port_to == "" and ausnahme == 0:   # Testen ob der Port TO angegeben wurde
          # Wenn der Port nicht angegeben wurde, kann keine Regel angelegt werden
          fehlermeldung = "31"
          self.redirect('/gruppenaendern?gruppe='+gruppe+'&message='+fehlermeldung)
        elif port_from.isdigit() == False and port_to.isdigit() == False and ausnahme == 0:
          # Testen ob der Port FROM und Port TO eine Zahl ist
          # Wenn nicht ausschließlich eine Zahl eingegeben wurde sondern evtl. Buchstaben oder Sonderzeichen
          fehlermeldung = "32"
          self.redirect('/gruppenaendern?gruppe='+gruppe+'&message='+fehlermeldung)
        elif port_from.isdigit() == False and ausnahme == 0:
          # Testen ob der Port FROM eine Zahl ist
          # Wenn nicht ausschließlich eine Zahl eingegeben wurde sondern evtl. Buchstaben oder Sonderzeichen
          fehlermeldung = "33"
          self.redirect('/gruppenaendern?gruppe='+gruppe+'&message='+fehlermeldung)
        elif port_to.isdigit() == False and ausnahme == 0:
          # Testen ob der Port TO eine Zahl ist
          # Wenn nicht ausschließlich eine Zahl eingegeben wurde sondern evtl. Buchstaben oder Sonderzeichen
          fehlermeldung = "34"
          self.redirect('/gruppenaendern?gruppe='+gruppe+'&message='+fehlermeldung)
        else:

          try:
            # Liste mit den Security Groups
            # Man kann nicht direkt versuchen mit get_all_security_groups(gruppen_liste)
            # die anzulegende Gruppe zu erzeugen. Wenn die Gruppe noch nicht existiert,
            # gibt es eine Fehlermeldung
            liste_security_groups = conn_region.get_all_security_groups()
          except EC2ResponseError:
            # Wenn es nicht klappt...
            fehlermeldung = "35"
            self.redirect('/securitygroups?message='+fehlermeldung)
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            fehlermeldung = "35"
            self.redirect('/securitygroups?message='+fehlermeldung)
          else:
            # Wenn es geklappt hat und die Liste geholt wurde...

            # Anzahl der Elemente in der Liste
            laenge_liste_security_groups = len(liste_security_groups)

            for i in range(laenge_liste_security_groups):
              # Vergleichen
              if liste_security_groups[i].name == gruppe:
                # Jetzt ist die Richtige Security Group gefunden.

                # Liste mit den Regeln der Security Group
                liste_regeln = liste_security_groups[i].rules
                # Anzahl der Elemente in der Liste mit den Regeln
                laenge_liste_regeln = len(liste_regeln)

                # Es sind noch keine Regeln in der Security Group vorhanden
                if laenge_liste_regeln == 0:
                  #self.response.out.write('leer')
                  try:
                    #Jetzt anlegen
                    liste_security_groups[i].authorize(ip_protocol=protokoll, from_port=port_from, to_port=port_to, cidr_ip=cidr_ip, src_group=None)
                  except EC2ResponseError:
                    fehlermeldung = "39"
                    self.redirect('/gruppenaendern?gruppe='+gruppe+'&message='+fehlermeldung)
                  except DownloadError:
                    # Diese Exception hilft gegen diese beiden Fehler:
                    # DownloadError: ApplicationError: 2 timed out
                    # DownloadError: ApplicationError: 5
                    fehlermeldung = "8"
                    self.redirect('/gruppenaendern?gruppe='+gruppe+'&message='+fehlermeldung)
                  else:
                    fehlermeldung = "28"
                    self.redirect('/gruppenaendern?gruppe='+gruppe+'&message='+fehlermeldung)
                else:
                  for i in range(laenge_liste_regeln):
                    # self.response.out.write('nicht leer ')
                    # Hier muss die neue Regel mit den bestehenden Regeln verglichen werden
                    # Variable erzeugen zum Erfassen, ob die neue Regel schon existiert
                    schon_vorhanden = 0
                    regel = 'IPPermissions:'+protokoll+'('+port_from+'-'+port_to+')'
                    for k in range(laenge_liste_regeln):
                      # Vergleichen
                      if str(liste_regeln[k]) == regel:
                        schon_vorhanden = 1
                        fehlermeldung = "35"
                        self.redirect('/gruppenaendern?gruppe='+gruppe+'&message='+fehlermeldung)
                  if schon_vorhanden == 0:
                    for z in range(laenge_liste_security_groups):
                      # Vergleichen
                      if liste_security_groups[z].name == gruppe:
                        try:
                          #Jetzt die Regel anlegen
                          liste_security_groups[z].authorize(ip_protocol=protokoll, from_port=port_from, to_port=port_to, cidr_ip=cidr_ip, src_group=None)
                        except EC2ResponseError:
                          fehlermeldung = "39"
                          self.redirect('/gruppenaendern?gruppe='+gruppe+'&message='+fehlermeldung)
                        except DownloadError:
                          # Diese Exception hilft gegen diese beiden Fehler:
                          # DownloadError: ApplicationError: 2 timed out
                          # DownloadError: ApplicationError: 5
                          fehlermeldung = "8"
                          self.redirect('/gruppenaendern?gruppe='+gruppe+'&message='+fehlermeldung)
                        else:
                          fehlermeldung = "28"
                          self.redirect('/gruppenaendern?gruppe='+gruppe+'&message='+fehlermeldung)


class GruppeRegelEntfernen(webapp.RequestHandler):
    def get(self):
        # Den Namen der betreffenden Gruppe holen
        gruppe = self.request.get('gruppe')
        # Den Namen der zu löschenden Gruppe holen
        regel = self.request.get('regel')
        cidr_ip = '0.0.0.0/0'
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Liste mit den Security Groups
          # Man kann nicht direkt versuchen mit get_all_security_groups(gruppen_liste)
          # die anzulegende Gruppe zu erzeugen. Wenn die Gruppe noch nicht existiert,
          # gibt es eine Fehlermeldung
          liste_security_groups = conn_region.get_all_security_groups()
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "35"
          self.redirect('/securitygroups?message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "35"
          self.redirect('/securitygroups?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat und die Liste geholt wurde...

          # Anzahl der Elemente in der Liste
          laenge_liste_security_groups = len(liste_security_groups)
  
          # Mit dieser Variable wird überprüft, ob die Regel gleich gefunden wird
          # Wenn die Regel nicht gefunden wird, braucht auch nichts entfernt zu werden
          gefunden = 0
          for i in range(laenge_liste_security_groups):
            # Vergleichen
            if liste_security_groups[i].name == gruppe:
              # Jetzt ist die Richtige Security Group gefunden.
              # Liste mit den Regeln der Security Group holen
              liste_regeln = liste_security_groups[i].rules
              # Anzahl der Elemente in der Liste mit den Regeln
              laenge_liste_regeln = len(liste_regeln)

              for k in range(laenge_liste_regeln):
                vergleich = str(liste_regeln[k])         # Regel in einen String umwandeln
                if vergleich == regel:                   # Vergleichen
                  # Die Regel wurde gefunden!
                  gefunden = 1
                  try:
                    liste_security_groups[i].revoke(ip_protocol=liste_regeln[k].ip_protocol,
                                                    from_port=liste_regeln[k].from_port,
                                                    to_port=liste_regeln[k].to_port,
                                                    cidr_ip=cidr_ip,
                                                    src_group=None)
                  except EC2ResponseError:
                    fehlermeldung = "36"
                    self.redirect('/gruppenaendern?gruppe='+gruppe+'&message='+fehlermeldung)
                  except DownloadError:
                    # Diese Exception hilft gegen diese beiden Fehler:
                    # DownloadError: ApplicationError: 2 timed out
                    # DownloadError: ApplicationError: 5
                    fehlermeldung = "8"
                    self.redirect('/gruppenaendern?gruppe='+gruppe+'&message='+fehlermeldung)
                  else:
                    fehlermeldung = "37"
                    self.redirect('/gruppenaendern?gruppe='+gruppe+'&message='+fehlermeldung)

          # Wenn die Instanz nicht gefunden werden konnte
          if gefunden == 0:
            fehlermeldung = "38"
            self.redirect('/gruppenaendern?gruppe='+gruppe+'&message='+fehlermeldung)



class GruppeErzeugen(webapp.RequestHandler):
    def post(self):
        #self.response.out.write('posted!')
        neuergruppenname = self.request.get('gruppenname')
        neuegruppenbeschreibung = self.request.get('gruppenbeschreibung')

        username = users.get_current_user()      # Den Usernamen erfahren

        conn_region, regionname = login(username)

        if neuergruppenname == "" and neuegruppenbeschreibung == "":
            # Wenn kein Name und keine Beschreibung angegeben wurde
            #fehlermeldung = "Sie haben keinen Namen und keine Beschreibung angegeben"
            fehlermeldung = "41"
            self.redirect('/securitygroups?message='+fehlermeldung)
        elif neuergruppenname == "":
            # Testen ob ein Name für die neue Gruppe angegeben wurde
            #fehlermeldung = "Sie haben keinen Namen angegeben"
            fehlermeldung = "42"
            self.redirect('/securitygroups?message='+fehlermeldung)
        elif neuegruppenbeschreibung == "":
            # Testen ob eine Beschreibung für die neue Gruppe angegeben wurde
            #fehlermeldung = "Sie haben keine Beschreibung angegeben"
            fehlermeldung = "43"
            self.redirect('/securitygroups?message='+fehlermeldung)
        elif re.search(r'[^\-_a-zA-Z0-9]', neuergruppenname) != None:
            # Testen ob für den neuen Gruppennamen nur erlaubte Zeichen verwendet wurden
            fehlermeldung = "45"
            self.redirect('/securitygroups?message='+fehlermeldung)
        elif re.search(r'[^\ \-_a-zA-Z0-9]', neuegruppenbeschreibung) != None:
            # Testen ob für die Beschreibung der den neuen Gruppe nur erlaubte Zeichen verwendet wurden
            # Leerzeichen sind in der Gruppenbezeichnung ok
            fehlermeldung = "46"
            self.redirect('/securitygroups?message='+fehlermeldung)
        else:
            try:
                # Liste mit den Security Groups
                # Man kann nicht direkt versuchen mit get_all_security_groups(gruppen_liste)
                # die anzulegende Gruppe zu erzeugen. Wenn die Gruppe noch nicht existiert,
                # gibt es eine Fehlermeldung
                liste_security_groups = conn_region.get_all_security_groups()
            except EC2ResponseError:
                # Wenn es nicht klappt...
                fehlermeldung = "47"
                self.redirect('/securitygroups?message='+fehlermeldung)
            except DownloadError:
                # Diese Exception hilft gegen diese beiden Fehler:
                # DownloadError: ApplicationError: 2 timed out
                # DownloadError: ApplicationError: 5
                fehlermeldung = "47"
                self.redirect('/securitygroups?message='+fehlermeldung)
            else:
                # Wenn es geklappt hat und die Liste geholt wurde...

                # Anzahl der Elemente in der Liste
                laenge_liste_security_groups = len(liste_security_groups)

                # Variable erzeugen zum Erfassen, ob die neu Gruppe schon existiert
                schon_vorhanden = 0
                for i in range(laenge_liste_security_groups):
                    # Vergleichen
                    # Für jede existierende Gruppe den Namen der Gruppe
                    # mit dem neuen Gruppennamen vergleichen
                    if liste_security_groups[i].name == neuergruppenname:
                        # Security Gruppe existiert schon!
                        schon_vorhanden = 1
                        fehlermeldung = "44"
                        self.redirect('/securitygroups?message='+fehlermeldung)

                # Wenn der Schlüssel noch nicht existiert...anlegen!
                if schon_vorhanden == 0:
                    try:
                        # Security Group anlegen
                        conn_region.create_security_group(neuergruppenname, neuegruppenbeschreibung)
                    except EC2ResponseError:
                        fehlermeldung = "47"
                        self.redirect('/securitygroups?message='+fehlermeldung)
                    except DownloadError:
                        # Diese Exception hilft gegen diese beiden Fehler:
                        # DownloadError: ApplicationError: 2 timed out
                        # DownloadError: ApplicationError: 5
                        fehlermeldung = "8"
                        self.redirect('/securitygroups?message='+fehlermeldung)
                    else:
                        fehlermeldung = "40"
                        self.redirect('/securitygroups?message='+fehlermeldung)



class Keys(webapp.RequestHandler):
    def get(self):
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')
        # Wurde ein neuer Schlüssel angelegt?
        neu = self.request.get('neu')
        # Name des neuen Schlüssels
        neuerkeyname = self.request.get('neuerkeyname')
        # Name des Datastore-Schlüssels, unter dem der Secret-Key angehegt ist
        secretkey = self.request.get('secretkey')
        # Eventuell vorhande Fehlermeldung holen
        message = self.request.get('message')

        #So könnte man vielleicht den File-Download-Dialog bekommen
        #Content-disposition: attachment; filename="fname.ext"


        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if results:
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
          if message in ("99", "103"):
            # wird sie hier, in der Hilfsfunktion grün formatiert
            input_error_message = format_error_message_green(input_error_message)
          # Ansonsten wird die Nachricht rot formatiert
          elif message in ("8", "92", "100", "101", "102", "104"):
            input_error_message = format_error_message_red(input_error_message)
          else:
            input_error_message = ""

          try:
            # Liste mit den Keys
            liste_key_pairs = conn_region.get_all_key_pairs()
          except EC2ResponseError:
            # Wenn es nicht klappt...
            if sprache == "de":
              keytabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
            else:
              keytabelle = '<font color="red">An error occured</font>'
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            if sprache == "de":
              keytabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
            else:
              keytabelle = '<font color="red">A timeout error occured</font>'
          else:
            # Wenn es geklappt hat...
            laenge_liste_keys = len(liste_key_pairs)        # Anzahl der Elemente in der Liste

            if laenge_liste_keys == 0:
              keytabelle = 'Es sind keine Schl&uuml;sselpaare in der Zone vorhanden.'
            else:
              keytabelle = ''
              keytabelle = keytabelle + '<table border="3" cellspacing="0" cellpadding="5">'
              keytabelle = keytabelle + '<tr>'
              keytabelle = keytabelle + '<th>&nbsp;</th>'
              keytabelle = keytabelle + '<th align="center">Name</th>'
              if sprache == "de":
                keytabelle = keytabelle + '<th align="center">Pr&uuml;fsumme (Fingerprint)</th>'
              else:
                keytabelle = keytabelle + '<th align="center">Fingerprint</th>'
              keytabelle = keytabelle + '</tr>'
              for i in range(laenge_liste_keys):
                  keytabelle = keytabelle + '<tr>'
                  keytabelle = keytabelle + '<td>'
                  keytabelle = keytabelle + '<a href="/schluesselentfernen?key='
                  keytabelle = keytabelle + liste_key_pairs[i].name
                  keytabelle = keytabelle + '"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Schl&uuml;sselpaar l&ouml;schen"></a>'
                  keytabelle = keytabelle + '</td>'
                  keytabelle = keytabelle + '<td>'
                  keytabelle = keytabelle + '<tt>'
                  keytabelle = keytabelle + liste_key_pairs[i].name
                  keytabelle = keytabelle + '</tt>'
                  keytabelle = keytabelle + '</td><td>'
                  keytabelle = keytabelle + '<tt>'
                  keytabelle = keytabelle + liste_key_pairs[i].fingerprint
                  keytabelle = keytabelle + '</tt>'
                  keytabelle = keytabelle + '</td>'
                  keytabelle = keytabelle + '</tr>'
              keytabelle = keytabelle + '</table>'

            if neu == "ja":
              secretkey_memcache_mit_zeilenumbruch = memcache.get(secretkey)
              secretkey_memcache = secretkey_memcache_mit_zeilenumbruch.replace("\n","<BR>")
              bodycommand = ' onLoad="newkey()" '
              secretkey = "test"
              javascript_funktion = '''<SCRIPT LANGUAGE="JavaScript">
  function newkey()
  {
  OpenWindow=window.open("", "newwin", "height=600, width=600,toolbar=no,scrollbars="+scroll+",menubar=no");
  OpenWindow.document.write("<TITLE>Secret Key</TITLE>")
  OpenWindow.document.write("<BODY BGCOLOR=white>")
  OpenWindow.document.write("<h1>Secret Key</h1>")
  OpenWindow.document.write("<P></P>")
  OpenWindow.document.write("<tt>'''
              javascript_funktion = javascript_funktion + secretkey_memcache
              if sprache == "de":
                javascript_funktion = javascript_funktion + '''</tt>")
                OpenWindow.document.write("<P></P>")
                OpenWindow.document.write("<B>Achtung!</B> Den Secret Key m&uuml;ssen Sie speichern.<BR>")
                OpenWindow.document.write("Am besten in einer Datei <tt>'''
              else:
                javascript_funktion = javascript_funktion + '''</tt>")
                OpenWindow.document.write("<P></P>")
                OpenWindow.document.write("<B>Attention!</B> The secret key need to be saved.<BR>")
                OpenWindow.document.write("As an advise use the filename <tt>'''
              javascript_funktion = javascript_funktion + neuerkeyname
              javascript_funktion = javascript_funktion + '''.secret</tt>.")
              OpenWindow.document.write("<P></P>")
              OpenWindow.document.write("<tt>chmod 600 '''
              javascript_funktion = javascript_funktion + neuerkeyname
              javascript_funktion = javascript_funktion + '''.secret</tt>")
  OpenWindow.document.write("</BODY>")
  OpenWindow.document.write("</HTML>")
  OpenWindow.document.close()
  self.name="main"
  }
  </SCRIPT>'''
            else:
                bodycommand = " "
                javascript_funktion = " "

            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'keytabelle': keytabelle,
            'bodycommand': bodycommand,
            'javascript_funktion': javascript_funktion,
            'zonen_liste': zonen_liste,
            'input_error_message': input_error_message,
            }

            #if sprache == "de": naechse_seite = "keys_de.html"
            #else:               naechse_seite = "keys_en.html"
            #path = os.path.join(os.path.dirname(__file__), naechse_seite)
            path = os.path.join(os.path.dirname(__file__), "templates", sprache, "keys.html")
            self.response.out.write(template.render(path,template_values))
        else:
            self.redirect('/')







class KeyErzeugen(webapp.RequestHandler):
    def post(self):
        #self.response.out.write('posted!')
        neuerkeyname = self.request.get('keyname')

        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        if neuerkeyname == "":
          # Testen ob ein Name für den neuen key angegeben wurde
          # Wenn kein Name angegeben wurde, kann kein Key angelegt werden
          #fehlermeldung = "Sie haben keine Namen angegeben"
          fehlermeldung = "92"
          self.redirect('/schluessel?message='+fehlermeldung)
        elif re.search(r'[^\-_a-zA-Z0-9]', neuerkeyname) != None:
          # Testen ob der Name für den neuen key nicht erlaubte Zeichen enthält
          fehlermeldung = "100"
          self.redirect('/schluessel?message='+fehlermeldung)
        else:

          liste_key_pairs = conn_region.get_all_key_pairs()
          # Anzahl der Elemente in der Liste
          laenge_liste_keys = len(liste_key_pairs)
          # Variable erzeugen zum Erfassen, ob der neue Schlüssel schon existiert
          schon_vorhanden = 0

          for i in range(laenge_liste_keys):
            # Vergleichen
            if str(liste_key_pairs[i].name) == neuerkeyname:
              # Schlüssel existiert schon!
              schon_vorhanden = 1
              neu = "nein"
              fehlermeldung = "102"
              self.redirect('/schluessel?message='+fehlermeldung)

          # Wenn der Schlüssel noch nicht existiert...
          if schon_vorhanden == 0:
            try:
              # Schlüsselpaar erzeugen
              neuer_key = conn_region.create_key_pair(neuerkeyname)
            except EC2ResponseError:
              fehlermeldung = "101"
              self.redirect('/schluessel?message='+fehlermeldung)
            except DownloadError:
              # Diese Exception hilft gegen diese beiden Fehler:
              # DownloadError: ApplicationError: 2 timed out
              # DownloadError: ApplicationError: 5
              fehlermeldung = "8"
              self.redirect('/schluessel?message='+fehlermeldung)
            else:
              neu = "ja"
              secretkey = neuer_key.material
              aktuelle_zeit = str(time())
              keyname = str(neuerkeyname)
              keyname = keyname + "_"
              keyname = keyname + regionname
              keyname = keyname + "_"
              keyname = keyname + str(aktuelle_zeit)
              # der Secret Key wird für 10 Minuten im Memcache gespeichert
              memcache.add(key=keyname, value=secretkey, time=600)
              fehlermeldung = "99"
              self.redirect('/schluessel?message='+fehlermeldung+'&neu='+neu+'&neuerkeyname='+neuerkeyname+'&secretkey='+keyname)



class RegionWechseln(webapp.RequestHandler):
    def post(self):
        # Zum Testen, ob das "post" geklappt hat
        #self.response.out.write('posted!')
        # Die ausgewählte Region holen
        regionen = self.request.get('regionen')
        # Den Usernamen erfahren
        username = users.get_current_user()

        suchen = ""
        if 'US East' in regionen:
          zone = "us-east-1"
          zugangstyp = "Amazon"
        elif 'US West' in regionen:
          zone = "us-west-1"
          zugangstyp = "Amazon"
        elif 'EU West' in regionen:
          zone = "eu-west-1"
          zugangstyp = "Amazon"
        elif 'Asia Pacific' in regionen:
          zone = "ap-southeast-1"
          zugangstyp = "Amazon"
        else:
          zone = regionen
          zugangstyp = "keinAmazon"

        # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
        testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

        # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
        results = testen.fetch(100)
        for result in results:
          result.delete()

        if zugangstyp == "keinAmazon":
          testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND eucalyptusname = :regionen_db", username_db=username, regionen_db=regionen)
          results = testen.fetch(100) # Einträge holen

          for result in results:
            zugangstyp = result.zugangstyp


        logindaten = KoalaCloudDatenbankAktiveZone(aktivezone=zone,
                                                   user=username,
                                                   zugangstyp=zugangstyp)

        try:
          # In den Datastore schreiben
          logindaten.put()
        except:
          # Wenn es nicht klappt...
          self.redirect('/')
        else:
          # Wenn es geklappt hat...
          self.redirect('/')

class Sprache(webapp.RequestHandler):
    def get(self):
        # Die ausgewählte Sprache holen
        lang = self.request.get('lang')
        # Den Usernamen erfahren
        username = users.get_current_user()

        if username:

          # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
          testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankSprache WHERE user = :username_db", username_db=username)

          # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
          results = testen.fetch(100)

          for result in results:
            result.delete()

          logindaten = KoalaCloudDatenbankSprache(sprache=lang,
                                                  user=username)

          try:
            # In den Datastore schreiben
            logindaten.put()
          except:
            # Wenn es nicht klappt...
            self.redirect('/')
          else:
            # Wenn es geklappt hat...
            self.redirect('/')
        else:
          self.redirect('/')


class FavoritEntfernen(webapp.RequestHandler):
    def get(self):
        # AMI des zu löschenden Favoriten holen
        ami = self.request.get('ami')
        # Zone des zu löschenden Favoriten holen
        zone = self.request.get('zone')
        # Den Usernamen erfahren
        username = users.get_current_user()

        ami = str(ami)

        testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankFavouritenAMIs WHERE user = :username_db AND ami = :ami_db AND zone = :zone_db", username_db=username, ami_db=ami, zone_db=zone)
        # Wenn Einträge vorhanden sind, werden sie aus der DB geholt
        results = testen.fetch(100)
        for result in results:
          try:
            result.delete()
            # Versuchen den Favorit zu löschen
          except:
            # Wenn es nicht klappt...
            self.redirect('/images')
          else:
            # Wenn es geklappt hat...
            self.redirect('/images')

        # Wenn es keine Einträge im Datastore gab...
        self.redirect('/images')

class FavoritAMIerzeugen(webapp.RequestHandler):
    def post(self):
        #self.response.out.write('posted!')
        ami = self.request.get('ami')
        zone = self.request.get('zone')
        # Den Usernamen erfahren
        username = users.get_current_user()

        if ami == "":
          # Testen ob die AMI-Bezeichnung angegeben wurde
          # Wenn keine AMI-Bezeichnung angegeben wurde, kann kein Favorit angelegt werden
          #fehlermeldung = "Sie haben keine AMI-Bezeichnung angegeben"
          fehlermeldung = "84"
          self.redirect('/images?message='+fehlermeldung)
        else:
          if re.match('ami-*', ami) == None:  
            # Erst überprüfen, ob die Eingabe mit "ami-" angängt
            fehlermeldung = "85"
            self.redirect('/images?message='+fehlermeldung)
          elif len(ami) != 12:
            # Überprüfen, ob die Eingabe 12 Zeichen lang ist
            fehlermeldung = "86"
            self.redirect('/images?message='+fehlermeldung)
          elif re.search(r'[^\-a-zA-Z0-9]', ami) != None:
            # Überprüfen, ob die Eingabe nur erlaubte Zeichen enthält
            # Die Zeichen - und a-zA-Z0-9 sind erlaubt. Alle anderen nicht. Darum das ^
            fehlermeldung = "87"
            self.redirect('/images?message='+fehlermeldung)
          else:
            # Erst überprüfen, ob schon ein AMI-Eintrag dieses Benutzers in der Zone vorhanden ist.
            testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankFavouritenAMIs WHERE user = :username_db AND ami = :ami_db AND zone = :zone_db", username_db=username, ami_db=ami, zone_db=zone)
            # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
            results = testen.fetch(100)
            for result in results:
              result.delete()

            # Erst testen, ob es dieses AMI überhaupt gibt.
            # Eine leere Liste für das AMI erzeugen
            ami_liste = []
            # Das AMIs in die Liste einfügen
            ami_liste.append(ami)

            conn_region, regionname = login(username)
            try:
              liste_favoriten_ami_images = conn_region.get_all_images(image_ids=ami_liste)
            except EC2ResponseError:
              fehlermeldung = "88"
              self.redirect('/images?message='+fehlermeldung)
            else:
              # Favorit erzeugen
              # Festlegen, was in den Datastore geschrieben werden soll
              favorit = KoalaCloudDatenbankFavouritenAMIs(ami=ami,
                                                          zone=zone,
                                                          user=username)
              # In den Datastore schreiben
              favorit.put()

              fehlermeldung = "83"
              self.redirect('/images?message='+fehlermeldung)

class Info(webapp.RequestHandler):
    def get(self):
        # Den Usernamen erfahren
        username = users.get_current_user()

        if users.get_current_user():
            # Nachsehen, ob eine Region/Zone ausgewählte wurde
            aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
            results = aktivezone.fetch(100)

            if not results:
              regionname = 'keine'
              zone_amazon = ""
            else:
              conn_region, regionname = login(username)
              zone_amazon = amazon_region(username)

            # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
            sprache = aktuelle_sprache(username)
            navigations_bar = navigations_bar_funktion(sprache)

            url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
            url_linktext = 'Logout'

        else:
            sprache = "en"
            navigations_bar = navigations_bar_funktion(sprache)
            url = users.create_login_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
            url_linktext = 'Login'
            regionname = 'keine'
            zone_amazon = ""

        zonen_liste = zonen_liste_funktion(username,sprache)

        template_values = {
        'navigations_bar': navigations_bar,
        'zone': regionname,
        'zone_amazon': zone_amazon,
        'url': url,
        'url_linktext': url_linktext,
        'zonen_liste': zonen_liste,
        }

        #if sprache == "de": naechse_seite = "info_de.html"
        #else:               naechse_seite = "info_en.html"
        #path = os.path.join(os.path.dirname(__file__), naechse_seite)
        path = os.path.join(os.path.dirname(__file__), "templates", sprache, "info.html")
        self.response.out.write(template.render(path,template_values))


class Images(webapp.RequestHandler):
    def get(self):
        # Den Usernamen erfahren
        username = users.get_current_user()
        # Eventuell vorhande Fehlermeldung holen
        message = self.request.get('message')
        if not username:
            self.redirect('/')

        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if results:
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache)
          # So wird der HTML-Code korrekt
          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          #url = users.create_logout_url(self.request.uri)
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache)
          # Herausfinden, in welcher Zone wird gerade sind
          # Die Ergebnisse des SELECT durchlaufen (ist nur eins) 
          for result in results:
            zone_in_der_wir_uns_befinden = result.aktivezone

          if regionname == "Amazon":

            if sprache != "de":
              sprache = "en"

            input_error_message = error_messages.get(message, {}).get(sprache)

            # Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
            if input_error_message == None:
              input_error_message = ""

            # Wenn die Nachricht grün formatiert werden soll...
            if message in ("83"):
              # wird sie hier, in der Hilfsfunktion grün formatiert
              input_error_message = format_error_message_green(input_error_message)
            # Ansonsten wird die Nachricht rot formatiert
            elif message in ("84", "85", "86", "87", "88"):
              input_error_message = format_error_message_red(input_error_message)
            else:
              input_error_message = ""

            # Nachsehen, ob schon AMI-Favoriten existieren
            aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankFavouritenAMIs WHERE user = :username_db AND zone = :zone_db", username_db=username, zone_db=zone_in_der_wir_uns_befinden)
            results = aktivezone.fetch(100)
            if results:
              # Eine leere Liste mit den AMIs der Favoriten erzeugen
              liste_ami_favoriten = []
              # Die Ergebnisse des SELECT durchlaufen
              for result in results:
                # Die AMIs in die Liste einfügen
                liste_ami_favoriten.append(result.ami)

              liste_favoriten_ami_images = conn_region.get_all_images(image_ids=liste_ami_favoriten)
              laenge_liste_favoriten_ami_images = len(liste_favoriten_ami_images)

              liste_favouriten = ''
              liste_favouriten = liste_favouriten + '<table border="3" cellspacing="0" cellpadding="5">'
              liste_favouriten = liste_favouriten + '<tr>'
              liste_favouriten = liste_favouriten + '<th>&nbsp;</th>'
              liste_favouriten = liste_favouriten + '<th>&nbsp;</th>'
              liste_favouriten = liste_favouriten + '<th align="center">Image ID</th>'
              liste_favouriten = liste_favouriten + '<th align="center">&nbsp;&nbsp;&nbsp;</th>'
              if sprache == "de":
                liste_favouriten = liste_favouriten + '<th align="center">Typ</th>'
              else:
                liste_favouriten = liste_favouriten + '<th align="center">Type</th>'
              liste_favouriten = liste_favouriten + '<th align="center">Manifest</th>'
              if sprache == "de":
                liste_favouriten = liste_favouriten + '<th align="center">Architektur</th>'
              else:
                liste_favouriten = liste_favouriten + '<th align="center">Architecture</th>'
              liste_favouriten = liste_favouriten + '<th align="center">Status</th>'
              if sprache == "de":
                liste_favouriten = liste_favouriten + '<th align="center">Besitzer</th>'
              else:
                liste_favouriten = liste_favouriten + '<th align="center">Owner</th>'
              liste_favouriten = liste_favouriten + '</tr>'
              for i in range(laenge_liste_favoriten_ami_images):
                  liste_favouriten = liste_favouriten + '<tr>'
                  #liste_favouriten = liste_favouriten + '<td>&nbsp;</td>'
                  liste_favouriten = liste_favouriten + '<td>'
                  if liste_favoriten_ami_images[i].type == u'machine':
                    if sprache == "de":
                      liste_favouriten = liste_favouriten + '<a href="/imagestarten?image='
                      liste_favouriten = liste_favouriten + liste_favoriten_ami_images[i].id
                      liste_favouriten = liste_favouriten + '&amp;arch='
                      liste_favouriten = liste_favouriten + liste_favoriten_ami_images[i].architecture
                      liste_favouriten = liste_favouriten + '"title="Instanz starten"><img src="bilder/plus.png" width="16" height="16" border="0" alt="Instanz starten"></a>'
                    else:
                      liste_favouriten = liste_favouriten + '<a href="/imagestarten?image='
                      liste_favouriten = liste_favouriten + liste_favoriten_ami_images[i].id
                      liste_favouriten = liste_favouriten + '&amp;arch='
                      liste_favouriten = liste_favouriten + liste_favoriten_ami_images[i].architecture
                      liste_favouriten = liste_favouriten + '"title="start instance"><img src="bilder/plus.png" width="16" height="16" border="0" alt="start instance"></a>'
                  else:
                    # Wenn es kein Machine-Image ist, dann das Feld leer lassen
                    liste_favouriten = liste_favouriten + '&nbsp;'
                  liste_favouriten = liste_favouriten + '</td>'
                  liste_favouriten = liste_favouriten + '<td>'
                  if sprache == "de":
                    liste_favouriten = liste_favouriten + '<a href="/favoritentfernen?ami='
                    liste_favouriten = liste_favouriten + liste_favoriten_ami_images[i].id
                    liste_favouriten = liste_favouriten + '&amp;zone='
                    liste_favouriten = liste_favouriten + zone_in_der_wir_uns_befinden
                    liste_favouriten = liste_favouriten + '"title="Favorit entfernen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Favorit entfernen"></a>'
                  else:
                    liste_favouriten = liste_favouriten + '<a href="/favoritentfernen?ami='
                    liste_favouriten = liste_favouriten + liste_favoriten_ami_images[i].id
                    liste_favouriten = liste_favouriten + '&amp;zone='
                    liste_favouriten = liste_favouriten + zone_in_der_wir_uns_befinden
                    liste_favouriten = liste_favouriten + '"title="erase from list"><img src="bilder/delete.png" width="16" height="16" border="0" alt="erase from list"></a>'
                  liste_favouriten = liste_favouriten + '</td>'

                  # Hier kommt die Spalte mit der Image-ID
                  liste_favouriten = liste_favouriten + '<td>'
                  liste_favouriten = liste_favouriten + '<tt>'
                  liste_favouriten = liste_favouriten + liste_favoriten_ami_images[i].id
                  liste_favouriten = liste_favouriten + '</tt>'
                  liste_favouriten = liste_favouriten + '</td>'

                  liste_favouriten = liste_favouriten + '<td align="center">'
                  beschreibung_in_kleinbuchstaben = liste_favoriten_ami_images[i].location.lower()
                  if beschreibung_in_kleinbuchstaben.find('fedora') != -1:
                    liste_favouriten = liste_favouriten + '<img src="bilder/fedora_icon_48.png" width="24" height="24" border="0" alt="Fedora">'
                  elif beschreibung_in_kleinbuchstaben.find('ubuntu') != -1:
                    liste_favouriten = liste_favouriten + '<img src="bilder/ubuntu_icon_48.png" width="24" height="24" border="0" alt="Ubuntu">'
                  elif beschreibung_in_kleinbuchstaben.find('debian') != -1:
                    liste_favouriten = liste_favouriten + '<img src="bilder/debian_icon_48.png" width="24" height="24" border="0" alt="Debian">'
                  elif beschreibung_in_kleinbuchstaben.find('gentoo') != -1:
                    liste_favouriten = liste_favouriten + '<img src="bilder/gentoo_icon_48.png" width="24" height="24" border="0" alt="Gentoo">'
                  elif beschreibung_in_kleinbuchstaben.find('suse') != -1:
                    liste_favouriten = liste_favouriten + '<img src="bilder/suse_icon_48.png" width="24" height="24" border="0" alt="SUSE">'
                  elif beschreibung_in_kleinbuchstaben.find('centos') != -1:
                    liste_favouriten = liste_favouriten + '<img src="bilder/centos_icon_48.png" width="24" height="24" border="0" alt="CentOS">'
                  elif beschreibung_in_kleinbuchstaben.find('redhat') != -1:
                    liste_favouriten = liste_favouriten + '<img src="bilder/redhat_icon_48.png" width="24" height="24" border="0" alt="RedHat">'
                  elif beschreibung_in_kleinbuchstaben.find('windows') != -1:
                    liste_favouriten = liste_favouriten + '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
                  elif beschreibung_in_kleinbuchstaben.find('win') != -1:
                    liste_favouriten = liste_favouriten + '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
                  elif beschreibung_in_kleinbuchstaben.find('opensolaris') != -1:
                    liste_favouriten = liste_favouriten + '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                  elif beschreibung_in_kleinbuchstaben.find('solaris') != -1:
                    liste_favouriten = liste_favouriten + '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                  elif beschreibung_in_kleinbuchstaben.find('osol') != -1:
                    liste_favouriten = liste_favouriten + '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                  else:
                    liste_favouriten = liste_favouriten + '<img src="bilder/linux_icon_48.gif" width="24" height="24" border="0" alt="Other Linux">'
                  liste_favouriten = liste_favouriten + '</td>'

                  # Hier kommt die Spalte mit dem Instanztyp
                  liste_favouriten = liste_favouriten + '<td align="center">'
                  liste_favouriten = liste_favouriten + liste_favoriten_ami_images[i].type
                  liste_favouriten = liste_favouriten + '</td>'

                  # Hier kommt die Spalte mit der Manifest-Datei
                  liste_favouriten = liste_favouriten + '<td>'
                  liste_favouriten = liste_favouriten + '<tt>'
                  liste_favouriten = liste_favouriten + liste_favoriten_ami_images[i].location
                  liste_favouriten = liste_favouriten + '</tt>'
                  liste_favouriten = liste_favouriten + '</td>'
                  liste_favouriten = liste_favouriten + '<td align="center">'
                  liste_favouriten = liste_favouriten + '<tt>'
                  liste_favouriten = liste_favouriten + liste_favoriten_ami_images[i].architecture
                  liste_favouriten = liste_favouriten + '</tt>'
                  liste_favouriten = liste_favouriten + '</td>'
                  if liste_favoriten_ami_images[i].state == u'available':
                    liste_favouriten = liste_favouriten + '<td bgcolor="#c3ddc3" align="center">'
                    liste_favouriten = liste_favouriten + liste_favoriten_ami_images[i].state
                  else:
                    liste_favouriten = liste_favouriten + '<td align="center">'
                    liste_favouriten = liste_favouriten + liste_favoriten_ami_images[i].state
                  liste_favouriten = liste_favouriten + '</td>'
                  liste_favouriten = liste_favouriten + '<td>'
                  liste_favouriten = liste_favouriten + liste_favoriten_ami_images[i].ownerId
                  liste_favouriten = liste_favouriten + '</td>'
                  liste_favouriten = liste_favouriten + '</tr>'
              liste_favouriten = liste_favouriten + '</table>'

            else:
              if sprache == "de":
                liste_favouriten = 'Es wurden noch keine Favoriten in der Zone '
                liste_favouriten = liste_favouriten + zone_in_der_wir_uns_befinden
                liste_favouriten = liste_favouriten + ' festgelegt'
              else:
                liste_favouriten = 'No favourite AMIs exist in the zone '
                liste_favouriten = liste_favouriten + zone_in_der_wir_uns_befinden

            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'zonen_liste': zonen_liste,
            'liste_favouriten': liste_favouriten,
            'zone_in_der_wir_uns_befinden': zone_in_der_wir_uns_befinden,
            'input_error_message': input_error_message,
            }

            #if sprache == "de": naechse_seite = "images_amazon_de.html"
            #else:               naechse_seite = "images_amazon_en.html"
            #path = os.path.join(os.path.dirname(__file__), naechse_seite)
            path = os.path.join(os.path.dirname(__file__), "templates", sprache, "images_amazon.html")
            self.response.out.write(template.render(path,template_values))

          # Die Region ist Eucalyptus oder Nimbus
          else:

            try:
              # Liste mit den Images
              liste_images = conn_region.get_all_images()
            except EC2ResponseError:
              # Wenn es nicht klappt...
              if sprache == "de":
                imagestabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
              else:
                imagestabelle = '<font color="red">An error occured</font>'
            except DownloadError:
              # Diese Exception hilft gegen diese beiden Fehler:
              # DownloadError: ApplicationError: 2 timed out
              # DownloadError: ApplicationError: 5
              if sprache == "de":
                imagestabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
              else:
                imagestabelle = '<font color="red">A timeout error occured</font>'
            else:
              # Wenn es geklappt hat...
              # Anzahl der Images in der Liste
              laenge_liste_images = len(liste_images)

              #self.response.out.write(laenge_liste_images)

              if laenge_liste_images == 0:
                # Wenn noch keine Images in der Region existieren
                if sprache == "de":
                  imagestabelle = 'Es sind keine Images in der Region vorhanden.'
                else:
                  imagestabelle = 'Still no images exist inside this region.'
              else:
                # Wenn schon Images in der Region existieren
                imagestabelle = ''
                imagestabelle = imagestabelle + '<table border="3" cellspacing="0" cellpadding="5">'
                imagestabelle = imagestabelle + '<tr>'
                imagestabelle = imagestabelle + '<th>&nbsp;</th>'
                imagestabelle = imagestabelle + '<th align="center">Image ID</th>'
                imagestabelle = imagestabelle + '<th align="center">&nbsp;&nbsp;&nbsp;</th>'
                if sprache == "de":
                  imagestabelle = imagestabelle + '<th align="center">Typ</th>'
                else:
                  imagestabelle = imagestabelle + '<th align="center">Type</th>'
                imagestabelle = imagestabelle + '<th align="center">Manifest</th>'
                if sprache == "de":
                  imagestabelle = imagestabelle + '<th align="center">Architektur</th>'
                else:
                  imagestabelle = imagestabelle + '<th align="center">Architecture</th>'
                imagestabelle = imagestabelle + '<th align="center">Status</th>'
                if sprache == "de":
                  imagestabelle = imagestabelle + '<th align="center">Besitzer</th>'
                else:
                  imagestabelle = imagestabelle + '<th align="center">Owner</th>'
                imagestabelle = imagestabelle + '</tr>'
                for i in range(laenge_liste_images):
                    imagestabelle = imagestabelle + '<tr>'
                    #imagestabelle = imagestabelle + '<td>&nbsp;</td>'
                    imagestabelle = imagestabelle + '<td>'
                    if liste_images[i].type == u'machine':
                      if sprache == "de":
                        imagestabelle = imagestabelle + '<a href="/imagestarten?image='
                        imagestabelle = imagestabelle + liste_images[i].id
                        imagestabelle = imagestabelle + '"title="Instanz starten"><img src="bilder/plus.png" width="16" height="16" border="0" alt="Instanz starten"></a>'
                      else:
                        imagestabelle = imagestabelle + '<a href="/imagestarten?image='
                        imagestabelle = imagestabelle + liste_images[i].id
                        imagestabelle = imagestabelle + '"title="start instance"><img src="bilder/plus.png" width="16" height="16" border="0" alt="start instance"></a>'
                    else:
                      # Wenn es kein Machine-Image ist, dann das Feld leer lassen
                      imagestabelle = imagestabelle + '&nbsp;'
                    imagestabelle = imagestabelle + '</td>'
                    imagestabelle = imagestabelle + '<td>'
                    imagestabelle = imagestabelle + '<tt>'
                    imagestabelle = imagestabelle + liste_images[i].id
                    imagestabelle = imagestabelle + '</tt>'
                    imagestabelle = imagestabelle + '</td>'


                    imagestabelle = imagestabelle + '<td align="center">'
                    beschreibung_in_kleinbuchstaben = liste_images[i].location.lower()
                    if str(liste_images[i].type) == "kernel":
                      imagestabelle = imagestabelle + '<img src="bilder/1pixel.gif" width="24" height="24" border="0" alt="">'
                    elif str(liste_images[i].type) == "ramdisk":
                      imagestabelle = imagestabelle + '<img src="bilder/1pixel.gif" width="24" height="24" border="0" alt="">'
                    elif str(liste_images[i].type) == "machine":
                      if beschreibung_in_kleinbuchstaben.find('fedora') != -1:
                        imagestabelle = imagestabelle + '<img src="bilder/fedora_icon_48.png" width="24" height="24" border="0" alt="Fedora">'
                      elif beschreibung_in_kleinbuchstaben.find('ubuntu') != -1:
                        imagestabelle = imagestabelle + '<img src="bilder/ubuntu_icon_48.png" width="24" height="24" border="0" alt="Ubuntu">'
                      elif beschreibung_in_kleinbuchstaben.find('debian') != -1:
                        imagestabelle = imagestabelle + '<img src="bilder/debian_icon_48.png" width="24" height="24" border="0" alt="Debian">'
                      elif beschreibung_in_kleinbuchstaben.find('gentoo') != -1:
                        imagestabelle = imagestabelle + '<img src="bilder/gentoo_icon_48.png" width="24" height="24" border="0" alt="Gentoo">'
                      elif beschreibung_in_kleinbuchstaben.find('suse') != -1:
                        imagestabelle = imagestabelle + '<img src="bilder/suse_icon_48.png" width="24" height="24" border="0" alt="SUSE">'
                      elif beschreibung_in_kleinbuchstaben.find('centos') != -1:
                        imagestabelle = imagestabelle + '<img src="bilder/centos_icon_48.png" width="24" height="24" border="0" alt="CentOS">'
                      elif beschreibung_in_kleinbuchstaben.find('redhat') != -1:
                        imagestabelle = imagestabelle + '<img src="bilder/redhat_icon_48.png" width="24" height="24" border="0" alt="RedHat">'
                      elif beschreibung_in_kleinbuchstaben.find('windows') != -1:
                        imagestabelle = imagestabelle + '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
                      elif beschreibung_in_kleinbuchstaben.find('win') != -1:
                        imagestabelle = imagestabelle + '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
                      elif beschreibung_in_kleinbuchstaben.find('opensolaris') != -1:
                        imagestabelle = imagestabelle + '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                      elif beschreibung_in_kleinbuchstaben.find('solaris') != -1:
                        imagestabelle = imagestabelle + '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                      elif beschreibung_in_kleinbuchstaben.find('osol') != -1:
                        imagestabelle = imagestabelle + '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                      else:
                        imagestabelle = imagestabelle + '<img src="bilder/linux_icon_48.gif" width="24" height="24" border="0" alt="Other Linux">'
                    else:
                      imagestabelle = imagestabelle + '<img src="bilder/1pixel.gif" width="24" height="24" border="0" alt="">'
                    imagestabelle = imagestabelle + '</td>'

                    imagestabelle = imagestabelle + '<td align="center">'
                    imagestabelle = imagestabelle + liste_images[i].type
                    imagestabelle = imagestabelle + '</td>'
                    imagestabelle = imagestabelle + '<td>'
                    imagestabelle = imagestabelle + '<tt>'
                    imagestabelle = imagestabelle + liste_images[i].location
                    imagestabelle = imagestabelle + '</tt>'
                    imagestabelle = imagestabelle + '</td>'
                    imagestabelle = imagestabelle + '<td align="center">'
                    imagestabelle = imagestabelle + '<tt>'
                    imagestabelle = imagestabelle + liste_images[i].architecture
                    imagestabelle = imagestabelle + '</tt>'
                    imagestabelle = imagestabelle + '</td>'
                    if liste_images[i].state == u'available':
                      imagestabelle = imagestabelle + '<td bgcolor="#c3ddc3" align="center">'
                      imagestabelle = imagestabelle + liste_images[i].state
                    else:
                      imagestabelle = imagestabelle + '<td align="center">'
                      imagestabelle = imagestabelle + liste_images[i].state
                    imagestabelle = imagestabelle + '</td>'
                    imagestabelle = imagestabelle + '<td>'
                    imagestabelle = imagestabelle + liste_images[i].ownerId
                    imagestabelle = imagestabelle + '</td>'
                    imagestabelle = imagestabelle + '</tr>'
                imagestabelle = imagestabelle + '</table>'

            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'imagestabelle': imagestabelle,
            'zonen_liste': zonen_liste,
            }

            #if sprache == "de": naechse_seite = "images_de.html"
            #else:               naechse_seite = "images_en.html"
            #path = os.path.join(os.path.dirname(__file__), naechse_seite)
            path = os.path.join(os.path.dirname(__file__), "templates", sprache, "images.html")
            self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')

class ImageStarten(webapp.RequestHandler):
    def get(self):
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')
        # Die ID des zu startenden Images holen
        image = self.request.get('image')
        # Die Architektur des zu startenden Images holen
        arch = self.request.get('arch')

        sprache = aktuelle_sprache(username)
        navigations_bar = navigations_bar_funktion(sprache)
        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if not results:
          regionname = 'keine'
          zone_amazon = ""
        else:
          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

        # So wird der HTML-Code korrekt
        url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
        #url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'

        zonen_liste = zonen_liste_funktion(username,sprache)

        for result in results:
          if result.zugangstyp == "Amazon":
            imageliste = [image]
            # Liste mit den Images
            liste_images = conn_region.get_all_images(image_ids=imageliste)  
            # Anzahl der Images in der Liste
            laenge_liste_images = len(liste_images)
            for i in range(laenge_liste_images):
              if liste_images[i].id == image:
                manifest = str(liste_images[i].location)
          else:
            # Liste mit den Images
            liste_images = conn_region.get_all_images()
            # Anzahl der Images in der Liste
            laenge_liste_images = len(liste_images)
            for i in range(laenge_liste_images):
              if liste_images[i].id == image:
                manifest = str(liste_images[i].location)


        if result.zugangstyp == "Nimbus":

          imagetextfeld = '<input name="image_id" type="text" size="70" maxlength="70" value="'
          imagetextfeld = imagetextfeld + image
          imagetextfeld = imagetextfeld + '" readonly>'

          manifesttextfeld = '<input name="image_manifest" type="text" size="70" maxlength="70" value="'
          manifesttextfeld = manifesttextfeld + manifest
          manifesttextfeld = manifesttextfeld + '" readonly>'

          if sprache == "de": number_instances_min_anfang = "Instanzen (min):"
          else:               number_instances_min_anfang = "Instances (min):"

          if sprache == "de": number_instances_max_anfang = "Instanzen (max):"
          else:               number_instances_max_anfang = "Instances (max):"

          if sprache == "de": image_starten_ueberschrift_anfang = "Image starten: "
          else:               image_starten_ueberschrift_anfang = "Start image: "

          if sprache == "de": value_button_image_starten = "Image starten"
          else:               value_button_image_starten = "start image"

          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'image': imagetextfeld,
          'manifest': manifesttextfeld,
          'zonen_liste': zonen_liste,
          'number_instances_max_anfang': number_instances_max_anfang,
          'number_instances_min_anfang': number_instances_min_anfang,
          'image_starten_ueberschrift_anfang': image_starten_ueberschrift_anfang,
          'value_button_image_starten': value_button_image_starten,
          }

          #path = os.path.join(os.path.dirname(__file__), 'image_starten_nimbus.html')
          path = os.path.join(os.path.dirname(__file__), "templates", sprache, "image_starten_nimbus.html")
          self.response.out.write(template.render(path,template_values))

        else: # Wenn es nicht Nimbus ist


          # Wenn es Amazon EC2 ist
          if result.zugangstyp == "Amazon":
            if arch == "i386":
              # Liste mit den Instanz-Typen wenn es ein 32-Bit Image ist
              liste_instanztypen_eucalyptus = ["m1.small", "c1.medium"]
            else:
              # Liste mit den Instanz-Typen wenn es ein 64-Bit Image ist
              liste_instanztypen_eucalyptus = ["m1.large", "m1.xlarge", "m2.xlarge", "m2.2xlarge", "m2.4xlarge", "c1.xlarge"]
            # Anzahl der Elemente in der Liste
            laenge_liste_instanztypen_eucalyptus = len(liste_instanztypen_eucalyptus)

            instance_types_liste = ""
            for i in range(laenge_liste_instanztypen_eucalyptus):
                if i == 0:
                  instance_types_liste = instance_types_liste + '<option selected="selected">'
                else:
                  instance_types_liste = instance_types_liste + "<option>"
                instance_types_liste = instance_types_liste + liste_instanztypen_eucalyptus[i]
                instance_types_liste = instance_types_liste + "</option>"

            instance_types_liste_laenge = laenge_liste_instanztypen_eucalyptus
          elif result.zugangstyp == "Nimbus":
            # Wenn es Nimbus ist
            instance_types_liste_laenge = 0
            liste_instanztypen_eucalyptus = []
            laenge_liste_instanztypen_eucalyptus = 0
            instance_types_liste = []
          else:
            # Wenn es Eucalyptus ist
            liste_instanztypen_eucalyptus = ["m1.small", "c1.medium", "m1.large", "m1.xlarge", "c1.xlarge"] 
            # Anzahl der Elemente in der Liste mit den Instanz-Typen
            laenge_liste_instanztypen_eucalyptus = len(liste_instanztypen_eucalyptus) 

            instance_types_liste = ""
            for i in range(laenge_liste_instanztypen_eucalyptus):
                if i == 0:
                  instance_types_liste = instance_types_liste + '<option selected="selected">'
                else:
                  instance_types_liste = instance_types_liste + "<option>"
                instance_types_liste = instance_types_liste + liste_instanztypen_eucalyptus[i]
                instance_types_liste = instance_types_liste + "</option>"

            instance_types_liste_laenge = laenge_liste_instanztypen_eucalyptus

          # Liste mit den Zonen
          liste_zonen = conn_region.get_all_zones()
          # Anzahl der Elemente in der Liste
          laenge_liste_zonen = len(liste_zonen)

          # Hier wird die Auswahlliste der Zonen erzeugt
          # Diese Auswahlliste ist zum Erzeugen neuer Volumes notwendig
          zonen_in_der_region = ''
          for i in range(laenge_liste_zonen):
              zonen_in_der_region = zonen_in_der_region + "<option>"
              zonen_in_der_region = zonen_in_der_region + liste_zonen[i].name
              zonen_in_der_region = zonen_in_der_region + "</option>"

          # Liste mit den Schlüsseln
          liste_key_pairs = conn_region.get_all_key_pairs()
          # Anzahl der Elemente in der Liste
          laenge_liste_keys = len(liste_key_pairs)

          keys_liste = ''
          if laenge_liste_keys == 0:
            if sprache == "de":
              keys_liste = '<font color="red">Es sind keine Schl&uuml in der Zone vorhanden</font>'
            else:
              keys_liste = '<font color="red">No keypairs exist inside this security zone</font>'
          elif laenge_liste_keys == 1:
            keys_liste = '<input name="keys_liste" type="text" size="70" maxlength="70" value="'
            keys_liste = keys_liste + liste_key_pairs[0].name
            keys_liste = keys_liste + '" readonly>'
          else:
            keys_liste = keys_liste + '<select name="keys_liste" size="'
            keys_liste = keys_liste + str(laenge_liste_keys)
            keys_liste = keys_liste + '">'
            for i in range(laenge_liste_keys):
              if i == 0:
                keys_liste = keys_liste + '<option selected="selected">'
              else:
                keys_liste = keys_liste + '<option>'
              keys_liste = keys_liste + liste_key_pairs[i].name
              keys_liste = keys_liste + '</option>'
            keys_liste = keys_liste + '</select>'

          if sprache == "de": keys_liste_anfang = "Schl&uuml;ssel"
          else:               keys_liste_anfang = "Keypair"

          if sprache == "de": number_instances_min_anfang = "Instanzen (min):"
          else:               number_instances_min_anfang = "Instances (min):"

          if sprache == "de": number_instances_max_anfang = "Instanzen (max):"
          else:               number_instances_max_anfang = "Instances (max):"

          if sprache == "de": typ_anfang = "Typ: "
          else:               typ_anfang = "Type: "

          if sprache == "de": image_starten_ueberschrift_anfang = "Image starten:"
          else:               image_starten_ueberschrift_anfang = "Start image:"

          if sprache == "de": value_button_image_starten = "Image starten"
          else:               value_button_image_starten = "start image"

          if sprache == "de": nicht_zwingend_notwendig = "Nicht zwingend notwendig"
          else:               nicht_zwingend_notwendig = "Not essential"

          if sprache == "de": zonen_anfang = "Verf&uuml;gbarkeitszone:"
          else:               zonen_anfang = "Availability Zone:"

          # Liste mit den Security Groups
          liste_security_groups = conn_region.get_all_security_groups()
          # Anzahl der Elemente in der Liste
          laenge_liste_security_groups = len(liste_security_groups)

          gruppen_liste = ''
          if laenge_liste_security_groups == 0:
            if sprache == "de":
              gruppen_liste = '<font color="red">Es sind keine Sicherheitsgruppen in der Zone vorhanden</font>'
            else:
              gruppen_liste = '<font color="red">No Security Groups exist inside this security zone</font>'
          elif laenge_liste_security_groups == 1:
            gruppen_liste = liste_security_groups[0].name
          else:
            gruppen_liste = gruppen_liste + '<select name="gruppen_liste" size="'
            gruppen_liste = gruppen_liste + str(laenge_liste_security_groups)
            gruppen_liste = gruppen_liste + '">'
            for i in range(laenge_liste_security_groups):
              if i == 0:
                gruppen_liste = gruppen_liste + '<option selected="selected">'
              else:
                gruppen_liste = gruppen_liste + '<option>'
              gruppen_liste = gruppen_liste + liste_security_groups[i].name
              #gruppen_liste = gruppen_liste + ' ('
              #gruppen_liste = gruppen_liste + liste_security_groups[i].owner_id
              #gruppen_liste = gruppen_liste + ')'
              gruppen_liste = gruppen_liste + '</option>'
            gruppen_liste = gruppen_liste + '</select>'

          imagetextfeld = '<input name="image_id" type="text" size="70" maxlength="70" value="'
          imagetextfeld = imagetextfeld + image
          imagetextfeld = imagetextfeld + '" readonly>'

          manifesttextfeld = '<input name="image_manifest" type="text" size="70" maxlength="70" value="'
          manifesttextfeld = manifesttextfeld + manifest
          manifesttextfeld = manifesttextfeld + '" readonly>'

          # Wenn es Amazon EC2 ist
          if result.aktivezone == "us-east-1" or result.aktivezone == "eu-west-1" or result.aktivezone == "us-west-1":
            if arch == "i386": # 32-Bit Image
              tabelle_ec2_instanztypen = '<table border="3" cellspacing="0" cellpadding="5">'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<tr>'
              if sprache == "de": # Wenn die Sprache Deutsch ist...
                tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<th>Instanztyp</th>'
              else:               # Wenn die Sprache Englisch ist...
                tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<th>Type</th>'
              if sprache == "de": # Wenn die Sprache Deutsch ist...
                tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<th>Architektur</th>'
              else:               # Wenn die Sprache Englisch ist...
                tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<th>Architecture</th>'
              if sprache == "de": # Wenn die Sprache Deutsch ist...
                tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<th>Virtuelle Cores</th>'
              else:               # Wenn die Sprache Englisch ist...
                tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<th>Virtual Cores</th>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<th>EC2 Compute Units</th>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '</tr>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<tr>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td><tt>m1.small</tt></td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">32-Bit</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">1</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">1</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '</tr>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<tr>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td><tt>c1.medium</tt></td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">32-Bit</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">2</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">5</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '</tr>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '</table'
            elif arch == "x86_64": # 64-Bit Image
              tabelle_ec2_instanztypen = '<table border="3" cellspacing="0" cellpadding="5">'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<tr>'
              if sprache == "de": # Wenn die Sprache Deutsch ist...
                tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<th>Instanztyp</th>'
              else:               # Wenn die Sprache Englisch ist...
                tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<th>Type</th>'
              if sprache == "de": # Wenn die Sprache Deutsch ist...
                tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<th>Architektur</th>'
              else:               # Wenn die Sprache Englisch ist...
                tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<th>Architecture</th>'
              if sprache == "de": # Wenn die Sprache Deutsch ist...
                tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<th>Virtuelle Cores</th>'
              else:               # Wenn die Sprache Englisch ist...
                tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<th>Virtual Cores</th>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<th>EC2 Compute Units</th>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '</tr>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<tr>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td><tt>m1.large</tt></td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">64-Bit</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">2</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">4</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '</tr>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<tr>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td><tt>m1.xlarge</tt></td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">64-Bit</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">4</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">8</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '</tr>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<tr>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td><tt>m2.xlarge</tt></td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">64-Bit</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">2</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">6.5</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '</tr>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<tr>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td><tt>m2.2xlarge</tt></td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">64-Bit</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">4</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">13</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '</tr>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<tr>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td><tt>m2.4xlarge</tt></td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">64-Bit</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">8</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">26</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '</tr>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<tr>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td><tt>c1.xlarge</tt></td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">64-Bit</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">8</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '<td align="center">20</td>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '</tr>'
              tabelle_ec2_instanztypen = tabelle_ec2_instanztypen + '</table'
            else:
              # Wenn es etwas ganz anderes ist...?
              tabelle_ec2_instanztypen = ''
          else:
            # wenn es Eucalyptus ist
            tabelle_ec2_instanztypen = ''

          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'image': imagetextfeld,
          'manifest': manifesttextfeld,
          'instance_types_liste': instance_types_liste,
          'instance_types_liste_laenge': instance_types_liste_laenge,
          'keys_liste': keys_liste,
          'keys_liste_anfang': keys_liste_anfang,
          'gruppen_liste': gruppen_liste,
          'zonen_liste': zonen_liste,
          'number_instances_max_anfang': number_instances_max_anfang,
          'number_instances_min_anfang': number_instances_min_anfang,
          'typ_anfang': typ_anfang,
          'image_starten_ueberschrift_anfang': image_starten_ueberschrift_anfang,
          'value_button_image_starten': value_button_image_starten,
          'nicht_zwingend_notwendig': nicht_zwingend_notwendig,
          'tabelle_ec2_instanztypen':tabelle_ec2_instanztypen,
          'zonen_in_der_region': zonen_in_der_region,
          'laenge_liste_zonen': laenge_liste_zonen,
          'zonen_anfang': zonen_anfang,
          }

          path = os.path.join(os.path.dirname(__file__), "templates", sprache, "image_starten.html")
          self.response.out.write(template.render(path,template_values))


class ConsoleOutput(webapp.RequestHandler):
    def get(self):
        # self.response.out.write('posted!')
        # Den Usernamen erfahren
        username = users.get_current_user()  
        if not username:
            self.redirect('/')
        # Die ID der zu löschenden Instanz holen
        instance_id = self.request.get('id')

        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if results:
          # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache)

          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache)
          fehlermeldung = ""

          try:
            console_output = conn_region.get_console_output(str(instance_id))
          except EC2ResponseError:
            # Wenn es nicht klappt...
            if sprache == "de":
              fehlermeldung = '<p>&nbsp;</p> <font color="red">Beim Versuch die Konsolenausgabe der Instanz zu holen, kam es zu einem Fehler</font>'
            else:
              fehlermeldung = '<p>&nbsp;</p> <font color="red">While the system tried to get the console output, an error occured</font>'
            console_ausgabe = ''

            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'instance_id': instance_id,
            'zone': regionname,
            'fehlermeldung': fehlermeldung,
            'zone_amazon': zone_amazon,
            'console_ausgabe': console_ausgabe,
            'zonen_liste': zonen_liste,
            }

            #if sprache == "de": naechse_seite = "console_output.html"
            #else:               naechse_seite = "console_output_en.html"
            #path = os.path.join(os.path.dirname(__file__), naechse_seite)
            path = os.path.join(os.path.dirname(__file__), "templates", sprache, "console_output.html")
            self.response.out.write(template.render(path,template_values))
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            if sprache == "de":
              fehlermeldung = '<p>&nbsp;</p> <font color="red">Beim Versuch die Konsolenausgabe der Instanz zu holen, kam es zu einem Timeout-Fehler.</font>'
            else:
              fehlermeldung = '<p>&nbsp;</p> <font color="red">While the system tried to get the console output, a timeout error occured.</font>'
            console_ausgabe = ''

            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'instance_id': instance_id,
            'zone': regionname,
            'fehlermeldung': fehlermeldung,
            'zone_amazon': zone_amazon,
            'console_ausgabe': console_ausgabe,
            'zonen_liste': zonen_liste,
            }

            #if sprache == "de": naechse_seite = "console_output.html"
            #else:               naechse_seite = "console_output_en.html"
            #path = os.path.join(os.path.dirname(__file__), naechse_seite)
            path = os.path.join(os.path.dirname(__file__), "templates", sprache, "console_output.html")
            self.response.out.write(template.render(path,template_values))
          else:
            # Wenn es geklappt hat...

            if console_output.output == '':
              if sprache == "de":
                console_ausgabe = '<font color="green">Es liegt noch keine Konsolenausgabe vor</font>'
              else:
                console_ausgabe = '<font color="green">Still no console output exists</font>'
            else:
              console_ausgabe = ''
              console_ausgabe = console_ausgabe + '<tt>'
              console_ausgabe = console_ausgabe + console_output.output.replace("\n","<BR>").replace(" ", "&nbsp;").replace("", "&nbsp;")
              console_ausgabe = console_ausgabe + '</tt>'

            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'instance_id': instance_id,
            'zone': regionname,
            'fehlermeldung': fehlermeldung,
            'zone_amazon': zone_amazon,
            'console_ausgabe': console_ausgabe,
            'zonen_liste': zonen_liste,
            }

            #if sprache == "de": naechse_seite = "console_output_de.html"
            #else:               naechse_seite = "console_output_en.html"
            #path = os.path.join(os.path.dirname(__file__), naechse_seite)
            path = os.path.join(os.path.dirname(__file__), "templates", sprache, "console_output.html")
            self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')


class PersoenlicheDatanLoeschen(webapp.RequestHandler):
    def get(self):
        # Den Usernamen erfahren
        username = users.get_current_user()

        # Überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
        results = aktivezone.fetch(100)
        for result in results:
          result.delete()

        # Überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
        sprache = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankSprache WHERE user = :username_db", username_db=username)
        # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
        results = sprache.fetch(100)
        for result in results:
          result.delete()

        # Überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
        testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db", username_db=username)
        # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
        results = testen.fetch(100)
        for result in results:
          result.delete()

        # Überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
        testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankFavouritenAMIs WHERE user = :username_db", username_db=username)
        # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
        results = testen.fetch(100)
        for result in results:
          result.delete()

        self.redirect('/')


class PersoenlicheFavoritenLoeschen(webapp.RequestHandler):
    def get(self):
        # Den Usernamen erfahren
        username = users.get_current_user()

        # Überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
        testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankFavouritenAMIs WHERE user = :username_db", username_db=username)
        # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
        results = testen.fetch(100)
        for result in results:
          result.delete()

        self.redirect('/')


class ZugangEinrichten(webapp.RequestHandler):
    def post(self):
        nameregion = self.request.get('nameregion')
        endpointurl = self.request.get('endpointurl')
        port = self.request.get('port')
        accesskey = self.request.get('accesskey')
        secretaccesskey = self.request.get('secretaccesskey')
        typ = self.request.get('typ')
        # Den Usernamen erfahren
        username = users.get_current_user()
        # self.response.out.write('posted!')

        if users.get_current_user():

          # Wenn ein EC2-Zugang angelegt werden soll
          if typ == "ec2":

            if accesskey == "" and secretaccesskey == "":
              # Wenn kein Access Key und kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Access Key und keinen Secret Access Key angegeben"
              fehlermeldung = "89"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif accesskey == "": 
              #fehlermeldung = "Sie haben keinen Access Key angegeben"
              fehlermeldung = "90"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif secretaccesskey == "": 
              # Wenn kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Secret Access Key angegeben"
              fehlermeldung = "91"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', accesskey) != None:
              # Wenn der Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "94"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\/a-zA-Z0-9+=]', secretaccesskey) != None:
              # Wenn der Secret Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Secret Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "95"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            else: # Access Key und Secret Access Key wurden angegeben
              # Prüfen, ob die Zugangsdaten für EC2 korrekt sind
              try:
                # Zugangsdaten testen
                region = RegionInfo(name="ec2", endpoint="ec2.amazonaws.com")
                connection = boto.connect_ec2(aws_access_key_id=accesskey,
                                            aws_secret_access_key=secretaccesskey,
                                            is_secure=False,
                                            region=region,
                                            #port=8773,
                                            path="/")

                liste_zonen = connection.get_all_zones()
              except EC2ResponseError:
                # Wenn die Zugangsdaten falsch sind, dann wird umgeleitet zur Regionenseite
                fehlermeldung = "98"
                self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
              else:
                # Wenn die Zugangsdaten für EC2 korrekt sind, dann wird hier weiter gemacht...
                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db="Amazon")
                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                secretaccesskey_encrypted = xor_crypt_string(str(secretaccesskey), key=str(username))
                secretaccesskey_base64encoded = base64.b64encode(secretaccesskey_encrypted)
                logindaten = KoalaCloudDatenbank(regionname="us-east-1",
                                                eucalyptusname="Amazon",
                                                accesskey=accesskey,
                                                endpointurl="ec2.amazonaws.com",
                                                zugangstyp="Amazon",
                                                secretaccesskey=secretaccesskey_base64encoded,
                                                port=None,
                                                user=username)
                # In den Datastore schreiben
                logindaten.put()

                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                logindaten = KoalaCloudDatenbankAktiveZone(aktivezone="us-east-1",
                                                           user=username)
                # In den Datastore schreiben
                logindaten.put()

                self.redirect('/regionen')

          # Wenn ein Nimbus-Zugang angelegt werden soll
          elif typ == "nimbus":
            if accesskey == "" and secretaccesskey == "":
              # Wenn kein Access Key und kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Access Key und keinen Secret Access Key angegeben"
              fehlermeldung = "89"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif accesskey == "": 
              #fehlermeldung = "Sie haben keinen Access Key angegeben"
              fehlermeldung = "90"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif secretaccesskey == "": 
              # Wenn kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Secret Access Key angegeben"
              fehlermeldung = "91"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif nameregion == "": 
              # Wenn kein Name eingegeben wurde
              fehlermeldung = "92"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif endpointurl == "": 
              # Wenn keine Endpoint URL eingegeben wurde
              fehlermeldung = "93"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', accesskey) != None:
              # Wenn der Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "94"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\/a-zA-Z0-9+=]', secretaccesskey) != None:
              # Wenn der Secret Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Secret Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "95"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\ \-._a-zA-Z0-9]', nameregion) != None:
              # Wenn der Name nicht erlaubte Zeichen enthält
              fehlermeldung = "96"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\ \/\-.:_a-zA-Z0-9]', endpointurl) != None:
              # Wenn die Endpoint URL nicht erlaubte Zeichen enthält
              fehlermeldung = "97"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            else:
              # Access Key und  Secret Access Key wurden angegeben

              # Prüfen, ob die Zugangsdaten für Eucalyptus korrekt sind
              try:
                # Zugangsdaten testen
                port = int(port)
                connection = boto.connect_ec2(str(accesskey), str(secretaccesskey), port=port)
                connection.host = str(endpointurl)

                liste_zonen = connection.get_all_zones()

              except:
                # Wenn die Zugangsdaten falsch sind, dann wird umgeleitet zur Regionenseite
                fehlermeldung = "98"
                self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
              else:
                # Wenn die Zugangsdaten für Nimbus korrekt sind, dann wird hier weiter gemacht...

                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND regionname = :regionname_db AND eucalyptusname = :eucalyptusname_db", username_db=username, regionname_db="nimbus", eucalyptusname_db=nameregion)
                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                port = str(port) # Sicherstellen, dass der Port ein String ist
                secretaccesskey_encrypted = xor_crypt_string(str(secretaccesskey), key=str(username))
                secretaccesskey_base64encoded = base64.b64encode(secretaccesskey_encrypted)
                logindaten = KoalaCloudDatenbank(regionname=typ,
                                                eucalyptusname=nameregion,
                                                accesskey=accesskey,
                                                endpointurl=endpointurl,
                                                zugangstyp="Nimbus",
                                                secretaccesskey=secretaccesskey_base64encoded,
                                                port=port,
                                                user=username)
                # In den Datastore schreiben
                logindaten.put()

                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                logindaten = KoalaCloudDatenbankAktiveZone(aktivezone=nameregion,
                                                          user=username)
                # In den Datastore schreiben
                logindaten.put()

                self.redirect('/regionen')


          # Wenn ein Eucalyptus-Zugang angelegt werden soll
          else:
            if accesskey == "" and secretaccesskey == "":
              # Wenn kein Access Key und kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Access Key und keinen Secret Access Key angegeben"
              fehlermeldung = "89"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif accesskey == "": 
              #fehlermeldung = "Sie haben keinen Access Key angegeben"
              fehlermeldung = "90"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif secretaccesskey == "": 
              # Wenn kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Secret Access Key angegeben"
              fehlermeldung = "91"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif nameregion == "": 
              # Wenn kein Name eingegeben wurde
              fehlermeldung = "92"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif endpointurl == "": 
              # Wenn keine Endpoint URL eingegeben wurde
              fehlermeldung = "93"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', accesskey) != None:
              # Wenn der Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "94"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\/a-zA-Z0-9+=]', secretaccesskey) != None:
              # Wenn der Secret Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Secret Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "95"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\ \-._a-zA-Z0-9]', nameregion) != None:
              # Wenn der Name nicht erlaubte Zeichen enthält
              fehlermeldung = "96"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\ \/\-.:_a-zA-Z0-9]', endpointurl) != None:
              # Wenn die Endpoint URL nicht erlaubte Zeichen enthält
              fehlermeldung = "97"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            else:
              # Access Key und  Secret Access Key wurden angegeben

              # Prüfen, ob die Zugangsdaten für Eucalyptus korrekt sind
              try:
                # Zugangsdaten testen
                port = int(port)
                region = RegionInfo(name=nameregion, endpoint=endpointurl)
                connection = boto.connect_ec2(aws_access_key_id=accesskey,
                                              aws_secret_access_key=secretaccesskey,
                                              is_secure=False,
                                              region=region,
                                              port=port,
                                              path="/services/Eucalyptus")

                liste_zonen = connection.get_all_zones()
              except:
                # Wenn die Zugangsdaten falsch sind, dann wird umgeleitet zur Regionenseite
                fehlermeldung = "98"
                self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
              else:
                # Wenn die Zugangsdaten für Eucalyptus korrekt sind, dann wird hier weiter gemacht...

                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND regionname = :regionname_db AND eucalyptusname = :eucalyptusname_db", username_db=username, regionname_db="eucalyptus", eucalyptusname_db=nameregion)
                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                # Sicherstellen, dass der Port ein String ist
                port = str(port)
                secretaccesskey_encrypted = xor_crypt_string(str(secretaccesskey), key=str(username))
                secretaccesskey_base64encoded = base64.b64encode(secretaccesskey_encrypted)
                logindaten = KoalaCloudDatenbank(regionname=typ,
                                                eucalyptusname=nameregion,
                                                accesskey=accesskey,
                                                endpointurl=endpointurl,
                                                zugangstyp="Eucalyptus",
                                                secretaccesskey=secretaccesskey_base64encoded,
                                                port=port,
                                                user=username)
                # In den Datastore schreiben
                logindaten.put()

                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                logindaten = KoalaCloudDatenbankAktiveZone(aktivezone=nameregion,
                                                          user=username)
                # In den Datastore schreiben
                logindaten.put()

                self.redirect('/regionen')
        else:
            self.redirect('/')


class InstanzAnlegenNimbus(webapp.RequestHandler):
    def post(self):
        #self.response.out.write('posted!')
        image_manifest = self.request.get('image_manifest')
        image_id = self.request.get('image_id')
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')

        conn_region, regionname = login(username)

        try:
          # Instanz(en) anlegen
          reservation = conn_region.run_instances(image_id)
        except EC2ResponseError:
          # Wenn es nicht geklappt hat
          fehlermeldung = "78"
          self.redirect('/instanzen?message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/instanzen?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat
          fehlermeldung = "77"
          self.redirect('/instanzen?message='+fehlermeldung)



class S3(webapp.RequestHandler):
    def get(self):
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

        if results:
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
          path = os.path.join(os.path.dirname(__file__), "templates", sprache, "s3.html")
          self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')



class BucketErzeugen(webapp.RequestHandler):
    def post(self):
        # self.response.out.write('posted!')
        # Die Eingabe aus dem Formular holen
        neuerbucketname = self.request.get('bucketname')

        # Den Usernamen erfahren
        username = users.get_current_user()

        if neuerbucketname == "":
          # Testen ob ein Name für den neuen key angegeben wurde
          # Wenn kein Name angegeben wurde, kann kein Key angelegt werden
          #fehlermeldung = "Sie haben keine Namen angegeben"
          fehlermeldung = "92"
          self.redirect('/s3?message='+fehlermeldung)
        elif re.search(r'[^\-.a-zA-Z0-9]', neuerbucketname) != None:
          # Testen ob der Name für den neuen key nicht erlaubte Zeichen enthält
          fehlermeldung = "106"
          self.redirect('/s3?message='+fehlermeldung)
        else:
          # Mit S3 verbinden
          conn_s3 = logins3(username)
          try:
            # Liste der Buckets
            liste_buckets = conn_s3.get_all_buckets()
          except:
            # Wenn es nicht klappt...
            fehlermeldung = "107"
            self.redirect('/s3?message='+fehlermeldung)
          else:
            # Wenn es geklappt hat...
            # Variable erzeugen zum Erfassen, ob der neue Bucket schon existiert
            laenge_liste_buckets = len(liste_buckets)

            # Variable erzeugen zum Erfassen, ob der neue Bucket schon existiert
            schon_vorhanden = 0
            for i in range(laenge_liste_buckets):
              # Bucket-Namen in einen String umwandeln
              vergleich = str(liste_buckets[i].name)
              # Vergleichen
              if vergleich == neuerbucketname:
                # Bucket-Name existiert schon!
                schon_vorhanden = 1

            if schon_vorhanden == 0:
              # Wenn man noch keinen Bucket mit dem eingegebenen Namen besitzt...
              try:
                # Versuch den Bucket anzulegen
                conn_s3.create_bucket(neuerbucketname)
              except:
                fehlermeldung = "107"
                # Wenn es nicht klappt...
                self.redirect('/s3?message='+fehlermeldung)
              else:
                fehlermeldung = "105"
                # Wenn es geklappt hat...
                self.redirect('/s3?message='+fehlermeldung)
            else:
              # Wenn man schon einen Bucket mit dem eingegeben Namen hat...
              fehlermeldung = "108"
              self.redirect('/s3?message='+fehlermeldung)


class BucketEntfernen(webapp.RequestHandler):
    def get(self):
        #self.response.out.write('posted!')
        # Den Namen des zu löschen Buckets holen
        bucketname = self.request.get('bucket')

        # Den Usernamen erfahren
        username = users.get_current_user()

        # Mit S3 verbinden
        conn_s3 = logins3(username)
        try:
          # Versuch den Bucket zu löschen
          conn_s3.delete_bucket(bucketname)
        except:
          fehlermeldung = "109"
          # Wenn es nicht klappt...
          self.redirect('/s3?message='+fehlermeldung)
        else:
          fehlermeldung = "110"
          # Wenn es geklappt hat...
          self.redirect('/s3?message='+fehlermeldung)


class BucketInhalt(webapp.RequestHandler):
    def get(self):
        # self.response.out.write('posted!')
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')
        # Eventuell vorhande Fehlermeldung holen
        message = self.request.get('message')
        # Eventuell vorhandes Verzeichnis holen
        directory = self.request.get('dir')
        # Namen des Buckets holen, dessen Inhalt angezeigt wird
        bucketname = self.request.get('bucket')


        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if results:
          # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache)

          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache)

          AWSAccessKeyId = aws_access_key_erhalten(username,regionname)
          AWSSecretAccessKeyId = aws_secret_access_key_erhalten(username,regionname)

          input_error_message = ""

          if sprache != "de":
            sprache = "en"

          input_error_message = error_messages.get(message, {}).get(sprache)

          # Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
          if input_error_message == None:
            input_error_message = ""

          # Wenn die Nachricht grün formatiert werden soll...
          if message in ("111", "115", "118", "120"):
            # wird sie hier, in der Hilfsfunktion grün formatiert
            input_error_message = format_error_message_green(input_error_message)
          # Ansonsten wird die Nachricht rot formatiert
          elif message in ("112", "113", "114", "116", "117", "119", "121"):
            input_error_message = format_error_message_red(input_error_message)
          else:
            input_error_message = ""

          # Mit S3 verbinden
          conn_s3 = logins3(username)
          bucket_instance = conn_s3.get_bucket(bucketname)

          # Wenn die Variable "directory" gesetzt ist, also ein Verzeichnis angegeben wurde...
          if directory:
            # An das Verzeichnis ein "/" angängen
            directory = directory + '/'
            # Liste der Keys im Bucket
            liste_keys = bucket_instance.get_all_keys(prefix=directory)
            # Anzahl der Keys in der Liste
            laenge_liste_keys = len(liste_keys)
            # Die Variable "level" ist quasi die Ebene im Dateibaum.
            # Die Zahl in "level" ist gleich der "/" in den Key-Namen der Keys, die
            # in dem Verzeichnis drin sind.
            level = directory.count("/")
          # Wenn kein Verzeichnis angegeben wurde...
          else:
            # Dann wird die Variable "directory" gesetzt und zwar auf "/"
            directory = '/'
            # Liste der Keys im Bucket
            liste_keys = bucket_instance.get_all_keys()
            # Anzahl der Keys in der Liste
            laenge_liste_keys = len(liste_keys)
            # Die Variable "level" ist quasi die Ebene im Dateibaum.
            # level = 0 heißt, wir sind in der Root-Ebene.
            level = 0

          # Wenn wir uns im "Root"-Verzeichnis des Buckets befinden, wird aus
          # der Liste der Keys alle Keys entfernt, die einen / im Keynamen haben
          if directory == '/':
            liste_keys2 = []
            for i in range(laenge_liste_keys):
              if re.search(r'[/]', str(liste_keys[i].name)) == None:
                liste_keys2.append(liste_keys[i])
            laenge_liste_keys2 = len(liste_keys2)
            laenge_liste_keys = laenge_liste_keys2
            liste_keys = liste_keys2
          # Wenn wir uns nicht im "Root"-Verzeichnis des Buckets befinden,
          # dann wird für jeden Key geschaut, ob er die gleiche Anzahl an "/" im
          # Namen hat, wie die Variable "level" als Zahl enthält.
          else:
            liste_keys2 = []
            for i in range(laenge_liste_keys):
              if str(liste_keys[i].name).count("/") == level:
                liste_keys2.append(liste_keys[i])
            laenge_liste_keys2 = len(liste_keys2)
            laenge_liste_keys = laenge_liste_keys2
            liste_keys = liste_keys2

          # Wenn wir im Root-Verzeichnis sind und es sind keine Keys vorhanden...
          if laenge_liste_keys == 0 and directory == '/':
            if sprache == "de":
              bucket_keys_tabelle = 'Der Bucket <B>'+ bucketname+' </B>ist leer.'
            else:
              bucket_keys_tabelle = 'The bucket <B>'+ bucketname+' </B>is empty.'
          # Wenn wir nicht im Root-Verzeichnis sind und es sind keine Keys vorhanden...
          elif laenge_liste_keys == 0 and directory != '/':
            if sprache == "de":
              bucket_keys_tabelle = 'Das Verzeichnis <B>'+ directory+' </B>ist leer.'
              bucket_keys_tabelle = bucket_keys_tabelle + '<p>&nbsp;</p>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<a href="/bucket_inhalt?bucket='
              bucket_keys_tabelle = bucket_keys_tabelle + str(bucketname)
              # Wenn das aktuelle Verzeichnis zwei oder mehr "/" enthält, dann müssen
              # wir eine Rücksprungmöglichkeit bauen. Dabei wird erst der
              # letzte Slash entfernt und dann der Text bis zum nächsten Slash.
              # Wenn das aktuelle Verzeichnis NICHT zwei oder mehr "/" enthält,
              # dann geben wir gar kein Verzeichnis an, weil dann wollen wir zur
              # Root-Ansicht zurückkehren.
              if str(directory).count("/") >= 2:
                bucket_keys_tabelle = bucket_keys_tabelle + '&amp;dir='
                bucket_keys_tabelle = bucket_keys_tabelle + str(directory)[:str(directory)[:-1].rfind('/')]
              bucket_keys_tabelle = bucket_keys_tabelle + '" title="Zur&uuml;ck">'
              bucket_keys_tabelle = bucket_keys_tabelle + '<img src="bilder/left.png" width="16" height="16" border="0" alt="'
              bucket_keys_tabelle = bucket_keys_tabelle + 'Zur&uuml;ck'
              bucket_keys_tabelle = bucket_keys_tabelle + '"> '
              bucket_keys_tabelle = bucket_keys_tabelle + '</a>'
            else:
              bucket_keys_tabelle = 'The directory <B>'+ directory+' </B>is empty.'
              bucket_keys_tabelle = bucket_keys_tabelle + '<p>&nbsp;</p>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<a href="/bucket_inhalt?bucket='
              bucket_keys_tabelle = bucket_keys_tabelle + str(bucketname)
              # Wenn das aktuelle Verzeichnis zwei oder mehr "/" enthält, dann müssen
              # wir eine Rücksprungmöglichkeit bauen. Dabei wird erst der
              # letzte Slash entfernt und dann der Text bis zum nächsten Slash.
              # Wenn das aktuelle Verzeichnis NICHT zwei oder mehr "/" enthält,
              # dann geben wir gar kein Verzeichnis an, weil dann wollen wir zur
              # Root-Ansicht zurückkehren.
              if str(directory).count("/") >= 2:
                bucket_keys_tabelle = bucket_keys_tabelle + '&amp;dir='
                bucket_keys_tabelle = bucket_keys_tabelle + str(directory)[:str(directory)[:-1].rfind('/')]
              bucket_keys_tabelle = bucket_keys_tabelle + '" title="Switch back">'
              bucket_keys_tabelle = bucket_keys_tabelle + '<img src="bilder/left.png" width="16" height="16" border="0" alt="'
              bucket_keys_tabelle = bucket_keys_tabelle + 'Switch back'
              bucket_keys_tabelle = bucket_keys_tabelle + '"> '
              bucket_keys_tabelle = bucket_keys_tabelle + '</a>'
          # Wenn wir irgendwo sind und es sind Keys vorhanden...
          else:
            if regionname == "Amazon": # Bei Amazon geht mehr (alles)
              bucket_keys_tabelle = ''
              bucket_keys_tabelle = bucket_keys_tabelle + '<table border="3" cellspacing="0" cellpadding="5">'
              bucket_keys_tabelle = bucket_keys_tabelle + '<tr>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<th>&nbsp;</th>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<th>&nbsp;</th>'
              if sprache == "de":
                bucket_keys_tabelle = bucket_keys_tabelle + '<th align="left">'
                bucket_keys_tabelle = bucket_keys_tabelle + str(directory)
                bucket_keys_tabelle = bucket_keys_tabelle + '</th>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Dateigr&ouml;&szlig;e</th>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Letzte &Auml;nderung</th>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Zugriffsberechtigung</th>'
              else:
                bucket_keys_tabelle = bucket_keys_tabelle + '<th align="left">'
                bucket_keys_tabelle = bucket_keys_tabelle + str(directory)
                bucket_keys_tabelle = bucket_keys_tabelle + '</th>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Filesize</th>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Last Modified</th>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Access Control List</th>'
              bucket_keys_tabelle = bucket_keys_tabelle + '</tr>'
              # Wenn wir uns nicht im Root-Ordner des Buckets befinden, dann brauchen wir eine Rücksprungmöglichkeit
              if directory != '/':
                bucket_keys_tabelle = bucket_keys_tabelle + '<tr>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<td>&nbsp;</td>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<td>&nbsp;</td>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<td>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<a href="/bucket_inhalt?bucket='
                bucket_keys_tabelle = bucket_keys_tabelle + str(bucketname)
                # Wenn das aktuelle Verzeichnis zwei oder mehr "/" enthält, dann müssen
                # wir eine Rücksprungmöglichkeit bauen. Dabei wird erst der
                # letzte Slash entfernt und dann der Text bis zum nächsten Slash.
                # Wenn das aktuelle Verzeichnis NICHT zwei oder mehr "/" enthält,
                # dann geben wir gar kein Verzeichnis an, weil dann wollen wir zur
                # Root-Ansicht zurückkehren.
                if str(directory).count("/") >= 2:
                  bucket_keys_tabelle = bucket_keys_tabelle + '&amp;dir='
                  bucket_keys_tabelle = bucket_keys_tabelle + str(directory)[:str(directory)[:-1].rfind('/')]

                if sprache == "de":
                  bucket_keys_tabelle = bucket_keys_tabelle + '" title="Zur&uuml;ck">'
                else:
                  bucket_keys_tabelle = bucket_keys_tabelle + '" title="Switch back">'
                # Hier wird das aktuelle Verzeichnis vom Key-Namen vorne abgeschnitten
                #liste_keys[i].name = liste_keys[i].name.replace ( directory, '' )
                bucket_keys_tabelle = bucket_keys_tabelle + '<img src="bilder/left.png" width="16" height="16" border="0" alt="'
                if sprache == "de":
                  bucket_keys_tabelle = bucket_keys_tabelle + 'Zur&uuml;ck'
                else:
                  bucket_keys_tabelle = bucket_keys_tabelle + 'Switch back'
                bucket_keys_tabelle = bucket_keys_tabelle + '">'
                bucket_keys_tabelle = bucket_keys_tabelle + '</a>'
                bucket_keys_tabelle = bucket_keys_tabelle + '</td>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<td>&nbsp;</td>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<td>&nbsp;</td>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<td>&nbsp;</td>'
                bucket_keys_tabelle = bucket_keys_tabelle + '</tr>'

              for i in range(laenge_liste_keys):
                  bucket_keys_tabelle = bucket_keys_tabelle + '<tr>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '<td>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '<a href="/bucketkeyentfernen?bucket='
                  bucket_keys_tabelle = bucket_keys_tabelle + str(bucketname)
                  bucket_keys_tabelle = bucket_keys_tabelle + '&amp;typ=kompfort'
                  bucket_keys_tabelle = bucket_keys_tabelle + '&amp;key='
                  bucket_keys_tabelle = bucket_keys_tabelle + str(liste_keys[i].name)
                  bucket_keys_tabelle = bucket_keys_tabelle + '&amp;dir='
                  bucket_keys_tabelle = bucket_keys_tabelle + str(directory)
                  if sprache == "de":
                    bucket_keys_tabelle = bucket_keys_tabelle + '" title="Key l&ouml;schen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Key l&ouml;schen"></a>'
                  else:
                    bucket_keys_tabelle = bucket_keys_tabelle + '" title="erase key"><img src="bilder/delete.png" width="16" height="16" border="0" alt="erase key"></a>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '</td>'


                  bucket_keys_tabelle = bucket_keys_tabelle + '<td>'
                  # Wenn der Name des Key mit dem String $folder$ endet, dann ist es ein Verzeichnis
                  if str(liste_keys[i].name).endswith("$folder$") == True:
                    if sprache == "de":
                      bucket_keys_tabelle = bucket_keys_tabelle + '<img src="bilder/folder.png" width="16" height="16" border="0" alt="Verzeichnis">'
                    else:
                      bucket_keys_tabelle = bucket_keys_tabelle + '<img src="bilder/folder.png" width="16" height="16" border="0" alt="Folder">'
                  else:      # Ansonsten ist es eine Datei
                    if sprache == "de":
                      bucket_keys_tabelle = bucket_keys_tabelle + '<img src="bilder/document.png" width="16" height="16" border="0" alt="Datei">'
                    else:
                      bucket_keys_tabelle = bucket_keys_tabelle + '<img src="bilder/document.png" width="16" height="16" border="0" alt="File">'
                  bucket_keys_tabelle = bucket_keys_tabelle + '</td>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '<td>'
                  # Wenn der Key ein Verzeichnis ist, werden vom Key-Namen die letzten 9 Zeichen
                  # abgeschnitten. Es wird einfach nur das "_$folder$" abgeschnitten.
                  if str(liste_keys[i].name).endswith("$folder$") == True:
                    bucket_keys_tabelle = bucket_keys_tabelle + '<a href="/bucket_inhalt?bucket='
                    bucket_keys_tabelle = bucket_keys_tabelle + str(bucketname)
                    bucket_keys_tabelle = bucket_keys_tabelle + '&amp;dir='
                    bucket_keys_tabelle = bucket_keys_tabelle + str(liste_keys[i].name[:-9])
                    if sprache == "de":
                      bucket_keys_tabelle = bucket_keys_tabelle + '" title="In das Verzeichnis wechseln">'
                    else:
                      bucket_keys_tabelle = bucket_keys_tabelle + '" title="Switch to directory">'
                    # Hier wird das aktuelle Verzeichnis vom Key-Namen vorne abgeschnitten
                    name_tmp = liste_keys[i].name.replace( directory, '')
                    bucket_keys_tabelle = bucket_keys_tabelle + str(name_tmp[:-9])
                    bucket_keys_tabelle = bucket_keys_tabelle + '</a>'
                  # Wenn es sich nicht um ein Verzeichnis handelt
                  else:
                    # Nur wenn es nicht der None-Eintrag bei Eucalyptus ist, wird ein Link gebildet
                    # if liste_keys[i].name != None:
                    # Dummerweise funktionieren die Links unter Eucalyptus nicht richtig
                    # Darum erst mal nur Links bei Amazon
                    if regionname == "Amazon":
                      bucket_keys_tabelle = bucket_keys_tabelle + '<a href="'
                      bucket_keys_tabelle = bucket_keys_tabelle + liste_keys[i].generate_url(600, method='GET', headers=None, query_auth=True, force_http=False).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
                      bucket_keys_tabelle = bucket_keys_tabelle + '">'
                      # Hier wird das aktuelle Verzeichnis vom Key-Namen vorne abgeschnitten
                      name_tmp = liste_keys[i].name.replace(directory, '')
                      # Wenn der Key kein Verzeinis ist, muss hinten nichts abgeschnitten werden.
                      bucket_keys_tabelle = bucket_keys_tabelle + str(name_tmp)
                      bucket_keys_tabelle = bucket_keys_tabelle + '</a>'
                    else:
                      # Hier wird das aktuelle Verzeichnis vom Key-Namen vorne abgeschnitten
                      name_tmp = liste_keys[i].name.replace(directory, '')
                      # Wenn der Key kein Verzeinis ist, muss hinten nichts abgeschnitten werden.
                      bucket_keys_tabelle = bucket_keys_tabelle + str(name_tmp)
                    bucket_keys_tabelle = bucket_keys_tabelle + '</td>'

                  bucket_keys_tabelle = bucket_keys_tabelle + '<td align="right">'
                  if str(liste_keys[i].name) != None:
                    # Wenn der Keyname auf "$folder" endet, dann wird keine
                    # Dateigröße ausgegeben.
                    if str(liste_keys[i].name).endswith("$folder$") == True:
                      bucket_keys_tabelle = bucket_keys_tabelle + '&nbsp;'
                    # Wenn der Keyname nicht auf $folder$ endet, wird die 
                    # Dateigröße ausgegeben.
                    else:
                      bucket_keys_tabelle = bucket_keys_tabelle + str(liste_keys[i].size)
                  else:
                    bucket_keys_tabelle = bucket_keys_tabelle + '&nbsp;'
                  bucket_keys_tabelle = bucket_keys_tabelle + '</td>'


                  bucket_keys_tabelle = bucket_keys_tabelle + '<td>'
                  # Den ISO8601 Zeitstring umwandeln, damit es besser aussieht.
                  datum_der_letzten_aenderung = parse(liste_keys[i].last_modified)
                  bucket_keys_tabelle = bucket_keys_tabelle + str(datum_der_letzten_aenderung.strftime("%Y-%m-%d  %H:%M:%S"))
                  #bucket_keys_tabelle = bucket_keys_tabelle + str(liste_keys[i].last_modified)
                  bucket_keys_tabelle = bucket_keys_tabelle + '</td>'

                  bucket_keys_tabelle = bucket_keys_tabelle + '<td align="center">'
                  bucket_keys_tabelle = bucket_keys_tabelle + '<a href="/acl_einsehen?bucket='
                  bucket_keys_tabelle = bucket_keys_tabelle + str(bucketname)
                  bucket_keys_tabelle = bucket_keys_tabelle + '&amp;typ=kompfort'
                  bucket_keys_tabelle = bucket_keys_tabelle + '&amp;key='+str(liste_keys[i].name)
                  bucket_keys_tabelle = bucket_keys_tabelle + '&amp;dir='+str(directory)
                  if sprache == "de":
                    bucket_keys_tabelle = bucket_keys_tabelle + '" title="ACL einsehen/&auml;ndern">ACL einsehen/&auml;ndern</a>'
                  else:
                    bucket_keys_tabelle = bucket_keys_tabelle + '" title="view/edit ACL">view/edit ACL</a>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '</td>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '</tr>'
              bucket_keys_tabelle = bucket_keys_tabelle + '</table>'
            else: # Bei Eucalyptus gibt es eine andere Tabelle mit weniger Informationen
              # Bei Eucalyptus (Walrus) gibt es einige Sachen nicht
              bucket_keys_tabelle = ''
              bucket_keys_tabelle = bucket_keys_tabelle + '<table border="3" cellspacing="0" cellpadding="5">'
              bucket_keys_tabelle = bucket_keys_tabelle + '<tr>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<th>&nbsp;</th>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<th>&nbsp;</th>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<th align="left">Name</th>'
              bucket_keys_tabelle = bucket_keys_tabelle + '</tr>'
              for i in range(laenge_liste_keys):
                  bucket_keys_tabelle = bucket_keys_tabelle + '<tr>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '<td>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '<a href="/bucketkeyentfernen?bucket='
                  bucket_keys_tabelle = bucket_keys_tabelle + str(bucketname)
                  bucket_keys_tabelle = bucket_keys_tabelle + '&amp;typ=kompfort'
                  bucket_keys_tabelle = bucket_keys_tabelle + '&amp;key='
                  bucket_keys_tabelle = bucket_keys_tabelle + str(liste_keys[i].name)
                  if sprache == "de":
                    bucket_keys_tabelle = bucket_keys_tabelle + '" title="Key l&ouml;schen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Key l&ouml;schen"></a>'
                  else:
                    bucket_keys_tabelle = bucket_keys_tabelle + '" title="erase key"><img src="bilder/delete.png" width="16" height="16" border="0" alt="erase key"></a>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '</td>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '<td>'
                  # Wenn der Name des Key mit dem String $folder$ endet, dann ist es ein Verzeichnis
                  if str(liste_keys[i].name).endswith("$folder$") == True:
                    if sprache == "de":
                      bucket_keys_tabelle = bucket_keys_tabelle + '<img src="bilder/folder.png" width="16" height="16" border="0" alt="Verzeichnis">'
                    else:
                      bucket_keys_tabelle = bucket_keys_tabelle + '<img src="bilder/folder.png" width="16" height="16" border="0" alt="Folder">'
                  else:      # Ansonsten ist es eine Datei
                    if sprache == "de":
                      bucket_keys_tabelle = bucket_keys_tabelle + '<img src="bilder/document.png" width="16" height="16" border="0" alt="Datei">'
                    else:
                      bucket_keys_tabelle = bucket_keys_tabelle + '<img src="bilder/document.png" width="16" height="16" border="0" alt="File">'
                  bucket_keys_tabelle = bucket_keys_tabelle + '</td>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '<td>'
                  # Wenn der Key ein Verzeichnis ist, werden vom Key-Namen die letzten 9 Zeichen
                  # abgeschnitten. Es wird einfach nur das "_$folder$" abgeschnitten.
                  if str(liste_keys[i].name).endswith("$folder$") == True:
                    bucket_keys_tabelle = bucket_keys_tabelle + str(liste_keys[i].name[:-9])
                  else:
                    # Wenn der Key kein Verzeinis ist, muss auch nichts abgeschnitten werden.
                    bucket_keys_tabelle = bucket_keys_tabelle + str(liste_keys[i].name)
                  bucket_keys_tabelle = bucket_keys_tabelle + '</td>'

                  bucket_keys_tabelle = bucket_keys_tabelle + '</tr>'
              bucket_keys_tabelle = bucket_keys_tabelle + '</table>'

          # "Verzeichnisse" gehen nur bei Amazon S3
          # Der Grund ist, dass das _$folder$ nicht in Walrus gespeichert werden kann.
          # In Walrus wird das so gespeichert: _%24folder%24
          if regionname == "Amazon":
            if sprache == "de":
              eingabeformular_neues_verzeichnis = ''
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + '<form action="/bucketverzeichniserzeugen" method="post" accept-charset="utf-8">\n'
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + '<input type="hidden" name="bucket" value="'
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + str(bucketname)
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + '">\n'
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + '<input type="hidden" name="dir" value="'
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + directory
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + '">\n'
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + '<input name="verzeichnisname" type="text" size="25" maxlength="25"> '
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + '<input type="submit" value="Verzeichnis erzeugen">\n'
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + '</form>\n'
            else:
              eingabeformular_neues_verzeichnis = ''
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + '<form action="/bucketverzeichniserzeugen" method="post" accept-charset="utf-8">\n'
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + '<input type="hidden" name="bucket" value="'
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + str(bucketname)
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + '">\n'
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + '<input type="hidden" name="dir" value="'
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + directory
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + '">\n'
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + '<input name="verzeichnisname" type="text" size="25" maxlength="25"> '
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + '<input type="submit" value="create directory">\n'
              eingabeformular_neues_verzeichnis = eingabeformular_neues_verzeichnis + '</form>\n'
          else: 
            if sprache == "de":
              eingabeformular_neues_verzeichnis = 'Das Erzeugen von Verzeichnissen funktioniert unter Eucalyptus noch nicht'
            else:
              eingabeformular_neues_verzeichnis = 'The creation of directories is still not working with Eucaplyptus'

          if sprache == "de":
            verzeichnis_warnung = 'In S3 existieren keine Verzeichnisse, sondern nur Keys. S3 ist ein flacher Namensraum. <a href="http://www.s3fox.net" style="color:blue">S3Fox</a> z.B. simuliert Verzeichnisse dadurch, dass bestimmte Keys als Platzhalter f&uuml;r das Verzeichnis dienen. Diese enden auf den Namen <b>_&#36;folder&#36;</b>. Ein Key, der einem Verzeichnis zugeordnet werden soll, hat das folgende Namensschema: <b>verzeichnis/unterverzeichnis/dateiname</b>'
          else:
            verzeichnis_warnung = 'There are no folders within a S3 bucket. S3 is a completely flat name space. However, you can simulate hierarchical folders with clever use of key names. <a href="http://www.s3fox.net" style="color:blue">S3Fox</a> for instance uses keys that end with <b>_&#36;folder&#36;</b> as directory placeholders and. A key that is meant staying inside are folder has a name following this schema <b>folder/subfolder/filename</b>'


          # Hier wird das Policy-Dokument erzeugt
          policy_document = ''
          policy_document = policy_document + '{'
          policy_document = policy_document + '"expiration": "2100-01-01T00:00:00Z",'
          policy_document = policy_document + '"conditions": ['
          policy_document = policy_document + '{"bucket": "'+bucketname+'"},'
          policy_document = policy_document + '["starts-with", "$acl", ""],'
          policy_document = policy_document + '["starts-with", "$success_action_redirect", ""],'
          if directory == '/':
            policy_document = policy_document + '["starts-with", "$key", ""],'
          else:
            policy_document = policy_document + '["starts-with", "$key", "'+directory+'"],'
          policy_document = policy_document + '["starts-with", "$Content-Type", ""]'
          policy_document = policy_document + ']'
          policy_document = policy_document + '}'

          policy = base64.b64encode(policy_document)

          signature = base64.b64encode(hmac.new(AWSSecretAccessKeyId, policy, sha).digest())

          # Das Hochladen von Keys funktioniert nur unter Amazon EC2
          if regionname == "Amazon":
            keys_upload_formular = '<p>&nbsp;</p>\n'
            keys_upload_formular = keys_upload_formular + '<form action="http://s3.amazonaws.com/'
            keys_upload_formular = keys_upload_formular + bucketname
            keys_upload_formular = keys_upload_formular + '" method="post" enctype="multipart/form-data">\n'
            keys_upload_formular = keys_upload_formular + '<table border="0" cellspacing="0" cellpadding="5">'
            keys_upload_formular = keys_upload_formular + '<tr>'
            keys_upload_formular = keys_upload_formular + '<td>'
            if directory == '/':
              keys_upload_formular = keys_upload_formular + '<input type="hidden" name="key" value="${filename}">\n'
            else:
              keys_upload_formular = keys_upload_formular + '<input type="hidden" name="key" value="'+directory+'${filename}">\n'
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
            if directory == '/':
              keys_upload_formular = keys_upload_formular + '<input type="hidden" name="success_action_redirect" value="/bucket_inhalt?bucket='
              keys_upload_formular = keys_upload_formular + bucketname
              keys_upload_formular = keys_upload_formular + '">\n'
            else:
              keys_upload_formular = keys_upload_formular + '<input type="hidden" name="success_action_redirect" value="/bucket_inhalt?bucket='
              keys_upload_formular = keys_upload_formular + bucketname
              keys_upload_formular = keys_upload_formular + '&amp;dir='
              keys_upload_formular = keys_upload_formular + directory[:-1]
              keys_upload_formular = keys_upload_formular + '">\n'
            keys_upload_formular = keys_upload_formular + '<input type="hidden" name="AWSAccessKeyId" value="'+AWSAccessKeyId+'">\n'
            keys_upload_formular = keys_upload_formular + '<input type="hidden" name="policy" value="'+policy+'">\n'
            keys_upload_formular = keys_upload_formular + '<input type="hidden" name="signature" value="'+signature+'">\n'
            keys_upload_formular = keys_upload_formular + '<input type="file" name="file" size="80">\n'
            keys_upload_formular = keys_upload_formular + '</td>'
            keys_upload_formular = keys_upload_formular + '</tr>'
            keys_upload_formular = keys_upload_formular + '<tr>'
            keys_upload_formular = keys_upload_formular + '<td>'
            if sprache == "de":
              keys_upload_formular = keys_upload_formular + '<input type="submit" name="submit" value="Datei hochladen">\n'
            else:
              keys_upload_formular = keys_upload_formular + '<input type="submit" name="submit" value="upload file">\n'
            keys_upload_formular = keys_upload_formular + '</td>'
            keys_upload_formular = keys_upload_formular + '</tr>'
            keys_upload_formular = keys_upload_formular + '</table>'
            keys_upload_formular = keys_upload_formular + '</form>'
          # Unter Eucalyptus funktioniert das Hochladen von Keys nicht
          else:
            if sprache == "de":
              keys_upload_formular = '<p>&nbsp;</p>\n Das Hochladen von Keys funktioniert unter Eucalyptus noch nicht'
            else:
              keys_upload_formular = '<p>&nbsp;</p>\n The key upload is still not working with Eucaplyptus'

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
          'eingabeformular_neues_verzeichnis': eingabeformular_neues_verzeichnis,
          'keys_upload_formular': keys_upload_formular,
          'verzeichnis_warnung': verzeichnis_warnung,
          }

          #if sprache == "de": naechse_seite = "s3_keys_de.html"
          #else:               naechse_seite = "s3_keys_en.html"
          #path = os.path.join(os.path.dirname(__file__), naechse_seite)
          path = os.path.join(os.path.dirname(__file__), "templates", sprache, "s3_keys.html")
          self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')


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

        if results:
          # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache)

          results = aktivezone.fetch(100)

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
          bucket_instance = conn_s3.get_bucket(bucketname)

          liste_keys = bucket_instance.get_all_keys()
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
            else:
              bucket_keys_tabelle = bucket_keys_tabelle + '<th align="left">Keys</th>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Filesize</th>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Last Modified</th>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Access Control List</th>'
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
                # Dummerweise funktionieren die Links unter Eucalyptus nicht richtig
                # Darum erst mal nur Links bei Amazon
                #if regionname == "Amazon":
                bucket_keys_tabelle = bucket_keys_tabelle + '<a href="'
                bucket_keys_tabelle = bucket_keys_tabelle + liste_keys[i].generate_url(600, method='GET', headers=None, query_auth=True, force_http=False).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
                bucket_keys_tabelle = bucket_keys_tabelle + '">'
                bucket_keys_tabelle = bucket_keys_tabelle + str(liste_keys[i].name)
                # Dummerweise funktionieren die Links unter Eucalyptus nicht richtig
                # Darum erst mal nur Links bei Amazon
                #if regionname == "Amazon":
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
                bucket_keys_tabelle = bucket_keys_tabelle + '</tr>'
            bucket_keys_tabelle = bucket_keys_tabelle + '</table>'

          # Wenn man sich NICHT unter Amazon befindet, funktioniert der Download von Keys nicht.
          if regionname != "Amazon":
            if sprache == "de":
              eucalyptus_warnung = '<B>Achtung!</B> Unter Eucalyptus 1.6, 1.6.1 und 1.6.2 funktioniert der Download von Keys nicht. Dabei handelt es sich um einen Fehler von Eucalyptus. Es kommt zu dieser Fehlermeldung:<BR><B>Failure: 500 Internal Server Error</B>'
            else:
              eucalyptus_warnung = '<B>Attention!</B> With Eucalyptus 1.6, 1.6.1 and 1.6.2 the download of Keys is broken. This is a bug of Eucalyptus. The result is this error message:<BR><B>Failure: 500 Internal Server Error</B>'
          else: 
            eucalyptus_warnung = ''


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
          policy_document = policy_document + '["starts-with", "$success_action_redirect", ""],'
          policy_document = policy_document + '["starts-with", "$key", ""],'
          policy_document = policy_document + '["starts-with", "$Content-Type", ""]'
          policy_document = policy_document + ']'
          policy_document = policy_document + '}'

          policy = base64.b64encode(policy_document)

          signature = base64.b64encode(hmac.new(AWSSecretAccessKeyId, policy, sha).digest())

          # Das Hochladen von Keys funktioniert nur unter Amazon EC2
          if regionname == "Amazon":
            keys_upload_formular = '<p>&nbsp;</p>\n'
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
            keys_upload_formular = keys_upload_formular + '<input type="hidden" name="success_action_redirect" value="/bucket_inhalt_pure?bucket='
            keys_upload_formular = keys_upload_formular + bucketname
            keys_upload_formular = keys_upload_formular + '">\n'
            keys_upload_formular = keys_upload_formular + '<input type="hidden" name="AWSAccessKeyId" value="'+AWSAccessKeyId+'">\n'
            keys_upload_formular = keys_upload_formular + '<input type="hidden" name="policy" value="'+policy+'">\n'
            keys_upload_formular = keys_upload_formular + '<input type="hidden" name="signature" value="'+signature+'">\n'
            keys_upload_formular = keys_upload_formular + '<input type="file" name="file" size="80">\n'
            keys_upload_formular = keys_upload_formular + '</td>'
            keys_upload_formular = keys_upload_formular + '</tr>'
            keys_upload_formular = keys_upload_formular + '<tr>'
            keys_upload_formular = keys_upload_formular + '<td>'
            if sprache == "de":
              keys_upload_formular = keys_upload_formular + '<input type="submit" name="submit" value="Datei hochladen">\n'
            else:
              keys_upload_formular = keys_upload_formular + '<input type="submit" name="submit" value="upload file">\n'
            keys_upload_formular = keys_upload_formular + '</td>'
            keys_upload_formular = keys_upload_formular + '</tr>'
            keys_upload_formular = keys_upload_formular + '</table>'
            keys_upload_formular = keys_upload_formular + '</form>'
          # Unter Eucalyptus funktioniert das Hochladen von Keys nicht
          else:
            if sprache == "de":
              keys_upload_formular = '<p>&nbsp;</p>\n Das Hochladen von Keys funktioniert unter Eucalyptus noch nicht'
            else:
              keys_upload_formular = '<p>&nbsp;</p>\n The key upload is still not working with Eucaplyptus'


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
          'eucalyptus_warnung': eucalyptus_warnung,
          'alle_keys_loeschen_button': alle_keys_loeschen_button,
          }

          #if sprache == "de": naechse_seite = "s3_keys_pur_de.html"
          #else:               naechse_seite = "s3_keys_pur_en.html"
          #path = os.path.join(os.path.dirname(__file__), naechse_seite)
          path = os.path.join(os.path.dirname(__file__), "templates", sprache, "s3_keys_pur.html")
          self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')


class BucketKeyEntfernen(webapp.RequestHandler):
    def get(self):
        #self.response.out.write('posted!')
        # Den Namen des zu löschen Keys holen
        keyname = self.request.get('key')
        # Namen des Buckets holen, aus dem der Key gelöscht werden soll
        bucketname = self.request.get('bucket')
        # War es die reine S3-Darstellung oder die Komfort-Darstellung, aus der die 
        # Anfrage zu Löschen des Keys kam?
        typ = self.request.get('typ')
        # Das Verzeichnis aus dem Formular holen
        directory = self.request.get('dir')

        # Den Slash am Ende des Verzeichnisses entfernen
        directory = str(directory[:-1])

        # Den Usernamen erfahren
        username = users.get_current_user()

        # Mit S3 verbinden
        conn_s3 = logins3(username)

        bucket_instance = conn_s3.get_bucket(bucketname)
        # Liste der Keys im Bucket
        liste_keys = bucket_instance.get_all_keys()
        # Anzahl der Keys in der Liste
        laenge_liste_keys = len(liste_keys)

        for i in range(laenge_liste_keys):
          # Key-Name in einen String umwandeln
          vergleich = str(liste_keys[i].name)
          if vergleich == keyname:
          # Vergleichen
            try:
              # Versuch den Key zu löschen
              liste_keys[i].delete()
            except:
              fehlermeldung = "112"
              # Wenn es nicht klappt...
              if typ == "pur":
                if directory == "/":
                  self.redirect('/bucket_inhalt_pure?bucket='+bucketname+'&message='+fehlermeldung)
                else:
                  self.redirect('/bucket_inhalt_pure?bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)
              else:
                if directory == "/":
                  self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung)
                else:
                  self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)
            else:
              fehlermeldung = "111"
              # Wenn es geklappt hat...
              if typ == "pur":
                if directory == "/":
                  self.redirect('/bucket_inhalt_pure?bucket='+bucketname+'&message='+fehlermeldung)
                else:
                  self.redirect('/bucket_inhalt_pure?bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)
              else:
                if directory == "/":
                  self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung)
                else:
                  self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)


class BucketVerzeichnisErzeugen(webapp.RequestHandler):
    def post(self):
        #self.response.out.write('posted!')
        # Die Eingabe aus dem Formular holen
        verzeichnisname = self.request.get('verzeichnisname') 
        # Den Bucketnamen aus dem Formular holen
        bucketname = self.request.get('bucket')
        # Das Verzeichnis aus dem Formular holen
        directory = self.request.get('dir')

        # Den Usernamen erfahren
        username = users.get_current_user()

        if verzeichnisname == "":
          # Testen ob ein Name für den neuen key angegeben wurde
          # Wenn kein Name angegeben wurde, kann kein Key angelegt werden
          #fehlermeldung = "Sie haben keine Namen angegeben"
          fehlermeldung = "113"
          if directory == "/":
            self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung)
          else:
            # Den Slash am Ende des Verzeichnisses entfernen
            directory = str(directory[:-1])
            self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)
        elif re.search(r'[^\-_a-zA-Z0-9]', verzeichnisname) != None:
          # Testen ob der Name für den neuen key nicht erlaubte Zeichen enthält
          fehlermeldung = "114"
          if directory == "/":
            self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung)
          else:
            # Den Slash am Ende des Verzeichnisses entfernen
            directory = str(directory[:-1])
            self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)
        else:
          # Mit S3 verbinden
          conn_s3 = logins3(username) 
          # Mit dem Bucket verbinden
          bucket_instance = conn_s3.get_bucket(bucketname)
          # Liste der Keys im Bucket
          liste_keys = bucket_instance.get_all_keys()
          # Anzahl der Keys in der Liste
          laenge_liste_keys = len(liste_keys)

          verzeichnisname = verzeichnisname+'_$folder$'

          # Variable erzeugen zum Erfassen, ob das neue Verzeichnis schon existiert
          schon_vorhanden = 0
          for i in range(laenge_liste_keys):
            # Key-Namen in einen String umwandeln
            vergleich = str(liste_keys[i].name)
            # Vergleichen
            if vergleich == verzeichnisname:
              # Verzeichnis-Name existiert schon!
              schon_vorhanden = 1
              fehlermeldung = "117"
              if directory == "/":
                self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung)
              else:
                # Den Slash am Ende des Verzeichnisses entfernen
                directory = str(directory[:-1])
                self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)

          # Wenn man noch kein Verzeichnis mit dem eingegebenen Namen besitzt... 
          if schon_vorhanden == 0:
            try:
              # Versuch das Verzeichnis anzulegen
              # Mit dem Bucket sind wir schon verbunden über die Zeile
              # bucket_instance = conn_s3.get_bucket(bucketname)
              if directory == '/':
                key = bucket_instance.new_key(verzeichnisname)
                key.set_contents_from_string('')
              else:
                verzeichnisname = directory + verzeichnisname
                key = bucket_instance.new_key(verzeichnisname)
                key.set_contents_from_string('')
            except:
              # Wenn es nicht klappt...
              fehlermeldung = "116"
              if directory == "/":
                self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung)
              else:
                # Den Slash am Ende des Verzeichnisses entfernen
                directory = str(directory[:-1])
                self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)
            else:
              # Wenn es geklappt hat...
              fehlermeldung = "115"
              if directory == "/":
                self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung)
              else:
                # Den Slash am Ende des Verzeichnisses entfernen
                directory = str(directory[:-1])
                self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)


class ACL_einsehen(webapp.RequestHandler):
    def get(self):
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')
        # Namen des Buckets holen, in dem der Key ist
        bucketname = self.request.get('bucket')
        # Namen des Keys holen, dessen ACL angezeigt wird
        keyname = self.request.get('key')
        # War es die reine S3-Darstellung oder die Komfort-Darstellung, aus der die 
        # Anfrage zu Löschen des Keys kam?
        typ = self.request.get('typ')
        # Verzeichnis holen, wenn es die Komfort-Ansicht war
        directory = self.request.get('dir')

        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if results:
          # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache)

          results = aktivezone.fetch(100)

          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache)

          # Mit S3 verbinden
          conn_s3 = logins3(username)
          bucket_instance = conn_s3.get_bucket(bucketname)

          key_instance = bucket_instance.get_acl(keyname)

          acl = bucket_instance.get_acl(key_name=keyname)

          AllUsersREAD  = ''
          AllUsersWRITE = ''
          AllUsersFULL  = ''
          AuthentUsersREAD   = ''
          AuthentUsersWRITE  = ''
          AuthentUsersFULL   = ''
          OwnerName   = ''
          OwnerREAD   = ''
          OwnerWRITE  = ''
          OwnerFULL   = ''

          for grant in acl.acl.grants:
            if str(grant.uri).find('AllUsers') != -1 and grant.permission == 'READ':
              AllUsersREAD  = 'tick.png'
            if str(grant.uri).find('AllUsers') != -1 and grant.permission == 'WRITE':
              AllUsersWRITE = 'tick.png'
            if str(grant.uri).find('AllUsers') != -1 and grant.permission == 'FULL_CONTROL':
              AllUsersREAD  = 'tick.png'
              AllUsersWRITE = 'tick.png'
              AllUsersFULL  = 'tick.png'
            if str(grant.uri).find('AuthenticatedUsers') != -1 and grant.permission == 'READ':
              AuthentUsersREAD  = 'tick.png'
            elif str(grant.uri).find('AuthenticatedUsers') != -1 and grant.permission == 'WRITE':
              AuthentUsersWRITE = 'tick.png'
            elif str(grant.uri).find('AuthenticatedUsers') != -1 and grant.permission == 'FULL_CONTROL':
              AuthentUsersFULL  = 'tick.png'
            # Wenn der Besitzer des Keys dieser Eintrag hier ist...
            if str(key_instance.owner.id) == str(grant.id):
              OwnerName = str(grant.display_name)
              if grant.permission == 'READ':
                OwnerREAD   = 'tick.png'
              if grant.permission == 'WRITE':
                OwnerWRITE  = 'tick.png'
              if grant.permission == 'FULL_CONTROL':
                OwnerREAD   = 'tick.png'
                OwnerWRITE  = 'tick.png'
                OwnerFull   = 'tick.png'

          if AllUsersREAD  == '': AllUsersREAD  = 'delete.png'
          if AllUsersWRITE == '': AllUsersWRITE = 'delete.png'
          if AllUsersFULL  == '': AllUsersFULL  = 'delete.png'
          if AuthentUsersREAD  == '': AuthentUsersREAD  = 'delete.png'
          if AuthentUsersWRITE == '': AuthentUsersWRITE = 'delete.png'
          if AuthentUsersFULL  == '': AuthentUsersFULL  = 'delete.png'
          if OwnerREAD  == '': OwnerREAD  = 'delete.png'
          if OwnerWRITE == '': OwnerWRITE = 'delete.png'
          if OwnerFull  == '': OwnerFull  = 'delete.png'

          acl_tabelle = '\n'
          acl_tabelle = acl_tabelle + '<table border="1" cellspacing="0" cellpadding="5"> \n'
          acl_tabelle = acl_tabelle + '<tr> \n'
          if sprache == "de": 
            acl_tabelle = acl_tabelle + '<th>Benutzer</th> \n'
            acl_tabelle = acl_tabelle + '<th>Lesen</th> \n'
            acl_tabelle = acl_tabelle + '<th>Schreiben</th> \n'
            acl_tabelle = acl_tabelle + '<th>Voller Zugriff</th> \n'
          else:
            acl_tabelle = acl_tabelle + '<th>User</th> \n'
            acl_tabelle = acl_tabelle + '<th>Read</th> \n'
            acl_tabelle = acl_tabelle + '<th>Write</th> \n'
            acl_tabelle = acl_tabelle + '<th>Full Control</th> \n'
          acl_tabelle = acl_tabelle + '</tr> \n'
          acl_tabelle = acl_tabelle + '<tr> \n'
          if sprache == "de": acl_tabelle = acl_tabelle + '<td>Alle</td> \n'
          else:               acl_tabelle = acl_tabelle + '<td>Everyone</td> \n'
          acl_tabelle = acl_tabelle + '<td align="center"> \n'
          acl_tabelle = acl_tabelle + '<img src="bilder/'+AllUsersREAD+'" width="24" height="24" border="0" alt="'+AllUsersREAD+'"> \n'
          acl_tabelle = acl_tabelle + '</td> \n'
          acl_tabelle = acl_tabelle + '<td align="center"> \n'
          acl_tabelle = acl_tabelle + '<img src="bilder/'+AllUsersWRITE+'" width="24" height="24" border="0" alt="'+AllUsersWRITE+'"> \n'
          acl_tabelle = acl_tabelle + '</td> \n'
          acl_tabelle = acl_tabelle + '<td align="center"> \n'
          acl_tabelle = acl_tabelle + '<img src="bilder/'+AllUsersFULL+'" width="24" height="24" border="0" alt="'+AllUsersFULL+'"> \n'
          acl_tabelle = acl_tabelle + '</td> \n'
          acl_tabelle = acl_tabelle + '</tr> \n'
          acl_tabelle = acl_tabelle + '<tr> \n'
          if sprache == "de": acl_tabelle = acl_tabelle + '<td>Authentifizierte Benutzer</td> \n'
          else:               acl_tabelle = acl_tabelle + '<td>Authenticated Users</td> \n'
          acl_tabelle = acl_tabelle + '<td align="center"> \n'
          acl_tabelle = acl_tabelle + '<img src="bilder/'+AuthentUsersREAD+'" width="24" height="24" border="0" alt="'+AuthentUsersREAD+'"> \n'
          acl_tabelle = acl_tabelle + '</td> \n'
          acl_tabelle = acl_tabelle + '<td align="center"> \n'
          acl_tabelle = acl_tabelle + '<img src="bilder/'+AuthentUsersWRITE+'" width="24" height="24" border="0" alt="'+AuthentUsersWRITE+'"> \n'
          acl_tabelle = acl_tabelle + '</td> \n'
          acl_tabelle = acl_tabelle + '<td align="center"> \n'
          acl_tabelle = acl_tabelle + '<img src="bilder/'+AuthentUsersFULL+'" width="24" height="24" border="0" alt="'+AuthentUsersFULL+'"> \n'
          acl_tabelle = acl_tabelle + '</td> \n'
          acl_tabelle = acl_tabelle + '</tr> \n'
          acl_tabelle = acl_tabelle + '<tr> \n'
          if sprache == "de": acl_tabelle = acl_tabelle + '<td>'+OwnerName+' (Besitzer)</td> \n'
          else:               acl_tabelle = acl_tabelle + '<td>'+OwnerName+' Owner</td> \n'
          acl_tabelle = acl_tabelle + '<td align="center"> \n'
          acl_tabelle = acl_tabelle + '<img src="bilder/'+OwnerREAD+'" width="24" height="24" border="0" alt="'+OwnerREAD+'"> \n'
          acl_tabelle = acl_tabelle + '</td> \n'
          acl_tabelle = acl_tabelle + '<td align="center"> \n'
          acl_tabelle = acl_tabelle + '<img src="bilder/'+OwnerWRITE+'" width="24" height="24" border="0" alt="'+OwnerWRITE+'"> \n'
          acl_tabelle = acl_tabelle + '</td> \n'
          acl_tabelle = acl_tabelle + '<td align="center"> \n'
          acl_tabelle = acl_tabelle + '<img src="bilder/'+OwnerFull+'" width="24" height="24" border="0" alt="'+OwnerFull+'"> \n'
          acl_tabelle = acl_tabelle + '</td> \n'
          acl_tabelle = acl_tabelle + '</tr> \n'
          acl_tabelle = acl_tabelle + '</table> \n'

          # Wenn man sich NICHT unter Amazon befindet, funktioniert das Ändern der ACL nicht.
          if regionname != "Amazon":
            if sprache == "de":
              eucalyptus_warnung = '<B>Achtung!</B> Unter Eucalyptus 1.6 und 1.6.1 funktioniert das &Auml;ndern der Zugriffsberechtigung (Access Control List) nicht.</B>'
            else:
              eucalyptus_warnung = '<B>Attention!</B> With Eucalyptus 1.6 and 1.6.1 changing the ACL is broken.</B>'
          else: 
            eucalyptus_warnung = ''

          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'zonen_liste': zonen_liste,
          'bucketname': bucketname,
          'keyname': keyname,
          'acl_tabelle': acl_tabelle,
          'typ': typ,
          'directory': directory,
          'eucalyptus_warnung': eucalyptus_warnung,
          }

          #if sprache == "de": naechse_seite = "acl_de.html"
          #else:               naechse_seite = "acl_en.html"
          #path = os.path.join(os.path.dirname(__file__), naechse_seite)
          path = os.path.join(os.path.dirname(__file__), "templates", sprache, "acl.html")
          self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')


class ACL_Aendern(webapp.RequestHandler):
    def post(self):
        # Zum Testen, ob "post" funktioniert hat
        # self.response.out.write('posted!')
        keyname    = self.request.get('keyname')
        bucketname = self.request.get('bucketname')
        canned_acl = self.request.get('canned_acl')
        typ        = self.request.get('typ')
        directory  = self.request.get('dir')

        # Den Usernamen erfahren
        username = users.get_current_user()

        # Mit S3 verbinden
        conn_s3 = logins3(username)
        # Mit dem Bucket verbinden
        bucket_instance = conn_s3.get_bucket(bucketname)

        try:
          # Access Control List (ACL) setzen
          bucket_instance.set_acl(canned_acl, key_name=keyname)
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "119"
          if typ == "pur":
            self.redirect('/bucket_inhalt_pure?bucket='+bucketname+'&message='+fehlermeldung)
          else:
            if directory == "/":
              self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung)
            else:
              directory = str(directory)[:-1]
              self.redirect('/bucket_inhalt?bucket='+bucketname+'&dir='+directory+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "118"
          if typ == "pur":
            self.redirect('/bucket_inhalt_pure?bucket='+bucketname+'&message='+fehlermeldung)
          else:
            if directory == "/":
              self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung)
            else:
              directory = str(directory)[:-1]
              self.redirect('/bucket_inhalt?bucket='+bucketname+'&dir='+directory+'&message='+fehlermeldung)


class AlleKeysLoeschenFrage(webapp.RequestHandler):
    def get(self):
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')
        # Den Namen des Buckets erfahren
        bucketname = self.request.get('bucket_name')
        # Die S3-Ansicht (pur oder Komfort) erfahren
        s3_ansicht = self.request.get('s3_ansicht')

        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if results:
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache)
          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache)

          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'zonen_liste': zonen_liste,
          'bucketname': bucketname,
          's3_ansicht': s3_ansicht,
          }

          #if sprache == "de": naechse_seite = "alle_keys_loeschen_frage_de.html"
          #else:               naechse_seite = "alle_keys_loeschen_frage_en.html"
          #path = os.path.join(os.path.dirname(__file__), naechse_seite)
          path = os.path.join(os.path.dirname(__file__), "templates", sprache, "alle_keys_loeschen_frage.html")
          self.response.out.write(template.render(path,template_values))


class AlleKeysLoeschenDefinitiv(webapp.RequestHandler):
    def get(self):
        # Den Usernamen erfahren
        username = users.get_current_user()
        # Den Namen des Buckets erfahren
        bucketname = self.request.get('bucket')
        # Die S3-Ansicht (pur oder Komfort) erfahren
        s3_ansicht = self.request.get('s3_ansicht')

        conn_region, regionname = login(username)

        # Mit S3 verbinden
        conn_s3 = logins3(username)
        bucket_instance = conn_s3.get_bucket(bucketname)

        liste_keys = bucket_instance.get_all_keys()
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


        try:
          for i in range(laenge_liste_keys):
            # Versuch den Key zu löschen
            liste_keys[i].delete()
        except:
          # Wenn es nicht klappt...
          fehlermeldung = "121"
          self.redirect('/bucket_inhalt_pure?bucket='+bucketname+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "120"
          self.redirect('/bucket_inhalt_pure?bucket='+bucketname+'&message='+fehlermeldung)


def aws_access_key_erhalten(username,regionname):
  Anfrage_nach_AWSAccessKeyId = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user =  :username_db AND eucalyptusname = :regionname_db", username_db=username, regionname_db=regionname)
  for db_eintrag in Anfrage_nach_AWSAccessKeyId:
    AWSAccessKeyId = db_eintrag.accesskey

  return AWSAccessKeyId

def aws_secret_access_key_erhalten(username,regionname):
  Anfrage_nach_AWSSecretAccessKeyId = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user =  :username_db AND eucalyptusname = :regionname_db", username_db=username, regionname_db=regionname)
  for db_eintrag in Anfrage_nach_AWSSecretAccessKeyId:
    AWSSecretAccessKeyId = db_eintrag.secretaccesskey
    secretaccesskey_base64decoded = base64.b64decode(str(AWSSecretAccessKeyId))
    AWSSecretAccessKeyId = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))

  return AWSSecretAccessKeyId


def logins3(username):
  # Die Zugangsdaten des Benutzers holen
  aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

  for db_eintrag in aktivezone:
    zoneinderdb = db_eintrag.aktivezone

    if zoneinderdb == "us-east-1" or zoneinderdb == "us-west-1" or zoneinderdb == "eu-west-1":
      aktuellezone = "Amazon"
    else:
      aktuellezone = zoneinderdb


  if aktivezone:
    # In der Spalte "eucalyptusname_db" steht entweder "Amazon" oder der Eucalyptus-Name der Private Cloud
    zugangsdaten = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db=aktuellezone)

    for db_eintrag in zugangsdaten:
      accesskey = db_eintrag.accesskey
      secretaccesskey = db_eintrag.secretaccesskey
      endpointurl = db_eintrag.endpointurl
      port = db_eintrag.port

    if zoneinderdb == "us-east-1" or zoneinderdb == "eu-west-1" or zoneinderdb == "us-west-1":
      calling_format=boto.s3.connection.OrdinaryCallingFormat()
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_s3 = boto.s3.Connection(aws_access_key_id=accesskey,
                                        aws_secret_access_key=secretaccesskey,
                                        is_secure=False,
                                        host="s3.amazonaws.com",
                                        calling_format=calling_format,
                                        path="/")

      regionname = aktuellezone
    else:
      port = int(port)
      calling_format=boto.s3.connection.OrdinaryCallingFormat()
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_s3 = boto.s3.Connection(aws_access_key_id=accesskey,
                                        aws_secret_access_key=secretaccesskey,
                                        is_secure=False,
                                        host=endpointurl,
                                        port=port,
                                        calling_format=calling_format,
                                        path="/services/Walrus")

      regionname = aktuellezone
  else:
    regionname = "keine"
  return conn_s3



def main():
    application = webapp.WSGIApplication([('/', MainPage),
                                          ('/regionen', Regionen),
                                          ('/instanzen', Instanzen),
                                          ('/alle_instanzen_beenden', AlleInstanzenBeendenFrage),
                                          ('/alle_instanzen_beenden_definitiv', AlleInstanzenBeenden),
                                          ('/instanzbeenden', InstanzBeenden),
                                          ('/instanzreboot', InstanzReboot),
                                          ('/instanzanlegen', InstanzAnlegen),
                                          ('/instanzanlegen_nimbus', InstanzAnlegenNimbus),
                                          ('/images', Images),
                                          ('/imagestarten', ImageStarten),
                                          ('/console_output', ConsoleOutput),
                                          ('/login', Login),
                                          ('/schluessel', Keys),
                                          ('/schluesselentfernen', KeyEntfernen),
                                          ('/schluesselerzeugen', KeyErzeugen),
                                          ('/securitygroups', SecurityGroups),
                                          ('/gruppenentfernen', GruppeEntfernen),
                                          ('/gruppenerzeugen', GruppeErzeugen),
                                          ('/grupperegelanlegen', GruppeRegelErzeugen),
                                          ('/grupperegelentfernen', GruppeRegelEntfernen),
                                          ('/gruppenaendern', GruppeAendern),
                                          ('/zonen', Zonen),
                                          ('/sprache', Sprache),
                                          ('/info', Info),
                                          ('/loadbalancer', LoadBalancer),
                                          ('/delete_load_balancer', DeleteLoadBalancer),
                                          ('/create_load_balancer', CreateLoadBalancer),
                                          ('/loadbalanceraendern', LoadBalancer_Aendern),
                                          ('/loadbalancer_instanz_zuordnen', LoadBalancer_Instanz_Zuordnen),
                                          ('/loadbalancer_deregister_instance', LoadBalancer_Instanz_Entfernen),
                                          ('/loadbalancer_deregister_zone', LoadBalancer_Zone_Entfernen),
                                          ('/loadbalancer_zone_zuordnen', LoadBalancer_Zone_Zuordnen),
                                          ('/elb_definiv_erzeugen', CreateLoadBalancerWirklich),
                                          ('/elastic_ips', Elastic_IPs),
                                          ('/ip_definitiv_anhaengen', IP_Definitiv_Anhaengen),
                                          ('/release_address', Release_IP),
                                          ('/allocate_address', Allocate_IP),
                                          ('/associate_address', Associate_IP),
                                          ('/disassociate_address', Disassociate_IP),
                                          ('/zugangeinrichten', ZugangEinrichten),
                                          ('/zugangentfernen', ZugangEntfernen),
                                          ('/regionwechseln', RegionWechseln),
                                          ('/persoenliche_datan_loeschen', PersoenlicheDatanLoeschen),
                                          ('/persoenliche_favoriten_loeschen', PersoenlicheFavoritenLoeschen),
                                          ('/favoritamierzeugen', FavoritAMIerzeugen),
                                          ('/favoritentfernen', FavoritEntfernen),
                                          ('/s3', S3),
                                          ('/bucketerzeugen', BucketErzeugen),
                                          ('/bucketentfernen', BucketEntfernen),
                                          ('/bucket_inhalt', BucketInhalt),
                                          ('/bucket_inhalt_pure', BucketInhaltPur),
                                          ('/bucketkeyentfernen', BucketKeyEntfernen),
                                          ('/bucketverzeichniserzeugen', BucketVerzeichnisErzeugen),
                                          ('/acl_einsehen', ACL_einsehen),
                                          ('/acl_aendern', ACL_Aendern),
                                          ('/alle_keys_loeschen', AlleKeysLoeschenFrage),
                                          ('/alle_keys_loeschen_definitiv', AlleKeysLoeschenDefinitiv),
                                          ('/snapshots', Snapshots),
                                          ('/snapshotsentfernen', SnapshotsEntfernen),
                                          ('/snapshoterzeugen', SnapshotsErzeugen),
                                          ('/snapshoterzeugendefinitiv', SnapshotsErzeugenDefinitiv),
                                          ('/volumes', Volumes),
                                          ('/volumeentfernen', VolumesEntfernen),
                                          ('/volumeanhaengen', VolumesAnhaengen),
                                          ('/volumedefinitivanhaengen', VolumeDefinitivAnhaengen),
                                          ('/volumeerzeugen', VolumesErzeugen),
                                          ('/volumeloesen', VolumesLoesen),
                                          ('/alle_volumes_loeschen', AlleVolumesLoeschenFrage),
                                          ('/alle_volumes_loeschen_definitiv', AlleVolumesLoeschenDefinitiv)],
                                          debug=True)
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == "__main__":
    main()





