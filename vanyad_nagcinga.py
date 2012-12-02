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

import time
import pipes
import livestatus
from vanyad_shelves import *

class ConnectLivestatus:
    """The most fundamental class. Nearly all stuff here shall start from this."""
    socket_path=None
    def __init__(self):
	config=ReadConf()
	monitor_dir=config.monitor_dir
	self.socket_path=config.socket_live


    def get_query(self,get,columns,filtering,*args):
	command=[]
	c_list=[]
	output_str='OutputFormat: python\n'
	command=['GET '+get,'Columns: '+' '.join([column for column in columns])]+['Filter: '+fltr for fltr in filtering]+[arg for arg in args]+[output_str]
	get_command='\n'.join(command)
	status=livestatus.SingleSiteConnection(self.socket_path).query_table(get_command)
	return status

