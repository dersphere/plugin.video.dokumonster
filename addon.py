#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 Tristan Fischer (sphere@dersphere.de)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from string import ascii_lowercase, digits
from xbmcswift2 import Plugin, xbmc
from resources.lib.api import DokuMonsterApi, NetworkError

plugin = Plugin()
api = DokuMonsterApi()

STRINGS = {
    'popular_docus': 30001,
    'new_docus': 30002,
    'tags': 30003,
    'all': 30004,
    'top_docus': 30005,
    'network_error': 30200
}


@plugin.route('/')
def show_root():
    items = (
        # FIXME: Reihe
        {'label': _('popular_docus'), 'path': plugin.url_for(
            endpoint='show_popular_docus'
        )},
        {'label': _('new_docus'), 'path': plugin.url_for(
            endpoint='show_new_docus'
        )},
        {'label': _('tags'), 'path': plugin.url_for(
            endpoint='show_tags'
        )},
        {'label': _('all'), 'path': plugin.url_for(
            endpoint='show_initials'
        )},
        {'label': _('top_docus'), 'path': plugin.url_for(
            endpoint='show_top_docus'
        )},
        # FIXME: suche

    )
    return plugin.finish(items)


@plugin.route('/tags/')
def show_tags():
    tags = api.get_tags()
    items = [{
        'label': '%s [%s]' % (tag.get('name'), tag.get('count')),
        'path': plugin.url_for(
            endpoint='show_docus_by_tag',
            tag_id=tag['id']
        )
    } for tag in tags]
    return plugin.finish(items)


@plugin.route('/tags/<tag_id>/')
def show_docus_by_tag(tag_id):
    docus, total_count = api.get_docus_by_tag(tag_id)
    return __add_docus(docus)


@plugin.route('/initals/')
def show_initials():
    items = []
    for char in list(ascii_lowercase + digits):
        items.append({
            'label': char.upper(),
            'path': plugin.url_for(
                endpoint='show_docus_by_initial',
                initial=char
            )
        })
    return plugin.finish(items)


@plugin.route('/initals/<initial>/')
def show_docus_by_initial(initial):
    docus, total_count = api.get_docus_by_initial(initial)
    return __add_docus(docus)


@plugin.route('/popular_docus/')
def show_popular_docus():
    docus, total_count = api.get_popular_docus()
    return __add_docus(docus)


@plugin.route('/top_docus/')
def show_top_docus():
    docus, total_count = api.get_top_docus()
    return __add_docus(docus)


@plugin.route('/new_docus/')
def show_new_docus():
    docus, total_count = api.get_newest_docus()
    return __add_docus(docus)


@plugin.route('/play/<docu_id>')
def play(docu_id):
    docu = api.get_docu(docu_id)
    plugin.log.info(repr(docu))
    # FIXME: Replace with 'media'-Code
    import re
    playback_url = None

    re_youtube_id = re.compile('watch\?v=(.*)')
    m = re_youtube_id.search(docu['embed'])
    if m:
        video_id = m.groups(1)
        playback_url = ('plugin://plugin.video.youtube/'
                        '?action=play_video&videoid=%s' % video_id)

    re_youtube_playlist = re.compile('playlist\?list=(.*)')
    m = re_youtube_playlist.search(docu['embed'])
    if m:
        video_id = m.groups(1)
        playback_url = ('plugin://plugin.video.youtube/'
                        '?action=play_all&playlist=%s' % video_id)
    if playback_url:
        plugin.log.info('Found URL: %s' % playback_url)
        return plugin.set_resolved_url(playback_url)
    else:
        plugin.notify(msg=_('Not Implemented yet'))


def __add_docus(docus):
    # FIXME: Pagination
    items = []
    for i, docu in enumerate(docus):
        item = {
            'label': docu['title'],
            'icon': docu['thumb'],
            'info': {
                #'count': str(i),
                'studio': docu['username'] or '',
                'genre': docu['tags'] or '',
                'tagline': docu['lang'] or '',
                #'votes': int(docu['views'] or '0'),
            },
            'path': plugin.url_for(
                endpoint='play',
                docu_id=docu['id']
            ),
            'is_playable': True
        }
        items.append(item)
    finish_kwargs = {
        # FIXME: Sort methods
        #'sort_methods': ('TITLE', 'VOTES')
    }
    if plugin.get_setting('force_viewmode_podcasts') == 'true':
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


def __keyboard(title, text=''):
    keyboard = xbmc.Keyboard(text, title)
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        return keyboard.getText()


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id


if __name__ == '__main__':
    try:
        plugin.run()
    except NetworkError:
        plugin.notify(msg=_('network_error'))
