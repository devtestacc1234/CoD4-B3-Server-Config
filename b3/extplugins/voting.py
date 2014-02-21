# headshots Plugin for Big Brother Bot
# Copyright (C) 2011 Melroy van den Berg
# Inspired by Ismael Garrido
# 
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# CHANGELOG
# 21/02/11 - 2.2
# Fixed to accept the vote the total count of yes must be higher or equal to the minimum vote setting.
# Bug fixed votemap
# 05/02/11 - 2.1
# Fixed minimum votes for each vote type.
# 04/02/11 - 2.0
# Fixed default settings if configuration file failed to load or didn't load properly.
# 26/01/11 - 1.9
# Added !votemapgametype
# 17/01/11 - 1.8
# Added !votemaprotate (this will skip the current map)
# 17/01/11 - 1.7
# Both kick & tempban commands have as reason description "Voted out" and saves the caller in admin field of the database,
# this allows you to search to all the kick/tempban votes and to find the caller again.
# Extended / fixed configuration file
# New configuration options
# 14/01/11 - 1.6
# Added !votegametype
# Fixed some small bugs
# The exact full map / gametype name is only allowed. The server (CoD4) hangs for example at !vm killhouse instead of !vm mp_killhouse
# 13/01/11 - 1.5
# Fixed bug: "A vote is already in progress"
# 25/07/09
# Added !votemap
# Revamped the system, more modular now.
# 12/06/09
# !vk requires a motive to kick
# If more than a certain percent of voters vote yes, the victim is tempbanned
# added !vkveto
# Modlevel is read from admin plugin settings (thanks Bakes)
# 30/05/09
# Added delays between failed votes
# Initial version

__version__ = '2.1'
__author__  = 'Melroy'

import b3
import b3.plugin
import b3.cron
from b3 import clients
import time

class VotingPlugin(b3.plugin.Plugin):
    _adminPlugin = None
    _currentVote = None

    _caller = None

    _in_progress = False
    _yes = 0
    _no = 0
    _vetoed = 0
    _times = 0
    _vote_times = 3
    _vote_interval_announcements = 1
    _vote_interval_failed = 2
    _vote_minvotes = 2
    _votes = {}
    
    def startup(self):
        """\
        Initialize plugin settings
        """

        # get the plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
            self.error('Could not find admin plugin')
            return False
        
        self._vote_times = self.config.getint('settings', 'vote_times')
        self._vote_interval_announcements = self.config.getint('settings', 'vote_interval_announcements')
        self._vote_interval_failed = self.config.getint('settings', 'vote_interval_failed')
        self._vote_minvotes = self.config.getint('settings', 'vote_minvotes')

        try:
            minLevel_vote = self.config.getint('settings', 'min_level_vote')
        except:
            minLevel_vote = 1
        try:
            modLevel = self._adminPlugin.config.getint("settings","admins_level")  
        except:
            minLevel = 20
        
        
        self._adminPlugin.registerCommand(self, 'voteyes', minLevel_vote,  self.cmd_voteyes,  'vy')
        self._adminPlugin.registerCommand(self, 'voteno', minLevel_vote, self.cmd_voteno,  'vn')
        self._adminPlugin.registerCommand(self, 'voteveto', modLevel, self.cmd_veto,  'vveto')

        try:
            minLevel_kick = self.config.getint('votekick', 'min_level_kick')
        except:
            minLevel_kick = 20
        self._adminPlugin.registerCommand(self, 'votekick', minLevel_kick, self.cmd_votekick,  'vk')

        self._votes["kick"] = KickVote()
        self._votes["kick"].startup(self._adminPlugin,  self.console,  self.config)

        try:
            minLevel_map = self.config.getint('votemap', 'min_level_map')
        except:
            minLevel_map = 1        
        self._adminPlugin.registerCommand(self, 'votemap', minLevel_map, self.cmd_votemap,  'vm')
        self._adminPlugin.registerCommand(self, 'maplist', 0, self.cmd_maplist,  'mapl')
        self._votes["map"] = MapVote()
        self._votes["map"].startup(self._adminPlugin,  self.console,  self.config)

        try:
            minLevel_gametype = self.config.getint('votegametype', 'min_level_gametype')
        except:
            minLevel_gametype = 1
        self._adminPlugin.registerCommand(self, 'votegametype', minLevel_gametype, self.cmd_votegametype,  'vg')
        self._adminPlugin.registerCommand(self, 'gametypelist', 0, self.cmd_gametypelist,  'gamel')
        self._votes["gametype"] = GametypeVote()
        self._votes["gametype"].startup(self._adminPlugin,  self.console,  self.config)

        try:
            minLevel_maprotate = self.config.getint('votemaprotate', 'min_level_maprotate')
        except:
            minLevel_maprotate = 1
        self._adminPlugin.registerCommand(self, 'votemaprotate', minLevel_maprotate, self.cmd_votemaprotate,  'vr')
        self._votes["maprotate"] = MaprotateVote()
        self._votes["maprotate"].startup(self._adminPlugin,  self.console,  self.config)

        try:
            minLevel_mapgametype = self.config.getint('votemapgametype', 'min_level_mapgametype')
        except:
            minLevel_mapgametype = 1       
        self._adminPlugin.registerCommand(self, 'votemapgametype', minLevel_mapgametype, self.cmd_votemapgametype,  'vmg')
        self._votes["mapgametype"] = MapGametypeVote()
        self._votes["mapgametype"].startup(self._adminPlugin,  self.console, self.config, self._votes["map"], self._votes["gametype"])

    def cmd_maplist(self,  data,  client,  cmd=None):
        client.message("Maps available: " + ", ".join(self._votes["map"]._mapList))
  
    def cmd_gametypelist(self,  data,  client,  cmd=None):
        client.message("Gametypes available: " + ", ".join(self._votes["gametype"]._gametypeList))
  
    def pre_vote(self,  client):
        if self._in_progress:
            client.message("A vote is already in progress, wait until it finishes")
            return False
        
        if client.var(self,  'holding_vote').value:
            client.message("You have to wait between failed votes!")
            return False
        return True


    def cmd_votekick(self, data, client, cmd=None):
        """\
        <name> <motive> - call a votekick on that player for that motive
        """
        if not self.pre_vote(client):
            return False
        
        self._currentVote = self._votes["kick"]
        
        if not self._currentVote.start_vote(data, client):
            return False
        
        self.go_vote(client)

    def cmd_votemap(self, data, client, cmd=None):
        """\
        <map> - call a votemap for that map
        """
        if not self.pre_vote(client):
            return False
        
        self._currentVote = self._votes["map"]

        if not self._currentVote.start_vote(data, client):
            return False
        
        self.go_vote(client)

    def cmd_votegametype(self, data, client, cmd=None):
        """\
        <gametype> - call a votegametype for that gametype
        """
        if not self.pre_vote(client):
            return False
        
        self._currentVote = self._votes["gametype"]

        if not self._currentVote.start_vote(data, client):
            return False
        
        self.go_vote(client)

    def cmd_votemaprotate(self, data, client, cmd=None):
        """\
        call a maprotate, this will skip the current map
        """
        if not self.pre_vote(client):
            return False
        
        self._currentVote = self._votes["maprotate"]

        if not self._currentVote.start_vote(data, client):
            return False
        
        self.go_vote(client)

    def cmd_votemapgametype(self, data, client, cmd=None):
        """\
        <map> <gametype> - call a votemap and a votegametype
        """
        if not self.pre_vote(client):
            return False
        
        self._currentVote = self._votes["mapgametype"]

        if not self._currentVote.start_vote(data, client):
            return False
        
        self.go_vote(client)

    def go_vote(self,  client):
        self._caller = client
        self._in_progress = True
        self._times = self._vote_times
        self._no = 0
        self._vetoed = 0
        
        self._yes = 1
        client.var(self,  'voted').value = True #The caller of the vote votes yes by default
        
        reason = self._currentVote.vote_reason()
        self.console.say("Calling a vote " + reason)
        self.console.say("Type ^2!vy ^7to vote ^2yes^7, ^1!vn ^7to vote ^1no")
        self.console.cron + b3.cron.OneTimeCronTab(self.update_vote,  "*/%s" %self._vote_interval_announcements)
    

    def cmd_veto(self, data, client, cmd=None):
        """\
        Cancel current vote
        """
        self._vetoed = 1

    def update_vote(self):
        if not self._vetoed:
            reason = self._currentVote.vote_reason()
            self.console.say("[%d/%d] Voting " % (self._vote_times - self._times + 1,  self._vote_times) + reason)
            self.console.say("Type ^2!vy ^7to vote ^2yes^7, ^1!vn ^7to vote ^1no")
            self.console.say("^2Yes: %s^7, ^1No: %s" %(self._yes,  self._no))
            self._times -= 1
            if self._times > 0:
                self.console.cron + b3.cron.OneTimeCronTab(self.update_vote,  "*/%s" %self._vote_interval_announcements)
            else:
                self.console.cron + b3.cron.OneTimeCronTab(self.end_vote,  "*/1")
        else:
            self.console.say("Vote ^1vetoed!")
            self._in_progress = False
            self._currentVote = None
    
    def end_vote(self):
        self.console.say("Vote ended")
        self._in_progress = False
        self.console.say("^2Yes: %s^7, ^1No: %s" %(self._yes,  self._no))
        if self._yes > self._no:
            if self._yes >= self._vote_minvotes:
                self._currentVote.end_vote_yes(self._yes,  self._no)
            else:
                self._caller.message('^7Vote failed. Too few people voted ^2yes')
        else:
            self._currentVote.end_vote_no(self._yes,  self._no)
            #The vote failed, the caller can't call another vote for a while
            self._caller.var(self,  'holding_vote').value = True
            temp = self._caller
            def let_caller_vote():
                self.debug("clearing %s" % temp.exactName)
                temp.var(self,  'holding_vote').value = False
            
            self.console.cron + b3.cron.OneTimeCronTab(let_caller_vote,  0, "*/%s" %self._vote_interval_failed)
        
        self._in_progress = False
        self._currentVote = None
    
        for c in self.console.clients.getList():
            c.var(self,  'voted').value = False

    def cmd_voteyes(self, data, client, cmd=None):
        if self.vote(client,  cmd):
            self._yes += 1
            cmd.sayLoudOrPM(client,  "Voted ^1YES")

    def cmd_voteno(self, data, client, cmd=None):
        if self.vote(client,  cmd):
            self._no += 1
            cmd.sayLoudOrPM(client,  "Voted ^2NO")
    
    def vote(self,  client,  cmd):
        if self._in_progress:
            if not client.var(self,  'voted').value:
                client.var(self,  'voted').value = True
                return True
            else:
                cmd.sayLoudOrPM(client,  "You already voted!")
        else:
            cmd.sayLoudOrPM(client,  "No vote in progress")
        return False

class KickVote(object):
    _adminPlugin = None
    console = None
    config = None
    
    _victim = None
    _caller = None
    _reason = None

    _modLevel = 20

    _tempban_duration = 2
    _tempban_percent  = 75

    def startup(self,  adminPlugin,  console,  config):
        """\
        Initialize plugin settings
        """

        self._adminPlugin = adminPlugin
        self.console = console
        self.config = config

        self._modLevel = self._adminPlugin.config.getint("settings","admins_level")   
   
        self._tempban_percent = self.config.getint('votekick', 'tempban_percent')
        self._tempban_duration = self.config.getint('votekick', 'tempban_duration')
        
    def start_vote(self,  data,  client):
        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False
        if not m[1]:
            client.message('^7Invalid parameters, must provide a reason!')
            return False            
        if len(m[1]) < 3:
            client.message("^7You should write a better motive")
        
        cid = m[0]
        sclient = self._adminPlugin.findClientPrompt(cid, client)
        if not sclient:
            return False
            
        if sclient.maxLevel >= self._modLevel:
            client.message("You can't kick an admin! Owned :)")
            return False
        
        self._caller = client
        self._victim = sclient
        self._reason = m[1]
        return True

    def vote_reason(self):
        return "against ^3%s because ^3%s" % (self._victim.exactName,  self._reason)
    
    def end_vote_yes(self,  yes,  no):
        self.console.say("^1KICKING ^3%s" %self._victim.exactName)
        self._victim.kick("Voted out",  self._caller)
        if self._tempban_duration and ((yes*100.0 / no) > self._tempban_percent):
            self._victim.tempban("", "Voted out", self._tempban_duration, self._caller)
        self._victim = None

    def end_vote_no(self,  yes,  no):
        self.console.say("Player is ^2safe!")
        self._victim = None


class MapVote:
    _adminPlugin = None
    console = None
    config = None

    _mapList = []
    _map= None

    def startup(self,  adminPlugin,  console,  config):
        """\
        Initialize plugin settings
        """

        self._adminPlugin = adminPlugin
        self.console = console
        self.config = config  

        f = open(self.config.getpath('votemap',  'mapfile'))
        for line in f:
            self._mapList.append(line.strip())
            

    def start_vote(self,  data,  client):
        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False
        if not m[0]:
            client.message('^7Invalid parameters, must provide a map to vote!')
            return False
            
        s = m[0]
        matched = False
        
        for map in self._mapList:
            if s == map:
                self._map  = map
                if matched:
                    client.message('^7More than one map matches the name, be more specific')
                    return False
                matched = True
                
        if not matched:
            client.message('^7No map matched that name. Please use: !maplist')
        return matched

    def vote_reason(self):
        return "to change map to ^3%s" % (self._map)

    def end_vote_yes(self,  yes,  no):
        self.console.say("^1Changing map to ^3%s" %self._map)
        time.sleep(2)
        self.console.write("map %s" %self._map)

    def end_vote_no(self,  yes,  no):
        self.console.say("Map ^2stays!")
    
class GametypeVote:
    _adminPlugin = None
    console = None
    config = None

    _gametypeList = []
    _gametype= None

    def startup(self,  adminPlugin,  console,  config):
        """\
        Initialize plugin settings
        """

        self._adminPlugin = adminPlugin
        self.console = console
        self.config = config 
        
        f = open(self.config.getpath('votegametype',  'gametypefile'))
        for line in f:
            self._gametypeList.append(line.strip())
            

    def start_vote(self,  data,  client):
        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False
        if not m[0]:
            client.message('^7Invalid parameters, must provide a gametype to vote!')
            return False
            
        s = m[0]
        matched = False
        
        for gametype in self._gametypeList:
            if s == gametype:
                self._gametype  = gametype
                if matched:
                    client.message('^7More than one gametype matches the name, be more specific')
                    return False
                matched = True
                
        if not matched:
            client.message('^7No gametype matched that name. Please use: !gametypelist')
        return matched

    #rewrite function below later
    def start_vote_mapgametype(self,  data,  client):
        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters')
            return False
        if not m[1]: # only changed: 0 to 1
            client.message('^7Invalid parameters, must provide a gametype to vote!')
            return False
            
        s = m[1] # only changed: 0 to 1
        matched = False
        
        for gametype in self._gametypeList:
            if s == gametype:
                self._gametype  = gametype
                if matched:
                    client.message('^7More than one gametype matches the name, be more specific')
                    return False
                matched = True
                
        if not matched:
            client.message('^7No gametype matched that name. Please use: !gametypelist')
        return matched

    def vote_reason(self):
        return "to change gametype to ^3%s" % (self._gametype)

    def end_vote_yes(self,  yes,  no):
        self.console.say("^1Changing gametype to ^3%s" %self._gametype)
        self.console.write("g_gametype %s" %self._gametype)
        time.sleep(2)
        self.console.write("map_restart")

    def end_vote_no(self,  yes,  no):
        self.console.say("Gametype ^2stays!")

class MaprotateVote:
    _adminPlugin = None
    console = None
    config = None

    _data = None
    _client = None

    def startup(self,  adminPlugin,  console,  config):
        """\
        Initialize plugin settings
        """

        self._adminPlugin = adminPlugin
        self.console = console
        self.config = config 

    def start_vote(self,  data,  client):
        self._data = data
        self._client = client
        return True

    def vote_reason(self):
        return "to change to next map (map rotate)"

    def end_vote_yes(self,  yes,  no):
        self.console.say("^1Map ^3rotate to next map")
        self._adminPlugin.cmd_maprotate(self, self._client, self._client)

    def end_vote_no(self,  yes,  no):
        self.console.say("Current map ^2stays!")



class MapGametypeVote:
    _adminPlugin = None
    console = None
    config = None
    
    _mapVoteClass = None
    _gametypeVoteClass = None

    def startup(self,  adminPlugin,  console,  config, mapVote, gametypeVote):
        """\
        Initialize plugin settings
        """

        self._adminPlugin = adminPlugin
        self.console = console
        self.config = config
        self._mapVoteClass = mapVote        
        self._gametypeVoteClass = gametypeVote

    def start_vote(self,  data,  client):        
        if self._gametypeVoteClass.start_vote_mapgametype(data, client) and self._mapVoteClass.start_vote(data, client):
            return True
        else:
            return False

    def vote_reason(self):
        return "^1to change map to ^3%s ^1and  gametype to ^3%s" % (self._mapVoteClass._map, self._gametypeVoteClass._gametype)

    def end_vote_yes(self,  yes,  no):
        self.console.say("^1Changing map to ^3%s and gametype to ^3%s" %(self._mapVoteClass._map, self._gametypeVoteClass._gametype))
        self.console.write("g_gametype %s" %self._gametypeVoteClass._gametype)
        time.sleep(2)
        self.console.write("map %s" %self._mapVoteClass._map)

    def end_vote_no(self,  yes,  no):
        self.console.say("Map and Gametype ^2stays!")
