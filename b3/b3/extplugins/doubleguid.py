# DoubleGuid Plugin

__author__  = 'PtitBigorneau www.ptitbigorneau.fr'
__version__ = '1.0'


import b3
import b3.plugin
import b3.events
from b3 import clients

class DoubleguidPlugin(b3.plugin.Plugin):
    
    _adminPlugin = None   

    def onStartup(self):
        
        self._adminPlugin = self.console.getPlugin('admin')
        
        if not self._adminPlugin:

            self.error('Could not find admin plugin')
            return False

        self.registerEvent(b3.events.EVT_CLIENT_AUTH)

        self._adminPlugin.registerCommand(self, 'doubleguid',self._adminlevel, self.cmd_doubleguid)

    def onLoadConfig(self):

        self._pluginactived = self.config.get('settings', 'pluginactived')
        self._adminlevel = self.config.getint('settings', 'adminlevel')
        self._immunityminlevel = self.config.getint('settings', 'immunityminlevel')

    def onEvent(self, event):

        if self._pluginactived == 'off':

           return False

        if self._pluginactived == 'on':

           
            if event.type == b3.events.EVT_CLIENT_AUTH:
            
                client = event.client
            
                if client.maxLevel >= self._immunityminlevel:
            
                    return False            
                
                for x in self.console.clients.getList():

                    if x.guid == client.guid and x.cid != client.cid:

                        client.kick("Kick Double Guid",  None) 

    def cmd_doubleguid(self, data, client, cmd=None):
        
        """\
        activate / deactivate doubleguid 
        """
        
        if data:
            
            input = self._adminPlugin.parseUserCmd(data)
        
        else:
        
            if self._pluginactived == 'on':

                client.message('doubleguid ^2activated')

            if self._pluginactived == 'off':

                client.message('doubleguid ^1deactivated')

            client.message('!doubleguid <on / off>')
            return

        if input[0] == 'on':

            if self._pluginactived != 'on':

                self._pluginactived = 'on'
                message = '^2activated'

            else:

                client.message('doubleguid is already ^2activated') 

                return False

        if input[0] == 'off':

            if self._pluginactived != 'off':

                self._pluginactived = 'off'
                message = '^1deactivated'

            else:
                
                client.message('doubleguid is already ^1disabled')                

                return False

        client.message('doubleguid %s'%(message))


