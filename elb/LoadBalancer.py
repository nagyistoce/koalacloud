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
from library import loginelb

from dateutil.parser import *

from error_messages import error_messages

from boto.ec2.connection import *
from boto.ec2.elb import ELBConnection

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

          #self.response.out.write(regionname)

          zonen_liste = zonen_liste_funktion(username,sprache)

          if regionname != 'Amazon':
          #if zugangstyp != 'Amazon':

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
            path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "loadbalancer_non_aws.html")
            self.response.out.write(template.render(path,template_values))
          else:

            if sprache != "de":
              sprache = "en"

            input_error_message = error_messages.get(message, {}).get(sprache)

            # Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
            if input_error_message == None:
              input_error_message = ""

            # Wenn die Nachricht grün formatiert werden soll...
            if message in ("9", "70", "72"):
              # wird sie hier, in der Hilfsfunktion grün formatiert
              input_error_message = format_error_message_green(input_error_message)
            # Ansonsten wird die Nachricht rot formatiert
            elif message in ("8", "10", "71"):
              input_error_message = format_error_message_red(input_error_message)
            else:
              input_error_message = ""

            # Mit ELB verbinden
            conn_elb = loginelb(username)

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
            path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "loadbalancer.html")
            self.response.out.write(template.render(path,template_values))

          