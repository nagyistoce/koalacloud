#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp

from internal.Datastore import *

class Sprache(webapp.RequestHandler):
    def get(self):
        # Die ausgewählte Sprache holen
        # Get the chosen language
        lang = self.request.get('lang')
        # Den Pfad holen
        # Get the path      
        path = self.request.get('path')
        if not path:
          path = ''
        # Den Usernamen erfahren
        # Get the username
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
            # Write into the datastore
            logindaten.put()
          except:
            # Wenn es nicht klappt...
            # If it didn't work...
            self.redirect('/')
          else:
            # Wenn es geklappt hat...
            # If it worked...
            self.redirect('/'+path)
        else:
          self.redirect('/')
