#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

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




def xor_crypt_string(data, key):
    return ''.join(chr(ord(x) ^ ord(y)) for (x,y) in izip(data, cycle(key)))


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
  
  
def zonen_liste_funktion(username,sprache):
    testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db", username_db=username)
    # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
    # Wie viele Einträge des Benutzers sind schon vorhanden?
    anzahl = testen.count()
    # Alle Einträge des Benutzers holen?
    results = testen.fetch(100)

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
      
def loginelb(username):
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
