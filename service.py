# -*- coding: utf-8 -*- 

import os
import sys
import xbmc
import urllib
import xbmcvfs
import xbmcaddon
import xbmcgui
import xbmcplugin
import shutil
import unicodedata

__addon__ = xbmcaddon.Addon()
__author__     = __addon__.getAddonInfo('author')
__scriptid__   = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__    = __addon__.getAddonInfo('version')
__language__   = __addon__.getLocalizedString

__cwd__        = xbmc.translatePath( __addon__.getAddonInfo('path') ).decode("utf-8")
__profile__    = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
__resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) ).decode("utf-8")
__temp__       = xbmc.translatePath( os.path.join( __profile__, 'temp') ).decode("utf-8")

sys.path.append (__resource__)

from utilities import log, extract_subtitles, copy_subtitles_on_rar
from TitulkyClient import TitulkyClient as SubtitlesClient

def Search(item):

  #### Do whats needed to get the list of subtitles from service site
  #### use item["some_property"] that was set earlier
  #### once done, set xbmcgui.ListItem() below and pass it to xbmcplugin.addDirectoryItem()
  
  cli = SubtitlesClient(__addon__)
  found_subtitles = cli.search(item)

  if (found_subtitles == [] or found_subtitles == None):
    return False

  for subtitle in found_subtitles:
    listitem = xbmcgui.ListItem(label=subtitle['lang'],                                   # language name for the found subtitle
                                label2=subtitle['filename'],               # file name for the found subtitle
                                iconImage=subtitle['rating'],                                     # rating for the subtitle, string 0-5
                                thumbnailImage=subtitle['lang_flag']                            # language flag, ISO_639_1 language + gif extention, e.g - "en.gif"
                                )
    listitem.setProperty( "sync", ("false", "true")[int(subtitle['sync'])])  # set to "true" if subtitle is matched by hash,
    listitem.setProperty( "hearing_imp", "false" ) # set to "true" if subtitle is for hearing impared
  
  ## below arguments are optional, it can be used to pass any info needed in download function
  ## anything after "action=download&" will be sent to addon once user clicks listed subtitle to downlaod
    url = "plugin://%s/?action=download&id=%s&lang=%s" % (__scriptid__, subtitle['id'], subtitle['lang'])
  ## add it to list, this can be done as many times as needed for all subtitles found
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listitem,isFolder=False) 


def Download(sub_id, lang):
  subtitle_list = []
  ## Cleanup temp dir, we recomend you download/unzip your subs in temp folder and
  ## pass that to XBMC to copy and activate
  if xbmcvfs.exists(__temp__):
    shutil.rmtree(__temp__)
  xbmcvfs.mkdirs(__temp__)

  cli = SubtitlesClient(__addon__)
  if not cli.login(__addon__.getSetting("username"), __addon__.getSetting("password")):
    dialog = xbmcgui.Dialog()
    dialog.ok(__scriptname__,__language__(32012))
    return []

  downloaded_file = cli.download(sub_id)
  if downloaded_file == None: return []

  log(__scriptname__,"Extracting subtitles")
  subtitle_list = extract_subtitles(downloaded_file)
  log(__scriptname__,subtitle_list)
  # subtitle_list.append("/Path/Of/Subtitle2.srt") # this can be url, local path or network path.
  
  if __addon__.getSetting("copy_subs_if_rar_played") == "true": copy_subtitles_on_rar(subtitle_list,lang)

  return subtitle_list
 
def normalizeString(str):
  return unicodedata.normalize(
         'NFKD', unicode(unicode(str, 'utf-8'))
         ).encode('ascii','ignore')    
 
def get_params():
  param=[]
  paramstring=sys.argv[2]
  if len(paramstring)>=2:
    params=paramstring
    cleanedparams=params.replace('?','')
    if (params[len(params)-1]=='/'):
      params=params[0:len(params)-2]
    pairsofparams=cleanedparams.split('&')
    param={}
    for i in range(len(pairsofparams)):
      splitparams={}
      splitparams=pairsofparams[i].split('=')
      if (len(splitparams))==2:
        param[splitparams[0]]=splitparams[1]
                                
  return param

params = get_params()

print params


if params['action'] == 'search' or params['action'] == 'manualsearch':
  item = {}
  item['temp']               = False
  item['rar']                = False
  item['mansearch']          = False
  item['year']               = xbmc.getInfoLabel("VideoPlayer.Year")                           # Year
  item['season']             = str(xbmc.getInfoLabel("VideoPlayer.Season"))                    # Season
  item['episode']            = str(xbmc.getInfoLabel("VideoPlayer.Episode"))                   # Episode
  item['tvshow']             = normalizeString(xbmc.getInfoLabel("VideoPlayer.TVshowtitle"))   # Show
  item['title']              = normalizeString(xbmc.getInfoLabel("VideoPlayer.OriginalTitle")) # try to get original title
  item['file_original_path'] = urllib.unquote(xbmc.Player().getPlayingFile().decode('utf-8'))  # Full path of a playing file
  item['3let_language']      = []

  if 'searchstring' in params:
    item['mansearch'] = True
    item['mansearchstr'] = urllib.unquote(params['searchstring']).decode('utf-8')
  
  if 'languages' in params:
    for lang in urllib.unquote(params['languages']).decode('utf-8').split(","):
      item['3let_language'].append(xbmc.convertLanguage(lang,xbmc.ISO_639_2))
  
  if item['title'] == "":
    item['title']  = normalizeString(xbmc.getInfoLabel("VideoPlayer.Title"))      # no original title, get just Title
    
  if item['episode'].lower().find("s") > -1:                                      # Check if season is "Special"
    item['season'] = "0"                                                          #
    item['episode'] = item['episode'][-1:]
  
  if ( item['file_original_path'].find("http") > -1 ):
    item['temp'] = True

  elif ( item['file_original_path'].find("rar://") > -1 ):
    item['rar']  = True
    item['file_original_path'] = os.path.dirname(item['file_original_path'][6:])

  elif ( item['file_original_path'].find("stack://") > -1 ):
    stackPath = item['file_original_path'].split(" , ")
    item['file_original_path'] = stackPath[0][8:]
  
  Search(item)  

elif params['action'] == 'download':
  ## we pickup all our arguments sent from def Search()
  subs = Download(params["id"], params["lang"])
  ## we can return more than one subtitle for multi CD versions, for now we are still working out how to handle that in XBMC core
  for sub in subs:
    listitem = xbmcgui.ListItem(label=sub)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=sub,listitem=listitem,isFolder=False)
  
  
xbmcplugin.endOfDirectory(int(sys.argv[1])) ## send end of directory to XBMC
  
  
  
  
  
  
  
  
  
    
