#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2011, Grant Drake <grant.drake@gmail.com>'
__docformat__ = 'restructuredtext en'

import os, time, six

try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9

try:
    from PyQt5 import QtWidgets as QtGui
    from PyQt5.Qt import (Qt, QIcon, QPixmap, QLabel, QDialog, QHBoxLayout,
                          QTableWidgetItem, QFont, QLineEdit, QComboBox,
                          QVBoxLayout, QDialogButtonBox, QStyledItemDelegate, QDateTime,
                          QRegExpValidator, QRegExp, QTextEdit,
                          QListWidget, QAbstractItemView)
except ImportError:
    from PyQt4 import QtGui
    from PyQt4.Qt import (Qt, QIcon, QPixmap, QLabel, QDialog, QHBoxLayout,
                          QTableWidgetItem, QFont, QLineEdit, QComboBox,
                          QVBoxLayout, QDialogButtonBox, QStyledItemDelegate, QDateTime,
                          QRegExpValidator, QRegExp, QTextEdit,
                          QListWidget, QAbstractItemView)

from calibre.constants import iswindows, DEBUG
from calibre.gui2 import gprefs, error_dialog, UNDEFINED_QDATETIME, info_dialog
from calibre.gui2.actions import menu_action_unique_name
from calibre.gui2.complete2 import EditWithComplete
from calibre.gui2.keyboard import ShortcutConfig
from calibre.gui2.widgets import EnLineEdit
from calibre.utils.config import config_dir, tweaks
from calibre.utils.date import now, format_date, qt_to_dt, UNDEFINED_DATE
from calibre.utils.icu import sort_key
from calibre import prints

try:
    from calibre.gui2 import QVariant
    del QVariant
except ImportError:
    is_qt4 = False
    convert_qvariant = lambda x: x
else:
    is_qt4 = True
    
    def convert_qvariant(x):
        vt = x.type()
        if vt == x.String:
            return six.text_type(x.toString())
        if vt == x.List:
            return [convert_qvariant(i) for i in x.toList()]
        return x.toPyObject()

# Global definition of our plugin name. Used for common functions that require this.
plugin_name = None
# Global definition of our plugin resources. Used to share between the xxxAction and xxxBase
# classes if you need any zip images to be displayed on the configuration dialog.
plugin_icon_resources = {}

BASE_TIME = None
def debug_print(*args):
    global BASE_TIME
    if BASE_TIME is None:
        BASE_TIME = time.time()
    if DEBUG:
        prints('DEBUG MassSearch/Replace: ', *args)
        #prints('DEBUG MassSearch/Replace: %6.1f'%(time.time()-BASE_TIME), *args)

def debug_text(pre, text):
    debug_print(pre+':::\n'+text+'\n')

def set_plugin_icon_resources(name, resources):
    '''
    Set our global store of plugin name and icon resources for sharing between
    the InterfaceAction class which reads them and the ConfigWidget
    if needed for use on the customization dialog for this plugin.
    '''
    global plugin_icon_resources, plugin_name
    plugin_name = name
    plugin_icon_resources = resources


def get_icon(icon_name):
    '''
    Retrieve a QIcon for the named image from the zip file if it exists,
    or if not then from Calibre's image cache.
    '''
    if icon_name:
        pixmap = get_pixmap(icon_name)
        if pixmap is None:
            # Look in Calibre's cache for the icon
            return QIcon(I(icon_name))
        else:
            return QIcon(pixmap)
    return QIcon()


def get_pixmap(icon_name):
    '''
    Retrieve a QPixmap for the named image
    Any icons belonging to the plugin must be prefixed with 'images/'
    '''
    global plugin_icon_resources, plugin_name
    
    if not icon_name.startswith('images/'):
        # We know this is definitely not an icon belonging to this plugin
        pixmap = QPixmap()
        pixmap.load(I(icon_name))
        return pixmap
    
    # Check to see whether the icon exists as a Calibre resource
    # This will enable skinning if the user stores icons within a folder like:
    # ...\AppData\Roaming\calibre\resources\images\Plugin Name\
    if plugin_name:
        local_images_dir = get_local_images_dir(plugin_name)
        local_image_path = os.path.join(local_images_dir, icon_name.replace('images/', ''))
        if os.path.exists(local_image_path):
            pixmap = QPixmap()
            pixmap.load(local_image_path)
            return pixmap
    
    # As we did not find an icon elsewhere, look within our zip resources
    if icon_name in plugin_icon_resources:
        pixmap = QPixmap()
        pixmap.loadFromData(plugin_icon_resources[icon_name])
        return pixmap
    return None


def get_local_images_dir(subfolder=None):
    '''
    Returns a path to the user's local resources/images folder
    If a subfolder name parameter is specified, appends this to the path
    '''
    images_dir = os.path.join(config_dir, 'resources/images')
    if subfolder:
        images_dir = os.path.join(images_dir, subfolder)
    if iswindows:
        images_dir = os.path.normpath(images_dir)
    return images_dir

def get_library_uuid(db):
    try:
        library_uuid = db.library_id
    except:
        library_uuid = ''
    return library_uuid

def create_menu_action_unique(ia, parent_menu, menu_text, image=None, tooltip=None,
                              shortcut=None, shortcut_name=None, triggered=None, is_checked=None,
                              unique_name=None, favourites_menu_unique_name=None,submenu=None, enabled=True):
    '''
    Create a menu action with the specified criteria and action, using the new
    InterfaceAction.create_menu_action() function which ensures that regardless of
    whether a shortcut is specified it will appear in Preferences->Keyboard
    '''
    orig_shortcut = shortcut
    kb = ia.gui.keyboard
    if unique_name is None:
        unique_name = menu_text
    if not shortcut == False:
        full_unique_name = menu_action_unique_name(ia, unique_name)
        if full_unique_name in kb.shortcuts:
            shortcut = False
        else:
            if shortcut is not None and not shortcut == False:
                if len(shortcut) == 0:
                    shortcut = None
                else:
                    shortcut = _(shortcut)
    
    if shortcut_name is None:
        shortcut_name = menu_text.replace('&','')
    
    ac = ia.create_menu_action(parent_menu, unique_name, menu_text, icon=None, shortcut=shortcut,
        description=tooltip, triggered=triggered, shortcut_name=shortcut_name)
    if shortcut == False and not orig_shortcut == False:
        if ac.calibre_shortcut_unique_name in ia.gui.keyboard.shortcuts:
            kb.replace_action(ac.calibre_shortcut_unique_name, ac)
    if image:
        ac.setIcon(get_icon(image))
    if is_checked is not None:
        ac.setCheckable(True)
        if is_checked:
            ac.setChecked(True)
            
    if submenu:
        ac.setMenu(submenu)
        
    if not enabled:
        ac.setEnabled(False)
    else:
        ac.setEnabled(True)
    return ac

class ImageTitleLayout(QHBoxLayout):
    '''
    A reusable layout widget displaying an image followed by a title
    '''
    def __init__(self, parent, icon_name, title):
        QHBoxLayout.__init__(self)
        self.title_image_label = QLabel(parent)
        self.update_title_icon(icon_name)
        self.addWidget(self.title_image_label)
        
        title_font = QFont()
        title_font.setPointSize(16)
        shelf_label = QLabel(title, parent)
        shelf_label.setFont(title_font)
        self.addWidget(shelf_label)
        self.insertStretch(-1)
    
    def update_title_icon(self, icon_name):
        #debug_print("Icon: ", icon_name)
        pixmap = get_pixmap(icon_name)
        if pixmap is None:
            error_dialog(self.parent(), _('Restart required'),
                         _('Title image not found - you must restart Calibre before using this plugin!'), show=True)
        else:
            self.title_image_label.setPixmap(pixmap)
        self.title_image_label.setMaximumSize(32, 32)
        self.title_image_label.setScaledContents(True)

class SizePersistedDialog(QDialog):
    '''
    This dialog is a base class for any dialogs that want their size/position
    restored when they are next opened.
    '''
    def __init__(self, parent, unique_pref_name):
        QDialog.__init__(self, parent)
        self.unique_pref_name = unique_pref_name
        self.geom = gprefs.get(unique_pref_name, None)
        self.finished.connect(self.dialog_closing)
    
    def resize_dialog(self):
        if self.geom is None:
            self.resize(self.sizeHint())
        else:
            self.restoreGeometry(self.geom)
    
    def dialog_closing(self, result):
        geom = bytearray(self.saveGeometry())
        gprefs[self.unique_pref_name] = geom
        self.persist_custom_prefs()
    
    def persist_custom_prefs(self):
        '''
        Invoked when the dialog is closing. Override this function to call
        save_custom_pref() if you have a setting you want persisted that you can
        retrieve in your __init__() using load_custom_pref() when next opened
        '''
        pass
    
    def load_custom_pref(self, name, default=None):
        return gprefs.get(self.unique_pref_name+':'+name, default)
    
    def save_custom_pref(self, name, value):
        gprefs[self.unique_pref_name+':'+name] = value

class KeyValueComboBox(QComboBox):
    
    def __init__(self, parent, values, selected_key):
        QComboBox.__init__(self, parent)
        self.values = values
        self.populate_combo(selected_key)
    
    def populate_combo(self, selected_key):
        self.clear()
        selected_idx = idx = -1
        for key, value in six.iteritems(self.values):
            idx = idx + 1
            self.addItem(value)
            if key == selected_key:
                selected_idx = idx
        self.setCurrentIndex(selected_idx)
    
    def selected_key(self):
        for key, value in six.iteritems(self.values):
            if value == six.text_type(self.currentText()).strip():
                return key

class NoWheelComboBox(QComboBox):

    def wheelEvent (self, event):
        # Disable the mouse wheel on top of the combo box changing selection as plays havoc in a grid
        event.ignore()

class KeyboardConfigDialog(SizePersistedDialog):
    '''
    This dialog is used to allow editing of keyboard shortcuts.
    '''
    def __init__(self, gui, group_name):
        SizePersistedDialog.__init__(self, gui, _('Keyboard shortcut dialog'))
        self.gui = gui
        self.setWindowTitle(_('Keyboard shortcuts'))
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        self.keyboard_widget = ShortcutConfig(self)
        layout.addWidget(self.keyboard_widget)
        self.group_name = group_name
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.commit)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Cause our dialog size to be restored from prefs or created on first usage
        self.resize_dialog()
        self.initialize()
    
    def initialize(self):
        self.keyboard_widget.initialize(self.gui.keyboard)
        self.keyboard_widget.highlight_group(self.group_name)
    
    def commit(self):
        self.keyboard_widget.commit()
        self.accept()


import sys
PYTHON = sys.version_info
PYTHON2 = (sys.version_info[0] == 2)
PYTHON3 = (sys.version_info[0] == 3)

import re
# Simple Regex
class regex():
    
    def __init__(self, flag=None):
        
        #set the default flag
        self.flag = flag
        if self.flag == None:
            if PYTHON2:
                self.flag = re.MULTILINE + re.DOTALL
            else:
                self.flag = re.ASCII + re.MULTILINE + re.DOTALL
                # calibre 5 // re.ASCII for Python3 only
            
    
    def match(self, pattern, string, flag=None):
        if flag == None: flag = self.flag
        return re.fullmatch(pattern, string, flag)
    
    def search(self, pattern, string, flag=None):
        if flag == None: flag = self.flag
        return re.search(pattern, string, flag)
    
    def searchall(self, pattern, string, flag=None):
        if flag == None: flag = self.flag
        if self.search(pattern, string, flag):
            return re.finditer(pattern, string, flag)
        else:
            return None
    
    def split(self, pattern, string, maxsplit=0, flag=None):
        if flag == None: flag = self.flag
        return re.split(pattern, string, maxsplit, flag)
    
    def simple(self, pattern, repl, string, flag=None):
        if flag == None: flag = self.flag
        return re.sub(pattern, repl, string, 0, flag)
    
    def loop(self, pattern, repl, string, flag=None):
        if flag == None: flag = self.flag
        i = 0
        while self.search(pattern, string, flag):
            if i > 1000:
                raise regexException('the pattern and substitution string caused an infinite loop', pattern, repl)
            string = self.simple(pattern, repl, string, flag)
            i+=1
            
        return string

class regexException(BaseException):
    def __init__(self, msg, pattern=None, repl=None):
        self.pattern = pattern
        self.repl = repl
        self.msg = msg
    
    def __str__(self):
        return self.msg


def CSS_CleanRules(css):
    #remove space and invalid character
    r = regex()
    css = r.loop(r'[.*!()?+<>\\]', r'', css.lower())
    css = r.loop(r'(,|;|:|\n|\r|\s{2,})', r' ', css)
    css = r.simple(r'^\s*(.*?)\s*$', r'\1', css); 
    # split to table and remove duplicate
    css = list(dict.fromkeys(css.split(' ')))
    # sort
    css = sorted(css)
    # join in a string
    css = ' '.join(css)
    return css
