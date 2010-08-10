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
from ec2.InstanzAnlegenNimbus import *
from ec2.InstanzReboot import *
from ec2.InstanzBeenden import *
from ec2.AlleInstanzenBeendenFrage import *
from ec2.Images import *
from ec2.ImageStarten import *
from ec2.Instanzen import *

from elb.LoadBalancer import *
from elb.LoadBalancer_Instanz_Zuordnen import *
from elb.LoadBalancer_Instanz_Entfernen import *
from elb.LoadBalancer_Zone_Entfernen import *
from elb.LoadBalancer_Zone_Zuordnen import *
from elb.LoadBalancer_Aendern import *
from elb.DeleteLoadBalancer import *
from elb.CreateLoadBalancer import *
from elb.CreateLoadBalancerWirklich import *

from s3.AlleKeysLoeschenDefinitiv import *
from s3.ACL_Aendern import *
from s3.AlleKeysLoeschenFrage import *
from s3.BucketEntfernen import *
from s3.BucketKeyEntfernen import *
from s3.BucketVerzeichnisErzeugen import *
from s3.BucketErzeugen import *
from s3.ACL_einsehen import *
from s3.BucketInhalt import *
from s3.BucketInhaltPur import *
from s3.S3 import *

from library import login
from library import xor_crypt_string
from library import aktuelle_sprache
from library import navigations_bar_funktion
from library import amazon_region
from library import zonen_liste_funktion
from library import format_error_message_green
from library import format_error_message_red
from library import loginelb
from library import logins3
from library import aws_access_key_erhalten
from library import aws_secret_access_key_erhalten


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

class ConsoleOutput(webapp.RequestHandler):
    def get(self):
        # self.response.out.write('posted!')
        # Den Usernamen erfahren
        username = users.get_current_user()  
        if not username:
            self.redirect('/')
        # Die ID der Instanz holen
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





