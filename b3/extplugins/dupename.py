#
# Plugin for BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2005 www.xlr8or.com
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# Changelog:
#

__version__ = '1.0.0'
__author__  = 'xlr8or'

import b3, time, thread
import b3.events
import b3.plugin
import b3.cron

#--------------------------------------------------------------------------------------------------
class DupenamePlugin(b3.plugin.Plugin):
  _interval = 0
  _checkdupes = 0
  _checkunknown = 0
  _ignoreTill = 0
  _cronTab = None
  _adminPlugin = None

  def onStartup(self):

    # get the admin plugin so we can issue warnings
    self._adminPlugin = self.console.getPlugin('admin')
    if not self._adminPlugin:
      # something is wrong, can't start without admin plugin
      self.error('Could not find admin plugin')
      return False

    self.registerEvent(b3.events.EVT_GAME_EXIT)

    # dont check on startup
    self._ignoreTill = self.console.time() + 120

  def onLoadConfig(self):
    try:
      self._interval = self.config.getint('settings', 'interval')
    except:
      self._interval = 3
      self.debug('Using default value (%s) for interval', self._interval)
    
    # set a min interval
    if self._interval < 1:
      self._interval = 1
    # set a max interval
    if self._interval > 59:
      self._interval = 59
    self.debug('Interval: %s' %(self._interval))
    
    try:
      self._checkdupes = self.config.getboolean('settings', 'checkdupes')
    except:
      self._checkdupes = True
      self.debug('Using default value (%s) for checkdupes', self._checkdupes)
    self.debug('Dupechecking: %s' %(self._checkdupes))
    try:
      self._checkunknown = self.config.getboolean('settings', 'checkunknown')
    except:
      self._checkunknown = True
      self.debug('Using default value (%s) for checkunknown', self._checkunknown)
    self.debug('Check unknowns: %s' %(self._checkunknown))

    if self._cronTab:
      # remove existing crontab
      self.console.cron - self._cronTab

    self._cronTab = b3.cron.PluginCronTab(self, self.check, 0, '*/%s' % (self._interval))
    self.console.cron + self._cronTab

  def onEvent(self, event):
    if event.type == b3.events.EVT_GAME_EXIT:
      # ignore checking for 2 minutes
      self._ignoreTill = self.console.time() + 120

  def check(self):    
    self.debug('Checking for Dupes')
    d = {}
    if self.isEnabled() and (self.console.time() > self._ignoreTill):     
      for player in self.console.clients.getList():
        if not d.has_key(player.name):
          d[player.name] = [player.cid]
        else:
          #l = d[player.name]
          #l.append(cid)
          #d[player.name]=l
          d[player.name].append(player.cid)
      
      for pname,cidlist in d.items():
        if (self._checkdupes and len(cidlist) > 1) or (self._checkunknown and (pname == 'Unknown Soldier' or pname == 'UnnamedPlayer')):
          self.debug('Warning Players')
          for cid in cidlist:
            client = self.console.clients.getByCID(cid)
            self._adminPlugin.warnClient(client, 'badname')
        else:
          self.debug('No players to warn')
