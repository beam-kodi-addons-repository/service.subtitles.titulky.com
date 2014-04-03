# -*- coding: utf-8 -*- 

from utilities import log, file_size_and_hash
import urllib, re, os, xbmc, xbmcgui
import urllib2, cookielib
import HTMLParser
import time,calendar

class TitulkyClient(object):

	def __init__(self):
		self.server_url = 'http://www.titulky.com'
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar()))
		opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
		urllib2.install_opener(opener)

	def download(self,link,sub_id,dest_dir):
		log(__name__,["Downoad", link, sub_id, dest_dir])

	def search(self,item):
		if not ((item['tvshow'] == None) or (item['tvshow'] == '')):
			title = "%s S%02dE%02d" % (item['tvshow'], int(item['season']), int(item['episode'])) # Searching TV Show
		else:
			title = item['title'] # Searching movie

		log(__name__, "Search pattern: " + title)

		found_subtitles = self.search_subtitle(title)
		log(__name__, "Parsed subtitles: %s" % found_subtitles )

		if found_subtitles.__len__() == 0:
			log(__name__, "Subtitles not found")
			return None
			
		file_size, file_hash = file_size_and_hash(item['file_original_path'], item['rar'])
		if not (file_size == -1): file_size = round(float(file_size)/(1024*1024),2)
		log(__name__, "File size: " + str(file_size))

		max_down_count = self.detect_max_download_stats(found_subtitles)

		result_subtitles = []
		for found_subtitle in found_subtitles:

			print_out_filename = (found_subtitle['version'], found_subtitle['title'])[found_subtitle['version'] == '']
			result_subtitles.append({ 
				'filename': HTMLParser.HTMLParser().unescape(print_out_filename + " by " + found_subtitle['author']),
				'id': found_subtitle['id'],
				'link': self.server_url + '/idown.php?' + urllib.urlencode({'R':str(calendar.timegm(time.gmtime())),'titulky':found_subtitle['id'],'histstamp':'','zip':'z'}),
				'lang': found_subtitle['lang'],
	 			'rating': str(found_subtitle['down_count']*5/max_down_count),
				'sync': (found_subtitle['size'] == file_size),
				'lang_flag': xbmc.convertLanguage(found_subtitle['lang'],xbmc.ISO_639_1),
			})

		log(__name__,"Search RESULT")
		log(__name__,result_subtitles)
		return result_subtitles

	def detect_max_download_stats(self, subtitle_list):
		max_down_count = 0
		for subtitle in subtitle_list:
			if max_down_count < subtitle['down_count']:
				max_down_count = subtitle['down_count']

		log(__name__,"Max download count: " + str(max_down_count))
		return max_down_count


	def search_subtitle(self, title):
		url = self.server_url + '/index.php?' + urllib.urlencode({'Fulltext': title ,'FindUser':''})
		log(__name__, "Opening: %s" % url)

		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		content = response.read()
		response.close()

		log(__name__,'Parsing result page')

		subtitles = []
		for row in re.finditer('<tr class=\"r(.+?)</tr>', content, re.IGNORECASE | re.DOTALL):
			subtitle = {}
			subtitle['id'] = re.search('[^<]+<td[^<]+<a href=\"[\w-]+-(?P<data>\d+).htm\"',row.group(1),re.IGNORECASE | re.DOTALL ).group('data')
			subtitle['title'] = re.search('[^<]+<td[^<]+<a[^>]+>(<div[^>]+>)?(?P<data>[^<]+)',row.group(1),re.IGNORECASE | re.DOTALL ).group('data')
			try:
				subtitle['version'] = re.search('((.+?)</td>)[^>]+>[^<]*<a(.+?)title=\"(?P<data>[^\"]+)',row.group(1),re.IGNORECASE | re.DOTALL ).group('data')
			except:
				subtitle['version'] = None
			subtitle['season_and_episode'] = re.search('((.+?)</td>){2}[^>]+>(?P<data>[^<]+)',row.group(1),re.IGNORECASE | re.DOTALL ).group('data')
			subtitle['year'] = re.search('((.+?)</td>){3}[^>]+>(?P<data>[^<]+)',row.group(1),re.IGNORECASE | re.DOTALL ).group('data')
			subtitle['down_count'] = int(re.search('((.+?)</td>){4}[^>]+>(?P<data>[^<]+)',row.group(1),re.IGNORECASE | re.DOTALL ).group('data'))
			subtitle['lang'] = re.search('((.+?)</td>){5}[^>]+><img alt=\"(?P<data>\w{2})\"',row.group(1),re.IGNORECASE | re.DOTALL ).group('data')
			if subtitle['lang'] == "CZ": subtitle['lang'] = "Czech"
			if subtitle['lang'] == "SK": subtitle['lang'] = "Slovak"
			subtitle['num_of_dics'] = re.search('((.+?)</td>){6}[^>]+>(?P<data>[^<]+)',row.group(1),re.IGNORECASE | re.DOTALL ).group('data')
			try:
				subtitle['size'] = float(re.search('((.+?)</td>){7}[^>]+>(?P<data>[\d\.]+)',row.group(1),re.IGNORECASE | re.DOTALL ).group('data'))
			except:
				subtitle['size'] = None
			subtitle['author'] = re.search('((.+?)</td>){8}[^>]+>[^>]+<a href[^>]+>(?P<data>[^<]+)',row.group(1),re.IGNORECASE | re.DOTALL | re.MULTILINE ).group('data').strip()
			subtitles.append(subtitle)

		return subtitles
