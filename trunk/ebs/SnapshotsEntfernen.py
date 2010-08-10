#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import login

from boto.ec2.connection import *

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
