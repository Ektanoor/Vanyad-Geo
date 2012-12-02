Vanyad-Geo
==========

A separate project for geolocation analysis

WARNING - This is a work in progress, so expect big changes to the code. And note - there is NO WARRANTIES whatsoever.
          This code is under GPLv2, so it's kiss it or kick it.


Presently, the main script is vanyad_latlon.py. It creates a series of configurations for the geomap utility in Nagvis.


------------
Requirements:
 A working Nagios/Icinga system.
 Python 2.7, not the 3.x versions. This is an issue of compatibility with modules still working under the 2.* branch.
 On python you have have these modules installed:
  -shelve
  -ConfigParser
  -collections
  -time
  -pipes
  -unidecode
  -httplib
  -urllib
  -json

 Obviously you will need Nagvis. Better to use version 1.7.2 and forward.
 Livestatus (http://mathias-kettner.de/checkmk_livestatus.html) is a must.
 A direct connection to nominatim.openstreetmap.org

Some notes on requirements:

 -The program was written in python as its "origin" came from Livestatus, which is mostly written in python and 
 capable of sending python formatted data to other programs.

 -It uses Livestatus to gather information on hosts from Nagios/Icinga. Possibly, with some tweaking to the code,
 it may work for services and other Nagios/Icinga objects. The main requirement for the Nagios/Icinga hosts is
 that they shall carry a custom variable "_location", with specific parameters (see below).

 Also, with some serious tweaking to the code, it may not need Livestatus. However, here, we use it,
 we have strict, near real-time requirements, so, it would be nonsense to seek other alternatives.

 -The program uses nominatim.openstreetmap.org to get coordinates and other information for each host. For 
 this we need the httplib,urllib and json modules.

 There are some restrictions on the use of Nominatim. Besides, it would be a costly nonsense to produce 
 repeated queries for one and the same location. So we use the module "shelve" to create something similar
 to a "cache".

 -To create unique filenames, data from Nominatim is used. However, many names come in the national languages
  of the countries where hosts are located. Sometimes, these names carry codes which the file systems consider unacceptable.
  So, we use unidecode (and some other tricks) to unify these names.


-------------
Installation:
 -Create a working dir. Ex. Vanyad-Geo. Copy all the vanyad-*.py files into that dir.
 DO NOT INSTALL vanyad_latlon.py and other vanyad* modules in the standard python tree! It will surely create a 
 mess. Currently, vanyas_latlon is configured such a way that it will create several dirs under its working directory.
 How many? This fully depends on the number of locations you have and some properties they possess. 

 -You have to copy the file [check_mk|livestatus dir]/api/python/livestatus.py to your working directory.

 -Inside Nagios/Icinga configuration, under every host you want to locate, you have to add the custom variable "_location". This 
  variable has the following format:

        _location      country_code,state,city/county,street/road,<postcode>

   Ex. _location  ru,Central Administrative Okrug,Москва,Ленинградский Проспект,47

   A more complete example:

        define host{
         use                     sw-template,host-pnp
         host_name               D-Link
         address                 10.10.10.10
         hostgroups              dlink
         _location               de,Lower Saxony,Wolfsburg,Heinrich-Nordhoff-Straße,69
        }

  Note that field "postcode" is facultative (see below)

  The names shall be the closest possible to their equivalents in Nominatim. It is acceptable to use partial names,
  as Nominatim is frequently able to give the correct data under partial info. However this is not always the case.
  For example, if you have a "Market Avenue" and a "Market Road", you have to give the full name for 
  the road/street.

  Meanwhile there are cities where you may have several roads with one and the same name. For example, here, we have some seven
  "Garden Roads" (official names and completely different roads). To distinguish them, we need a separate variable, in our case,
  the postal index or Nominatim's "postcode". This parameter is only needed on those places where this confusion may arise.

  Note - After adding _location to all hosts you need, you have to restart Nagios/Icinga

  -Create a vanyad.conf in you working dir. Inside, write the following lines:

          [monitor]
          system=icinga

 If your Nagios/Icinga dir is in a different location from the standard installation, you may have to add:

        monitor_dir=<your Nagios/Icinga working dir> (Ex. /var/lib/icinga/)
        socket_live=<path to livestatus socket>      (Ex, /var/lib/icinga/rw/live)



----------
Launching:
 -Just launch vanyad_latlon.py. The program will create:

 geomap dir - Inside you have the lists of hosts with their coordinates. Copy those files (not dirs!) you need to /etc/nagvis/geomap.
 
 maps dir - These are the configurations maps. As above, copy the necessary files (not dirs!) to the /etc/nagvis/maps.

 Note - If you have installed Nagvis config in other place, you have to find it and copy the files to their corresponding dirs.
 Warning - NEVER EVER try to create a direct/automatic copy of these files to Nagvis. Depending on your mileage, this data may 
           become enormous and Nagvis behaves badly when the number of maps reaches a few tens.

 ambiguous_data.txt - Data that the program found ambiguous - wrong roads, wrong house numbers, etc. This checking is far from perfect 
                      but it gives up the most common problems.

 outcasts.txt - Hosts for which no lat-lon was found. Reasons may vary, wrong initial data, errors in Nominatim, imcomplete data etc.

 locations.txt - A generic file with all hosts for which geodata was found. You can use it with the "demo" configs on Nagvis, however,
                 beware of serious lags.

 outcasts-generic.txt - Hosts for which lat-lon was not found. Note this file may significatly differ from outcasts.txt. This is due to
                        the use of a slightly different way to gather data. As I noted, this program is still work in progress.


Some notes on lauching:

 Depending on the country, results may look a bit funny. This is due to people using different tags in different countries to remark entities.
 For example "county" in Russia is frequently used in place of "city" (but "village" is always "village"!). These cases are difficult to unify,
 but not impossible. OpenStreetMap itself has semantic bases that attempt to help or solve these discrepancies. So this is one of the TODO's
 of this program.

Well, for the moment, that's all folks...
