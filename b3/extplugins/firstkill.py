# firstkill Plugin

__author__  = 'PtitBigorneau www.ptitbigorneau.fr'
__version__ = '1.4.1'

import b3
import b3.plugin
import b3.events

class FirstkillPlugin(b3.plugin.Plugin):
    
    _adminPlugin = None
    _kill = 0
    _tk = 0
    _hs = 0

    def onStartup(self):

        self._adminPlugin = self.console.getPlugin('admin')
        
        if not self._adminPlugin:

            self.error('Could not find admin plugin')
            return False
        
        self.registerEvent(b3.events.EVT_CLIENT_KILL)
        self.registerEvent(b3.events.EVT_CLIENT_KILL_TEAM)
        self.registerEvent(b3.events.EVT_GAME_ROUND_START)

        self._adminPlugin.registerCommand(self, 'firstkill',self._adminlevel, self.cmd_firstkill)
        self._adminPlugin.registerCommand(self, 'firsttk',self._adminlevel, self.cmd_firsttk)

        self.gamename = self.console.game.gameName
        
        if  self.gamename == 'iourt41':
            self._adminPlugin.registerCommand(self, 'firsths',self._adminlevel, self.cmd_firsths)

    def onLoadConfig(self):

        self._tkonoff = self.config.get('settings', 'tkonoff')
        self._fkonoff = self.config.get('settings', 'fkonoff')
        self._hsonoff = self.config.get('settings', 'hsonoff')
        self._adminlevel = self.config.get('settings', 'adminlevel')

    def onEvent(self, event):
        
        if event.type == b3.events.EVT_GAME_ROUND_START:
    
            self._kill =0
            self._tk =0
            self._hs =0

        if event.type == b3.events.EVT_CLIENT_KILL: 

            self._kill += 1
            
            client = event.client
            target = event.target
            
            if  self.gamename == 'iourt41':
            
                weapon = event.data[1]
                hitlocation = event.data[2]
            
            else:
                
                weapon = 99
                hitlocation = 99
                self._hsonoff = "no"
            
            if weapon not in (23, 25):
                
                if hitlocation == "0" or hitlocation == "1":
                    
                    self._hs += 1

            if self._fkonoff == "on":

                if self._kill == 1:     
                
                    if self.gamename == 'iourt41':
                        
                        if self._hs == 1 and self._hsonoff == "on":
                            
                            self.console.write('bigtext"^2First Kill ^5By Headshot ^3: %s killed %s"' % (client.exactName, target.exactName))
                            self._hs += 1
                            return
                        
                        else:

                            self.console.write('bigtext"^2First Kill ^3: %s killed %s"' % (client.exactName, target.exactName))

                    elif self.gamename[:3] == "cod":

                        self.console.say("^2First Kill ^3: %s killed %s" % (client.exactName, target.exactName))
                    
                    else:

                        self.console.saybig("^2First Kill ^3: %s killed %s" % (client.exactName, target.exactName))

            if self._hsonoff == "on":

                if self._kill == 1:

                    return

                if self._hs == 1:     
  
                    self.console.write('bigtext"^5First Kill by Headshot ^3: %s"' % (client.exactName))
                    self._hs += 1

        if (event.type == b3.events.EVT_CLIENT_KILL_TEAM) and (self._tkonoff=="on"):
            
            self._tk += 1
            
            client = event.client
            target = event.target

            if self._tk == 1:
          
                if self.gamename == 'iourt41':

                    self.console.write('bigtext"^1First TeamKill ^3:%s killed %s"' % (client.exactName, target.exactName))
                
                elif self.gamename[:3] == "cod":

                    self.console.say("^1First TeamKill ^3:%s killed %s" % (client.exactName, target.exactName))
                
                else:

                    self.console.saybig("^1First TeamKill ^3:%s killed %s" % (client.exactName, target.exactName))
                
    def cmd_firstkill(self, data, client, cmd=None):
        
        """\
        activate / deactivate firstkill
        """
        
        if data:
            
            input = self._adminPlugin.parseUserCmd(data)
        
        else:
        
            if self._fkonoff == 'on':

                client.message('firstkill ^2activated')

            if self._fkonoff == 'off':

                client.message('firstkill ^1deactivated')

            client.message('!firstkill <on / off>')
            return

        if input[0] == 'on':

            if self._fkonoff != 'on':

                self._fkonoff = 'on'
                message = '^2activated'

            else:

                client.message('firstkill is already ^2activated') 

                return False

        if input[0] == 'off':

            if self._fkonoff != 'off':

                self._fkonoff = 'off'
                message = '^1deactivated'

            else:
                
                client.message('firstkill is already ^1disabled')                

                return False

        client.message('firstkill %s'%(message))

    def cmd_firsttk(self, data, client, cmd=None):
        
        """\
        activate / deactivate first teamkill
        """
        
        if data:
            
            input = self._adminPlugin.parseUserCmd(data)
        
        else:
        
            if self._tkonoff == 'on':

                client.message('first teamkill ^2activated')

            if self._tkonoff == 'off':

                client.message('first teamkill ^1deactivated')

            client.message('!firsttk <on / off>')
            return

        if input[0] == 'on':

            if self._tkonoff != 'on':

                self._tkonoff = 'on'
                message = '^2activated'

            else:

                client.message('first teamkill is already ^2activated') 

                return False

        if input[0] == 'off':

            if self._tkonoff != 'off':

                self._tkonoff = 'off'
                message = '^1deactivated'

            else:
                
                client.message('first teamkill is already ^1disabled')                

                return False

        client.message('first teamkill %s'%(message))

    def cmd_firsths(self, data, client, cmd=None):
        
        """\
        activate / deactivate first headshot
        """
        
        if data:
            
            input = self._adminPlugin.parseUserCmd(data)
        
        else:
        
            if self._hsonoff == 'on':

                client.message('first headshot ^2activated')

            if self._hsonoff == 'off':

                client.message('first headshot ^1deactivated')

            client.message('!firsths <on / off>')
            return

        if input[0] == 'on':

            if self._hsonoff != 'on':

                self._hsonoff = 'on'
                message = '^2activated'

            else:

                client.message('first headshot is already ^2activated') 

                return False

        if input[0] == 'off':

            if self._hsonoff != 'off':

                self._hsonoff = 'off'
                message = '^1deactivated'

            else:
                
                client.message('first headshot is already ^1disabled')                

                return False

        client.message('first headshot %s'%(message))