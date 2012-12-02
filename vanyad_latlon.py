#!/usr/bin/python
# -*- coding: utf-8; py-indent-offset: 4 -*-
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

#from __future__ import unicode_literals
from __future__ import print_function
from vanyad_nagcinga import *
from vanyad_shelves import *
from collections import defaultdict
from unidecode import unidecode
import httplib
import urllib
import shelve
import json
import sys
import os


class GenerateCoordinates(ConnectLivestatus):
    """This class grabs addresses from custom variable _physaddr...
    """

    config=None
    status=[]
    lat={}
    lon={}
    mapdata=None
    default_lat=None
    default_lon=None

    def __init__(self):
	self.config=ReadConf()
	ConnectLivestatus.__init__(self)
	self.mapdata=OpenShelves('osm')
	coors=self.config.no_data.split(',')
	self.default_lat=float(coors[0])
	self.default_lon=float(coors[1])

    def __del__(self):
	self.mapdata.__del__()

    def grab_addresses(self):
	location_keys=None
	postcode=None

#We need these keys to avoid beating OSM with repeated queries
	if self.mapdata: location_keys=self.mapdata.osm.keys()

#Get data from Nagios/Icinga through livestatus.
#String format is country_code,state,city/county,street/road,<postcode>
#postcode is a safeguard for ambiguities on some cities, ex. 7 streets with the same name.
#Other identificators are too weak to solve such ambiguities.
#It shall be used only when such ambiguities occur.
	self.locations=defaultdict(list)
	status=self.get_query('hosts',('host_name','custom_variables'),())
	for host_name,custom_variables in status:
	    if 'LOCATION' in custom_variables:
		self.locations[custom_variables['LOCATION']].append(host_name)

#No maps here. These requests get OSM data only.
	conn=httplib.HTTPConnection("nominatim.openstreetmap.org")
	for location in self.locations:
	    if location in location_keys: continue	#Avoid requests for data we already have
	    loc_details=location.split(',')
	    country=loc_details[0]
	    state=loc_details[1]
	    county=loc_details[2]
	    road=loc_details[3]
	    house_number=loc_details[4]
	    if len(loc_details)==6: postcode=loc_details[5]
	    url='/search?q=+'+house_number+'+'+road+',+'+county
	    if postcode: url+=',+'+postcode
	    url+='&format=json&countrycodes='+country+'&polygon=0&addressdetails=1'
	    url=urllib.quote(url.encode('utf-8'),',/+=&?')
	    conn.request('GET',url)
	    response=conn.getresponse()
	    if response.status==200:
		data=response.read()
		if not data: print('No data for: '+str(location)+'\n',file=f)
		else:
		    data=json.loads(data)
		    self.mapdata.osm[location]=data
	conn.close()

#On Nominatim fields inside records do not seem to be strictly positioned. Besides, the system is flexible enough to give data that partially fits the query.
#So, to avoid multiple conflicts, first we read a whole record and then check.
#The gathering algorithm here corresponds to the way Nominatim stores data on Russian entities. In other countries your mileage may vary.
    def fill_data(self):
	self.houses=defaultdict(list)
	self.roads=defaultdict(list)
	self.suburbs=defaultdict(list)
	self.districts=defaultdict(list)
	self.cities=defaultdict(list)
	self.counties=defaultdict(list)
	self.administratives=defaultdict(list)
	self.countries=defaultdict(list)
	self.hosts=defaultdict(tuple)
	ambiguous_data='ambiguous_data.txt'
#Check ambiguous_data.txt for unexact or questionable data
	f=open(ambiguous_data,'w')
	for location in self.mapdata.osm:
	    postcode=None
	    loc_details=location.split(',')
	    road=loc_details[3]
	    house_number=loc_details[4]
	    if len(loc_details)==6: postcode=loc_details[5]
	    for item in self.mapdata.osm[location]:
		cur_country_code=None
		cur_country=None
		cur_administrative=None
		cur_state=None
		cur_city=None
		cur_county=None
		cur_city_district=None
		cur_suburb=None
		cur_road=None
		cur_house_number=None
		cur_postcode=None
		for item2 in item:
		    other_fields={}
		    if item2=='lat': cur_lat=float(item[item2])
		    if item2=='lon': cur_lon=float(item[item2])
		    if item2=='boundingbox': cur_bbox=item[item2]
		    if item2=='address':
			for detail in item[item2]:
			    i=item[item2][detail].decode('utf-8')
			    if detail=='country_code': cur_country_code=i
			    elif detail=='country': cur_country=i
			    elif detail=='administrative': cur_administrative=i
			    elif detail=='state': cur_state=i
#In certain regions county=city, with no 'city' on the records. Why, I really don't know. But one of these places is just here.
			    elif detail=='county': cur_county=i
			    elif detail=='city': cur_city=i
#From docs, it seems that field 'village' always overlaps with 'city'. Presently there is no need to differ these fields
			    elif detail=='village': cur_city=i
			    elif detail=='city_district': cur_city_district=i
#Here state_district is much the same as city_district, the difference is that it is applied to rural areas.
			    elif detail=='state_district': cur_city_district=i
			    elif detail=='suburb': cur_suburb=i
			    elif detail=='road': cur_road=i
			    elif detail=='house_number': cur_house_number=i
			    elif detail=='postcode': cur_postcode=i
#Some records have custom fields. We still have to study them.
			    else: other_fields[detail]=i

		self.lat[location]=cur_lat
		self.lon[location]=cur_lon

		if other_fields:
		    print('Custom fields found for '+str(location)+':\n',file=f)
		    for field in other_fields: print(field+': '+other_fields[field]+'\n',file=f)
		    print(str(self.mapdata.osm[location])+'\n',file=f)

		msg=None
		if not cur_road: print('No road for: '+str(location)+'\n'+str(self.mapdata.osm[location])+'\n',file=f)
		elif road not in cur_road: print('Wrong road for: '+str(location)+'\n'+str(cur_road)+'\n'+str(self.mapdata.osm[location])+'\n',file=f)
		if not cur_house_number: msg='No house number for: '+str(location)+'\n'+str(self.mapdata.osm[location])+'\n'
		elif house_number!=cur_house_number[:len(house_number)]:
		    msg='Wrong house number for: '+str(location)+'\n'+str(cur_house_number)+'\n'+str(self.mapdata.osm[location])+'\n'
		elif postcode and postcode!=cur_postcode: pass
		else: continue
		if msg: print(msg,file=f)

#It looks crazy? Yes, because IT IS crazy! Can you realize a city with 7 completely different roads, officialy carrying one and the same name? Or how many Moscows exist on Earth? 
#Even Paris has a "twin" in the Urals. And it does not end here! Many big cities in ex-USSR have a "Moscow district". And what about something as a state or province? 
#Searching for "just" California will give you three states in two different countries. Much as "just" Washington may stubbornly show some city called Seattle.
#Portugal had a province called "Estremadura", which some use till today and sounding nearly as the Spanish "Extremadura". Mozambique has a "Gaza" province.
#And even countries are not far from this, just try to look for "Guinea" or "Korea".

	    for host in self.locations[location]:
		self.hosts[host]=(cur_lat,cur_lon,cur_bbox,cur_country_code,cur_country,cur_administrative,
		    cur_state,cur_county,cur_city,cur_city_district,cur_suburb,cur_road,cur_house_number,cur_postcode)
		if postcode: self.houses[(cur_country_code,cur_administrative,cur_state,cur_county,cur_city,cur_city_district,cur_suburb,cur_road,cur_house_number,cur_postcode)].append(host)
		else: self.houses[(cur_country_code,cur_administrative,cur_state,cur_county,cur_city,cur_city_district,cur_suburb,cur_road,cur_house_number)].append(host)
		if postcode: self.roads[(cur_country_code,cur_administrative,cur_state,cur_county,cur_city,cur_road,cur_postcode)].append(host)
		else: self.roads[(cur_country_code,cur_administrative,cur_state,cur_county,cur_city,cur_road)].append(host)
		self.suburbs[(cur_country_code,cur_administrative,cur_state,cur_county,cur_city,cur_city_district,cur_suburb)].append(host)
		self.districts[(cur_country_code,cur_administrative,cur_state,cur_county,cur_city,cur_city_district)].append(host)
		self.cities[(cur_country_code,cur_administrative,cur_state,cur_county,cur_city)].append(host)
		self.counties[(cur_country_code,cur_administrative,cur_state,cur_county)].append(host)
		self.administratives[(cur_country_code,cur_administrative)].append(host)
		self.countries[(cur_country,cur_country_code)].append(host)
	f.close()

    def make_generic(self):
	outcasts='outcasts-generic.txt'
	locations='locations.txt'
	f=open(outcasts,'w')
	g=open(locations,'w')
	for location in self.locations:
	    for host in self.locations[location]:
		if location in self.lat:
		    nagvis=(host,location,str(self.lat[location]),str(self.lon[location]))
		    print(';'.join(nagvis),file=g)
		else: print(host,file=f)
	g.close()
	f.close()

    def do_nagvis_cfg(self,name,u_name,iconset,backend,width,height,border,zoom):
	global_cfg=[]
	global_cfg.append('define global {')
	global_cfg.append('    sources=geomap')
	global_cfg.append('    alias='+name)
	global_cfg.append('    iconset='+iconset)
	global_cfg.append('    backend_id='+backend)
	global_cfg.append('    source_file='+u_name)
	global_cfg.append('    width='+str(width))
	global_cfg.append('    height='+str(height))
	global_cfg.append('    geomap_border='+str(border))
	global_cfg.append('    geomap_zoom='+str(zoom))
	global_cfg.append('}')
	cfg='\n'.join(global_cfg)
	return cfg


    def create_nagvis_conf(self,resource,name,data):
	maps='./maps'
	geo='./geomap'
	iconset='std_small'
	backend='live_1'
	width=1600
	height=1400
	border=0.0
	zoom=10

	if not os.path.exists(maps): os.makedirs(maps)
	if not os.path.exists(geo): os.makedirs(geo)
	if not os.path.exists(maps+'/'+resource): os.makedirs(maps+'/'+resource)
	if not os.path.exists(geo+'/'+resource): os.makedirs(geo+'/'+resource)
	u_name=unidecode(name.decode('utf8'))
	u_name=u_name.replace("'","")
	u_name=u_name.replace("/","-")
	u_name=u_name.replace(".","")
	u_name=u_name.replace(' ','')
	m=open(maps+'/'+resource+'/'+u_name+'.cfg','w')
	cfg=self.do_nagvis_cfg(name,u_name,iconset,backend,width,height,border,zoom)
	print(cfg,file=m)
	m.close()
	g=open(geo+'/'+resource+'/'+u_name+'.csv','w')
	for host in data:
	    nagvis=(host,name,str(self.hosts[host][0]),str(self.hosts[host][1]))
	    print(';'.join(nagvis),file=g)
	g.close()


    def create_nagvis_geobase(self):
#Nodes that could have missed the criteria
	outcasts='outcasts.txt'

	f=open(outcasts,'w')
	for house in self.houses:
	    if len(house)==10:
		if house[-6]: city=house[-6]
		else: city=house[-7]
		if not house[-3]:
		    print('Errors@houses with - '+str(house),file=f)
		    continue
		else: name=str(house[0])+'-'+str(city)+'-'+str(house[-1])+'-'+str(house[-3])+'-'+str(house[-2])
	    else:
		if house[-5]: city=house[-5]
		else: city=house[-6]
		if not house[-2]:
		    print('Errors@houses with - '+str(house),file=f)
		    continue
		else: name=str(house[0])+'-'+str(city)+'-'+str(house[-2])+'-'+str(house[-1])
	    self.create_nagvis_conf('houses',name,self.houses[house])

	for road in self.roads:
	    if len(road)==7:
		if road[-4]: city=road[-4]
		else: city=road[-5]
		if not road[-2]: 
		    print('Errors@roads with - '+str(road),file=f)
		    continue
		else: name=str(road[0])+'-'+str(city)+'-'+str(road[-1])+'-'+str(road[-2])
	    else:
		if road[-3]: city=road[-3]
		else: city=road[-4]
		if not road[-1]: 
		    print('Errors@roads with - '+str(road),file=f)
		    continue
		else: name=str(road[0])+'-'+str(city)+'-'+str(road[-1])
	    self.create_nagvis_conf('roads',name,self.roads[road])

	for suburb in self.suburbs:
	    if not suburb[-1]: 
		print('Errors@suburbs with - '+str(suburb),file=f)
		continue
	    if suburb[-3]: name=str(suburb[0])+'-'+str(suburb[-3])+'-'+str(suburb[-1])
	    else: name=str(suburb[0])+'-'+str(suburb[-4])+'-'+str(suburb[-1])
	    self.create_nagvis_conf('suburbs',name,self.suburbs[suburb])

	for district in self.districts:
	    if not district[-1]: 
		print('Errors@districts with - '+str(district),file=f)
		continue
	    if district[-2]: name=str(district[0])+'-'+str(district[-2])+'-'+str(district[-1])
	    else: name=str(district[0])+'-'+str(district[-3])+'-'+str(district[-1])
	    self.create_nagvis_conf('districts',name,self.districts[district])

	for city in self.cities:
	    if not city[-1]: 
		print('Errors@cities with - '+str(city),file=f)
		continue
	    if city[-2]: name=str(city[0])+'-'+str(city[-2])+'-'+str(city[-1])
	    else: name=str(city[0])+'-'+str(city[-3])+'-'+str(city[-1])
	    self.create_nagvis_conf('cities',name,self.cities[city])

	for county in self.counties:
	    if not county[-1]: 
		print('Errors@counties with - '+str(county),file=f)
		continue
	    if county[-2]: name=str(county[0])+'-'+str(county[-2])+'-'+str(county[-1])
	    else: name=str(county[0])+'-'+str(county[-2])+'-'+str(county[-1])
	    self.create_nagvis_conf('counties',name,self.counties[county])

	for admin in self.administratives:
	    if not admin[-1]: 
		print('Errors@administratives with - '+str(admin),file=f)
		continue
	    if not admin[0]: print('Errors@administratives with - '+str(admin),file=f)
	    else: name=str(admin[0])+'-'+admin[-1]
	    self.create_nagvis_conf('administratives',name,self.administratives[admin])

	for country in self.countries:
	    if not country[0]: 
		print('Errors@countries with - '+str(country),file=f)
		continue
	    else: name=country[0]
	    self.create_nagvis_conf('countries',name,self.countries[country])

	f.close()

    def Experimental(self):
	maps='./maps'
	geo='./geomap'
	if not os.path.exists(maps): os.makedirs(maps)
	if not os.path.exists(geo): os.makedirs(geo)
	for road in self.roads:
	    if road[-3]: roadname=str(road[-3])+'-'+str(road[-1])
	    else: roadname=str(road[-4])+'-'+str(road[-1])
	    u_roadname=unidecode(roadname.decode('utf8'))
	    u_roadname=u_roadname.replace("'","")
	    u_roadname=u_roadname.replace(".","")
	    u_roadname=u_roadname.replace(' ','')
	    m=open(maps+'/'+u_roadname+'.cfg','w')
	    print('define global {',file=m)
	    print('    sources=geomap',file=m)
	    print('    alias='+roadname,file=m)
	    print('    iconset=std_medium',file=m)
	    print('    backend_id=live_1',file=m)
	    print('    source_file='+u_roadname,file=m)
	    print('    width=1600',file=m)
	    print('    height=1400',file=m)
	    print('    geomap_border=0.0',file=m)
	    print('    geomap_zoom=10',file=m)
	    print('}',file=m)
	    m.close()
	    g=open(geo+'/'+u_roadname+'.csv','w')
	    for host in self.roads[road]:
		nagvis=(host,roadname,str(self.hosts[host][0]),str(self.hosts[host][1]))
		print(';'.join(nagvis),file=g)
	    g.close()

    def Experimental4(self):
	check_group='routers'

	maps='./maps'
	geo='./geomap'
	if not os.path.exists(maps): os.makedirs(maps)
	if not os.path.exists(geo): os.makedirs(geo)
	for city in self.cities:
	    if city[-1]: cityname=str(city[-1])
	    else: cityname=str(city[-2])
	    u_cityname=unidecode(cityname.decode('utf8'))
	    u_cityname=u_cityname.replace("'","")
	    u_cityname=u_cityname.replace(".","")
	    u_cityname=u_cityname.replace(' ','')
	    m=open(maps+'/'+u_cityname+'-EXPERIMENT.cfg','w')
	    print('define global {',file=m)
	    print('    sources=geomap',file=m)
	    print('    alias='+cityname,file=m)
	    print('    iconset=std_small',file=m)
	    print('    backend_id=live_1',file=m)
	    print('    source_file='+u_cityname,file=m)
	    print('    width=1600',file=m)
	    print('    height=1400',file=m)
	    print('    geomap_border=0.0',file=m)
#	    print('    geomap_zoom=10',file=m)
	    print('}',file=m)
	    m.close()
	    g=open(geo+'/'+u_cityname+'-EXPERIMENT.csv','w')

	    status=self.get_query('hostgroups',('members',),('name = '+str(check_group),))
	    for members in status:
		for host in members[0]:
		    nagvis=(host,cityname,str(self.hosts[host][0]),str(self.hosts[host][1]))
		    print(';'.join(nagvis),file=g)
	    g.close()


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8') 
    bit=GenerateCoordinates()
    bit.grab_addresses()
    bit.fill_data()
    bit.make_generic()
    bit.create_nagvis_geobase()
    bit.Experimental4()
    bit.__del__()


