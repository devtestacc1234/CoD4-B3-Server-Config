# -*- coding: utf-8 -*-
# b3/plugins/antinoob.py
#
# Gamers 4 Gamers (http://g4g.pl)
# Copyright (C) 2009 Anubis
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
# $Id: antinoob.py 89 2008-06-06 22:38:34Z Anubis $
#
# CHANGELOG
#    06/06/2008 - 1.0.0 - Anubis
#    -- first version based on Antinoob plugin by MiLcH
#    07/06/2008 - 1.0.1 - Anubis
#    -- fixed airstrike issues 
#    23/12/2008 - 1.0.2 - Anubis
#    -- Damage = warn 
#    23/12/2008 - 1.0.3 - Anubis
#    -- New config - weapons/maps
#    12/02/2009 - 1.0.4 - Anubis
#    -- New config - MOD settings
#    16/02/2009 - 1.0.5 - Anubis
#    -- New config - MOD settings as restriction
#    26/03/2009 - 1.0.6 - Anubis
#    -- New config , new wepons handling
#    11/05/2009 - 1.0.7 - Anubis
#    -- Errors fixing
#    10/12/2009 - 1.0.8 - Melroy
#    -- Errors fixing

__version__ = '1.0.8'
__author__  = 'Anubis'
from b3 import clients
import b3, string, re, threading
import b3.events
import b3.plugin


class WeaponInfo:
    _weaponName = ""
    _mod = ""
    
class MapInfo:
    _mapName = None
    _duration = 10   

#--------------------------------------------------------------------------------------------------
class AntinoobPlugin(b3.plugin.Plugin):
    _adminPlugin = None
    _currentMap = None
    _bannedweaponswarn = []
    _bannedweaponskick = []    
    _weaponstimedwarn = []    
    _weaponstimedkick = []    
    _maps = []
    _warnduration = 10
    _warndurationdefault = 10
    _warningrule = 'rule10'
    _unlockmessage = '^3 %s seconds passed - ^3all weapons unlocked!!!'
    _infomessage = '^3 No nades, airstrike, tubes ^5for %s seconds of the round!!!'
    _bannedonlyinfomessage = '^3 Please, No nades, airstrike, tubes !!!'

    def onStartup(self):
        self.registerEvent(b3.events.EVT_CLIENT_KILL)
        self.registerEvent(b3.events.EVT_CLIENT_DAMAGE)
        self.registerEvent(b3.events.EVT_GAME_ROUND_START) 
        self._adminPlugin = self.console.getPlugin('admin')

    def onLoadConfig(self):
        self.debug('Loading Configuration Started')
        self._warndurationdefault = self.config.getint('settings', 'warn_duration')
        self.debug('_warndurationdefault: ' + str(self._warndurationdefault))
        self._warningrule = self.config.get('settings', 'warning_rule')
        self._bannedwarningrule = self.config.get('settings', 'banned_warning_rule')
        if self._bannedwarningrule == '':
            self._bannedwarningrule = self._warningrule
        self._unlockmessage = self.config.get('settings', 'unlock_message')
        self._infomessage = self.config.get('settings', 'info_message')       
        self._bannedonlyinfomessage = self.config.get('settings', 'bannedonly_info_message')
        
        for e in self.config.get('weapon_timed_warn/weapon'):
            #name  = setting.get('name') 
            _wi = WeaponInfo()
            if e.text:
                _wi._weaponName = e.text
            else:
                _wi._weaponName = ""
            
            _wi._mod = e.get('mod')
            
            if (_wi._mod != "" or _wi._weaponName != ""):
                self.debug('Timed Warn - Weapon loaded: >' + _wi._weaponName + '< Mod:>' + _wi._mod + '<')
                self._weaponstimedwarn.append(_wi)
            else:
                self.debug('Timed Warn - Empty definition ignored')
                
        for e in self.config.get('weapon_timed_kick/weapon'):
            #name  = setting.get('name') 
            _wi = WeaponInfo()
            if e.text:
                _wi._weaponName = e.text
            else:
                _wi._weaponName = ""
            
            _wi._mod = e.get('mod')
            
            if (_wi._mod != "" or _wi._weaponName != ""):
                self.debug('Timed Kick - Weapon loaded: >' + _wi._weaponName + '< Mod:>' + _wi._mod + '<')
                self._weaponstimedkick.append(_wi)
            else:
                self.debug('Timed Kick - Empty definition ignored')   
                
        for e in self.config.get('weapon_banned_kick/weapon'):
            #name  = setting.get('name') 
            _wi = WeaponInfo()
            if e.text:
                _wi._weaponName = e.text
            else:
                _wi._weaponName = ""
            
            _wi._mod = e.get('mod')
            
            if (_wi._mod != "" or _wi._weaponName != ""):
                self.debug('Banned Kick - Weapon loaded: >' + _wi._weaponName + '< Mod:>' + _wi._mod + '<')
                self._bannedweaponskick.append(_wi)
            else:
                self.debug('Banned Kick - Empty definition ignored')                  
                
        for e in self.config.get('weapon_banned_warn/weapon'):
            #name  = setting.get('name') 
            _wi = WeaponInfo()
            if e.text:
                _wi._weaponName = e.text
            else:
                _wi._weaponName = ""
            
            _wi._mod = e.get('mod')
            
            if (_wi._mod != "" or _wi._weaponName != ""):
                self.debug('Banned Warn - Weapon loaded: >' + _wi._weaponName + '< Mod:>' + _wi._mod + '<')
                self._bannedweaponswarn.append(_wi)
            else:
                self.debug('Banned Warn - Empty definition ignored')                     
            
        self._maps = []
        for e in self.config.get('maps/map'):
            #name  = setting.get('name') 
            _mi = MapInfo();
            _mi._mapName = e.get('name')
            _mi._duration = int(e.text.strip())
            self.debug('Map parsed: ' + _mi._mapName + ' duration: ' + str(_mi._duration))
           
            self._maps.append(_mi);
        
        self.debug('Loading Configuration Finished')
        return
        
                
    def _usingWeaponsAllowed(self):
        self.debug(self._unlockmessage % self._warnduration) 
        self.console.say(self._unlockmessage % self._warnduration)
        return
    
    def checkWeapon(self, weaponname, mod, player):
        if self.console.game.roundTime() <= self._warnduration:
            self.debug(weaponname + ' / ' + mod + ' - in warnduration: ' + str(self.console.game.roundTime()))
            #--------------------------------------------------------------------------------------#
            for weaponInfo in self._weaponstimedwarn:
                try:
                    if weaponInfo._weaponName == weaponname:
                        if(weaponInfo._mod == ""):
                            self.debug('Temporary Restricted Weapon: ' + str(weaponname) + ' - Round time: ' + str(self.console.game.roundTime()))
                            self.warnPlayerForTmpRestrictedWeapon(player)
                            return
                        else:
                            if(weaponInfo._mod == mod):
                                self.debug('Temporary Restricted Weapon: ' + str(weaponname) + ' Mod: ' + str(mod) + ' - Round time: ' + str(self.console.game.roundTime()))
                                self.warnPlayerForTmpRestrictedWeapon(player)
                                return
                            else:
                                return                
                    elif weaponInfo._weaponName == "":
                        if weaponInfo._mod == mod:
                            self.debug('Temporary Restricted MOD for weapon: ' + str(weaponname) + ' Mod: ' + str(mod) + ' - Round time: ' + str(self.console.game.roundTime()))
                            self.warnPlayerForTmpRestrictedWeapon(player)
                            return
                except:
                    self.debug('Unknown error while _weaponstimedwarn list processing')
            #--------------------------------------------------------------------------------------#
            for weaponInfo in self._weaponstimedkick:
                try:   
                    if weaponInfo._weaponName == weaponname:
                        if(weaponInfo._mod == ""):
                            self.debug('Temporary Restricted Weapon: ' + str(weaponname) + ' - Round time: ' + str(self.console.game.roundTime()))
                            self.kickPlayerForTmpRestrictedWeapon(player)
                            return
                        else:
                            if(weaponInfo._mod == mod):
                                self.debug('Temporary Restricted Weapon: ' + str(weaponname) + ' Mod: ' + str(mod) + ' - Round time: ' + str(self.console.game.roundTime()))
                                self.kickPlayerForTmpRestrictedWeapon(player)
                                return
                            else:
                                return
                    elif weaponInfo._weaponName == "":
                        if weaponInfo._mod == mod:
                            self.debug('Temporary Restricted MOD for weapon: ' + str(weaponname) + ' Mod: ' + str(mod) + ' - Round time: ' + str(self.console.game.roundTime()))
                            self.kickPlayerForTmpRestrictedWeapon(player)
                            return
                    
                except:
                    self.debug('Unknown error while _weaponstimedkick list processing')                                
        #--------------------------------------------------------------------------------------#
        for weaponInfo in self._bannedweaponswarn:
            try:            
                if weaponInfo._weaponName == weaponname:
                    if(weaponInfo._mod == ""):
                        self.debug('Banned Weapon: ' + str(weaponname) + ' - Round time: ' + str(self.console.game.roundTime()))
                        self.warnPlayerForBannedWeapon(player)
                        return
                    else:
                        if(weaponInfo._mod == mod):
                            self.debug('Banned Weapon: ' + str(weaponname) + ' Mod: ' + str(mod) + ' - Round time: ' + str(self.console.game.roundTime()))
                            self.warnPlayerForBannedWeapon(player)
                            return
                        else:
                            return
                elif weaponInfo._weaponName == "":
                    if weaponInfo._mod == mod:
                        self.debug('Banned MOD for weapon: ' + str(weaponname) + ' Mod: ' + str(mod) + ' - Round time: ' + str(self.console.game.roundTime()))
                        self.warnPlayerForBannedWeapon(player)
                        return
                
            except:
                self.debug('Unknown error while _bannedweaponswarn list processing')                                
        #--------------------------------------------------------------------------------------#
        for weaponInfo in self._bannedweaponskick:
            try:    
                if weaponInfo._weaponName == weaponname:
                    if(weaponInfo._mod == ""):
                        self.debug('Banned Weapon: ' + str(weaponname) + ' - Round time: ' + str(self.console.game.roundTime()))
                        self.kickPlayerForBannedWeapon(player)
                        return
                    else:
                        if(weaponInfo._mod == mod):
                            self.debug('Banned Weapon: ' + str(weaponname) + ' Mod: ' + str(mod) + ' - Round time: ' + str(self.console.game.roundTime()))
                            self.kickPlayerForBannedWeapon(player)
                            return
                        else:
                            return
                elif weaponInfo._weaponName == "":
                    if weaponInfo._mod == mod:
                        self.debug('Banned MOD for weapon: ' + str(weaponname) + ' Mod: ' + str(mod) + ' - Round time: ' + str(self.console.game.roundTime()))
                        self.kickPlayerForBannedWeapon(player)
                        return
            except:
                self.debug('Unknown error while _bannedweaponskick list processing')                                
                        
        #--------------------------------------------------------------------------------------#          
        return
        
        
    #---------------------------------------------------------------------------#
    # Penalties  / Kick  
    #---------------------------------------------------------------------------#
    def kickPlayerForBannedWeapon(self, player):
        if player:
            warningmsg = self.getKickWarningForBannedWeapon()
            self.debug('player.kick: ' + str(player.name) + ' Warn: ' + str(warningmsg))
            player.kick(warningmsg)
        return
        
    def kickPlayerForTmpRestrictedWeapon(self, player):
        if player:
            warningmsg = self.getKickWarningForTmpRestrictedWeapon()
            self.debug('player.kick: ' + str(player.name) + ' Warn: ' + str(warningmsg))
            player.kick(warningmsg, '', none)
        return        
    #---------------------------------------------------------------------------#
    # Penalties  / Warn  
    #---------------------------------------------------------------------------#
    def warnPlayerForTmpRestrictedWeapon(self, player):
        if player:
            warningrule = self.getWarningRuleForTmpRestrictedWeapon()
            self.debug('[TMP]WarnClient: ' + str(player.name) + ' WarnRule: ' + str(warningrule))
            self._adminPlugin.warnClient(player, warningrule , None, False)
        return    

    def warnPlayerForBannedWeapon(self, player):
        if player:
            warningrule = self.getWarningRuleForBannedWeapon()
            self.debug('[Banned]WarnClient: ' + str(player.name) + ' WarnRule: ' + str(warningrule))
            self._adminPlugin.warnClient(player, self._warningrule , None, False)
        return  
    #---------------------------------------------------------------------------#
    # WARNING RULES    
    #---------------------------------------------------------------------------#
    def getWarningRuleForBannedWeapon(self):
        return self._bannedwarningrule
    
    
    def getWarningRuleForTmpRestrictedWeapon(self):  
        return self._warningrule
    #---------------------------------------------------------------------------#
    
    #---------------------------------------------------------------------------#
    # Kick Messages   
    #---------------------------------------------------------------------------#
    def getKickWarningForBannedWeapon(self):
        defwarning = "Do not use banned weapon!"
        try:
            duration, warning = self._adminPlugin.getWarning(self._bannedwarningrule)
        except:
            warning = defwarning
        
        return warning
        
    def getKickWarningForTmpRestrictedWeapon(self):  
        defwarning = "Do not use restricted weapon!"
        try:
            duration, warning = self._adminPlugin.getWarning(self._warningrule)
        except:
            warning = defwarning
        
        return warning
    #---------------------------------------------------------------------------# 

    def onEvent(self, event):
        if event.type == b3.events.EVT_CLIENT_KILL or event.type ==  b3.events.EVT_CLIENT_DAMAGE:
            weaponname = event.data[1]
            mod = event.data[3]
            self.checkWeapon(weaponname, mod, event.client)

        elif event.type == b3.events.EVT_GAME_ROUND_START:
            if self._currentMap == None or self.console.game.mapName != self._currentMap:
                self._currentMap = self.console.game.mapName
                self.debug('New Map: ' + str(self._currentMap))
                self._warnduration = self._warndurationdefault
                for mapinfo in self._maps:
                    if(mapinfo):
                        if self._currentMap == mapinfo._mapName:
                            self._warnduration = mapinfo._duration
                            self.debug('New Duration: ' + str(self._warnduration))
                            break
            if len(self._weaponstimedwarn) > 0 or len(self._weaponstimedkick) > 0:
                self.debug(self._infomessage % self._warnduration)
                self.console.say(self._infomessage % self._warnduration)
                t = threading.Timer(self._warnduration+1, self._usingWeaponsAllowed)
                t.start()
            if len(self._bannedweaponswarn) > 0 or len(self._bannedweaponskick) > 0:
                self.debug(self._bannedonlyinfomessage)
                self.console.say(self._bannedonlyinfomessage)                
            return 
