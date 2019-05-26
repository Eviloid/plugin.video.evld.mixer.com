#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, urllib, sys, urllib2, re, cookielib, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import CommonFunctions as common
from tccleaner import TextureCacheCleaner as tcc

PLUGIN_NAME   = 'Mixer plugin'

MAX_ITEMS = 25

common.plugin = PLUGIN_NAME

LIVE_PREVIEW_TEMPLATE = '%//thumbs.mixer.com/channel/%'  # sqlite LIKE pattern

try:handle = int(sys.argv[1])
except:pass

addon = xbmcaddon.Addon(id='plugin.video.evld.mixer.com')

Pdir = addon.getAddonInfo('path')
icon = xbmc.translatePath(os.path.join(Pdir, 'icon.png'))
fanart = xbmc.translatePath(os.path.join(Pdir, 'fanart.jpg'))

xbmcplugin.setContent(handle, 'movies')

def get_html(url, params={}, post={}, noerror=True):
    headers = {'Accept':'application/json'}

    html = ''

    try:
        conn = urllib2.urlopen(urllib2.Request('%s?%s' % (url, urllib.urlencode(params)), headers=headers))
        html = conn.read()
        conn.close()
    except urllib2.HTTPError, err:
        if not noerror:
            html = err.code

    return html 


def stream_list(params):

    page = int(params.get('page', 0))
    id = params.get('id', None)

    payload = { 'order':'viewersCurrent:DESC',
                'limit':MAX_ITEMS,
                'page':page,
                'fields':'id,name,type,user',
                'where':'name:ne:""' }

    if id == None:
        if page == 0:
            add_item('[B]TOP GAMES[/B]', {'mode':'games', 'page':page}, fanart=fanart, isFolder=True)

        data = get_html('https://mixer.com/api/v1/channels', payload, noerror=False)
    else:
        data = get_html('https://mixer.com/api/v1/types/%s/channels' % id, payload, noerror=False)

    if not isinstance(data, basestring):
        if page > 0:
            params['page'] = page - 1
            stream_list(params)
    else:
        data = json.loads(data)
        if len(data) == 0:
            if page > 0:
                params['page'] = page - 1
                stream_list(params)
        else:
            for channel in data:
                title = channel['name']
                preview = 'https://thumbs.mixer.com/channel/%d.small.jpg' % channel['id']
            
                type = channel.get('type')
            
                if type != None:
                    plot = '[B][COLOR=yellow]%s[/COLOR][/B]\n%s' % (type['name'], channel['user']['username'])
                else:
                    plot = channel['user']['username']
            
                add_item(title, url='https://mixer.com/api/v1/channels/%d/manifest.m3u8' % channel['id'], thumb=preview, fanart=fanart, plot=plot, isFolder=False)

            params['page'] = page + 1
            add_nav(u'Next > %d' % params['page'], params)


def main_menu(params):

    stream_list(params)

    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)


def game_list(params):

    page = int(params.get('page', 0))
    data = get_html('https://mixer.com/api/v1/types', {
                'order':'viewersCurrent:DESC',
                'limit':MAX_ITEMS,
                'page':page,
                'where':'online:gt:0',
                'fields':'id,name,description,coverUrl,backgroundUrl'}, noerror=False)

    if not isinstance(data, basestring):
        if page > 0:
            params['page'] = page - 1
            game_list(params)
    else:
        data = json.loads(data)
        if len(data) == 0:
            if page > 0:
                params['page'] = page - 1
                game_list(params)
        else:
            for game in data:
                title = game['name']
                id = game['id']
                logo = game['coverUrl']
                fanart = game['backgroundUrl']
                plot = game['description']

                if not logo: logo = icon

                add_item(title, {'id':id, 'page':'0'} , icon=logo, thumb=logo, fanart=fanart, plot=plot, isFolder=True)

            params['page'] = page + 1
            add_nav(u'Next > %d' % params['page'], params)

    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)


def add_nav(title, params={}):
    url = '%s?%s' % (sys.argv[0], urllib.urlencode(params))
    item = xbmcgui.ListItem(title)
    xbmcplugin.addDirectoryItem(handle, url=url, listitem=item, isFolder=True)


def add_item(title, params={}, icon='', banner='', fanart='', poster='', thumb='', plot='', isFolder=False, isPlayable=False, url=None):
    if url == None: url = '%s?%s' % (sys.argv[0], urllib.urlencode(params))

    item = xbmcgui.ListItem(title, iconImage = icon, thumbnailImage = thumb)
    item.setInfo(type='video', infoLabels={'Title': title, 'Plot': plot})

    if isPlayable:
        item.setProperty('IsPlayable', 'true')
    
    if banner != '':
        item.setArt({'banner': banner})
    if fanart != '':
        item.setArt({'fanart': fanart})
    if poster != '':
        item.setArt({'poster': poster})
    if thumb != '':
        item.setArt({'thumb':  thumb})

    xbmcplugin.addDirectoryItem(handle, url=url, listitem=item, isFolder=isFolder)


params = common.getParameters(sys.argv[2])

mode = params.get('mode', '')

if mode == 'games':
    game_list(params)

if mode == '':
    tcc().remove_like(LIVE_PREVIEW_TEMPLATE, False)
    main_menu(params)
