#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import login

from boto.ec2.connection import *

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
          