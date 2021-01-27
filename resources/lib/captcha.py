# -*- coding: utf-8 -*-
import xbmcgui, xbmc, xbmcvfs, os

class CaptchaWindow( xbmcgui.WindowXMLDialog ):

    def __init__(self, *args, **kwargs):
        self.img = kwargs.get('captcha')
        title_text = kwargs.get('title_text')
        self.kbd = xbmc.Keyboard('',title_text,False)

    def onInit(self):
        self.getControl(101).setImage(self.img)

    def get(self):
        self.show()
        xbmc.sleep(500)
        self.kbd.doModal()
        if (self.kbd.isConfirmed()):
            text = self.kbd.getText()
            self.close()
            return text
        self.close()
        return False

def ask_for_captcha(addon, img, title):
    current_skin_name = xbmc.getSkinDir()
    if xbmcvfs.exists(xbmcvfs.translatePath(os.path.join(addon.getAddonInfo('path'), 'resources', 'skins', current_skin_name, '720p', 'captcha-image.xml'))):
        default_skin_name = current_skin_name
    else:
        default_skin_name = "default"
    solver = CaptchaWindow('captcha-image.xml',addon.getAddonInfo('path'),default_skin_name,'720p', captcha = img, title_text = title)
    return solver.get()
