__all__ = ['PhilipsHueAddon', 'PhilipsHueAddonError']


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


HUE_BRIDGE_IP = '10.0.0.1'

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
        self.hue = self.connecthue(HUE_BRIDGE_IP)
        self.log('Philips Hue connected.')
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
            '/': self.listlights,
            '/light': None,
            '/light/set': self.setlight,
        }
        try:
            self.routing[self.urlpath](**self.urlargs)
        except KeyError:
            self.log('Addon routing error!', level=xbmc.LOGERROR)
            self.notify('Addon routing error!', icon=xbmcgui.NOTIFICATION_ERROR)
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
                xbmcgui.Dialog().ok('Authorize add-on:', 'Please [B]press the button on hub[/B] and then [B]press OK[/B]')
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
        heading = '{0} ({1})'.format(self.addon.getAddonInfo('name'), self.addon.getAddonInfo('id'))
        xbmcgui.Dialog().notification(heading, msg, icon)

    """ ----- Action handlers ----- """

    def listlights(self, **kwargs):
        # get hue lights
        lights = self.hue.get_light()
        self.log('Hue lights: {0}'.format(lights))
        # create list items for lights
        listitems = []
        for lightid in lights:
            li = xbmcgui.ListItem(label=lights[str(lightid)]['name'])
            cmi = []
            cmi.append(('[COLOR blue]Switch ON[/COLOR]', 'RunPlugin({0})'.format(self.buildurl('/light/set', {'lightid': lightid, 'param': 'on', 'value': True}))))
            cmi.append(('[COLOR blue]Switch OFF[/COLOR]', 'RunPlugin({0})'.format(self.buildurl('/light/set', {'lightid': lightid, 'param': 'on', 'value': False}))))
            li.addContextMenuItems(cmi)
            listitems.append(
                (self.buildurl('/light', {'lightid': lightid}), li, FOLDER)
            )
        # show list in kodi
        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.addDirectoryItems(self.handle, listitems, len(listitems))
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(self.handle)

    def setlight(self, **kwargs):
        # set light
        lightid = kwargs.get('lightid', None)
        param = kwargs.get('param', None)
        value = kwargs.get('value', None)
        if lightid is not None:
            # value type mangling
            boolparams = ['on']
            intparams = []
            if param in boolparams:
                value = True if value == 'True' else False
            elif param in intparams:
                value = int(value)
            result = self.hue.set_light(int(lightid), param, bool(value))
            self.log('Setting light id:{0} param:{1} value:{2}. Result:{3}'.format(lightid, param, value, result))
            # self.notify('Light set OK')


class PhilipsHueAddonError(Exception):
    """
    Exception type raised for all addon errors.
    :param errmsg: str
    """
    def __init__(self, errmsg):
        self.errmsg = errmsg


if __name__ == '__main__':
    # run addon
    PhilipsHueAddon()
