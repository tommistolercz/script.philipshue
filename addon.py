#!/usr/bin/env python
__all__ = ['PhilipsHueAddon', 'PhilipsHueAddonError']


import json
import os
import sys
import urllib
try:
    import urlparse  # py2
except ImportError:
    import urllib.parse as urlparse  # py3

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

sys.path.append(os.path.join(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')), 'resources', 'lib'))
import phue  # noqa: E402
import colortools  # noqa: E402


PY2, PY3 = ((sys.version_info[0] == 2), (sys.version_info[0] == 3))
FOLDER, NOT_FOLDER = (True, False)


class PhilipsHueAddon():
    """
    Main addon class encapsulating all logic and data.
    """
    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.handle = int(sys.argv[1])
        # connect bridge
        self.hue = self.connecthue(self.addon.getSetting('huebridgeip'))
        self.log('Philips Hue bridge connected: {0}'.format(self.hue.ip))
        # parse addon url
        self.urlbase = 'plugin://' + self.addon.getAddonInfo('id')
        self.urlpath = sys.argv[0].replace(self.urlbase, '')
        self.urlargs = {}
        if sys.argv[2].startswith('?'):
            self.urlargs = urlparse.parse_qs(sys.argv[2].lstrip('?'))
            for k, v in list(self.urlargs.items()):
                self.urlargs[k] = v.pop()
        self.log('Addon URL parsed: {0}'.format(self.buildurl(self.urlpath, self.urlargs)))
        # dispatch addon routing by calling a handler for respective user action
        self.routing = {
            '/': self.listmainmenu,
            '/groups': self.listgroups,
            '/group': None,
            '/lights': self.listlights,
            '/light': self.listlightdetail,
            '/light/on': self.setlighton,
            '/light/color': self.setlightcolor,
        }
        try:
            self.routing[self.urlpath]()
        except KeyError:
            self.log('Addon routing error!', level=xbmc.LOGERROR)
            self.notify(self.addon.getLocalizedString(30023), icon=xbmcgui.NOTIFICATION_ERROR)
            exit()

    def buildurl(self, urlpath, urlargs=None):
        url = self.urlbase + urlpath
        if urlargs is not None and len(list(urlargs)) > 0:
            url += '?' + urllib.urlencode(urlargs)
        return url

    def connecthue(self, ip):
        hue = None
        while hue is None:
            try:
                hue = phue.Bridge(ip)
            except phue.PhueRegistrationException:
                xbmcgui.Dialog().ok(heading=self.addon.getLocalizedString(30020), line1=self.addon.getLocalizedString(30021))
        hue.connect()
        return hue

    def log(self, msg, level=xbmc.LOGDEBUG):
        """
        Log message into default Kodi.log using an uniform style.
        (helper)
        :param msg: str
        :param level: xbmc.LOGDEBUG (default)
        """
        msg = '{0}: {1}'.format(self.addon.getAddonInfo('id'), msg)
        xbmc.log(msg, level)

    def notify(self, msg, icon=xbmcgui.NOTIFICATION_INFO):
        """
        Notify user using uniform style.
        (helper)
        :param msg: str;
        :param icon: int; xbmcgui.NOTIFICATION_INFO (default)
        """
        heading = '{0}'.format(self.addon.getAddonInfo('name'))
        xbmcgui.Dialog().notification(heading, msg, icon)

    # ===== action handlers =====

    def listmainmenu(self):
        """
        List main menu.
        """
        # create list items
        listitems = [
            (self.buildurl('/lights'), xbmcgui.ListItem('{0}'.format(self.addon.getLocalizedString(30030))), FOLDER),
            (self.buildurl('/groups'), xbmcgui.ListItem('{0}'.format(self.addon.getLocalizedString(30031))), FOLDER),
        ]
        # show in kodi
        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.addDirectoryItems(self.handle, listitems, len(listitems))
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(self.handle)

    def listlights(self):
        """
        List lights.
        """
        # request hue api
        lights = self.hue.get_light()
        self.log('Listing Philips Hue lights: {0}'.format(lights))
        # create list items for lights
        listitems = []
        for lightid in lights:
            li = xbmcgui.ListItem(lights[lightid]['name'])
            cmi = []
            if not lights[lightid]['state']['on']:
                # light is off
                cmi.append(('[COLOR blue]{0}[/COLOR]'.format(self.addon.getLocalizedString(30050)), 'RunPlugin({0})'.format(self.buildurl('/light/on', {'lightid': lightid, 'value': '1'}))))
            else:
                # light is on
                cmi.append(('[COLOR blue]{0}[/COLOR]'.format(self.addon.getLocalizedString(30051)), 'RunPlugin({0})'.format(self.buildurl('/light/on', {'lightid': lightid, 'value': '0'}))))
                cmi.append(('[COLOR blue]{0}[/COLOR]'.format(self.addon.getLocalizedString(30052)), 'RunPlugin({0})'.format(self.buildurl('/light/color', {'lightid': lightid}))))
            li.addContextMenuItems(cmi)
            listitems.append(
                (self.buildurl('/light', {'lightid': lightid}), li, FOLDER)
            )
        # show list in kodi
        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.addDirectoryItems(self.handle, listitems, len(listitems))
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(self.handle)

    def listgroups(self):
        """
        List light groups.
        """
        # request hue api
        groups = self.hue.get_group()
        self.log('Listing Philips Hue light groups: {0}'.format(groups))
        # create list items for light groups
        listitems = []
        for groupid in groups:
            listitems.append(
                (
                    self.buildurl('/group', {'groupid': groupid}),
                    xbmcgui.ListItem('{0} [COLOR blue]({1})[/COLOR]'.format(groups[groupid]['name'], len(groups[groupid]['lights']))),
                    FOLDER
                )
            )
        # show list in kodi
        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.addDirectoryItems(self.handle, listitems, len(listitems))
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(self.handle)

    def listlightdetail(self):
        """
        List light detail.
        """
        # get url args
        lightid = int(self.urlargs.get('lightid'))
        # request hue api
        light = self.hue.get_light(lightid)
        self.log('Listing detail for Philips Hue light: lightid:{0}, {1}'.format(lightid, light))
        # create list items
        listitems = []
        # show in kodi
        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.addDirectoryItems(self.handle, listitems, len(listitems))
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(self.handle)

    def setlighton(self):
        """
        Set light on/off.
        """
        # get url args
        lightid = int(self.urlargs.get('lightid'))
        value = bool(int(self.urlargs.get('value')))
        # request hue api
        param = 'on'
        result = self.hue.set_light(lightid, param, value)
        self.log('Philips Hue light set: lightid:{0}, param:{1}, value:{2}. Result:{3}'.format(lightid, param, value, result))
        xbmc.executebuiltin('Container.refresh')

    def setlightcolor(self):
        """
        Set light color.
        """
        # get url args
        lightid = int(self.urlargs.get('lightid'))
        # load colors
        fp = os.path.join(xbmc.translatePath(self.addon.getAddonInfo('path')), 'resources', 'data', 'colors.json')
        with open(fp) as f:
            colors = json.load(f)
        # show color selector
        i = xbmcgui.Dialog().select(heading='Select color:', list=list(colors))
        if i is not None:
            hexcolor = colors[list(colors).pop(i)]
        # request hue api
        param = 'xy'
        value = colortools.hex2xy(hexcolor)
        result = self.hue.set_light(lightid, param, value)
        self.log('Philips Hue light set: lightid:{0}, param:{1}, value:{2}. Result:{3}'.format(lightid, param, value, result))
        xbmc.executebuiltin('Container.refresh')


class PhilipsHueAddonError(Exception):
    """
    Exception type raised for all addon errors.
    :param errmsg: str
    """
    def __init__(self, errmsg):
        """
        :param errmsg: str
        """
        self.errmsg = errmsg


if __name__ == '__main__':
    # run addon
    PhilipsHueAddon()
