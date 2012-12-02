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

class NetconAlert:
    """Presently this is only a stub, to record the temporary version of alert hierarchy
    """
    netcon={
	    0:'Zero Warns',
	    1:'Only Warns',
	    2:'Minor Problems',
	    3:'Generic Problems',
	    4:'Major Problems',
	    5:'Critical - Nodes',
	    6:'Critical - Segments',
	    7:'Critical - Networks',
	    8:'Critical - Internet',
	    9:'Critical - No Access',
	    10:'Broken Arrow'
	    }

    def __init__(self):
	pass

class ReadConf:
    config=None
    system=None
    monitor_dir=None
    socket_live=None
    socket_command=None
    snmp_community=None

    debug=0

    xmpp_address=None
    xmpp_command=None
    xmpp_server=None
    xmpp_user=None
    xmpp_passwd=None

    sms_address=None
    sms_command=None
    check_smsd=None
    script=None
    sms_zombies=None

    mail_address=None
    mail_server=None
    mail_sender=None
    
    contacts=[]

    def __init__(self):
	config=ConfigParser.RawConfigParser()
	config.read('vanyad.conf')
	if config.has_option('monitor','user'): self.user=config.get('monitor', 'user')
	else: self.user='vanyad'
	if config.has_option('monitor','system'): self.system=config.get('monitor', 'system')
	else: self.system='icinga'
	if config.has_option('monitor','monitor_dir'): self.monitor_dir=config.get('monitor', 'monitor_dir')
	else: self.monitor_dir='/var/lib/'+self.system
	if config.has_option('monitor','socket_live'): self.socket_path=config.get('monitor', 'socket_live')
	else: self.socket_live='unix:'+self.monitor_dir+'/rw/live'
	if config.has_option('monitor','socket_command'): self.socket_command=config.get('monitor', 'socket_command')
	else: self.socket_command=self.monitor_dir+'/rw/'+self.system+'.cmd'

	if config.has_option('contacts','users'): 
	    contact_string=config.get('contacts', 'users')
	    self.contacts=contact_string.split(',')
	else: self.user='admin'

	if config.has_option('contacts','monitors'): 
	    contact_string=config.get('contacts', 'monitors')
	    self.monitors=contact_string.split(',')
	else: self.monitors='admin'

	if config.has_option('geo','no_data'): 
	    self.no_data=config.get('geo', 'no_data')
	else: self.no_data='0,0'

	if config.has_option('geo','step'): 
	    self.step=float(config.get('geo', 'step'))
	else: self.step=0.0

	if config.has_option('snmp','community'): self.snmp_community=config.get('snmp', 'community')
	else: self.snmp_community='public'

	if config.has_option('comms','debug'): self.debug=config.get('comms', 'debug')

	if config.has_option('xmpp','address'): self.xmpp_address=config.get('xmpp', 'address')
	else: self.xmpp_address='address1'
	if config.has_option('xmpp','server'): self.xmpp_server=config.get('xmpp', 'server')
	else: raise NoOptions('Jabber server not specified')
	if config.has_option('xmpp','user'): self.xmpp_user=config.get('xmpp', 'user')
	else: raise NoOptions('Jabber user not specified')
	if config.has_option('xmpp','passwd'): self.xmpp_passwd=config.get('xmpp', 'passwd')
	else: raise NoOptions('Jabber password not specified')

	if config.has_option('sms','address'): self.sms_address=config.get('sms', 'address')
	else: self.sms_address='pager'
	if config.has_option('sms','check_smsd'): self.check_smsd=config.get('sms', 'check_smsd')
	else: self.check_smsd=0
	if config.has_option('sms','script'): self.script=config.get('sms', 'script')
	else: self.script='/usr/bin/sendsms'

	if config.has_option('sms','zombies'): self.sms_zombies=config.get('sms', 'zombies')
	else: self.sms_zombies=0

	if config.has_option('mail','address'): self.mail_address=config.get('mail','address')
	else: self.mail_address='email'
	if config.has_option('mail','server'): self.mail_server=config.get('mail','server')
	else: self.mail_server='relay'
	if config.has_option('mail','sender'): self.mail_sender=config.get('mail','sender')
	else: self.mail_sender='vanyad'




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

