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
from itertools import izip, cycle
import time
import base64
import hmac, sha
# für die Verschlüsselung
import base64

error_messages = {
  '0' :  { 'de' : 'Die IP wurde erfolgreich mit der Instanz verkn&uuml;pft',
           'en' : 'The IP was attached to the instance successfully' },
  '1' :  { 'de' : 'Beim Versuch, die IP mit der Instanz zu verkn&uuml;pfen, kam es zu einem Fehler',
           'en' : 'While the system tried to attach the IP to the instance, an error occured' },
  '2' :  { 'de' : 'Beim Versuch, die IP von der Instanz zu l&oumlsen, kam es zu einem Fehler',
           'en' : 'While the system tried to detach the IP from the instance, an error occured' },
  '3' :  { 'de' : 'Die IP wurde erfolgreich von der Instanz gel&ouml;st',
           'en' : 'The IP was detached from the instance successfully' },
  '4' :  { 'de' : 'Beim Versuch, die IP freizugeben, kam es zu einem Fehler',
           'en' : 'While the system tried to release the IP, an error occured' },
  '5' :  { 'de' : 'Die IP wurde erfolgreich freigegeben',
           'en' : 'The IP was released successfully' },
  '6' :  { 'de' : 'Beim Versuch, eine IP zu erzeugen, kam es zu einem Fehler',
           'en' : 'While the system tried to allocate an elastic IP, an error occured' },
  '7' :  { 'de' : 'Es wurde eine IP erzeugt',
           'en' : 'An IP was allocated successfully' },
  '8' :  { 'de' : 'Es ist ein Timeout-Fehler aufgetreten. M&ouml;glicherweise ist das Ergebnis dennoch korrekt',
           'en' : 'A timeout error occured but maybe the operation was successful' },
  '9' :  { 'de' : 'Es ist ein Timeout-Fehler aufgetreten',
           'en' : 'A timeout error occured' },
  '10' : { 'de' : 'Es ist ein Fehler aufgetreten',
           'en' : 'An error occured' },
  '11' : { 'de' : 'Der Snapshot wurde erfolgreich gel&ouml;scht',
           'en' : 'The snapshot was erased successfully' },
  '12' : { 'de' : 'Beim Versuch den Snapshot zu l&ouml;schen, kam es zu einem Fehler',
           'en' : 'While the system tried to erase the snapshot, an error occured' },
  '13' : { 'de' : 'Der Snapshot wurde erfolgreich erzeugt',
           'en' : 'The snapshot was created successfully' },
  '14' : { 'de' : 'Beim Versuch, den Snapshot zu erzeugen, kam es zu einem Fehler',
           'en' : 'While the system tried to create the snapshot, an error occured' },
  '15' : { 'de' : 'Das Volume wurde erfolgreich angelegt',
           'en' : 'The volume was created successfully' },
  '16' : { 'de' : 'Sie haben keine Gr&ouml;&szlig;e angegeben',
           'en' : 'No size given' },
  '17' : { 'de' : 'Sie haben keine Zahl angegeben',
           'en' : 'The size was not a number' },
  '18' : { 'de' : 'Beim Versuch, das neue Volume zu erzeugen, kam es zu einem Fehler',
           'en' : 'An error occured while the system tried to create the new volume' },
  '19' : { 'de' : 'Beim Versuch das Volume zu entfernen, kam es zu einem Fehler',
           'en' : 'An error occured while the system tried to delete the volume' },
  '20' : { 'de' : 'Beim Versuch, das Volume von der Instanz zu l&ouml;sen, kam es zu einem Fehler',
           'en' : 'An error occured while the system tried to detach the volume from the instance' },
  '21' : { 'de' : 'Beim Versuch, das Volume mit der Instanz zu verbinden, kam es zu einem Fehler',
           'en' : 'An error occured while the system tried to attach the volume with the instance' },
  '22' : { 'de' : 'Das Volume wurde erfolgreich gel&ouml;scht',
           'en' : 'The volume was erased successfully' },
  '23' : { 'de' : 'Das Volume wurde erfolgreich mit der Instanz verbunden',
           'en' : 'The volume was attached with the instance successfully' },
  '24' : { 'de' : 'Das Volume wurde erfolgreich von der Instanz gel&ouml;st',
           'en' : 'The volume was detached from the instance successfully' },
  '25' : { 'de' : 'EBS erm&ouml;glicht die Erstellung von Datentr&auml;gern mit einer Speicherkapazit&auml;t von 1 GB bis 1 TB',
           'en' : 'EBS allows to create storage volumes from 1 GB to 1 TB' },
  '26' : { 'de' : 'Beim Versuch, die Volumes zu l&ouml;schen, kam es zu einem Fehler',
           'en' : 'While the system tried to erase the volumes, an error occured' },
  '27' : { 'de' : 'Die Volumes wurden gel&ouml;scht',
           'en' : 'The volumes were erased successfully' },
  '28' : { 'de' : 'Die Regel wurde erfolgreich angelegt',
           'en' : 'The rule was created successfully' },
  '29' : { 'de' : 'Sie haben keinen From Port und keinen To Port f&uuml;r die neue Regel angegeben',
           'en' : 'The From Port and the To Port for the new rule was missing' },
  '30' : { 'de' : 'Sie haben keinen From Port f&uuml;r die neue Regel angegeben',
           'en' : 'The From Port for the new rule was missing' },
  '31' : { 'de' : 'Sie haben keinen To Port f&uuml;r die neue Regel angegeben',
           'en' : 'The To Port for the new rule was missing' },
  '32' : { 'de' : 'Sie haben f&uuml;r den From Port und f&uuml;r den To Port keine Zahl angegeben',
           'en' : 'The From Port and the To Port for the new rule have not been numbers' },
  '33' : { 'de' : 'Sie haben f&uuml;r den From Port keine Zahl angegeben',
           'en' : 'The From Port for the new rule was not a number' },
  '34' : { 'de' : 'Sie haben f&uuml;r den To Port keine Zahl angegeben',
           'en' : 'The To Port for the new rule was not a number' },
  '35' : { 'de' : 'Die Regel war schon vorhanden',
           'en' : 'The rule was still existing' },
  '36' : { 'de' : 'Beim Versuch, die Regel zu entfernen, kam es zu einem Fehler',
           'en' : 'While the system tried to remove the rule, an error occured' },
  '37' : { 'de' : 'Die Regel wurde erfolgreich entfernt',
           'en' : 'The rule was removed successfully' },
  '38' : { 'de' : 'Die zu l&ouml;schende Regel konnte nicht gefunden werden',
           'en' : 'The rule was not found' },
  '39' : { 'de' : 'Beim Versuch, die Regel zu anzulegen, kam es zu einem Fehler',
           'en' : 'While the system tried to create the rule, an error occured' },
  '40' : { 'de' : 'Die Sicherheitsgruppe wurde erfolgreich angelegt',
           'en' : 'The security group was created successfully' },
  '41' : { 'de' : 'Sie haben keinen Name und keine Beschreibung f&uuml;r die neue  Sicherheitsgruppe angegeben',
           'en' : 'No name and no description for the new security group given' },
  '42' : { 'de' : 'Sie haben keinen Namen f&uuml;r die neue  Sicherheitsgruppe angegeben',
           'en' : 'No name for the new security group given' },
  '43' : { 'de' : 'Sie haben keine Beschreibung f&uuml;r die neue  Sicherheitsgruppe angegeben',
           'en' : 'No description for the new security group given' },
  '44' : { 'de' : 'Es existiert schon eine Sicherheitsgruppe mit dem von Ihnen angegebenen Namen',
           'en' : 'A security group with this name sill exists' },
  '45' : { 'de' : 'Der Name für die neue Sicherheitsgruppe enthielt unerlaubte Zeichen',
           'en' : 'The name for the new security group had characters that are not allowed' },
  '46' : { 'de' : 'Die Beschreibung für die neue Sicherheitsgruppe enthielt unerlaubte Zeichen',
           'en' : 'The description for the new security group had characters that are not allowed' },
  '47' : { 'de' : 'Beim Versuch, die neue Sicherheitsgruppe anzulegen, kam es zu einem Fehler',
           'en' : 'While the system tried to create the new security group, an error occured' },
  '48' : { 'de' : 'Die Sicherheitsgruppe wurde erfolgreich gel&ouml;scht',
           'en' : 'The security group was erased successfully' },
  '49' : { 'de' : 'Beim Versuch, die neue Sicherheitsgruppe zu l&ouml;schen, kam es zu einem Fehler',
           'en' : 'While the system tried to erase the new security group, an error occured' },
  '50' : { 'de' : 'Sie haben keinen Namen angegeben',
           'en' : 'No name given' },
  '51' : { 'de' : 'Der Name darf nur Buchstaben, Zahlen und Bindestriche enthalten',
           'en' : 'The name cannot contain characters that are not letters, or digits or the dash' },
  '52' : { 'de' : 'Sie haben keinen Load Balancer Port angegeben',
           'en' : 'No load balancer port given' },
  '53' : { 'de' : 'Sie haben keinen EC2 Instanz Port angegeben',
           'en' : 'No EC2 instance port given' },
  '54' : { 'de' : 'Sie haben keinen Load Balancer Port und keinen EC2 Instanz Port angegeben',
           'en' : 'No load balancer port and no EC2 instance port given' },
  '55' : { 'de' : 'Der Load Balancer Port enthielt unerlaubt Zeichen',
           'en' : 'The load balancer port hat characters that are not allowed' },
  '56' : { 'de' : 'Der EC2 Instanz Port enthielt unerlaubt Zeichen',
           'en' : 'The EC2 instance port hat characters that are not allowed' },
  '57' : { 'de' : 'Beim Versuch, den Load Balancer zu erzeugen, kam es zu einem Fehler',
           'en' : 'While the system tried to create the load balancer, an error occured' },
  '58' : { 'de' : 'Sie haben keine Verf&uuml;gbarkeitszone angegeben',
           'en' : 'No availability zone given' },
  '59' : { 'de' : 'Der Load Balancer Port muss 80 oder 443 sein oder im Bereich von 1024 bis 65535 liegen',
           'en' : 'Load balancer port must be either 80, 443 or 1024-65535 inclusive' },
  '60' : { 'de' : 'Der EC2 instance port muss kleiner gleich 65535 sein',
           'en' : 'EC2 instance port must less than or equal to 65535' },
  '61' : { 'de' : 'Die Instanz wurde erfolgreich mit dem Load Balancer verkn&uuml;pft',
           'en' : 'The instance was attached to the load balancer successfully' },
  '62' : { 'de' : 'Beim Versuch, die Instanz mit dem Load Balancer zu verkn&uuml;pfen, kam es zu einem Fehler',
           'en' : 'While the system tried to attach the instance to the load balancer, an error occured' },
  '63' : { 'de' : 'Die Instanz wurde erfolgreich deregistriert',
           'en' : 'The instance was deregistered successfully' },
  '64' : { 'de' : 'Beim Versuch, die Instanz zu deregistrieren, kam es zu einem Fehler',
           'en' : 'While the system tried to deregister the instance, an error occured' },
  '65' : { 'de' : 'Beim Versuch, die Zone zu deregistrieren, kam es zu einem Fehler',
           'en' : 'While the system tried to deregister the zone, an error occured' },
  '66' : { 'de' : 'Die Zone wurde erfolgreich deregistriert',
           'en' : 'The zone was deregistered successfully' },
  '67' : { 'de' : 'Es muss mindestens eine Zone registriert sein',
           'en' : 'It is impossible to deregister all zones' },
  '68' : { 'de' : 'Die Zone wurde erfolgreich mit dem Load Balancer verkn&uuml;pft',
           'en' : 'The zone was attached to the load balancer successfully' },
  '69' : { 'de' : 'Beim Versuch, die Zone mit dem Load Balancer zu verkn&uuml;pfen, kam es zu einem Fehler',
           'en' : 'While the system tried to attach the zone to the load balancer, an error occured' },
  '70' : { 'de' : 'Der Load Balancer wurde erfolgreich gel&ouml;scht',
           'en' : 'The load balancer was deleted successfully' },
  '71' : { 'de' : 'Beim Versuch, den Load Balancer zu l&ouml;schen, kam es zu einem Fehler',
           'en' : 'While the system tried to delete the load balancer, an error occured' },
  '72' : { 'de' : 'Der Load Balancer wurde erfolgreich angelegt',
           'en' : 'The load balancer was created successfully' },
}

# Hilfsfunktion für die Formatierung der grünen Fehlermeldungen
def format_error_message_green(input_error_message):
    if input_error_message:
        return "<p>&nbsp;</p> <font color='green'>%s</font>" % (input_error_message)
    else:
        return ""

# Hilfsfunktion für die Formatierung der roten Fehlermeldungen
def format_error_message_red(input_error_message):
    if input_error_message:
        return "<p>&nbsp;</p> <font color='red'>%s</font>" % (input_error_message)
    else:
        return ""

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

            if message == "0":
              input_error_message = ''
            elif message == "1":
              if sprache == "de":
                input_error_message = '<p>&nbsp;</p> <font color="red">Sie haben keinen Access Key und keinen Secret Access Key angegeben</font>'
              else:
                input_error_message = '<p>&nbsp;</p> <font color="red">No Access Key and no Secret Access Key given</font>'
            elif message == "2":
              if sprache == "de":
                input_error_message = '<p>&nbsp;</p> <font color="red">Sie haben keinen Access Key angegeben</font>'
              else:
                input_error_message = '<p>&nbsp;</p> <font color="red">No Access Key given</font>'
            elif message == "3":
              if sprache == "de":
                input_error_message = '<p>&nbsp;</p> <font color="red">Sie haben keinen Secret Access Key angegeben</font>'
              else:
                input_error_message = '<p>&nbsp;</p> <font color="red">No Secret Access Key given</font>'
            elif message == "4":
              if sprache == "de":
                input_error_message = '<p>&nbsp;</p> <font color="red">Sie haben keinen Name angegeben</font>'
              else:
                input_error_message = '<p>&nbsp;</p> <font color="red">No Name given</font>'
            elif message == "5":
              if sprache == "de":
                input_error_message = '<p>&nbsp;</p> <font color="red">Sie haben keine Endpoint URL angegeben</font>'
              else:
                input_error_message = '<p>&nbsp;</p> <font color="red">No Endpoint given</font>'
            elif message == "6":
              if sprache == "de":
                input_error_message = '<p>&nbsp;</p> <font color="red">Ihr eingegebener Access Key enthielt nicht erlaubte Zeichen</font>'
              else:
                input_error_message = '<p>&nbsp;</p> <font color="red">The given Access Key had characters that are not allowed</font>'
            elif message == "7":
              if sprache == "de":
                input_error_message = '<p>&nbsp;</p> <font color="red">Ihr eingegebener Secret Access Key enthielt nicht erlaubte Zeichen</font>'
              else:
                input_error_message = '<p>&nbsp;</p> <font color="red">The given Secret Access Key had characters that are not allowed</font>'
            elif message == "8":
              if sprache == "de":
                input_error_message = '<p>&nbsp;</p> <font color="red">Ihr eingegebener Name enthielt nicht erlaubte Zeichen</font>'
              else:
                input_error_message = '<p>&nbsp;</p> <font color="red">The given Name had characters that are not allowed</font>'
            elif message == "9":
              if sprache == "de":
                input_error_message = '<p>&nbsp;</p> <font color="red">Ihre eingegebene Endpoint URL enthielt nicht erlaubte Zeichen</font>'
              else:
                input_error_message = '<p>&nbsp;</p> <font color="red">The given Endpoint URL had characters that are not allowed</font>'
            elif message == "10":
              if sprache == "de":
                input_error_message = '<p>&nbsp;</p> <font color="red">Die eingegebenen Zugangsdaten funktionieren nicht</font>'
              else:
                input_error_message = '<p>&nbsp;</p> <font color="red">The given credentials are wrong</font>'
            else:
              input_error_message = ''


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
              if sprache == "de":
                version_warnung = '<p><font color="red">KOALA unterst&uuml;tzt ausschlie&szlig;lich Eucalyptus 1.6.2.<br> '
                version_warnung = version_warnung + 'Fr&uuml;here Versionen haben einige Bugs, die zu Problemen f&uuml;hren k&ouml;nnen.<br>'
                version_warnung = version_warnung + 'Ein Update von Eucalyptus auf die aktuelle Version wird daher empfohlen.</font></p>'
              else:
                version_warnung = '<p><font color="red">KOALA supports only Eucalyptus 1.6.2.<br> '
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

          #if sprache != "de":
            #sprache = "en"

          #input_error_message = error_messages.get(message, {}).get(sprache)

          ## Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
          #if input_error_message == None:
            #input_error_message = ""

          ## Wenn die Nachricht grün formatiert werden soll...
          #if message == '28' or message == '37':
            ## wird sie hier, in der Hilfsfunktion grün formatiert
            #input_error_message = format_error_message_green(input_error_message)
          ## Ansonsten wird die Nachricht rot formatiert
          #else:
            #input_error_message = format_error_message_red(input_error_message)

          if message == "0":
            if sprache == "de":
              input_error_message = '<font color="green">Die Instanz wurde erfolgreich beendet</font> <p>&nbsp;</p>'
            else:
              input_error_message = '<font color="green">The instance was stopped successfully</font> <p>&nbsp;</p>'
          elif message == "1":
            if sprache == "de":
              input_error_message = '<font color="red">Beim Versuch die Instanz zu beenden ist ein Fehler aufgetreten</font> <p>&nbsp;</p>'
            else:
              input_error_message = '<font color="red">While the system tried to stop the instance, an error occured</font> <p>&nbsp;</p>'
          elif message == "2":
            if sprache == "de":
              input_error_message = '<font color="red">Die zu beendende Instanz konnte nicht gefunden werden</font> <p>&nbsp;</p>'
            else:
              input_error_message = '<font color="red">The instance was not found</font> <p>&nbsp;</p>'
          elif message == "3":
            if sprache == "de":
              input_error_message = '<font color="red">Die Instanz war schon im Status <b>terminated</b></font> <p>&nbsp;</p>'
            else:
              input_error_message = '<font color="red">The instance had still the state <b>terminated</b></font> <p>&nbsp;</p>'
          elif message == "4":
            if sprache == "de":
              input_error_message = '<font color="green">Die Instanz(en) wurde(n) erfolgreich angelegt</font> <p>&nbsp;</p>'
            else:
              input_error_message = '<font color="green">The instance(s) was/were created successfully</font> <p>&nbsp;</p>'
          elif message == "5":
            if sprache == "de":
              input_error_message = '<font color="red">Beim Versuch die Instanz(en) anzulegen, ist ein Fehler aufgetreten</font> <p>&nbsp;</p>'
            else:
              input_error_message = '<font color="red">While the system tried to create the instance(s), an error occured</font> <p>&nbsp;</p>'
          elif message == "6":
            if sprache == "de":
              input_error_message = '<font color="green">Die Instanz wurde erfolgreich neu gestartet</font> <p>&nbsp;</p>'
            else:
              input_error_message = '<font color="green">The instance was rebooted successfully</font> <p>&nbsp;</p>'
          elif message == "7":
            if sprache == "de":
              input_error_message = '<font color="red">Beim Versuch die Instanz neuzustarten, ist ein Fehler aufgetreten</font> <p>&nbsp;</p>'
            else:
              input_error_message = '<font color="red">While the system tried to reboot the instance, an error occured</font> <p>&nbsp;</p>'
          elif message == "8":
            if sprache == "de":
              input_error_message = '<font color="green">Die Instanzen wurden beendet</font> <p>&nbsp;</p>'
            else:
              input_error_message = '<font color="green">The instances were stopped successfully</font> <p>&nbsp;</p>'
          elif message == "9":
            if sprache == "de":
              input_error_message = '<font color="red">Es ist ein Fehler aufgetreten</font> <p>&nbsp;</p>'
            else:
              input_error_message = '<font color="red">An error occured</font> <p>&nbsp;</p>'
          elif message == "10":
            if sprache == "de":
              input_error_message = '<font color="red">Es ist ein Timeout-Fehler aufgetreten. M&ouml;glicherweise ist das Ergebnis dennoch korrekt</font> <p>&nbsp;</p>'
            else:
              input_error_message = '<font color="red">A timeout error occured but maybe the operation was successful</font> <p>&nbsp;</p>'
          elif message == "11":
            if sprache == "de":
              input_error_message = '<font color="red">Es ist ein Timeout-Fehler aufgetreten</font> <p>&nbsp;</p>'
            else:
              input_error_message = '<font color="red">A timeout error occured</font> <p>&nbsp;</p>'
          elif message == "12":
            if sprache == "de":
              input_error_message = '<font color="red">Beim Versuch die Instanzen zu beenden ist ein Fehler aufgetreten</font> <p>&nbsp;</p>'
            else:
              input_error_message = '<font color="red">While the system tried to stop the instances, an error occured</font> <p>&nbsp;</p>'
          else:
            input_error_message = ''

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
                    instanzentabelle = instanzentabelle + "&amp;aki="
                    instanzentabelle = instanzentabelle + str(x.kernel)
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
                    instanzentabelle = instanzentabelle + "&amp;aki="
                    instanzentabelle = instanzentabelle + str(x.kernel)
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
                  instanzentabelle = instanzentabelle + x.instance_type
                  instanzentabelle = instanzentabelle + '</tt>'
                  instanzentabelle = instanzentabelle + '</td><td align="center">'
                  instanzentabelle = instanzentabelle + '<tt>'
                  instanzentabelle = instanzentabelle + i.id
                  #y = str(i)
                  #z = y.replace('Reservation:', '')
                  #instanzentabelle = instanzentabelle + z
                  instanzentabelle = instanzentabelle + '</tt>'
                  instanzentabelle = instanzentabelle + '</td><td align="center">'
                  instanzentabelle = instanzentabelle + '<tt>'
                  instanzentabelle = instanzentabelle + i.owner_id
                  #y = str(i)
                  #z = y.replace('Reservation:', '')
                  #instanzentabelle = instanzentabelle + z
                  instanzentabelle = instanzentabelle + '</tt>'
                  instanzentabelle = instanzentabelle + '</td><td>'
                  instanzentabelle = instanzentabelle + '<tt>'+x.image_id+'</tt>'
                  instanzentabelle = instanzentabelle + '</td><td>'
                  instanzentabelle = instanzentabelle + '<tt>'+x.kernel+'</tt>'
                  instanzentabelle = instanzentabelle + '</td><td>'
                  instanzentabelle = instanzentabelle + '<tt>'+x.ramdisk+'</tt>'
                  instanzentabelle = instanzentabelle + '</td><td>'
                  instanzentabelle = instanzentabelle + x.placement
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
                  instanzentabelle = instanzentabelle + x.public_dns_name
                  #if x.public_dns_name != None:
                    #instanzentabelle = instanzentabelle + '<a href="http://'+x.public_dns_name+'" style="color:blue">Link</a>'
                  #else:
                    #instanzentabelle = instanzentabelle + x.private_dns_name
                  #instanzentabelle = instanzentabelle + '</td><td align="center">'
                  instanzentabelle = instanzentabelle + '</td><td>'
                  instanzentabelle = instanzentabelle + x.private_dns_name
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
          if message == '40' or message == '48':
            # wird sie hier, in der Hilfsfunktion grün formatiert
            input_error_message = format_error_message_green(input_error_message)
          # Ansonsten wird die Nachricht rot formatiert
          elif message == '8' or message == '41' or message == '42' or message == '43' or message == '44' or message == '45' or message == '46' or message == '47' or message == '49':
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
        if message == '28' or message == '37':
          # wird sie hier, in der Hilfsfunktion grün formatiert
          input_error_message = format_error_message_green(input_error_message)
        # Ansonsten wird die Nachricht rot formatiert
        elif message == '8' or message == '29' or message == '30' or message == '31' or message == '32' or message == '33' or message == '34' or message == '35' or message == '36' or message == '38' or message == '39':
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

class GruppeEntfernen(webapp.RequestHandler):
    def get(self):
      # Den Namen der zu löschenden Gruppe holen
        gruppe = self.request.get('gruppe')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Security Gruppe löschen
          conn_region.delete_security_group(gruppe)
        except EC2ResponseError:
          # Wenn es nicht geklappt hat...
          fehlermeldung = "49"
          self.redirect('/securitygroups?message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/securitygroups?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "48"
          self.redirect('/securitygroups?message='+fehlermeldung)

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

          if message == "0":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="green">Das Schl&uuml;sselpaar wurde erfolgreich angelegt</font>'
              # <br><a href="Hier">Hier</a> k&ouml;nnen Sie den Geheimen Schl&uuml;ssel herunterladen
            else:
              input_error_message = '<p>&nbsp;</p> <font color="green">The keypair was created successfully</font>'
          elif message == "1":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Sie haben keinen Namen angegeben</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">No name given</font>'
          elif message == "2":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Der Name f&uuml;r das neue Schl&uuml;sselpaar enthielt nicht erlaubt Zeichen</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">The name for the new keypair had characters that are not allowed</font>'
          elif message == "3":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Beim Versuch das neue Schl&uuml;sselpaar anzulegen, kam es zu einem Fehler</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">While the system tried to create the new keypair, an error occured</font>'
          elif message == "4":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Es existiert bereits ein Schl&uuml;sselpaar mit dem angegebenen Namen</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">A keypair with the given name already exists</font>'
          elif message == "5":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="green">Das Schl&uuml;sselpaar wurde erfolgreich gel&ouml;scht</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="green">The keypair was erased successfully</font>'
          elif message == "6":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Beim Versuch das Schl&uuml;sselpaar zu l&ouml;schen, kam es zu einem Fehler</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">While the system tried to erase the keypair, an error occured</font>'
          elif message == "7":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Es ist ein Timeout-Fehler aufgetreten. M&ouml;glicherweise ist das Ergebnis dennoch korrekt</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">A timeout error occured but maybe the operation was successful</font>'
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


class CreateLoadBalancer(webapp.RequestHandler):
    def get(self):
        #self.response.out.write('posted!')
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')
        # Eventuell vorhande Fehlermeldung holen
        message = self.request.get('message')

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
        if message == '8' or message == '50' or message == '51' or message == '52' or message == '53' or message == '54' or message == '55' or message == '56' or message == '57' or message == '58' or message == '59' or message == '60':
          # wird sie hier, in der Hilfsfunktion rot formatiert
          input_error_message = format_error_message_red(input_error_message)
        else:
          input_error_message = ""

        try:
          # Liste mit den Zonen
          liste_zonen = conn_region.get_all_zones()
        except EC2ResponseError:
          # Wenn es nicht geklappt hat...
          fehlermeldung = "10"
          self.redirect('/loadbalancer?message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/loadbalancer?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          # Anzahl der Elemente in der Liste
          laenge_liste_zonen = len(liste_zonen)

        elb_erzeugen_tabelle = ''
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<form action="/elb_definiv_erzeugen" method="post" accept-charset="utf-8">\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<table border="3" cellspacing="0" cellpadding="5">'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<tr>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>Name</td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td><input name="elb_name" type="text" size="40" maxlength="40"></td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</tr>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<tr>\n'
        if sprache == "de":
          elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>Verf&uuml;gbarkeitszonen</td>\n'
        else:
          elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>Availability Zones</td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>\n'
        for i in range(laenge_liste_zonen):
          elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<input type="checkbox" name="'+liste_zonen[i].name+'" value="'+liste_zonen[i].name+'"> '+liste_zonen[i].name+'<BR>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</tr>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<tr>\n'
        if sprache == "de":
          elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>Protokoll</td>\n'
        else:
          elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>Protocol</td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<select name="elb_protokoll" size="1">\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '  <option selected="selected">TCP</option>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '  <option>HTTP</option>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</select>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</tr>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<tr>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>Load Balancer Port</td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td><input name="ELBPort" type="text" size="10" maxlength="10"></td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</tr>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<tr>\n'
        if sprache == "de":
          elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>EC2 Instanz Port</td>\n'
        else:
          elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>EC2 Instance Port</td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td><input name="InstPort" type="text" size="10" maxlength="10"></td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</tr>\n'


        elb_erzeugen_tabelle = elb_erzeugen_tabelle + ''
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<tr>\n'
        if sprache == "de":
          elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td colspan="2"><input type="submit" value="Load Balancer anlegen"></td>\n'
        else:
          elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td colspan="2"><input type="submit" value="create load balancer"></td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</table>'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</form>'


        template_values = {
        'navigations_bar': navigations_bar,
        'url': url,
        'url_linktext': url_linktext,
        'zone': regionname,
        'zone_amazon': zone_amazon,
        'elb_erzeugen_tabelle': elb_erzeugen_tabelle,
        'input_error_message': input_error_message,
        'zonen_liste': zonen_liste,
        }

        #if sprache == "de": naechse_seite = "elb_create_de.html"
        #else:               naechse_seite = "elb_create_en.html"
        #path = os.path.join(os.path.dirname(__file__), naechse_seite)
        path = os.path.join(os.path.dirname(__file__), "templates", sprache, "elb_create.html")
        self.response.out.write(template.render(path,template_values))


class CreateLoadBalancerWirklich(webapp.RequestHandler):
    def post(self):
        elb_name = self.request.get('elb_name')
        elb_protokoll = self.request.get('elb_protokoll')
        ELBPort = self.request.get('ELBPort')
        InstPort = self.request.get('InstPort')
        useast1a = self.request.get('us-east-1a')
        useast1b = self.request.get('us-east-1b')
        useast1c = self.request.get('us-east-1c')
        useast1d = self.request.get('us-east-1d')
        uswest1a = self.request.get('us-west-1a')
        uswest1b = self.request.get('us-west-1b')
        euwest1a = self.request.get('eu-west-1a')
        euwest1b = self.request.get('eu-west-1b')
        apsoutheast1a = self.request.get('ap-southeast-1a')
        apsoutheast1b = self.request.get('ap-southeast-1b')

        # Der Name muss ein String sein
        elb_name = str(elb_name)
        # Das Protokoll muss ein String sein
        elb_protokoll = str(elb_protokoll)

        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        # Nachsehen, wo wir sind
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        for db_eintrag in aktivezone:
          aktivezone = db_eintrag.aktivezone


        if ELBPort.isdigit() == False:
          # Testen ob der Load Balancer Port eine Zahl ist
          # Wenn nicht ausschließlich eine Zahl eingegeben wurde sondern evtl. Buchstaben oder Sonderzeichen
          fehlermeldung = "55"
          self.redirect('/create_load_balancer?message='+fehlermeldung)
        else:
          # Der Load Balancer Port muss ein Integer sein
          ELBPort = int(ELBPort)

        if InstPort.isdigit() == False:
          # Testen ob der EC2 Instanz Port eine Zahl ist
          # Wenn nicht ausschließlich eine Zahl eingegeben wurde sondern evtl. Buchstaben oder Sonderzeichen
          fehlermeldung = "56"
          self.redirect('/create_load_balancer?message='+fehlermeldung)
        else:
          # Der EC2 Instanz Port muss ein Integer sein
          InstPort = int(InstPort)

        if elb_name == "":
          # Testen ob ein Name für den neue ELB angegeben wurde
          fehlermeldung = "50"
          self.redirect('/create_load_balancer?message='+fehlermeldung)
        elif re.search(r'[^\-a-zA-Z0-9]', elb_name) != None:
          # Überprüfen, ob der name nur erlaubte Zeichen enthält
          # Die Zeichen - und a-zA-Z0-9 sind erlaubt. Alle anderen nicht. Darum das ^
          fehlermeldung = "51"
          self.redirect('/create_load_balancer?message='+fehlermeldung)
        elif InstPort == "" and ELBPort == "":
          # Testen ob ein Load Balancer Port und ein EC2 Instanz Port für den neue ELB angegeben wurde
          fehlermeldung = "54"
          self.redirect('/create_load_balancer?message='+fehlermeldung)
        elif ELBPort == "":
          # Testen ob ein Load Balancer Port für den neue ELB angegeben wurde
          fehlermeldung = "52"
          self.redirect('/create_load_balancer?message='+fehlermeldung)
        elif InstPort == "":
          # Testen ob ein EC2 Instanz Port für den neue ELB angegeben wurde
          fehlermeldung = "53"
          self.redirect('/create_load_balancer?message='+fehlermeldung)
        elif aktivezone == "us-east-1" and useast1a == "" and useast1b == "" and useast1c == "" and useast1d == "":
          # Testen ob mindestens eine Zone angegeben wurde
          fehlermeldung = "58"
          self.redirect('/create_load_balancer?message='+fehlermeldung)
        elif aktivezone == "us-west-1" and uswest1a == "" and uswest1b == "":
          # Testen ob mindestens eine Zone angegeben wurde
          fehlermeldung = "58"
          self.redirect('/create_load_balancer?message='+fehlermeldung)
        elif aktivezone == "eu-west-1" and euwest1a == "" and euwest1b == "":
          # Testen ob mindestens eine Zone angegeben wurde
          fehlermeldung = "58"
          self.redirect('/create_load_balancer?message='+fehlermeldung)
        elif aktivezone == "ap-southeast-1" and apsoutheast1a == "" and apsoutheast1b == "":
          # Testen ob mindestens eine Zone angegeben wurde
          fehlermeldung = "58"
          self.redirect('/create_load_balancer?message='+fehlermeldung)
        elif not (ELBPort == 80 or ELBPort == 443 or (1024 <= ELBPort <= 65535)):
          # Testen ob ein korrekter Port für den Load Balancer Port angegeben wurde
          # Load Balancer port must be either 80, 443 or 1024~65535 inclusive
          fehlermeldung = "59"
          self.redirect('/create_load_balancer?message='+fehlermeldung)
        elif InstPort >= 65535:
          # Testen ob ein korrekter Port für den EC2 Instanz Port angegeben wurde
          # Member must have value less than or equal to 65535
          fehlermeldung = "60"
          self.redirect('/create_load_balancer?message='+fehlermeldung)
        else:

          conn_elb = loginselb(username) # Mit ELB verbinden

          zones_elb = []
          if aktivezone == "us-east-1":
            if useast1a != "":
              zones_elb.append('us-east-1a')
            if useast1b != "":
              zones_elb.append('us-east-1b')
            if useast1c != "":
              zones_elb.append('us-east-1c')
            if useast1d != "":
              zones_elb.append('us-east-1d')
          if aktivezone == "us-west-1":
            if uswest1a != "":
              zones_elb.append('us-west-1a')
            if uswest1b != "":
              zones_elb.append('us-west-1b')
          if aktivezone == "eu-west-1":
            if euwest1a != "":
              zones_elb.append('eu-west-1a')
            if euwest1b != "":
              zones_elb.append('eu-west-1b')
          if aktivezone == "ap-southeast-1":
            if apsoutheast1a != "":
              zones_elb.append('ap-southeast-1a')
            if apsoutheast1b != "":
              zones_elb.append('ap-southeast-1b')
          listeners_elb = []
          listeners_elb.append((ELBPort,InstPort,elb_protokoll))

          try:
            # Versuchen, den Load Balancer zu erzeugen
            neuer_loadbalancer = conn_elb.create_load_balancer(elb_name, zones_elb, listeners_elb)
          except EC2ResponseError:
            # Wenn es nicht geklappt hat...
            fehlermeldung = "57"
            self.redirect('/create_load_balancer?message='+fehlermeldung)
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            fehlermeldung = "8"
            self.redirect('/create_load_balancer?message='+fehlermeldung)
          else:
            # Wenn es geklappt hat...
            fehlermeldung = "72"
            self.redirect('/loadbalancer?message='+fehlermeldung)


class DeleteLoadBalancer(webapp.RequestHandler):
    def get(self):
        # Name des zu löschenden Load Balancers holen
        name = self.request.get('name')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)
        # Mit ELB verbinden
        conn_elb = loginselb(username)

        try:
          # Volume löschen
          conn_elb.delete_load_balancer(name)
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "71"
          self.redirect('/loadbalancer?message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/loadbalancer?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "70"
          self.redirect('/loadbalancer?message='+fehlermeldung)


class LoadBalancer(webapp.RequestHandler):
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

        for db_eintrag in aktivezone:
          zugangstyp = db_eintrag.zugangstyp

        if results:
          # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache)

          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')  
          #url = users.create_logout_url(self.request.uri)
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache)

          if zugangstyp != 'Amazon':

            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'zonen_liste': zonen_liste,
            }

            #if sprache == "de": naechse_seite = "loadbalancer_non_aws_de.html"
            #else:               naechse_seite = "loadbalancer_non_aws_en.html"
            #path = os.path.join(os.path.dirname(__file__), naechse_seite)
            path = os.path.join(os.path.dirname(__file__), "templates", sprache, "loadbalancer_non_aws.html")
            self.response.out.write(template.render(path,template_values))
          else:

            if sprache != "de":
              sprache = "en"

            input_error_message = error_messages.get(message, {}).get(sprache)

            # Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
            if input_error_message == None:
              input_error_message = ""

            # Wenn die Nachricht grün formatiert werden soll...
            if message == '9' or message == '70' or message == '72':
              # wird sie hier, in der Hilfsfunktion grün formatiert
              input_error_message = format_error_message_green(input_error_message)
            # Ansonsten wird die Nachricht rot formatiert
            elif message == '8' or message == '10' or message == '71':
              input_error_message = format_error_message_red(input_error_message)
            else:
              input_error_message = ""

            # Mit ELB verbinden
            conn_elb = loginselb(username)

            try:
              # Liste mit den LoadBalancern
              liste_load_balancers = conn_elb.get_all_load_balancers()
            except EC2ResponseError:
              # Wenn es nicht klappt...
              if sprache == "de":
                loadbalancertabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
              else:
                loadbalancertabelle = '<font color="red">An error occured</font>'
            except DownloadError:
              # Diese Exception hilft gegen diese beiden Fehler:
              # DownloadError: ApplicationError: 2 timed out
              # DownloadError: ApplicationError: 5
              if sprache == "de":
                loadbalancertabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
              else:
                loadbalancertabelle = '<font color="red">A timeout error occured</font>'
            else:
              # Wenn es geklappt hat...

              # Anzahl der Elemente in der Liste
              laenge_liste_load_balancers = len(liste_load_balancers)

              if laenge_liste_load_balancers == 0:
                if sprache == "de":
                  loadbalancertabelle = 'Es sind keine Load Balancer in der Region vorhanden.'
                else:
                  loadbalancertabelle = 'No load balancer exist inside this region.'
              else:
                loadbalancertabelle = ''
                loadbalancertabelle = loadbalancertabelle + '<table border="3" cellspacing="0" cellpadding="5">'
                loadbalancertabelle = loadbalancertabelle + '<tr>'
                loadbalancertabelle = loadbalancertabelle + '<th align="center">&nbsp;</th>'
                loadbalancertabelle = loadbalancertabelle + '<th align="center">Name</th>'
                loadbalancertabelle = loadbalancertabelle + '<th>&nbsp;</th>'
                if sprache == "de":
                  loadbalancertabelle = loadbalancertabelle + '<th align="center">Instanzen</th>'
                else:
                  loadbalancertabelle = loadbalancertabelle + '<th align="center">Instances</th>'
                loadbalancertabelle = loadbalancertabelle + '<th align="center">DNS Name</th>'
                loadbalancertabelle = loadbalancertabelle + '<th align="center">Ports</th>'
                if sprache == "de":
                  loadbalancertabelle = loadbalancertabelle + '<th align="center">Zonen</th>'
                else:
                  loadbalancertabelle = loadbalancertabelle + '<th align="center">Zones</th>'
                loadbalancertabelle = loadbalancertabelle + '<th align="center">Health Check</th>'
                if sprache == "de":
                  loadbalancertabelle = loadbalancertabelle + '<th align="center">Datum der Erzeugung</th>'
                else:
                  loadbalancertabelle = loadbalancertabelle + '<th align="center">Creation Date</th>'
                loadbalancertabelle = loadbalancertabelle + '</tr>'
                for i in range(laenge_liste_load_balancers):
                    loadbalancertabelle = loadbalancertabelle + '<tr>'
                    loadbalancertabelle = loadbalancertabelle + '<td>'
                    loadbalancertabelle = loadbalancertabelle + '<a href="/delete_load_balancer?name='
                    loadbalancertabelle = loadbalancertabelle + liste_load_balancers[i].name
                    if sprache == "de":
                      loadbalancertabelle = loadbalancertabelle + '" title="Load Balancer l&ouml;schen">'
                      loadbalancertabelle = loadbalancertabelle + '<img src="bilder/stop.png" width="16" height="16" border="0" alt="Load Balancer l&ouml;schen"></a>'
                    else:
                      loadbalancertabelle = loadbalancertabelle + '" title="delete load balancer">'
                      loadbalancertabelle = loadbalancertabelle + '<img src="bilder/stop.png" width="16" height="16" border="0" alt="delete load balancer"></a>'
                    loadbalancertabelle = loadbalancertabelle + '</td>'
                    loadbalancertabelle = loadbalancertabelle + '<td>'
                    loadbalancertabelle = loadbalancertabelle + '<tt>'
                    loadbalancertabelle = loadbalancertabelle + liste_load_balancers[i].name
                    loadbalancertabelle = loadbalancertabelle + '</tt>'
                    loadbalancertabelle = loadbalancertabelle + '</td>'
                    loadbalancertabelle = loadbalancertabelle + '<td>'
                    loadbalancertabelle = loadbalancertabelle + '<a href="/loadbalanceraendern?name='
                    loadbalancertabelle = loadbalancertabelle + liste_load_balancers[i].name
                    if sprache == "de":
                      loadbalancertabelle = loadbalancertabelle + '" title="Load Balancer einsehen/&auml;ndern"><img src="bilder/einstellungen.png" width="58" height="18" border="0" alt="Load Balancer einsehen/&auml;ndern"></a>'
                    else:
                      loadbalancertabelle = loadbalancertabelle + '" title="check/alter load balancer"><img src="bilder/einstellungen.png" width="58" height="18" border="0" alt="check/alter load balancer"></a>'
                    loadbalancertabelle = loadbalancertabelle + '</td>'
                    loadbalancertabelle = loadbalancertabelle + '<td align="center">'
                    loadbalancertabelle = loadbalancertabelle + '<tt>'
                    loadbalancertabelle = loadbalancertabelle + str(len(liste_load_balancers[i].instances))
                    loadbalancertabelle = loadbalancertabelle + '</tt>'
                    loadbalancertabelle = loadbalancertabelle + '</td>'
                    loadbalancertabelle = loadbalancertabelle + '<td>'
                    loadbalancertabelle = loadbalancertabelle + '<tt>'
                    loadbalancertabelle = loadbalancertabelle + liste_load_balancers[i].dns_name
                    loadbalancertabelle = loadbalancertabelle + '</tt>'
                    loadbalancertabelle = loadbalancertabelle + '</td>'
                    loadbalancertabelle = loadbalancertabelle + '<td>'
                    loadbalancertabelle = loadbalancertabelle + '<tt>'
                    for x in range(len(liste_load_balancers[i].listeners)):
                      loadbalancertabelle = loadbalancertabelle + str(liste_load_balancers[i].listeners[x])
                    loadbalancertabelle = loadbalancertabelle + '</tt>'
                    loadbalancertabelle = loadbalancertabelle + '</td>'
                    loadbalancertabelle = loadbalancertabelle + '<td>'
                    loadbalancertabelle = loadbalancertabelle + '<tt>'
                    for x in range(len(liste_load_balancers[i].availability_zones)):
                      loadbalancertabelle = loadbalancertabelle + str(liste_load_balancers[i].availability_zones[x])
                      loadbalancertabelle = loadbalancertabelle + '&nbsp;'
                    loadbalancertabelle = loadbalancertabelle + '</tt>'
                    loadbalancertabelle = loadbalancertabelle + '</td>'
                    loadbalancertabelle = loadbalancertabelle + '<td>'
                    loadbalancertabelle = loadbalancertabelle + '<tt>'
                    health_check_final = str(liste_load_balancers[i].health_check).replace( 'HealthCheck:', '' )
                    loadbalancertabelle = loadbalancertabelle + health_check_final
                    loadbalancertabelle = loadbalancertabelle + '</tt>'
                    loadbalancertabelle = loadbalancertabelle + '</td>'
                    loadbalancertabelle = loadbalancertabelle + '<td>'
                    loadbalancertabelle = loadbalancertabelle + '<tt>'
                    datum_der_erzeugung = parse(liste_load_balancers[i].created_time)
                    loadbalancertabelle = loadbalancertabelle + str(datum_der_erzeugung.strftime("%Y-%m-%d  %H:%M:%S"))
                    loadbalancertabelle = loadbalancertabelle + '</tt>'
                    loadbalancertabelle = loadbalancertabelle + '</td>'
                    loadbalancertabelle = loadbalancertabelle + '</tr>'
                loadbalancertabelle = loadbalancertabelle + '</table>'

            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'loadbalancertabelle': loadbalancertabelle,
            'zonen_liste': zonen_liste,
            'input_error_message': input_error_message,
            }

            #if sprache == "de": naechse_seite = "loadbalancer_de.html"
            #else:               naechse_seite = "loadbalancer_en.html"
            #path = os.path.join(os.path.dirname(__file__), naechse_seite)
            path = os.path.join(os.path.dirname(__file__), "templates", sprache, "loadbalancer.html")
            self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')

class LoadBalancer_Aendern(webapp.RequestHandler):
    def get(self):
        # Eventuell vorhande Fehlermeldung holen
        message = self.request.get('message')
        # Name des zu löschenden Load Balancers holen
        loadbalancer_name = self.request.get('name')
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')

        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if results:
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
          if message == '61' or message == '63' or message == '66' or message == '68':
            # wird sie hier, in der Hilfsfunktion grün formatiert
            input_error_message = format_error_message_green(input_error_message)
          # Ansonsten wird die Nachricht rot formatiert
          elif message == '8' or message == '62' or message == '64' or message == '65' or message == '67' or message == '69':
            input_error_message = format_error_message_red(input_error_message)
          else:
            input_error_message = ""

          try:
            # Liste mit den Instanzen
            # Man kann nicht direkt versuchen mit get_all_security_groups(gruppen_liste)
            # die anzulegende Gruppe zu erzeugen. Wenn die Gruppe noch nicht existiert,
            # gibt es eine Fehlermeldung
            liste_reservations = conn_region.get_all_instances()
          except EC2ResponseError:
            # Wenn es nicht klappt...
            fehlermeldung = "10"
            self.redirect('/loadbalancer?message='+fehlermeldung)
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            fehlermeldung = "9"
            self.redirect('/loadbalancer?message='+fehlermeldung)
          else:
            # Wenn es geklappt hat und die Liste geholt wurde...
            # Anzahl der Elemente in der Liste
            laenge_liste_reservations = len(liste_reservations)

            if laenge_liste_reservations == "0":
              # Wenn es keine laufenden Instanzen gibt
              instanzen_in_region = 0
            else:
              # Wenn es laufenden Instanzen gibt
              instanzen_in_region = 0
              for i in liste_reservations:
                for x in i.instances:
                  # Für jede Instanz wird geschaut...
                  # ...ob die Instanz in der Region des Volumes liegt und läuft
                  if x.state == u'running':
                    instanzen_in_region = instanzen_in_region + 1

            # Mit ELB verbinden
            conn_elb = loginselb(username)

            try:
              # Liste mit den LoadBalancern
              liste_load_balancers = conn_elb.get_all_load_balancers(load_balancer_name=str(loadbalancer_name))
            except EC2ResponseError:
              # Wenn es nicht klappt...
              fehlermeldung = "10"
              self.redirect('/loadbalancer?message='+fehlermeldung)
            except DownloadError:
              # Diese Exception hilft gegen diese beiden Fehler:
              # DownloadError: ApplicationError: 2 timed out
              # DownloadError: ApplicationError: 5
              fehlermeldung = "9"
              self.redirect('/loadbalancer?message='+fehlermeldung)
            else:
              # Wenn es geklappt hat...

              tabelle_instanz_anhaengen = ''
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<form action="/loadbalancer_instanz_zuordnen?loadbalancer='
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + loadbalancer_name
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '" method="post" accept-charset="utf-8">'
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '\n'
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<table border="3" cellspacing="0" cellpadding="5">\n'

              # Wenn dem Load Balancer noch keine Instanzen zugewiesen wurden...
              if len(liste_load_balancers[0].instances) == 0:
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<tr>\n'
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td colspan="2">\n'
                if sprache == "de":
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + 'Dem Load Balancer wurden noch keine Instanzen zugewiesen'
                else:
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + 'This load balancer is not asigned with any instances'
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</td>\n'
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</tr>\n'
              # Wenn dem Load Balancer schon Instanzen zugewiesen wurden...
              else:
                for z in range(len(liste_load_balancers[0].instances)):
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<tr>\n'
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td>\n'
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<a href="/loadbalancer_deregister_instance?loadbalancer='
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + loadbalancer_name
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '&amp;instanz='
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + liste_load_balancers[0].instances[z].id
                  if sprache == "de":
                    tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '" title="Instanz deregistrieren">'
                    tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<img src="bilder/stop.png" width="16" height="16" border="0" alt="Instanz deregistrieren"></a>'
                  else:
                    tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '" title="deregister instance">'
                    tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<img src="bilder/stop.png" width="16" height="16" border="0" alt="deregister instance"></a>'
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</td>\n'
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td colspan="2">\n'
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<tt>\n'
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + liste_load_balancers[0].instances[z].id
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</tt>\n'
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</td>\n'
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</tr>\n'
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<tr>\n'
              # Wenn mehr als eine Instanz dem Load Balancer zugewiesen ist, dann muss hier ein 
              # leeres Feld hin. Sonst sieht die Tabelle nicht gut aus!
              if len(liste_load_balancers[0].instances) != 0:
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td>&nbsp;</td>\n'

              if instanzen_in_region == 0:
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td align="center" colspan="2">\n'
                if sprache == "de":
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + 'Sie haben keine Instanzen'
                else:
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + 'You have no instances'
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</td>\n'
              else:
                if instanzen_in_region > 0:
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td align="center">\n'
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<select name="instanzen" size="1">\n'
                  for i in liste_reservations:
                    for x in i.instances:
                      if x.state == u'running':
                        tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<option>'
                        tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + x.id
                        tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</option>\n'
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</select>\n'
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</td>\n'
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td align="center">\n'
                if sprache == "de":
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<input type="submit" value="verkn&uuml;pfen">'
                else:
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<input type="submit" value="associate">'
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '\n'
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</td>\n'
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</tr>\n'
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</table>\n'
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</form>'


              try:
                # Liste mit den Zonen
                liste_zonen = conn_region.get_all_zones()
              except EC2ResponseError:
                # Wenn es nicht geklappt hat...
                if sprache == "de":
                  tabelle_zonen_aendern = '<font color="red">Es ist zu einem Fehler gekommen</font>'
                else:
                  tabelle_zonen_aendern = '<font color="red">An error occured</font>'
              except DownloadError:
                # Diese Exception hilft gegen diese beiden Fehler:
                # DownloadError: ApplicationError: 2 timed out
                # DownloadError: ApplicationError: 5
                if sprache == "de":
                  tabelle_zonen_aendern = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
                else:
                  tabelle_zonen_aendern = '<font color="red">A timeout error occured</font>'
              else:
                # Wenn es geklappt hat...
                # Anzahl der Elemente in der Liste
                laenge_liste_zonen = len(liste_zonen)

                tabelle_zonen_aendern = ''
                tabelle_zonen_aendern = tabelle_zonen_aendern + '<form action="/loadbalancer_zone_zuordnen?loadbalancer='
                tabelle_zonen_aendern = tabelle_zonen_aendern + loadbalancer_name
                tabelle_zonen_aendern = tabelle_zonen_aendern + '" method="post" accept-charset="utf-8">'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '<table border="3" cellspacing="0" cellpadding="5">\n'

                for z in range(len(liste_load_balancers[0].availability_zones)):
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '<tr>\n'
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '<td>\n'
                  # Wenn dem Load Balancer nur eine Zone zugewiesen ist...
                  if len(liste_load_balancers[0].availability_zones) == 1:
                    tabelle_zonen_aendern = tabelle_zonen_aendern + '<a href="/loadbalanceraendern?loadbalancer='
                    tabelle_zonen_aendern = tabelle_zonen_aendern + loadbalancer_name
                    tabelle_zonen_aendern = tabelle_zonen_aendern + '&amp;message=67'
                    if sprache == "de":
                      tabelle_zonen_aendern = tabelle_zonen_aendern + '" title="Zone deregistrieren">'
                      tabelle_zonen_aendern = tabelle_zonen_aendern + '<img src="bilder/stop.png" width="16" height="16" border="0" alt="Zone deregistrieren"></a>'
                    else:
                      tabelle_zonen_aendern = tabelle_zonen_aendern + '" title="deregister zone">'
                      tabelle_zonen_aendern = tabelle_zonen_aendern + '<img src="bilder/stop.png" width="16" height="16" border="0" alt="deregister zone"></a>'
                  # Wenn dem Load Balancer mehr als nur eine Zone zugewiesen ist...
                  else:
                    tabelle_zonen_aendern = tabelle_zonen_aendern + '<a href="/loadbalancer_deregister_zone?loadbalancer='
                    tabelle_zonen_aendern = tabelle_zonen_aendern + loadbalancer_name
                    tabelle_zonen_aendern = tabelle_zonen_aendern + '&amp;zone='
                    tabelle_zonen_aendern = tabelle_zonen_aendern + liste_load_balancers[0].availability_zones[z]
                    if sprache == "de":
                      tabelle_zonen_aendern = tabelle_zonen_aendern + '" title="Zone deregistrieren">'
                      tabelle_zonen_aendern = tabelle_zonen_aendern + '<img src="bilder/stop.png" width="16" height="16" border="0" alt="Zone deregistrieren"></a>'
                    else:
                      tabelle_zonen_aendern = tabelle_zonen_aendern + '" title="deregister zone">'
                      tabelle_zonen_aendern = tabelle_zonen_aendern + '<img src="bilder/stop.png" width="16" height="16" border="0" alt="deregister zone"></a>'
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '</td>\n'
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '<td colspan="2">\n'
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '<tt>\n'
                  tabelle_zonen_aendern = tabelle_zonen_aendern + liste_load_balancers[0].availability_zones[z]
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '</tt>\n'
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '</td>\n'
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '</tr>\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '<tr>\n'
                # Wenn mehr als eine Instanz dem Load Balancer zugewiesen ist, dann muss hier ein 
                # leeres Feld hin. Sonst sieht die Tabelle nicht gut aus!
                if len(liste_load_balancers[0].availability_zones) != 0:
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '<td>&nbsp;</td>\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '<td align="center">\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '<select name="zonen" size="1">\n'
                for i in range(laenge_liste_zonen):
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '<option>'
                  tabelle_zonen_aendern = tabelle_zonen_aendern + liste_zonen[i].name
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '</option>\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '</select>\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '</td>\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '<td align="center">\n'
                if sprache == "de":
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '<input type="submit" value="verkn&uuml;pfen">'
                else:
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '<input type="submit" value="associate">'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '</td>\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '</tr>\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '</table>\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '</form>'


              template_values = {
              'navigations_bar': navigations_bar,
              'url': url,
              'url_linktext': url_linktext,
              'zone': regionname,
              'zone_amazon': zone_amazon,
              'zonen_liste': zonen_liste,
              'load_balancer_name': loadbalancer_name,
              'tabelle_instanz_anhaengen': tabelle_instanz_anhaengen,
              'tabelle_zonen_aendern': tabelle_zonen_aendern,
              'input_error_message': input_error_message,
              }

              #if sprache == "de": naechse_seite = "loadbalancer_change_de.html"
              #else:               naechse_seite = "loadbalancer_change_en.html"
              #path = os.path.join(os.path.dirname(__file__), naechse_seite)
              path = os.path.join(os.path.dirname(__file__), "templates", sprache, "loadbalancer_change.html")
              self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')

class LoadBalancer_Instanz_Zuordnen(webapp.RequestHandler):
    def post(self):
        # self.response.out.write('posted!')
        # Zu verknüpfenden Load Balancer holen
        loadbalancer = self.request.get('loadbalancer')
        # Zu verknüpfende Instanz holen
        instanz = self.request.get('instanzen')
        # Den Usernamen erfahren
        username = users.get_current_user()

        # Mit ELB verbinden
        conn_elb = loginselb(username)

        # Eine leere Liste für das IDs der Instanzen erzeugen
        list_of_instances = []
        # Die Instanz in Liste einfügen
        list_of_instances.append(instanz)

        try:
          # Die Instanz verknüpfen
          conn_elb.register_instances(loadbalancer, list_of_instances)
        except EC2ResponseError:
          # Wenn es nicht geklappt hat...
          fehlermeldung = "62"
          self.redirect('/loadbalanceraendern?name='+loadbalancer+'&message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/loadbalanceraendern?name='+loadbalancer+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "61"
          self.redirect('/loadbalanceraendern?name='+loadbalancer+'&message='+fehlermeldung)


class LoadBalancer_Instanz_Entfernen(webapp.RequestHandler):
    def get(self):
        # self.response.out.write('posted!')
        # Betreffenden Load Balancer holen
        loadbalancer = self.request.get('loadbalancer')
        # Zu entfernende Instanz holen
        instanz = self.request.get('instanz')
        # Den Usernamen erfahren
        username = users.get_current_user()

        # Mit ELB verbinden
        conn_elb = loginselb(username)

        # Eine leere Liste für das IDs der Instanzen erzeugen
        list_of_instances = []
        # Die Instanz in Liste einfügen
        list_of_instances.append(instanz)

        try:
          # Die Instanz entfernen
          conn_elb.deregister_instances(loadbalancer, list_of_instances)
        except EC2ResponseError:
          # Wenn es nicht geklappt hat...
          fehlermeldung = "64"
          self.redirect('/loadbalanceraendern?name='+loadbalancer+'&message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/loadbalanceraendern?name='+loadbalancer+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "63"
          self.redirect('/loadbalanceraendern?name='+loadbalancer+'&message='+fehlermeldung)


class LoadBalancer_Zone_Entfernen(webapp.RequestHandler):
    def get(self):
        # self.response.out.write('posted!')
        # Betreffenden Load Balancer holen
        loadbalancer = self.request.get('loadbalancer')
        # Zu entfernende Zone holen
        zone = self.request.get('zone')
        # Den Usernamen erfahren
        username = users.get_current_user()

        # Mit ELB verbinden
        conn_elb = loginselb(username)

        # Eine leere Liste für die Zonen erzeugen
        list_of_zones = []
        # Die Zone in Liste einfügen
        list_of_zones.append(zone)

        try:
          # Die Instanz entfernen
          conn_elb.disable_availability_zones(loadbalancer, list_of_zones)
        except EC2ResponseError:
          # Wenn es nicht geklappt hat...
          fehlermeldung = "65"
          self.redirect('/loadbalanceraendern?name='+loadbalancer+'&message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/loadbalanceraendern?name='+loadbalancer+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "66"
          self.redirect('/loadbalanceraendern?name='+loadbalancer+'&message='+fehlermeldung)

class LoadBalancer_Zone_Zuordnen(webapp.RequestHandler):
    def post(self):
        # self.response.out.write('posted!')
        # Zu verknüpfenden Load Balancer holen
        loadbalancer = self.request.get('loadbalancer')
        # Zu verknüpfende Zone holen
        zone = self.request.get('zonen')
        # Den Usernamen erfahren
        username = users.get_current_user()

        # Mit ELB verbinden
        conn_elb = loginselb(username)

        # Eine leere Liste für die Zonen erzeugen
        list_of_zones = []
        # Die Zone in Liste einfügen
        list_of_zones.append(zone)

        try:
          # Die Instanz verknüpfen
          conn_elb.enable_availability_zones(loadbalancer, list_of_zones)
        except EC2ResponseError:
          # Wenn es nicht geklappt hat...
          fehlermeldung = "69"
          self.redirect('/loadbalanceraendern?name='+loadbalancer+'&message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/loadbalanceraendern?name='+loadbalancer+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "68"
          self.redirect('/loadbalanceraendern?name='+loadbalancer+'&message='+fehlermeldung)

class Elastic_IPs(webapp.RequestHandler):
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

          # So ist der HTML-Code korrekt
          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          # So ist der HTML-Code nicht korrekt
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
          if message == '0' or message == '3' or message == '5' or message == '7':
            # wird sie hier, in der Hilfsfunktion grün formatiert
            input_error_message = format_error_message_green(input_error_message)
          # Ansonsten wird die Nachricht rot formatiert
          elif message == '1' or message == '2' or message == '4' or message == '6' or message == '8' or message == '9' or message == '10':
            input_error_message = format_error_message_red(input_error_message)
          else:
            input_error_message = ""

          try:
            # Liste mit den Adressen
            liste_adressen = conn_region.get_all_addresses()
          except EC2ResponseError:
            # Wenn es nicht klappt...
            if sprache == "de":
              adressentabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
            else:
              adressentabelle = '<font color="red">An error occured</font>'
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            if sprache == "de":
              adressentabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
            else:
              adressentabelle = '<font color="red">A timeout error occured</font>'
          else:
            # Wenn es geklappt hat...
            # Anzahl der Elemente in der Liste
            laenge_liste_adressen = len(liste_adressen)

            if laenge_liste_adressen == 0:
              if sprache == "de":
                adressentabelle = 'Es sind keine elastischen IPs in der Region vorhanden.'
              else:
                adressentabelle = 'No elastic IPs exist inside this region.'
            else:
              adressentabelle = ''
              adressentabelle = adressentabelle + '<table border="3" cellspacing="0" cellpadding="5">'
              adressentabelle = adressentabelle + '<tr>'
              adressentabelle = adressentabelle + '<th align="center">&nbsp;</th>'
              if sprache == "de":
                adressentabelle = adressentabelle + '<th align="center">Adresse</th>'
              else:
                adressentabelle = adressentabelle + '<th align="center">Address</th>'
              if sprache == "de":
                adressentabelle = adressentabelle + '<th align="center">Instanz ID</th>'
              else:
                adressentabelle = adressentabelle + '<th align="center">Instance ID</th>'
              adressentabelle = adressentabelle + '<th align="center">&nbsp;</th>'
              adressentabelle = adressentabelle + '</tr>'
              for i in range(laenge_liste_adressen):
                  adressentabelle = adressentabelle + '<tr>'
                  adressentabelle = adressentabelle + '<td>'
                  adressentabelle = adressentabelle + '<a href="/release_address?address='
                  adressentabelle = adressentabelle + liste_adressen[i].public_ip
                  if sprache == "de":
                    adressentabelle = adressentabelle + '" title="Elastische IP freigeben">'
                    adressentabelle = adressentabelle + '<img src="bilder/stop.png" width="16" height="16" border="0" alt="Elastische IP freigeben"></a>'
                  else:
                    adressentabelle = adressentabelle + '" title="release elastic IP">'
                    adressentabelle = adressentabelle + '<img src="bilder/stop.png" width="16" height="16" border="0" alt="release elastic IP"></a>'
                  adressentabelle = adressentabelle + '</td>'
                  adressentabelle = adressentabelle + '<td>'
                  adressentabelle = adressentabelle + liste_adressen[i].public_ip
                  adressentabelle = adressentabelle + '</td>'
                  adressentabelle = adressentabelle + '<td>'
                  adressentabelle = adressentabelle + '<tt>'
                  if liste_adressen[i].instance_id:
                    adressentabelle = adressentabelle + liste_adressen[i].instance_id
                  else:
                    adressentabelle = adressentabelle + '&nbsp;'
                  adressentabelle = adressentabelle + '</tt>'
                  adressentabelle = adressentabelle + '</td>'
                  adressentabelle = adressentabelle + '<td>'
                  if liste_adressen[i].instance_id == "" or liste_adressen[i].instance_id == "nobody":
                    adressentabelle = adressentabelle + '<a href="/associate_address?address='
                    adressentabelle = adressentabelle + liste_adressen[i].public_ip
                    if sprache == "de":
                      adressentabelle = adressentabelle + '" title="Elastische IP mit Instanz verkn&uuml;pfen">'
                      adressentabelle = adressentabelle + '<img src="bilder/attach.png" width="52" height="18" border="0" alt="Elastische IP mit Instanz verkn&uuml;pfen"></a>'
                    else:
                      adressentabelle = adressentabelle + '" title="associate elastic IP with instance">'
                      adressentabelle = adressentabelle + '<img src="bilder/attach.png" width="52" height="18" border="0" alt="associate elastic IP with instance"></a>'
                  else:
                    adressentabelle = adressentabelle + '<a href="/disassociate_address?address='
                    adressentabelle = adressentabelle + liste_adressen[i].public_ip
                    if sprache == "de":
                      adressentabelle = adressentabelle + '" title="Elastische IP von der Instanz l&ouml;sen">'
                      adressentabelle = adressentabelle + '<img src="bilder/detach.png" width="52" height="18" border="0" alt="Elastische IP mit Instanz verkn&uuml;pfen"></a>'
                    else:
                      adressentabelle = adressentabelle + '" title="disassociate elastic IP from instance">'
                      adressentabelle = adressentabelle + '<img src="bilder/detach.png" width="52" height="18" border="0" alt="associate elastic IP with instance"></a>'
                  adressentabelle = adressentabelle + '</td>'
                  adressentabelle = adressentabelle + '</tr>'
              adressentabelle = adressentabelle + '</table>'

          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'adressentabelle': adressentabelle,
          'zonen_liste': zonen_liste,
          'input_error_message': input_error_message,
          }

          #if sprache == "de": naechse_seite = "adressen_de.html"
          #else:               naechse_seite = "adressen_en.html"
          #path = os.path.join(os.path.dirname(__file__), naechse_seite)
          path = os.path.join(os.path.dirname(__file__), "templates", sprache, "adressen.html")
          self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')

class Associate_IP(webapp.RequestHandler):
    def get(self):
        #self.response.out.write('posted!')
        # Anzuhängende Elastic IP-Adresse holen
        address = self.request.get('address')
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')

        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if results:
          # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache)

          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          #url = users.create_logout_url(self.request.uri)
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache)

          try:
            # Liste mit den Instanzen
            # Man kann nicht direkt versuchen mit get_all_security_groups(gruppen_liste)
            # die anzulegende Gruppe zu erzeugen. Wenn die Gruppe noch nicht existiert,
            # gibt es eine Fehlermeldung
            liste_reservations = conn_region.get_all_instances()
          except EC2ResponseError:
            # Wenn es nicht klappt...
            fehlermeldung = "10"
            self.redirect('/elastic_ips?message='+fehlermeldung)
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            fehlermeldung = "9"
            self.redirect('/elastic_ips?message='+fehlermeldung)
          else:
            # Wenn es geklappt hat und die Liste geholt wurde...
            # Anzahl der Elemente in der Liste
            laenge_liste_reservations = len(liste_reservations)

            if laenge_liste_reservations == "0":
              # Wenn es keine laufenden Instanzen gibt
              instanzen_in_region = 0
            else:
              # Wenn es laufenden Instanzen gibt
              instanzen_in_region = 0
              for i in liste_reservations:
                for x in i.instances:
                  # Für jede Instanz wird geschaut...
                  # ...ob die Instanz in der Region des Volumes liegt und läuft
                  if x.state == u'running':
                    instanzen_in_region = instanzen_in_region + 1

            tabelle_instanz_anhaengen = ''
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<form action="/ip_definitiv_anhaengen?address='
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + address
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '" method="post" accept-charset="utf-8">'
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '\n'
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<table border="3" cellspacing="0" cellpadding="5">'
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<tr>'
            if sprache == "de":
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td align="right"><B>Elastische IP-Adresse:</B></td>'
            else:
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td align="right"><B>Elastic IP Address:</B></td>'
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td>'
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + address
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</td>'
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</tr>'
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<tr>'
            if sprache == "de":
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td align="right"><B>Instanzen:</B></td>'
            else:
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td align="right"><B>Instances:</B></td>'
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td>'
            if instanzen_in_region == 0:
              if sprache == "de":
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + 'Sie haben keine Instanz'
              else:
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + 'You have still no instance'
            else:
              if instanzen_in_region > 0:
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<select name="instanzen" size="1">'
                for i in liste_reservations:
                  for x in i.instances:
                    if x.state == u'running':
                      tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<option>'
                      tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + x.id
                      tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</option>'
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</select>'
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</td>'
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</tr>'
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</table>'
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<p>&nbsp;</p>'
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '\n'
            if sprache == "de":
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<input type="submit" value="verkn&uuml;pfen">'
            else:
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<input type="submit" value="associate">'
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '\n'
            tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</form>'

            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'zonen_liste': zonen_liste,
            'tabelle_instanz_anhaengen': tabelle_instanz_anhaengen,
            }

            #if sprache == "de": naechse_seite = "ip_anhaengen_de.html"
            #else:               naechse_seite = "ip_anhaengen_en.html"
            #path = os.path.join(os.path.dirname(__file__), naechse_seite)
            path = os.path.join(os.path.dirname(__file__), "templates", sprache, "ip_anhaengen.html")
            self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')


class IP_Definitiv_Anhaengen(webapp.RequestHandler):
    def post(self):
        # self.response.out.write('posted!')
        # Zu verknüpfende Elastic IP-Adresse holen
        address = self.request.get('address')
        # Zu verknüpfende Instanz holen
        instanzen = self.request.get('instanzen')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Die Elastic IP-Adresse verknüpfen
          conn_region.associate_address(instanzen, address)
        except EC2ResponseError:
          # Wenn es nicht geklappt hat...
          fehlermeldung = "1"
          self.redirect('/elastic_ips?message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/elastic_ips?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "0"
          self.redirect('/elastic_ips?message='+fehlermeldung)


class Release_IP(webapp.RequestHandler):
    def get(self):
      # Zu löschende (release) Elastic IP-Adresse holen
      address = self.request.get('address')
      # Den Usernamen erfahren
      username = users.get_current_user()

      conn_region, regionname = login(username)

      try:
        # Die Elastic IP-Adresse freigeben (löschen)
        conn_region.release_address(address)
      except EC2ResponseError:
        # Wenn es nicht geklappt hat...
        fehlermeldung = "4"
        self.redirect('/elastic_ips?message='+fehlermeldung)
      except DownloadError:
        # Diese Exception hilft gegen diese beiden Fehler:
        # DownloadError: ApplicationError: 2 timed out
        # DownloadError: ApplicationError: 5
        fehlermeldung = "8"
        self.redirect('/elastic_ips?message='+fehlermeldung)
      else:
        # Wenn es geklappt hat...
        fehlermeldung = "5"
        self.redirect('/elastic_ips?message='+fehlermeldung)


class Disassociate_IP(webapp.RequestHandler):
    def get(self):
        # Zu enfelchtende (disassociate) Elastic IP-Adresse holen
        address = self.request.get('address')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Die Elastic IP-Adresse freigeben (löschen)
          conn_region.disassociate_address(address)
        except EC2ResponseError:
          # Wenn es nicht geklappt hat...
          fehlermeldung = "2"
          self.redirect('/elastic_ips?message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/elastic_ips?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "3"
          self.redirect('/elastic_ips?message='+fehlermeldung)


class Allocate_IP(webapp.RequestHandler):
    def post(self):
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Eine Elastic IP-Adresse bekommen
          conn_region.allocate_address()
        except EC2ResponseError:
          # Wenn es nicht geklappt hat...
          fehlermeldung = "6"
          self.redirect('/elastic_ips?message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/elastic_ips?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "7"
          self.redirect('/elastic_ips?message='+fehlermeldung)


class Zonen(webapp.RequestHandler):
    def get(self):
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')

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

          try:
            # Liste mit den Zonen
            liste_zonen = conn_region.get_all_zones()
          except EC2ResponseError:
            # Wenn es nicht klappt...
            if sprache == "de":
              zonentabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
            else:
              zonentabelle = '<font color="red">An error occured</font>'
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            if sprache == "de":
              zonentabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
            else:
              zonentabelle = '<font color="red">A timeout error occured</font>'
          else:
            # Wenn es geklappt hat...
            # Anzahl der Elemente in der Liste
            laenge_liste_zonen = len(liste_zonen)

            zonentabelle = ''
            zonentabelle = zonentabelle + '<table border="3" cellspacing="0" cellpadding="5">'
            zonentabelle = zonentabelle + '<tr>'
            zonentabelle = zonentabelle + '<th align="center">Name</th>'
            zonentabelle = zonentabelle + '<th align="center">Status</th>'
            zonentabelle = zonentabelle + '</tr>'
            for i in range(laenge_liste_zonen):
                zonentabelle = zonentabelle + '<tr>'
                zonentabelle = zonentabelle + '<td>'+liste_zonen[i].name+'</td>'
                if liste_zonen[i].state == u'available':
                  zonentabelle = zonentabelle + '<td bgcolor="#c3ddc3" align="center">'
                  if sprache == "de":
                    zonentabelle = zonentabelle + 'verf&uuml;gbar'
                  else:
                    zonentabelle = zonentabelle + liste_zonen[i].state
                else:
                  zonentabelle = zonentabelle + '<td align="center">'
                  zonentabelle = zonentabelle + liste_zonen[i].state
                zonentabelle = zonentabelle + '</td>'
                zonentabelle = zonentabelle + '</tr>'
            zonentabelle = zonentabelle + '</table>'

          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'zonenliste': zonentabelle,
          'zonen_liste': zonen_liste,
          }

          #if sprache == "de": naechse_seite = "zonen_de.html"
          #else:               naechse_seite = "zonen_en.html"
          #path = os.path.join(os.path.dirname(__file__), naechse_seite)
          path = os.path.join(os.path.dirname(__file__), "templates", sprache, "zonen.html")
          self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')


class InstanzReboot(webapp.RequestHandler):
    def get(self):
        # Die ID der neuzustartenden Instanz holen
        id = self.request.get('id')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        # Es muss eine Liste mit den IDs übergeben werden
        instance_ids = [id]

        try:
          # Instanz beenden
          conn_region.reboot_instances(instance_ids)
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "7"
          self.redirect('/instanzen?message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "10"
          self.redirect('/instanzen?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "6"
          self.redirect('/instanzen?message='+fehlermeldung)


class InstanzBeenden(webapp.RequestHandler):
    def get(self):
        # Die ID der zu löschenden Instanz holen
        id = self.request.get('id')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Liste der Instanzen holen
          instances = conn_region.get_all_instances()
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "9"
          self.redirect('/instanzen?message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "11"
          self.redirect('/instanzen?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...

          # Mit dieser Variable wird überprüft, ob die Instanz gleich gefunden wird
          # Wenn die Instanz nicht gefunden wird, braucht auch nichts beendet zu werden
          gefunden = 0
          for reserv in instances:
              for inst in reserv.instances:
                  # Vergleichen
                  if str(inst.id) == id:
                      # Die Instanz wurde gefunden!
                      gefunden = 1

                      # Wenn die Instanz schon im Zustand "terminated" ist,
                      # kann man sie nicht mehr beenden
                      if inst.state == u'terminated':
                        fehlermeldung = "3"
                        self.redirect('/instanzen?message='+fehlermeldung)
                      else:
                        try:
                          # Instanz beenden
                          inst.stop()
                        except EC2ResponseError:
                          # Wenn es nicht klappt...
                          fehlermeldung = "1"
                          self.redirect('/instanzen?message='+fehlermeldung)
                        except DownloadError:
                          # Diese Exception hilft gegen diese beiden Fehler:
                          # DownloadError: ApplicationError: 2 timed out
                          # DownloadError: ApplicationError: 5
                          fehlermeldung = "10"
                          self.redirect('/instanzen?message='+fehlermeldung)
                        else:
                          # Wenn es geklappt hat...
                          fehlermeldung = "0"
                          self.redirect('/instanzen?message='+fehlermeldung)

          # Wenn die Instanz nicht gefunden werden konnte
          if gefunden == 0:
            fehlermeldung = "2"
            self.redirect('/instanzen?message='+fehlermeldung)



class AlleInstanzenBeenden(webapp.RequestHandler):
    def get(self):
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Liste der Instanzen holen
          instances = conn_region.get_all_instances()
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "9"
          self.redirect('/instanzen?message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "10"
          self.redirect('/instanzen?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          for reserv in instances:
            for inst in reserv.instances:
              # Wenn die Instanz schon im Zustand "terminated" ist, dann kann man sie nicht mehr beenden
              if inst.state != u'terminated':

                try:
                  # Instanz beenden
                  inst.stop()
                except EC2ResponseError:
                  # Wenn es nicht klappt...
                  fehlermeldung = "1"
                  self.redirect('/instanzen?message='+fehlermeldung)
                except DownloadError:
                  # Diese Exception hilft gegen diese beiden Fehler:
                  # DownloadError: ApplicationError: 2 timed out
                  # DownloadError: ApplicationError: 5
                  fehlermeldung = "10"
                  self.redirect('/instanzen?message='+fehlermeldung)

          fehlermeldung = "8"
          self.redirect('/instanzen?message='+fehlermeldung)


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
          fehlermeldung = "1"
          self.redirect('/schluessel?message='+fehlermeldung)
        elif re.search(r'[^\-_a-zA-Z0-9]', neuerkeyname) != None:
          # Testen ob der Name für den neuen key nicht erlaubte Zeichen enthält
          fehlermeldung = "2"
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
              fehlermeldung = "4"
              self.redirect('/schluessel?message='+fehlermeldung)

          # Wenn der Schlüssel noch nicht existiert...
          if schon_vorhanden == 0:
            try:
              # Schlüsselpaar erzeugen
              neuer_key = conn_region.create_key_pair(neuerkeyname)
            except EC2ResponseError:
              fehlermeldung = "3"
              self.redirect('/schluessel?message='+fehlermeldung)
            except DownloadError:
              # Diese Exception hilft gegen diese beiden Fehler:
              # DownloadError: ApplicationError: 2 timed out
              # DownloadError: ApplicationError: 5
              fehlermeldung = "7"
              self.redirect('/schluessel?message='+fehlermeldung)
            else:
              neu = "ja"
              secretkey = neuer_key.material
              aktuelle_zeit = time.time()
              keyname = str(neuerkeyname)
              keyname = keyname + "_"
              keyname = keyname + regionname
              keyname = keyname + "_"
              keyname = keyname + str(aktuelle_zeit)
              # der Secret Key wird für 10 Minuten im Memcache gespeichert
              memcache.add(key=keyname, value=secretkey, time=600)
              fehlermeldung = "0"
              self.redirect('/schluessel?message='+fehlermeldung+'&neu='+neu+'&neuerkeyname='+neuerkeyname+'&secretkey='+keyname)


class KeyEntfernen(webapp.RequestHandler):
    def get(self):
        # Die ID der zu löschenden Instanz holen
        key = self.request.get('key')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Schlüsselpaar löschen
          conn_region.delete_key_pair(key)
        except EC2ResponseError:
          # Wenn es nicht geklappt hat...
          fehlermeldung = "6"
          self.redirect('/schluessel?message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "7"
          self.redirect('/schluessel?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "5"
          self.redirect('/schluessel?message='+fehlermeldung)


class SnapshotsEntfernen(webapp.RequestHandler):
    def get(self):
        # Name des zu löschenden Snapshots holen
        snapshot = self.request.get('snapshot')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Snapshot löschen
          conn_region.delete_snapshot(snapshot)
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "12"
          self.redirect('/snapshots?message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/snapshots?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "11"
          self.redirect('/snapshots?message='+fehlermeldung)


class SnapshotsErzeugenDefinitiv(webapp.RequestHandler):
    def post(self):
        # Name Volume holen, von dem ein Snapshot erzeugt werden soll
        volume = self.request.get('volume')
        # Die Beschreibung des Snapshots holen
        beschreibung = self.request.get('beschreibung')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        # Wenn die Variable "beschreibung" nicht gesetzt wurde,
        # dann wird sie als leere Variable erzeugt
        if not beschreibung: beschreibung = ''

        try:
          # Snapshot erzeugen
          conn_region.create_snapshot(volume, description=beschreibung)
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "14"
          self.redirect('/snapshots?message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/snapshots?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "13"
          self.redirect('/snapshots?message='+fehlermeldung)


class SnapshotsErzeugen(webapp.RequestHandler):
    def get(self):
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

        if results:
          # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache)

          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache)

          tabelle_snapshot = ''
          tabelle_snapshot = tabelle_snapshot + '<form action="/snapshoterzeugendefinitiv" method="post" accept-charset="utf-8"> \n'
          tabelle_snapshot = tabelle_snapshot + '<input type="hidden" name="volume" value="'+volume+'"> \n'
          tabelle_snapshot = tabelle_snapshot + '<table border="3" cellspacing="0" cellpadding="5">'
          tabelle_snapshot = tabelle_snapshot + '<tr>'
          tabelle_snapshot = tabelle_snapshot + '<td align="right"><B>Volume:</B></td>'
          tabelle_snapshot = tabelle_snapshot + '<td>'+volume+'</td>'
          tabelle_snapshot = tabelle_snapshot + '</tr>'
          tabelle_snapshot = tabelle_snapshot + '<tr>'
          if sprache == "de":
            tabelle_snapshot = tabelle_snapshot + '<td align="right"><B>Beschreibung:</B></td>'
          else:
            tabelle_snapshot = tabelle_snapshot + '<td align="right"><B>Description:</B></td>'
          tabelle_snapshot = tabelle_snapshot + '<td>'
          tabelle_snapshot = tabelle_snapshot + '<input name="beschreibung" type="text" size="80" maxlength="80"> \n'
          tabelle_snapshot = tabelle_snapshot + '</td>'
          tabelle_snapshot = tabelle_snapshot + '</tr>'
          tabelle_snapshot = tabelle_snapshot + '</table>'
          tabelle_snapshot = tabelle_snapshot + '<p>&nbsp;</p> \n'
          if sprache == "de":
            tabelle_snapshot = tabelle_snapshot + '<input type="submit" value="Snapshot erzeugen"> \n'
          else:
            tabelle_snapshot = tabelle_snapshot + '<input type="submit" value="create snapshot"> \n'
          tabelle_snapshot = tabelle_snapshot + '</form>'


          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'zonen_liste': zonen_liste,
          'tabelle_snapshot': tabelle_snapshot,
          }

          #if sprache == "de": naechse_seite = "snapshot_erzeugen_de.html"
          #else:               naechse_seite = "snapshot_erzeugen_en.html"
          #path = os.path.join(os.path.dirname(__file__), naechse_seite)
          path = os.path.join(os.path.dirname(__file__), "templates", sprache, "snapshot_erzeugen.html")
          self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')


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
          if message == '11' or message == '13':
            # wird sie hier, in der Hilfsfunktion grün formatiert
            input_error_message = format_error_message_green(input_error_message)
          # Ansonsten wird die Nachricht rot formatiert
          elif message == '8' or message == '12' or message == '14':
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
          path = os.path.join(os.path.dirname(__file__), "templates", sprache, "snapshots.html")
          self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')


class AlleVolumesLoeschenFrage(webapp.RequestHandler):
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

          #if sprache == "de": naechse_seite = "alle_volumes_loeschen_frage_de.html"
          #else:               naechse_seite = "alle_volumes_loeschen_frage_en.html"
          #path = os.path.join(os.path.dirname(__file__), naechse_seite)
          path = os.path.join(os.path.dirname(__file__), "templates", sprache, "alle_volumes_loeschen_frage.html")
          self.response.out.write(template.render(path,template_values))


class AlleVolumesLoeschenDefinitiv(webapp.RequestHandler):
    def get(self):
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Liste mit den Volumes
          liste_volumes = conn_region.get_all_volumes()
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "10"
          self.redirect('/volumes?message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/volumes?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          # Anzahl der Volumes in der Liste
          laenge_liste_volumes = len(liste_volumes)
          for i in range(laenge_liste_volumes):
                try:
                  # Volume entfernen
                  conn_region.delete_volume(liste_volumes[i].id)
                except EC2ResponseError:
                  # Wenn es nicht klappt...
                  fehlermeldung = "26"
                  self.redirect('/volumes?message='+fehlermeldung)
                except DownloadError:
                  # Diese Exception hilft gegen diese beiden Fehler:
                  # DownloadError: ApplicationError: 2 timed out
                  # DownloadError: ApplicationError: 5
                  fehlermeldung = "8"
                  self.redirect('/volumes?message='+fehlermeldung)

          fehlermeldung = "27"
          self.redirect('/volumes?message='+fehlermeldung)


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

        if results:
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
          if message == '15' or message == '22' or message == '23' or message == '24' or message == '27':
            # wird sie hier, in der Hilfsfunktion grün formatiert
            input_error_message = format_error_message_green(input_error_message)
          # Ansonsten wird die Nachricht rot formatiert
          elif message == '8' or message == '10' or message == '16' or message == '17' or message == '18' or message == '19' or message == '20' or message == '21' or message == '25' or message == '26':
            input_error_message = format_error_message_red(input_error_message)
          else:
            input_error_message = ""

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
                  volumestabelle = volumestabelle + '<tt>'
                  volumestabelle = volumestabelle + str(liste_volumes[i].id)
                  volumestabelle = volumestabelle + '</tt>'
                  volumestabelle = volumestabelle + '</td>'
                  volumestabelle = volumestabelle + '<td>'
                  volumestabelle = volumestabelle + '<tt>'
                  volumestabelle = volumestabelle + str(liste_volumes[i].snapshot_id)
                  volumestabelle = volumestabelle + '</tt>'
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
                    volumestabelle = volumestabelle + '<tt>'
                    volumestabelle = volumestabelle + str(liste_volumes[i].attach_data.device)
                    volumestabelle = volumestabelle + '</tt>'
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
          path = os.path.join(os.path.dirname(__file__), "templates", sprache, "volumes.html")
          self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')


class VolumesEntfernen(webapp.RequestHandler):
    def get(self):
        # Name des zu löschenden Volumes holen
        volume = self.request.get('volume')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Volume löschen
          conn_region.delete_volume(volume)
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "19"
          self.redirect('/volumes?message='+fehlermeldung) 
        except DownloadError:
          # Wenn es nicht klappt...
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/volumes?message='+fehlermeldung) 
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "22"
          self.redirect('/volumes?message='+fehlermeldung) 


class VolumeDefinitivAnhaengen(webapp.RequestHandler):
    def post(self):
        # Name des anzuhängenden Volumes holen
        volume = self.request.get('volume')
        # Instanz-ID holen
        instance_id = self.request.get('instanzen')
        # Device holen
        device = self.request.get('device')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Volume anhaengen
          neues_volume = conn_region.attach_volume(volume, instance_id, device)
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "21"
          self.redirect('/volumes?message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/volumes?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "23"
          self.redirect('/volumes?message='+fehlermeldung)


class VolumesAnhaengen(webapp.RequestHandler):
    def get(self):
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

        if results:
          # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache)

          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache)

          liste_reservations = conn_region.get_all_instances()
          # Anzahl der Elemente in der Liste
          laenge_liste_reservations = len(liste_reservations)

          if laenge_liste_reservations == "0":
            # Wenn es keine laufenden Instanzen gibt
            instanzen_in_region = 0
          else:
            # Wenn es laufenden Instanzen gibt
            instanzen_in_region = 0
            for i in liste_reservations:
              for x in i.instances:
                # Für jede Instanz wird geschaut...
                # ...ob die Instanz in der Region des Volumes liegt und läuft
                if x.placement == volume_zone and x.state == u'running':
                  instanzen_in_region = instanzen_in_region + 1

          tabelle_anhaengen = ''
          tabelle_anhaengen = tabelle_anhaengen + '<form action="/volumedefinitivanhaengen?volume='
          tabelle_anhaengen = tabelle_anhaengen + volume
          tabelle_anhaengen = tabelle_anhaengen + '" method="post" accept-charset="utf-8">'
          tabelle_anhaengen = tabelle_anhaengen + '\n'
          tabelle_anhaengen = tabelle_anhaengen + '<table border="3" cellspacing="0" cellpadding="5">'
          tabelle_anhaengen = tabelle_anhaengen + '<tr>'
          tabelle_anhaengen = tabelle_anhaengen + '<td align="right"><B>Volume:</B></td>'
          tabelle_anhaengen = tabelle_anhaengen + '<td>'
          tabelle_anhaengen = tabelle_anhaengen + volume
          tabelle_anhaengen = tabelle_anhaengen + '</td>'
          tabelle_anhaengen = tabelle_anhaengen + '<td>'
          if sprache == "de":
            tabelle_anhaengen = tabelle_anhaengen + 'in der Region <B>'
          else:
            tabelle_anhaengen = tabelle_anhaengen + 'in the region <B>'
          tabelle_anhaengen = tabelle_anhaengen + volume_zone
          tabelle_anhaengen = tabelle_anhaengen + '</B>'
          tabelle_anhaengen = tabelle_anhaengen + '</td>'
          tabelle_anhaengen = tabelle_anhaengen + '</tr>'
          tabelle_anhaengen = tabelle_anhaengen + '<tr>'
          if sprache == "de":
            tabelle_anhaengen = tabelle_anhaengen + '<td align="right"><B>Instanzen:</B></td>'
          else:
            tabelle_anhaengen = tabelle_anhaengen + '<td align="right"><B>Instances:</B></td>'
          tabelle_anhaengen = tabelle_anhaengen + '<td>'
          if instanzen_in_region == 0:
            if sprache == "de":
              tabelle_anhaengen = tabelle_anhaengen + 'Sie haben keine Instanz'
            else:
              tabelle_anhaengen = tabelle_anhaengen + 'You have still no instance'
          else:
            if instanzen_in_region > 0:
              tabelle_anhaengen = tabelle_anhaengen + '<select name="instanzen" size="1">'
              for i in liste_reservations:
                for x in i.instances:
                  if x.placement == volume_zone and x.state == u'running':
                    tabelle_anhaengen = tabelle_anhaengen + '<option>'
                    tabelle_anhaengen = tabelle_anhaengen + x.id
                    tabelle_anhaengen = tabelle_anhaengen + '</option>'
              tabelle_anhaengen = tabelle_anhaengen + '</select>'
          tabelle_anhaengen = tabelle_anhaengen + '</td>'
          tabelle_anhaengen = tabelle_anhaengen + '<td>'
          if sprache == "de":
            tabelle_anhaengen = tabelle_anhaengen + 'in der Region <B>'
          else:
            tabelle_anhaengen = tabelle_anhaengen + 'in the region <B>'
          tabelle_anhaengen = tabelle_anhaengen + volume_zone
          tabelle_anhaengen = tabelle_anhaengen + '</B>'
          tabelle_anhaengen = tabelle_anhaengen + '</td>'
          tabelle_anhaengen = tabelle_anhaengen + '</tr>'
          tabelle_anhaengen = tabelle_anhaengen + '<tr>'
          tabelle_anhaengen = tabelle_anhaengen + '<td align="right"><B>Device:</B></td>'
          tabelle_anhaengen = tabelle_anhaengen + '<td>'
          tabelle_anhaengen = tabelle_anhaengen + '<select name="device" size="1">'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sda</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdb</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option selected="selected">/dev/sdc</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdd</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sde</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdf</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdg</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdh</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdu</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdj</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdk</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdl</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdm</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdn</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdo</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdp</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdq</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdr</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sds</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdt</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdu</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdv</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdw</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdx</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdy</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdz</option>'
          tabelle_anhaengen = tabelle_anhaengen + '</select>'
          tabelle_anhaengen = tabelle_anhaengen + '</td>'
          tabelle_anhaengen = tabelle_anhaengen + '<td>'
          tabelle_anhaengen = tabelle_anhaengen + '&nbsp;'
          tabelle_anhaengen = tabelle_anhaengen + '</td>'
          tabelle_anhaengen = tabelle_anhaengen + '</tr>'
          tabelle_anhaengen = tabelle_anhaengen + '</table>'
          tabelle_anhaengen = tabelle_anhaengen + '<p>&nbsp;</p>'
          tabelle_anhaengen = tabelle_anhaengen + '\n'
          if instanzen_in_region == 0:
            tabelle_anhaengen = tabelle_anhaengen + ' '
          else:
            if sprache == "de":
              tabelle_anhaengen = tabelle_anhaengen + '<input type="submit" value="Volume anh&auml;ngen">'
            else:
              tabelle_anhaengen = tabelle_anhaengen + '<input type="submit" value="attach volume">'
          tabelle_anhaengen = tabelle_anhaengen + '\n'
          tabelle_anhaengen = tabelle_anhaengen + '</form>'

          if regionname != "Amazon":   # Wenn die Region nicht Amazon EC2, sondern Eucalyptus ist...
            if sprache == "de":        # ... und die Sprache deutsch ist ...
              ebs_volumes_eucalyptus_warnung = '<font color="red">Achtung! Das Verbinden von Volumes mit Instanzen dauert unter Eucalyptus teilweise mehrere Minuten.</font>'
            else:                      # ... und die Sprache englisch ist ...
              ebs_volumes_eucalyptus_warnung = '<font color="red">Attention! Attaching volumes with Instances at Eucalyptus needs some time (several minutes).</font>'
          else:                        # Wenn die Region Amazon EC2 ist...
            ebs_volumes_eucalyptus_warnung = "<p>&nbsp;</p>"

          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'zonen_liste': zonen_liste,
          'tabelle_anhaengen': tabelle_anhaengen,
          'ebs_volumes_eucalyptus_warnung': ebs_volumes_eucalyptus_warnung,
          }

          #if sprache == "de": naechse_seite = "volume_anhaengen_de.html"
          #else:               naechse_seite = "volume_anhaengen_en.html"
          #path = os.path.join(os.path.dirname(__file__), naechse_seite)
          path = os.path.join(os.path.dirname(__file__), "templates", sprache, "volume_anhaengen.html")
          self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')

class VolumesErzeugen(webapp.RequestHandler):
    def post(self):
        #self.response.out.write('posted!')
        groesse = self.request.get('groesse')
        GB_oder_TB = self.request.get('GB_oder_TB')
        zone = self.request.get('zone')

        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        if groesse == "":
          # Testen ob die Größe des neuen Volumes angegeben wurde
          # Wenn keine Größe angegeben wurde, kann kein Volume angelegt werden
          #fehlermeldung = "Sie haben keine Größe angegeben"
          fehlermeldung = "16"
          self.redirect('/volumes?message='+fehlermeldung)
        elif groesse.isdigit() == False: 
          # Testen ob die Größe eine Zahl ist
          # Wenn nicht ausschließlich eine Zahl eingegeben wurde sondern evtl. Buchstaben oder Sonderzeichen
          #fehlermeldung = "Sie haben keine Zahl angegeben"
          fehlermeldung = "17"
          self.redirect('/volumes?message='+fehlermeldung)
        elif GB_oder_TB == "TB" and int(groesse) > 1:
          # Testen ob TB als Maßeinheit angegeben wurde und die Größe > 1 TB ist
          # fehlermeldung = "Amazon EBS ermöglicht die Erstellung von Datenträgern
          # mit einer Speicherkapazität von 1 GB bis 1 TB"
          fehlermeldung = "25"
          self.redirect('/volumes?message='+fehlermeldung)
        else:
          # Die Eingabe in Integer umwandeln
          groesse = int(groesse)
          if GB_oder_TB == "TB":
            # Testen ob GB oder TB als Maßeinheit angegeben wurde
            # Bei TB wird die Zahl mit 1000 multipliziert
            groesse *= 1000
          # Volume erzeugen
          try:
            # Volume erzeugen
            neues_volume = conn_region.create_volume(groesse, zone, snapshot=None)
          except EC2ResponseError:
            # Wenn es nicht klappt...
            fehlermeldung = "18"
            self.redirect('/volumes?message='+fehlermeldung)
          except DownloadError:
            # Wenn es nicht klappt...
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            fehlermeldung = "8"
            self.redirect('/volumes?message='+fehlermeldung) 
          else:
            # Wenn es geklappt hat...
            fehlermeldung = "15"
            self.redirect('/volumes?message='+fehlermeldung)


class VolumesLoesen(webapp.RequestHandler):
    def get(self):
        # Name des zu lösenden Volumes holen
        volume = self.request.get('volume')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Volume entkoppeln
          conn_region.detach_volume(volume)
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "20"
          self.redirect('/volumes?message='+fehlermeldung) 
        except DownloadError:
          # Wenn es nicht klappt...
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/volumes?message='+fehlermeldung) 
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "24"
          self.redirect('/volumes?message='+fehlermeldung) 


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
          fehlermeldung = "1"
          self.redirect('/images?message='+fehlermeldung)
        else:
          if re.match('ami-*', ami) == None:  
            # Erst überprüfen, ob die Eingabe mit "ami-" angängt
            fehlermeldung = "2"
            self.redirect('/images?message='+fehlermeldung)
          elif len(ami) != 12:
            # Überprüfen, ob die Eingabe 12 Zeichen lang ist
            fehlermeldung = "3"
            self.redirect('/images?message='+fehlermeldung)
          elif re.search(r'[^\-a-zA-Z0-9]', ami) != None:
            # Überprüfen, ob die Eingabe nur erlaubte Zeichen enthält
            # Die Zeichen - und a-zA-Z0-9 sind erlaubt. Alle anderen nicht. Darum das ^
            fehlermeldung = "4"
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
              fehlermeldung = "5"
              self.redirect('/images?message='+fehlermeldung)
            else:
              # Favorit erzeugen
              # Festlegen, was in den Datastore geschrieben werden soll
              favorit = KoalaCloudDatenbankFavouritenAMIs(ami=ami,
                                                          zone=zone,
                                                          user=username)
              # In den Datastore schreiben
              favorit.put()

              fehlermeldung = "0"
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

            if message == "0":
              if sprache == "de":
                input_error_message = '<p>&nbsp;</p> <font color="green">Der Favorit wurde erfolgreich angelegt</font>'
              else:
                input_error_message = '<p>&nbsp;</p> <font color="green">The favourite was created successfully</font>'
            elif message == "1":
              if sprache == "de":
                input_error_message = '<p>&nbsp;</p> <font color="red">Sie haben keinen AMI angegeben</font>'
              else:
                input_error_message = '<p>&nbsp;</p> <font color="red">AMI was missing</font>'
            elif message == "2":
              if sprache == "de":
                input_error_message = '<p>&nbsp;</p> <font color="red">Die Eingabe hat nicht mit <B><TT>ami-</TT></B> angefangen</font>'
              else:
                input_error_message = '<p>&nbsp;</p> <font color="red">The input did not start wirh <B><TT>ami-</TT></B></font>'
            elif message == "3":
              if sprache == "de":
                input_error_message = '<p>&nbsp;</p> <font color="red">Ihre Eingabe hatte nicht die korrekte L&auml;nge</font>'
              else:
                input_error_message = '<p>&nbsp;</p> <font color="red">The input length was not correct</font>'
            elif message == "4":
              if sprache == "de":
                input_error_message = '<p>&nbsp;</p> <font color="red">Ihre Eingabe enthielt nicht erlaubte Zeichen</font>'
              else:
                input_error_message = '<p>&nbsp;</p> <font color="red">The input had characters that are not allowed</font>'
            elif message == "5":
              if sprache == "de":
                input_error_message = '<p>&nbsp;</p> <font color="red">Das von Ihnen eingegebene AMI existiert nicht</font>'
              else:
                input_error_message = '<p>&nbsp;</p> <font color="red">The AMI is not existing</font>'
            else:
              input_error_message = ''

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
                    imagestabelle = imagestabelle + '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
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
              fehlermeldung = "1"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif accesskey == "": 
              #fehlermeldung = "Sie haben keinen Access Key angegeben"
              fehlermeldung = "2"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif secretaccesskey == "": 
              # Wenn kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Secret Access Key angegeben"
              fehlermeldung = "3"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', accesskey) != None:
              # Wenn der Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "6"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', secretaccesskey) != None:
              # Wenn der Secret Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Secret Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "7"
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
                fehlermeldung = "10"
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
              fehlermeldung = "1"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif accesskey == "": 
              #fehlermeldung = "Sie haben keinen Access Key angegeben"
              fehlermeldung = "2"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif secretaccesskey == "": 
              # Wenn kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Secret Access Key angegeben"
              fehlermeldung = "3"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif nameregion == "": 
              # Wenn kein Name eingegeben wurde
              fehlermeldung = "4"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif endpointurl == "": 
              # Wenn keine Endpoint URL eingegeben wurde
              fehlermeldung = "5"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', accesskey) != None:
              # Wenn der Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "6"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9+=]', secretaccesskey) != None:
              # Wenn der Secret Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Secret Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "7"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\ \-._a-zA-Z0-9]', nameregion) != None:
              # Wenn der Name nicht erlaubte Zeichen enthält
              fehlermeldung = "8"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\ \/\-.:_a-zA-Z0-9]', endpointurl) != None:
              # Wenn die Endpoint URL nicht erlaubte Zeichen enthält
              fehlermeldung = "9"
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
                fehlermeldung = "10"
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
              fehlermeldung = "1"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif accesskey == "": 
              #fehlermeldung = "Sie haben keinen Access Key angegeben"
              fehlermeldung = "2"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif secretaccesskey == "": 
              # Wenn kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Secret Access Key angegeben"
              fehlermeldung = "3"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif nameregion == "": 
              # Wenn kein Name eingegeben wurde
              fehlermeldung = "4"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif endpointurl == "": 
              # Wenn keine Endpoint URL eingegeben wurde
              fehlermeldung = "5"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', accesskey) != None:
              # Wenn der Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "6"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', secretaccesskey) != None:
              # Wenn der Secret Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Secret Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "7"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\ \-._a-zA-Z0-9]', nameregion) != None:
              # Wenn der Name nicht erlaubte Zeichen enthält
              fehlermeldung = "8"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\ \/\-.:_a-zA-Z0-9]', endpointurl) != None:
              # Wenn die Endpoint URL nicht erlaubte Zeichen enthält
              fehlermeldung = "9"
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
                fehlermeldung = "10"
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
          fehlermeldung = "5"
          self.redirect('/instanzen?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat
          fehlermeldung = "4"
          self.redirect('/instanzen?message='+fehlermeldung)

class InstanzAnlegen(webapp.RequestHandler):
    def get(self):
        instance_type = self.request.get('type')
        keys_liste = self.request.get('key')
        image_id = self.request.get('image')
        gruppen_liste = self.request.get('gruppe')
        aki_id = self.request.get('aki')
        ari_id = self.request.get('ari')
        zonen_auswahl = self.request.get('zone')

        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')

        conn_region, regionname = login(username)

        try:
          # Instanz(en) anlegen
          reservation = conn_region.run_instances(image_id,
                                                  key_name=keys_liste,
                                                  instance_type=instance_type,
                                                  placement=zonen_auswahl,
                                                  kernel_id=aki_id,
                                                  ramdisk_id=ari_id)
                                                  #security_groups=gruppen_liste
        except EC2ResponseError:
          # Wenn es nicht geklappt hat
          fehlermeldung = "5"
          self.redirect('/instanzen?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat
          fehlermeldung = "4"
          self.redirect('/instanzen?message='+fehlermeldung)


    def post(self):
        #self.response.out.write('posted!')
        instance_type = self.request.get('instance_type')
        number_instances = self.request.get('number_instances')
        keys_liste = self.request.get('keys_liste')
        image_manifest = self.request.get('image_manifest')
        image_id = self.request.get('image_id')
        number_instances_max = self.request.get('number_instances_max')
        number_instances_min = self.request.get('number_instances_min')
        gruppen_liste = self.request.get('gruppen_liste')
        aki_id = self.request.get('aki_id')
        ari_id = self.request.get('ari_id')
        zonen_auswahl = self.request.get('zonen_auswahl')

        if not aki_id:
          aki_id = None

        if not ari_id:
          ari_id = None

        if not zonen_auswahl:
          zonen_auswahl = None

        # Wenn im Feld Instanzen (max) ein kleinerer Wert eingegebenen wurde als im Feld
        # Instanzen (min), dann macht das keinen Sinn.
        # In diesem Fall ist dann Instanzen (max) = Instanzen (min)
        if number_instances_max < number_instances_min:
          number_instances_max = number_instances_min

        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')

        conn_region, regionname = login(username)

        try:
          # Instanz(en) anlegen
          reservation = conn_region.run_instances(image_id,
                                                  min_count=number_instances_min,
                                                  max_count=number_instances_max,
                                                  key_name=keys_liste,
                                                  instance_type=instance_type,
                                                  placement=zonen_auswahl,
                                                  kernel_id=aki_id,
                                                  ramdisk_id=ari_id)
                                                  #security_groups=gruppen_liste
        except EC2ResponseError:
          # Wenn es nicht geklappt hat
          fehlermeldung = "5"
          self.redirect('/instanzen?message='+fehlermeldung)
        else:
          # Wenn es geklappt hat
          fehlermeldung = "4"
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

          if message == "0":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="green">Der Bucket wurde erfolgreich angelegt</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="green">The bucket was created successfully</font>'
          elif message == "1":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Sie haben keinen Namen angegeben</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">No name given</font>'
          elif message == "2":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Der Name f&uuml;r den neuen Bucket enthielt nicht erlaubt Zeichen</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">The name for the new bucket had characters that are not allowed</font>'
          elif message == "3":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Beim Versuch den Bucket anzulegen kam es zu einem Fehler</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">While trying zu create the bucket, an error occured</font>'
          elif message == "4":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Sie haben schon einen Bucket mit dem eingegebenen Namen</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">You already have a bucket with this name</font>'
          elif message == "5":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Beim Versuch den Bucket zu entfernen, kam es zu einem Fehler<br>Achtung! Es k&ouml;nnen nur leere Buckets gel&ouml;scht werden!</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">While the system tried to erase the bucket, an error occured<br>Attention! Buckets need to be empty before they can be deleted!</font>'
          elif message == "6":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="green">Der Bucket wurde erfolgreich entfernt</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="green">The bucket was erased successfully</font>'
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
          fehlermeldung = "1"
          self.redirect('/s3?message='+fehlermeldung)
        elif re.search(r'[^\-.a-zA-Z0-9]', neuerbucketname) != None:
          # Testen ob der Name für den neuen key nicht erlaubte Zeichen enthält
          fehlermeldung = "2"
          self.redirect('/s3?message='+fehlermeldung)
        else:
          # Mit S3 verbinden
          conn_s3 = logins3(username)
          try:
            # Liste der Buckets
            liste_buckets = conn_s3.get_all_buckets()
          except:
            # Wenn es nicht klappt...
            fehlermeldung = "3"
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
                fehlermeldung = "3"
                # Wenn es nicht klappt...
                self.redirect('/s3?message='+fehlermeldung)
              else:
                fehlermeldung = "0"
                # Wenn es geklappt hat...
                self.redirect('/s3?message='+fehlermeldung)
            else:
              # Wenn man schon einen Bucket mit dem eingegeben Namen hat...
              fehlermeldung = "4"
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
          fehlermeldung = "5"
          # Wenn es nicht klappt...
          self.redirect('/s3?message='+fehlermeldung)
        else:
          fehlermeldung = "6"
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

          if message == "0":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="green">Der Key wurde erfolgreich gel&ouml;scht</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="green">The key was erased successfully</font>'
          elif message == "1":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Beim Versuch den Key zu l&ouml;schen kam es zu einem Fehler</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">An error occured while trying to erase the key</font>'
          elif message == "2":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Sie haben keinen Namen f&uuml;r das neue Verzeichnis eingegeben</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">No name for the new directory given</font>'
          elif message == "3":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Ihr eingegebener Verzeichnisname enthielt nicht erlaubte Zeichen</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">The given name for the new directory had characters that are not allowed</font>'
          elif message == "4":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="green">Das neue Verzeichnis wurde erfolgreich angelegt</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="green">The new directory was successfully created</font>'
          elif message == "5":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Beim Versuch das neue Verzeichnis anzulegen kam es zu einem Fehler</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">An error occured while the system tried to create the new directory</font>'
          elif message == "6":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Es existiert bereits ein Verzeichnis mit dem eingegebenen Namen</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">A directory with the given name still exists</font>'
          elif message == "7":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="green">Die Zugriffsberechtigung wurde erfolgreich ge&auml;ndert</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="green">The Access Control List (ACL) was changed successfully</font>'
          elif message == "8":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Beim Versuch die Zugriffsberechtigung zu &auml;ndern kam es zu einem Fehler</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">An error occured while the system tried to change the Access Control List (ACL)</font>'
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

          AWSAccessKeyId = aws_access_key_erhalten(username,regionname)
          AWSSecretAccessKeyId = aws_secret_access_key_erhalten(username,regionname)

          input_error_message = ""

          if message == "0":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="green">Der Key wurde erfolgreich gel&ouml;scht</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="green">The key was erased successfully</font>'
          elif message == "1":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Beim Versuch den Key zu l&ouml;schen kam es zu einem Fehler</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">An error occured while trying to erase the key</font>'
          elif message == "2":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="green">Die Keys wurden erfolgreich gel&ouml;scht</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="green">The keys were erased successfully</font>'
          elif message == "3":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Beim Versuch die Keys zu l&ouml;schen kam es zu einem Fehler</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">An error occured while trying to erase the keys</font>'
          elif message == "7":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="green">Die Zugriffsberechtigung wurde erfolgreich ge&auml;ndert</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="green">The Access Control List (ACL) was changed successfully</font>'
          elif message == "8":
            if sprache == "de":
              input_error_message = '<p>&nbsp;</p> <font color="red">Beim Versuch die Zugriffsberechtigung zu &auml;ndern kam es zu einem Fehler</font>'
            else:
              input_error_message = '<p>&nbsp;</p> <font color="red">An error occured while the system tried to change the Access Control List (ACL)</font>'
          else:
            input_error_message = ""

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
              eucalyptus_warnung = '<B>Achtung!</B> Unter Eucalyptus 1.6 und 1.6.1 funktioniert der Download von Keys nicht. Dabei handelt es sich um einen Fehler von Eucalyptus. Es kommt zu dieser Fehlermeldung:<BR><B>Failure: 500 Internal Server Error</B>'
            else:
              eucalyptus_warnung = '<B>Attention!</B> With Eucalyptus 1.6 and 1.6.1 the download of Keys is broken. This is a bug of Eucalyptus. The result is this error message:<BR><B>Failure: 500 Internal Server Error</B>'
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
              fehlermeldung = "1"
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
              fehlermeldung = "0"
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
          fehlermeldung = "2"
          if directory == "/":
            self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung)
          else:
            # Den Slash am Ende des Verzeichnisses entfernen
            directory = str(directory[:-1])
            self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)
        elif re.search(r'[^\-_a-zA-Z0-9]', verzeichnisname) != None:
          # Testen ob der Name für den neuen key nicht erlaubte Zeichen enthält
          fehlermeldung = "3"
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
              fehlermeldung = "6"
              if directory == "/":
                self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung)
              else:
                # Den Slash am Ende des Verzeichnisses entfernen
                directory = str(directory[:-1])
                self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)

          if schon_vorhanden == 0:  # Wenn man noch kein Verzeichnis mit dem eingegebenen Namen besitzt...
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
              fehlermeldung = "5"
              if directory == "/":
                self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung)
              else:
                # Den Slash am Ende des Verzeichnisses entfernen
                directory = str(directory[:-1])
                self.redirect('/bucket_inhalt?bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)
            else:
              # Wenn es geklappt hat...
              fehlermeldung = "4"
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
          fehlermeldung = "8"
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
          fehlermeldung = "7"
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
          fehlermeldung = "3"
          self.redirect('/bucket_inhalt_pure?bucket='+bucketname+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "2"
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



def loginselb(username):
  # Die Zugangsdaten des Benutzers holen
  aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

  for db_eintrag in aktivezone:
    zoneinderdb = db_eintrag.aktivezone

    if zoneinderdb == "us-east-1" or zoneinderdb == "us-west-1" or zoneinderdb == "eu-west-1" or zoneinderdb == "ap-southeast-1":
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

    if zoneinderdb == "us-east-1":
      hostname = "us-east-1.elasticloadbalancing.amazonaws.com"
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_elb = boto.ec2.elb.ELBConnection(aws_access_key_id=accesskey,
                              aws_secret_access_key=secretaccesskey,
                              is_secure=False,
                              host=hostname,
                              #port=8773,
                              path="/")
      regionname = aktuellezone
    elif zoneinderdb == "eu-west-1":
      hostname = "eu-west-1.elasticloadbalancing.amazonaws.com"
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_elb = boto.ec2.elb.ELBConnection(aws_access_key_id=accesskey,
                              aws_secret_access_key=secretaccesskey,
                              is_secure=False,
                              host=hostname,
                              #port=8773,
                              path="/")
      regionname = aktuellezone
    elif zoneinderdb == "us-west-1":
      hostname = "us-west-1.elasticloadbalancing.amazonaws.com"
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_elb = boto.ec2.elb.ELBConnection(aws_access_key_id=accesskey,
                              aws_secret_access_key=secretaccesskey,
                              is_secure=False,
                              host=hostname,
                              #port=8773,
                              path="/")
      regionname = aktuellezone
    elif zoneinderdb == "ap-southeast-1":
      hostname = "ap-southeast-1.elasticloadbalancing.amazonaws.com"
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_elb = boto.ec2.elb.ELBConnection(aws_access_key_id=accesskey,
                              aws_secret_access_key=secretaccesskey,
                              is_secure=False,
                              host=hostname,
                              #port=8773,
                              path="/")
      regionname = aktuellezone
    else:
      regionname = "keine"
      #regionname = aktuellezone
  else:
    regionname = "keine"
  return conn_elb



def login(username):
  # Die Zugangsdaten des Benutzers holen
  aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

  for db_eintrag in aktivezone:
    zoneinderdb = db_eintrag.aktivezone

    if zoneinderdb == "us-east-1" or zoneinderdb == "us-west-1" or zoneinderdb == "eu-west-1" or zoneinderdb == "ap-southeast-1":
      aktuellezone = "Amazon"
    else:
      aktuellezone = zoneinderdb


  if aktivezone:
    # In der Spalte "eucalyptusname" steht entweder "Amazon" oder der Eucalyptus-Name der Private Cloud
    zugangsdaten = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db=aktuellezone)

    for db_eintrag in zugangsdaten:
      accesskey = db_eintrag.accesskey
      secretaccesskey = db_eintrag.secretaccesskey
      endpointurl = db_eintrag.endpointurl
      eucalyptusname = db_eintrag.eucalyptusname
      port = db_eintrag.port
      regionname = db_eintrag.regionname

    if zoneinderdb == "us-east-1" or zoneinderdb == "eu-west-1" or zoneinderdb == "us-west-1" or zoneinderdb == "ap-southeast-1":
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_region = boto.ec2.connect_to_region(zoneinderdb,
                                                aws_access_key_id=accesskey,
                                                aws_secret_access_key=secretaccesskey,
                                                is_secure = False)

      regionname = aktuellezone
    elif regionname == "nimbus":
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_region = boto.connect_ec2(str(accesskey), str(secretaccesskey), port=int(port))
      conn_region.host = str(endpointurl)

      regionname = aktuellezone
    else:
      port = int(port)
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_region = boto.connect_ec2(aws_access_key_id=accesskey,
                                    aws_secret_access_key=secretaccesskey,
                                    is_secure=False,
                                    region=RegionInfo(name="eucalyptus", endpoint=endpointurl),
                                    port=port,
                                    path="/services/Eucalyptus")

      regionname = aktuellezone
  else:
    regionname = "keine"
  return conn_region, regionname

def amazon_region(username):
    aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
    results = aktivezone.fetch(10)

    for result in results:
      if result.aktivezone == "us-east-1":
        zone_amazon = "(us-east-1)"
      elif result.aktivezone == "eu-west-1":
        zone_amazon = "(eu-west-1)"
      elif result.aktivezone == "us-west-1":
        zone_amazon = "(us-west-1)"
      elif result.aktivezone == "ap-southeast-1":
        zone_amazon = "(ap-southeast-1)"
      else:
        zone_amazon = ""

    return zone_amazon

def aktuelle_sprache(username):
  # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
  spracheanfrage = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankSprache WHERE user = :username_db", username_db=username)
  ergebnisse = spracheanfrage.fetch(10)

  if not ergebnisse:
      logindaten = KoalaCloudDatenbankSprache(sprache="en",
                                              user=username)
      logindaten.put()   # In den Datastore schreiben
      spracheanfrage = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankSprache WHERE user = :username_db", username_db=username)
      ergebnisse = spracheanfrage.fetch(10)

  for ergebnis in ergebnisse:
    if ergebnis.sprache == "en":
      sprache = "en"
    elif ergebnis.sprache == "de":
      sprache = "de"
    else:
      sprache = "en"

  return sprache

def navigations_bar_funktion(sprache):
  if sprache == "de":
    navigations_bar = '&nbsp; \n'
    navigations_bar = navigations_bar + '<a href="/regionen" title="Regionen">Regionen</a> | \n'
    navigations_bar = navigations_bar + '<a href="/instanzen" title="Instanzen">Instanzen</a> | \n'
    navigations_bar = navigations_bar + '<a href="/images" title="Images">Images</a> | \n'
    navigations_bar = navigations_bar + '<a href="/schluessel" title="Schl&uuml;ssel">Schl&uuml;ssel</a> | \n'
    navigations_bar = navigations_bar + '<a href="/volumes" title="Elastic Block Store">EBS</a> | \n'
    navigations_bar = navigations_bar + '<a href="/snapshots" title="Snapshots">Snapshots</a> | \n'
    navigations_bar = navigations_bar + '<a href="/elastic_ips" title="Elastic IPs">IPs</a> | \n'
    navigations_bar = navigations_bar + '<a href="/zonen" title="Verf&uuml;gbarkeitszonen">Zonen</a> | \n'
    navigations_bar = navigations_bar + '<a href="/securitygroups" title="Sicherheitsgruppen">Gruppen</a> | \n'
    navigations_bar = navigations_bar + '<a href="/s3" title="Simple Storage Service">S3</a> | \n'
    navigations_bar = navigations_bar + '<a href="/loadbalancer" title="Elastic Load Balancer">ELB</a> | \n'
    navigations_bar = navigations_bar + '<a href="/info" title="Info">Info</a> \n'
  else:
    navigations_bar = '&nbsp; \n'
    navigations_bar = navigations_bar + '<a href="/regionen" title="Regions">Regions</a> | \n'
    navigations_bar = navigations_bar + '<a href="/instanzen" title="Instances">Instances</a> | \n'
    navigations_bar = navigations_bar + '<a href="/images" title="Images">Images</a> | \n'
    navigations_bar = navigations_bar + '<a href="/schluessel" title="Keys">Keys</a> | \n'
    navigations_bar = navigations_bar + '<a href="/volumes" title="Elastic Block Store">EBS</a> | \n'
    navigations_bar = navigations_bar + '<a href="/snapshots" title="Snapshots">Snapshots</a> | \n'
    navigations_bar = navigations_bar + '<a href="/elastic_ips" title="Elastic IPs">IPs</a> | \n'
    navigations_bar = navigations_bar + '<a href="/zonen" title="Availability Zones">Zones</a> | \n'
    navigations_bar = navigations_bar + '<a href="/securitygroups" title="Security Groups">Groups</a> | \n'
    navigations_bar = navigations_bar + '<a href="/s3" title="Simple Storage Service">S3</a> | \n'
    navigations_bar = navigations_bar + '<a href="/loadbalancer" title="Elastic Load Balancer">ELB</a> | \n'
    navigations_bar = navigations_bar + '<a href="/info" title="Info">Info</a> \n'
  return navigations_bar

def zonen_liste_funktion(username,sprache):
  testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db", username_db=username)
  # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
  anzahl = testen.count()     # Wie viele Einträge des Benutzers sind schon vorhanden?

  results = testen.fetch(100) # Alle Einträge des Benutzers holen?

  zonen_liste = ''
  if anzahl:
    zonen_liste = zonen_liste + '<form action="/regionwechseln" method="post" accept-charset="utf-8">'
    zonen_liste = zonen_liste + '<select name="regionen" size="1">'
    for test in results:
      zonen_liste = zonen_liste + '<option>'
      if test.eucalyptusname == "Amazon":
        zonen_liste = zonen_liste + 'Amazon EC2 (US East)'
        zonen_liste = zonen_liste + '</option>'
        zonen_liste = zonen_liste + '<option>'
        zonen_liste = zonen_liste + 'Amazon EC2 (US West)'
        zonen_liste = zonen_liste + '</option>'
        zonen_liste = zonen_liste + '<option>'
        zonen_liste = zonen_liste + 'Amazon EC2 (EU West)'
        zonen_liste = zonen_liste + '</option>'
        zonen_liste = zonen_liste + '<option>'
        zonen_liste = zonen_liste + 'Amazon EC2 (Asia Pacific)'
      else:
        #zonen_liste = zonen_liste + 'Eucalyptus'
        #zonen_liste = zonen_liste + ' ('
        zonen_liste = zonen_liste + str(test.eucalyptusname)
        #zonen_liste = zonen_liste + ')'
      zonen_liste = zonen_liste + '</option>'
    zonen_liste = zonen_liste + '</select>'
    zonen_liste = zonen_liste + '&nbsp;'
    if sprache == "de":
      zonen_liste = zonen_liste + '<input type="submit" value="Region wechseln">'
    else:
      zonen_liste = zonen_liste + '<input type="submit" value="switch to region">'
    zonen_liste = zonen_liste + '</form>'
  else:
    zonen_liste = ''

  return zonen_liste


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

def xor_crypt_string(data, key):
    return ''.join(chr(ord(x) ^ ord(y)) for (x,y) in izip(data, cycle(key)))

if __name__ == "__main__":
    main()





