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

        if not results:
          self.redirect('/')
        else:
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
                liste_favouriten = liste_favouriten + '<th align="center">Root Device Typ</th>'
              else:
                liste_favouriten = liste_favouriten + '<th align="center">Root Device Type</th>'  
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
                  liste_favouriten = liste_favouriten + '<tt>'+str(liste_favoriten_ami_images[i].id)+'</tt>'
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
                  liste_favouriten = liste_favouriten + str(liste_favoriten_ami_images[i].type)
                  liste_favouriten = liste_favouriten + '</td>'

                  # Hier kommt die Spalte mit der Manifest-Datei
                  liste_favouriten = liste_favouriten + '<td>'
                  liste_favouriten = liste_favouriten + '<tt>'+str(liste_favoriten_ami_images[i].location)+'</tt>'
                  liste_favouriten = liste_favouriten + '</td>'
                  liste_favouriten = liste_favouriten + '<td align="center">'
                  liste_favouriten = liste_favouriten + '<tt>'+str(liste_favoriten_ami_images[i].architecture)+'</tt>'
                  liste_favouriten = liste_favouriten + '</td>'
                  if liste_favoriten_ami_images[i].state == u'available':
                    liste_favouriten = liste_favouriten + '<td bgcolor="#c3ddc3" align="center">'
                    liste_favouriten = liste_favouriten + str(liste_favoriten_ami_images[i].state)
                  else:
                    liste_favouriten = liste_favouriten + '<td align="center">'
                    liste_favouriten = liste_favouriten + str(liste_favoriten_ami_images[i].state)
                  liste_favouriten = liste_favouriten + '</td>'
                  liste_favouriten = liste_favouriten + '<td align="center">'+liste_favoriten_ami_images[i].root_device_type+'</td>'                  
                  liste_favouriten = liste_favouriten + '<td>'+str(liste_favoriten_ami_images[i].ownerId)+'</td>'
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
            path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "images_amazon.html")
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
                    imagestabelle = imagestabelle + '<tt>'+liste_images[i].id+'</tt>'
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
                    imagestabelle = imagestabelle + str(liste_images[i].type)
                    imagestabelle = imagestabelle + '</td>'
                    imagestabelle = imagestabelle + '<td>'
                    imagestabelle = imagestabelle + '<tt>'+str(liste_images[i].location)+'</tt>'
                    imagestabelle = imagestabelle + '</td>'
                    imagestabelle = imagestabelle + '<td align="center">'
                    imagestabelle = imagestabelle + '<tt>'+str(liste_images[i].architecture)+'</tt>'
                    imagestabelle = imagestabelle + '</td>'
                    if liste_images[i].state == u'available':
                      imagestabelle = imagestabelle + '<td bgcolor="#c3ddc3" align="center">'
                      imagestabelle = imagestabelle + str(liste_images[i].state)
                    else:
                      imagestabelle = imagestabelle + '<td align="center">'
                      imagestabelle = imagestabelle + str(liste_images[i].state)
                    imagestabelle = imagestabelle + '</td>'
                    imagestabelle = imagestabelle + '<td>'
                    imagestabelle = imagestabelle + str(liste_images[i].ownerId)
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
            path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "images.html")
            self.response.out.write(template.render(path,template_values))
