#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# VanyaD - Copyright - Ektanoor <ektanoor@bk.ru> 2012
#
# This is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  VanyaD is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# ails.  You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.

import shelve
import ConfigParser
from collections import *

class ReadConf:
    config=None
    system=None
    monitor_dir=None
    socket_live=None
    socket_command=None

    def __init__(self):
	config=ConfigParser.RawConfigParser()
	config.read('vanyad.conf')
	if config.has_option('monitor','system'): self.system=config.get('monitor', 'system')
	else: self.system='icinga'
	if config.has_option('monitor','monitor_dir'): self.monitor_dir=config.get('monitor', 'monitor_dir')
	else: self.monitor_dir='/var/lib/'+self.system
	if config.has_option('monitor','socket_live'): self.socket_path=config.get('monitor', 'socket_live')
	else: self.socket_live='unix:'+self.monitor_dir+'/rw/live'


class OpenShelves:
    """Things like blacklists, historical records and so. We need some memory here..."""
    lsts=[]
    osm={}
    sv=None
    working_shelve=None
    def __init__(self,shelve_name):
	self.sv = shelve.open(shelve_name)
	self.working_shelve=shelve_name
	if shelve_name=='blacklist':
	    blacklists=('hosts','services')
	    for blacklist in blacklists:
		if self.sv.has_key(blacklist): self.lsts+=self.sv[blacklist]
	if shelve_name=='osm':
	    if self.sv.has_key('osm'): self.osm=self.sv['osm']

    def __del__(self):
	if self.working_shelve=='osm': self.sv['osm']=self.osm
	self.sv.close()

