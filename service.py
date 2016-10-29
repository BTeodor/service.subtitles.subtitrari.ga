# -*- coding: utf-8 -*-
# encoding=utf8

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
from xbmc import log

import os
import re
import shutil
import string
import urllib
import requests
import json
from random import randint
from time import sleep

import sys
reload(sys)  # Reload does the trick!
sys.setdefaultencoding('UTF8')

__addon__ = xbmcaddon.Addon()
__author__ = __addon__.getAddonInfo('author')
__scriptid__ = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__language__ = __addon__.getLocalizedString

__cwd__ = xbmc.translatePath(__addon__.getAddonInfo('path'))
__profile__ = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__resource__ = xbmc.translatePath(os.path.join(__cwd__, 'resources', 'lib'))
__temp__ = xbmc.translatePath(os.path.join(__profile__, 'temp'))

sys.path.append(__resource__)

if os.path.exists(__temp__):
    shutil.rmtree(__temp__)
os.makedirs(__temp__)

s = requests.Session()

__API_URL__ = 'https://subtitrari.ga/api/subtitle/'


def normalize_filename(s):
    valid_chars = '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join([c for c in s if c in valid_chars])


def load_url(path):
    # there is no need to be overenthusiastic
    sleep(randint(5, 25) / 10.0)
    uri = __API_URL__ + path.replace(' ', '+')
    log('Getting uri: %s' % uri)
    req = s.get(uri)
    req.encoding = 'ISO-8859-9'
    res = req.text.encode('ISO-8859-9')
    log(res)
    subtitles = json.loads(res)
   
    return subtitles


def get_media_url(media_args):
    log('getting media url')
    querytype = media_args[0]
    title = re.sub(" \(?(.*.)\)", "", media_args[1])

    subtitles = load_url('search?search=%s' % title)

    for subtitle in subtitles:
        return 
    redirect_url = [sc.getText() for sc in page.findAll('script') if 'location.href' in sc.getText()]
    if len(redirect_url) > 0:
        a = redirect_url[0]
        episode_uri = a[a.find('"')+1:a.rfind('"')]
        log('Found uri via redirect')
        return episode_uri

    for result in page.findAll('td', attrs={'width': '60%'}):
        link = result.find('a')
        link_title = link.find('b').getText().strip()
        if querytype == "film":
            if str(year) == "" or str(year) in result.getText():
                return link["href"]
        elif querytype == "dizi" and link_title.startswith('"'):
            if str(year) == "" or str(year) in result.getText():
                return link["href"]
    raise ValueError('No valid results')


def search(mitem):
    tvshow = mitem["tvshow"]
    year = mitem["year"]
    season = mitem["season"]
    episode = mitem["episode"]
    title = mitem["title"]

    # Build an adequate string according to media type
    if len(tvshow) != 0:
        log("[SEARCH TVSHOW] Divxplanet: searching subtitles for %s %s %s %s" % (tvshow, year, season, episode))
        
        subtitles = load_url('search?search=%s&season=%s&episode=%s' % (tvshow, int(season), int(episode)))
    
        subtitles_list = []

        for subtitle in subtitles:
            log(json.dumps(subtitle))
            l_item = xbmcgui.ListItem(
                label='RO',  # language name for the found subtitle
                label2=subtitle['name'],  # file name for the found subtitle
                iconImage="0",  # rating for the subtitle, string 0-5
                thumbnailImage=xbmc.convertLanguage('RO', xbmc.ISO_639_1)
            )

            subtitles_list.append(l_item)

            url = "plugin://%s/?action=download&link=%s&lang=%s&description=%s" % (
                __scriptid__,
                subtitle['download'],
                'RO',
                normalize_filename(subtitle['name'])
            )

            xbmcplugin.addDirectoryItem(
                handle=int(sys.argv[1]),
                url=url,
                listitem=l_item,
                isFolder=False
            )

        log("Divxplanet: found %d subtitles" % (len(subtitles_list)))
    else:
        log("[SEARCH !TVSHOW] Divxplanet: searching subtitles for %s" % (title))

        subtitles = load_url('search?search=%s' % title)
    
        subtitles_list = []

        for subtitle in subtitles:
            log(json.dumps(subtitle))
            l_item = xbmcgui.ListItem(
                label='RO',  # language name for the found subtitle
                label2=subtitle['name'],  # file name for the found subtitle
                iconImage="0",  # rating for the subtitle, string 0-5
                thumbnailImage=xbmc.convertLanguage('RO', xbmc.ISO_639_1)
            )

            subtitles_list.append(l_item)

            url = "plugin://%s/?action=download&link=%s&lang=%s&description=%s" % (
                __scriptid__,
                subtitle['download'],
                'RO',
                normalize_filename(subtitle['name'])
            )

            xbmcplugin.addDirectoryItem(
                handle=int(sys.argv[1]),
                url=url,
                listitem=l_item,
                isFolder=False
            )
        log("[SEARCH END]Divxplanet: found %d subtitles" % (len(subtitles_list)))


def download(link):
    dpid = re.search('download/(\d+)', link).group(1)
    extract_path = __temp__

    subtitle_list = []

    # page = load_url(link)

    f = s.get(__API_URL__ + link, stream=True)
    if f.status_code == 200:
        if 'Content-Disposition' in f.headers:
            # use the provided file name if possible
            local_name = f.headers['Content-Disposition'].split('filename=')[1].strip('"\'')
        else:
            # use a generic name
            local_name = 'sub.srt'
        local_tmp_file = os.path.join(__temp__, local_name)
        with open(local_tmp_file, 'wb') as outfile:
            for chunk in f.iter_content(1024):
                outfile.write(chunk)
    else:
        raise ValueError("Couldn't Get The File")

    files = os.listdir(extract_path)

    for f in files:
        if string.split(f, '.')[-1] in ['srt', 'sub']:
            subs_file = os.path.join(extract_path, f)
            subtitle_list.append(subs_file)
            log("Divxplanet: Subtitles saved to '%s'" % local_tmp_file)
    return subtitle_list


def get_params():
    param = []
    paramstring = sys.argv[2]

    if len(paramstring) >= 2:
        mparam = paramstring
        cleanedparams = mparam.replace('?', '')

        if mparam[len(mparam) - 1] == '/':
            mparam = mparam[0:len(mparam) - 2]

        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if len(splitparams) == 2:
                param[splitparams[0]] = splitparams[1]

    return param

params = get_params()

if params['action'] == 'search':
    item = {
        'temp': False,
        'rar': False,
        'year': xbmc.getInfoLabel("VideoPlayer.Year"),
        'season': str(xbmc.getInfoLabel("VideoPlayer.Season")),
        'episode': str(xbmc.getInfoLabel("VideoPlayer.Episode")),
        'tvshow': xbmc.getInfoLabel("VideoPlayer.TVshowtitle"),
        'title': xbmc.getInfoLabel("VideoPlayer.OriginalTitle"),
        'file_original_path': urllib.unquote(xbmc.Player().getPlayingFile().decode('utf-8')), '3let_language': []
    }

    for lang in urllib.unquote(params['languages']).decode('utf-8').split(","):
        item['3let_language'].append(xbmc.convertLanguage(lang, xbmc.ISO_639_2))

    if item['title'] == "":
        item['title'] = xbmc.getInfoLabel("VideoPlayer.Title")

    if item['episode'].lower().find("s") > -1:  # Check if season is "Special"
        item['season'] = "0"
        item['episode'] = item['episode'][-1:]

    if item['file_original_path'].find("http") > -1:
        item['temp'] = True
    elif item['file_original_path'].find("rar://") > -1:
        item['rar'] = True
        item['file_original_path'] = os.path.dirname(item['file_original_path'][6:])
    elif item['file_original_path'].find("stack://") > -1:
        stackPath = item['file_original_path'].split(" , ")
        item['file_original_path'] = stackPath[0][8:]

    search(item)

elif params['action'] == 'download':
    subs = download(params["link"])
    for sub in subs:
        listitem = xbmcgui.ListItem(label=sub)
        xbmcplugin.addDirectoryItem(
                handle=int(sys.argv[1]),
                url=sub,
                listitem=listitem,
                isFolder=False
        )

xbmcplugin.endOfDirectory(int(sys.argv[1]))
s.close()
