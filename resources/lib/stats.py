import sys, os
import xbmc
from utilities import log
from uuid import getnode as uuid_node
from hashlib import md5
import urllib, urllib2

if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

def send_statistics_to_server(data):
	u = urllib2.urlopen("http://xbmc-repo-stats.bimovi.cz/save.php", urllib.urlencode({"data" : simplejson.dumps(data)}), 10)
	log("Usage Tracking", [simplejson.dumps(data), u.getcode()])
	return u.getcode() == 201

def send_statistics(action, addon, title, item, result_count):

	try:
		info = {
			'action'		: action,
			'xbmc_uniq_id' 	: md5(str(uuid_node())).hexdigest()
		}

		try:
			data = xbmc.executeJSONRPC('{"jsonrpc" : "2.0", "method": "XBMC.GetInfoLabels", "id" :1, "params": {"labels" : \
				["System.BuildVersion","System.ScreenHeight","System.ScreenWidth","System.KernelVersion","System.Language"]}}')  
			data = simplejson.loads(data)

			info['xbmc_resolution'] 	= '%sx%s' %(data['result']['System.ScreenWidth'],data['result']['System.ScreenHeight'])
			info['xbmc_language'] 			= data['result']['System.Language']
			info['xbmc_version'] 		= data['result']['System.BuildVersion']
		except:
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

		return send_statistics_to_server(info)
	except Exception, e:
		log("Usage Tracking", "Error: %s" % e)
		return False

