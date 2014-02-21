###################################################################################
#
# Plugin for B3 (www.bigbrotherbot.com)
# Countryfilter code by www.xlr8or.com (mailto:xlr8or@xlr8or.com)
# Geowelcome plugin (c) 2009 SGT
#
# This program is free software and licensed under the terms of
# the GNU General Public License (GPL), version 2.
#
# http://www.gnu.org/copyleft/gpl.html
#
###################################################################################

Geowelcome (v1.1.x) for B3
###################################################################################
This plugin show the country every time a user connect.
It also includes a command to show where a user is connecting from.

Requirements:
###################################################################################

- B3 version 1.2.2 or higher

Installation:
###################################################################################

1. Unzip the contents of this package into your B3 folder. It will
place the .py file in b3/extplugins and the config file .xml in
your b3/extplugins/conf folder. Libraries will be located in your B3
root folder.

2. Open the .xml file with your favorite editor and modify the
settings if you want them different. Do not edit the settingnames
for they will not function under a different name.

3. Open your B3.xml file (in b3/conf) and add the next line in the
<plugins> section of the file:

<plugin name="geowelcome" priority="12" config="@b3/extplugins/conf/geowelcome.xml"/>

Remove the original welcome plugin:

<plugin name="welcome" ...... />

The number 12 in this just an example. Make sure it fits your
plugin list.

Memcache:
###################################################################################

To enable memcache support install python-memcached and edit geoip.py replacing
MEMCACHE_HOST with your memcache host.

For example: 
  MEMCACHE_HOST = '127.0.0.1:11211'
  
ipinfodb API KEY
###################################################################################

If you want to use your custom API KEY. Create an account at ipinfodb.com and edit
geoip.py replacing API_KEY for your custom key.
You are free to use the provied KEY though.

Changelog
###################################################################################
v1.0.0         : Initial release
v1.0.1	       : Fix encoding issues
v1.0.2         : Add broadcast
v1.0.3         : Do not broadcast disconnected clients
v1.0.4         : Add custom message format
v1.0.5         : Add !greeting command removed from admin plugin since b3 1.3.x
		 Include own json module for geoip library (removes simplejson dependency)
v1.0.6	       : Add !whereis command for already connected players
v1.1.0         : Add countryfilter functions from countryfilter plugin by xlr8or
v1.1.3         : Some fixes. New service API and memcache support.
###################################################################################
