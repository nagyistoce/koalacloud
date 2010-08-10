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
          path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "instanzen.html")
          self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')

