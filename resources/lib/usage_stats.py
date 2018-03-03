import sys, os
import xbmc
from utilities import log
from uuid import getnode as uuid_node
from hashlib import md5
from time import sleep as sleep
import urllib, urllib2
from datetime import datetime

if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

start_time = None

def results_with_stats(results, addon, title, item):
	if addon.getSetting("send_statistics") == "true":
		results_count = 0 if (results == None) else len(results)
		send_statistics("search", addon, title, item, results_count)

	return results

def mark_start_time():
	global start_time
	start_time = datetime.utcnow()

def send_statistics_to_server(data):
	u = urllib2.urlopen("http://xbmc-repo-stats.bimovi.cz/save-stats", urllib.urlencode({"data" : simplejson.dumps(data)}), 10)
	log("Usage Tracking", [simplejson.dumps(data), u.getcode()])
	return u.getcode() == 201

def uniq_id(mac_addr):
	if not ":" in mac_addr: mac_addr = xbmc.getInfoLabel('Network.MacAddress')
	# hack response busy
	if not ":" in mac_addr:
		sleep(2)
		mac_addr = xbmc.getInfoLabel('Network.MacAddress')

	if ":" in mac_addr:
		return md5(str(mac_addr.decode("utf-8"))).hexdigest()
	else:
		return md5(str(uuid_node())).hexdigest()

def send_statistics(action, addon, title, item, result_count):

	try:
		info = {
			'action'		: action
		}
		try:
			data = xbmc.executeJSONRPC('{"jsonrpc" : "2.0", "method": "XBMC.GetInfoLabels", "id" :1, "params": {"labels" : \
				["System.BuildVersion","System.ScreenHeight","System.ScreenWidth","System.OSVersionInfo","System.Language", "Network.MacAddress"]}}')
			data = simplejson.loads(data)

			info['xbmc_resolution'] 	= '%sx%s' %(data['result']['System.ScreenWidth'],data['result']['System.ScreenHeight'])
			info['xbmc_language'] 			= data['result']['System.Language']
			info['xbmc_version'] 		= data['result']['System.BuildVersion']
			info['os_version']           = data['result']['System.OSVersionInfo']

		except Exception, e:
			log("Usage Tracking", "Error JSON: %s" % e)
			pass

		info['system_platform'] 		= sys.platform

		info['addon_id'] 				= addon.getAddonInfo('id')
		info['addon_version'] 			= addon.getAddonInfo('version')

		info['search_title'] 			= title
		info['search_results_count'] 	= result_count
		info['search_languages']		= item['3let_language']

		info['input_is_rar'] 			= item['rar']
		info['input_man_search'] 		= item['mansearch']
		info['input_year'] 				= item['year']
		info['input_season']			= item['season']
		info['input_episode']			= item['episode']
		info['input_tvshow']			= item['tvshow']
		info['input_title']				= item['title']

		info['xbmc_uniq_id']			= uniq_id(data['result']['Network.MacAddress'])

		if start_time:
			info['run_time']			= (datetime.utcnow() - start_time).total_seconds()

		return send_statistics_to_server(info)
	except Exception, e:
		log("Usage Tracking", "Error: %s" % e)
		return False
