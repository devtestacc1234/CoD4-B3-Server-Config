#
# Origial plugin: login.py version 1.1
# Plugin for extra authentication of privileged users in games with no private messaging
#
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Plugin for extra authentication of privileged users
# Copyright (C) 2005 Tim ter Laak (ttlogic@xlr8or.com)
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
#
# 1.0   - 26/03/2013 - d0nin380
#        * Initial release - modification of login.py
# 1.0.1 - 02/04/2013 - d0nin380
#        * Fixed a bug where temporary client.groupBits were saved
#           in the database by !q3setpassword

import random
import string
import time
from b3.clients import Client
import b3.events
import b3.plugin
from b3.functions import hash_password

__author__    = 'd0nin380'
__version__ = '1.0.1'


class Q3LoginPlugin(b3.plugin.Plugin):

    def onLoadConfig(self):
        try:
            self.threshold = self.config.getint('settings', 'thresholdlevel') 
        except Exception:
            self.threshold = 1000
            self.debug('Using default value (%i) for settings::thresholdlevel', self.threshold)
        try:
            self.passwdlevel = self.config.getint('settings', 'passwdlevel') 
        except Exception:
            self.passwdlevel = 100
            self.debug('Using default value (%i) for settings::passwdlevel', self.passwdlevel)
        return


    def onStartup(self):
        self.registerEvent(b3.events.EVT_CLIENT_AUTH)
        self.registerEvent(b3.events.EVT_CLIENT_SAY)
        self.registerEvent(b3.events.EVT_CLIENT_TEAM_SAY)
        self._adminPlugin = self.console.getPlugin('admin')
        if self._adminPlugin:
            self._adminPlugin.registerCommand(self, 'q3login', 2, self.cmd_q3login, secretLevel=1)
            self._adminPlugin.registerCommand(self, 'q3setpassword', self.passwdlevel, self.cmd_q3setpassword)

        self.eventHandlers = {
            b3.events.EVT_CLIENT_SAY: self.onChat,
            b3.events.EVT_CLIENT_TEAM_SAY: self.onChat,
            }


    def onEvent(self, event):
        if event.type == b3.events.EVT_CLIENT_AUTH:
            self.onAuth(event.client)
        elif event.type in self.eventHandlers:
            self.eventHandlers[event.type](event)
        else:
            self.debug('login.dumpEvent -- Type %s, Client %s, Target %s, Data %s', event.type, event.client, event.target, event.data)


    def onAuth(self, client):
        if client.maxLevel > self.threshold and not client.isvar(self, 'loggedin'):

            client_from_db = self._get_client_from_db(client.id)

            #save original groupbits
            self.verbose('setting login_groupbits: %s from db for client: %s' % (client_from_db.groupBits, client))
            client.setvar(self, 'login_groupbits', client_from_db.groupBits)

            #set new groupBits
            try:
                g = self.console.storage.getGroup('reg')
                client.groupBits = g.id
            except Exception:
                client.groupBits = 2

            if not client_from_db.password:
                client.message('You need a password to use all your privileges. Ask the administrator to set a password for you.')
                return
            else:
                message = 'Login for access'
                client.message(message)
                return

                
    def onChat(self, event):
        if event.data.startswith('password'):
            self._checkpassword(event.client, event.data, spam=1)
        _loggedin = event.client.var(self, 'loggedin').value
        _lw = event.client.var(self, 'loggedin_waiting').value
        if _lw == 1:
            _password = self._getpassword(event.client)
            if not _password:
                event.client.setvar(self, 'loggedin', 1)
                event.client.groupBits = event.client.var(self, 'login_groupbits').value
                event.client.delvar(self, 'loggedin_waiting')
                event.client.message('You have successfully logged in')
                self.debug('%s logged in' % event.client.name)


    def cmd_q3login(self, data, client, cmd=None):
        """\
         - use after you have set password via console
        """
        if data:
            message = 'Usage (via console): first /password yourpassword then !q3login'
            client.message(message)
            # Incase user does !q3login <your password> we have to check if the password matches and if it does we have to change it.
            self._checkpassword(client, data, spam=1)
            return
                
        if client.var(self, 'loggedin').value == 1:
            client.message('You are already logged in.')
            return
        
        if client.var(self, 'loggedin_waiting').value == 1:
            _lw = client.var(self, 'loggedin_waiting').value
            if _lw == 1:
                client.message('To complete login, type "/reset password" in console')
                return

        if not client.isvar(self, 'login_groupbits'):
            client.message('You do not need to log in.')
            return
        
        else:
            _password = self._getpassword(client)
            if _password:
                if self._checkpassword(client, _password):
                    client.message('To complete login, type /reset password in console')
                    client.setvar(self, 'loggedin_waiting', 1)
                else:
                    client.message('^1***Access denied***^7')
                    self.debug('Failed password attemp from: %s' % client.name)
            else:
                client.message('Empty password detected. FIRST /password yourpassword THEN !q3login')
                    
            
    def cmd_q3setpassword(self, data, client, cmd=None):
        """\
         - set a password for a client /password <new password>:[name]
        """
        _password = self._getpassword(client)
        _pdata = _password.split(':')
        if not _password:
            client.message('LOGIN for access')
            return

        data = data.split()
        if len(data) > 0:
            client.message('Usage in console: FIRST /password <new password>:[name] THEN !q3setpassword')
        self.verbose(len(_pdata))
        if len(_pdata) > 1:
            sclient = self._adminPlugin.findClientPrompt(_pdata[1], client)
            if not sclient: return
            if client.maxLevel <= sclient.maxLevel and client.maxLevel < 100:
                client.message('You can only change passwords of yourself or lower level players.')
                return
        else:
            sclient = client
        self.debug(_pdata)
        sclient.password = hash_password(_pdata[0])
        if sclient.isvar(self, 'login_groupbits'):
            sclient.groupBits = sclient.var(self, 'login_groupbits').value
            sclient.message('You have been logged in by B3')
        sclient.save()
        self.debug('New password saved to %s, by %s' % (sclient.name, client.name))
        if client == sclient:
            client.message("your new password is saved, do not forget to /reset password")
        else:
            client.message("new password for %s saved, do not forget to /reset password" % sclient.name)


    def _get_client_from_db(self, client_id):
        return self.console.storage.getClient(Client(id=client_id))
        
    
    def _getpassword(self, client):
        """
        get pass from rcon dumpuser
        """
        
        _dump = {}
        
        for _d in self.console.write('dumpuser %s'%client.name).strip().split('\n'): 
            _d = ' '.join(_d.split()).split()
            try:
                _dump[_d[0]] = _d[1]
            except Exception, err:
                pass
        self.debug('from _getpassword, _dump: %s' % _dump.items())
        try:
            _pass = _dump['password']
        except KeyError:
            _pass = None
        return _pass

    def _checkpassword(self, client, data, spam=False):
        """
        Check the password for match in database
        """
        data = data.split()
        if spam:
            digest = hash_password(data[1])
        else:
            digest = hash_password(data[0])
        client_from_db = self._get_client_from_db(client.id)
        if digest == client_from_db.password:
            if spam:
                _newpass = ''.join([random.choice(string.ascii_letters) for i in xrange(6)])
                client.password = hash_password(_newpass)
                client.save()
                self.debug('New password saved to %s, by B3 (spammed)' % client.name)
                client.message('OOOPS! Your new password is: %s' % _newpass)
            else:
                return True
                
