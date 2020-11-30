#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2020, un_pogaz <un.pogaz@gmail.com>'
__docformat__ = 'restructuredtext en'

import os, time
# calibre Python 3 compatibility.
from six import text_type as unicode

try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9

from functools import partial
from datetime import datetime
try:
    from PyQt5.Qt import QToolButton, QMenu, QProgressDialog, QTimer, QSize
except ImportError:
    from PyQt4.Qt import QToolButton, QMenu, QProgressDialog, QTimer, QSize

from calibre.ebooks.metadata.book.base import Metadata
from calibre.constants import numeric_version as calibre_version, isosx, isnewosx
from calibre.gui2 import error_dialog, question_dialog
from calibre.gui2.actions import InterfaceAction
from calibre.library import current_library_name

from calibre_plugins.mass_search_replace.config import PLUGIN_ICONS, PREFS, KEY
from calibre_plugins.mass_search_replace.common_utils import set_plugin_icon_resources, get_icon, create_menu_action_unique, create_menu_item, debug_print
from calibre_plugins.mass_search_replace.SearchReplace import SearchReplaceWidget_NoWindows, operation_string, operation_testGetError, operation_testGetLocalizedFieldError


class MassSearchReplaceAction(InterfaceAction):
    
    name = 'Mass Search/Replace'
    # Create our top-level menu/toolbar action (text, icon_path, tooltip, keyboard shortcut)
    action_spec = ('Mass Search/Replace', None, _('Applie a list of multiple saved Search/Replace operations'), None)
    popup_type = QToolButton.InstantPopup
    action_type = 'current'
    dont_add_to = frozenset(['context-menu-device'])
    
    def genesis(self):
        self.is_library_selected = True
        self.menu = QMenu(self.gui)
        
        icon_resources = self.load_resources(PLUGIN_ICONS)
        set_plugin_icon_resources(self.name, icon_resources)
        
        
        # Assign our menu to this action and an icon
        self.qaction.setMenu(self.menu)
        self.qaction.setIcon(get_icon(PLUGIN_ICONS[0]))
    
    def initialization_complete(self):
        # we implement here to have access to current_db
        # if we try this in genesis() we get the error:
        # AttributeError: 'Main' object has no attribute 'current_db'
        self.menu_actions = []
        self.rebuild_menus()
    
    def rebuild_menus(self):
        query_list = PREFS[KEY.MASS_SEARCH_REPLACE]
        self.menu.clear()
        self.query_menu = []
        sub_menus = {}
        
        for i, action in enumerate(self.menu_actions, 0):
            if hasattr(action, 'calibre_shortcut_unique_name'):
                self.gui.keyboard.unregister_shortcut(action.calibre_shortcut_unique_name)
            # starting in calibre 2.10.0, actions are registers at
            # the top gui level for OSX' benefit.
            if calibre_version >= (2,10,0) and i < len(self.menu_actions)-1:
                self.gui.removeAction(action)
            
        
        self.menu_actions = []
        
        for query in query_list:
            if not query_testGetError(query) and query[KEY.MENU_ACTIVE]:
                self.append_menu_item_ex(self.menu, sub_menus, query[KEY.MENU_TEXT], query[KEY.MENU_SUBMENU], query[KEY.MENU_IMAGE], query)
        
        self.menu.addSeparator()
        
        ac = create_menu_action_unique(self, self.menu, _('&Customize plugin...'), 'config.png',
                                             triggered=self.show_configuration,
                                             shortcut=False)
        self.menu_actions.append(ac)
        self.gui.keyboard.finalize()
    
    def append_menu_item_ex(self, parent_menu, sub_menus, menu_text, sub_menu_text, image_name, query):
        
        ac = None
        if sub_menu_text:
            # Create the sub-menu if it does not exist
            if sub_menu_text not in sub_menus:
                ac = create_menu_item(self, parent_menu, sub_menu_text, image_name, shortcut=None)
                sm = QMenu()
                ac.setMenu(sm)
                sub_menus[sub_menu_text] = sm
            # Now set our menu variable so the parent menu item will be the sub-menu
            parent_menu = sub_menus[sub_menu_text]
        
        if not menu_text:
            parent_menu.addSeparator()
        elif len(query[KEY.MENU_SEARCH_REPLACES])>0:
            if sub_menu_text:
                debug_print('Rebuilding menu for: {:s} > {:s}'.format(sub_menu_text, menu_text))
            else:
                debug_print('Rebuilding menu for: {:s}'.format(menu_text))
            
            ac = create_menu_action_unique(self, parent_menu, menu_text, image_name,
                           unique_name=menu_text,
                           triggered=partial(self.run_SearchReplace, query))
        
        if ac:
            # Maintain our list of menus by query references so we can easily enable/disable menus when user right-clicks.
            self.menu_actions.append(ac)
            self.query_menu.append((query, ac))
    
    
    def run_SearchReplace(self, query):
        
        if not self.is_library_selected:
            return error_dialog(self.gui, _('No selected book'),
                _('No book selected for Search/Replace.'), show=True)
            return
        
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows or len(rows) == 0:
            return error_dialog(self.gui, _('No selected book'),
                _('No book selected for Search/Replace.'), show=True)
        
        book_ids = self.gui.library_view.get_selected_ids()
        
        srpg = SearchReplacesProgressDialog(self, book_ids, query)
        srpg.close()
        del srpg
    
    def show_configuration(self):
        self.interface_action_base_plugin.do_user_config(self.gui)


def query_testGetError(query):
    try:
        val = query[KEY.MENU_ACTIVE]
        val = query[KEY.MENU_TEXT]
        val = query[KEY.MENU_SUBMENU]
        val = query[KEY.MENU_IMAGE]
        
        for operation in query[KEY.MENU_SEARCH_REPLACES]:
            err = operation_testGetError(operation)
            if err:
                return err
            
    except Exception as ex:
        return ex
    return None


class SearchReplacesProgressDialog(QProgressDialog):
    def __init__(self, plugin_action, book_ids, query):
        
        # plugin_action
        self.plugin_action = plugin_action
        # gui
        self.gui = plugin_action.gui
        
        # DB
        self.db = self.gui.current_db
        # DB API
        self.dbA = self.gui.current_db.new_api
        # liste of book id
        self.book_ids = book_ids
        # Count book
        self.book_count = len(self.book_ids)
        
        # Count update
        self.books_update = 0
        self.fields_update = 0
        
        # name of the search/replace
        self.menu_text = query[KEY.MENU_TEXT]
        
        # name of the search/replace
        self.operation_list = query[KEY.MENU_SEARCH_REPLACES]
        # Count of search/replace
        self.search_replaces_count = len(self.operation_list)
        
        # Count of search/replace
        self.total_operation_count = self.book_count*self.search_replaces_count
        
        # Exception
        self.exception = None
        
        QProgressDialog.__init__(self, '', _('Cancel'), 0, self.book_count, self.gui)
        
        self.setWindowTitle(_('Mass Search/Replace Progress'))
        self.setWindowIcon(get_icon(PLUGIN_ICONS[0]))
        
        self.setValue(0)
        self.setMinimumWidth(500)
        self.setMinimumDuration(100)
        
        self.setAutoClose(True)
        self.setAutoReset(False)
        
        self.hide()
        debug_print('Launch Search/Replace for {:d} books.'.format(self.book_count))
        debug_print(str(self.operation_list)+'\n')
        
        QTimer.singleShot(0, self._run_search_replaces)
        self.exec_()
        
        if self.wasCanceled():
            debug_print('Mass Search/Replace was cancelled. No change.')
        elif self.exception:
            debug_print('Mass Search/Replace was interupted. An exception has occurred:')
            debug_print(self.exception)
            raise self.exception
        else:
            debug_print('Search/Replace launched for {:d} books.'.format(self.book_count))
            debug_print('Search/Replace performed for {:d} books with a total of {:d} fields modify.'.format(self.books_update, self.fields_update))
            debug_print('Search/Replace execute in {:0.3f} seconds.'.format(self.time_execut))
            debug_print('{0}\n'.format(self.operation_list))
        
    def _run_search_replaces(self):
        start = time.time()
        try:
            self.setValue(0)
            
            alreadyRaiseError = False
            
            s_r = SearchReplaceWidget_NoWindows(self.plugin_action)
            s_r_load_settings = s_r.load_settings
            sr_testGetError = s_r.testGetError
            
            sr_search_replace = s_r.search_replace
            sr_updated_fields = s_r.updated_fields
            sr_close = s_r.close
            del s_r
            
            for num, book_id in enumerate(self.book_ids, 1):
                
                # update Progress
                self.setValue(num)
                
                miA = self.dbA.get_proxy_metadata(book_id)
                book_info = '"'+miA.get('title')+'" ('+' & '.join(miA.get('authors'))+') [book: '+str(num)+'/'+str(self.book_count)+']{id: '+str(book_id)+'}'
                
                debug_print('Search/Replace for '+book_info)
                
                for sr_op, operation in enumerate(self.operation_list, 1):
                    
                    err = operation_testGetLocalizedFieldError(operation)
                    if not err:
                        s_r_load_settings(operation)
                        err = sr_testGetError()
                    
                    if not alreadyRaiseError and err:
                        if question_dialog(self.gui, _('Invalid operation'),
                                _('An invalid operation was detected:\n{0}\n\nDo you want to continue the Search/Replace operation? Other errors may exist and will be ignoreds.').format(err),
                                default_yes=False, show_copy_button=True, override_icon=get_icon('dialog_warning.png') ):
                            
                            alreadyRaiseError = True
                            
                        else:
                            self.close()
                            self.db.clean()
                            sr_close()
                            return
                    
                    if not err:
                        
                        if sr_op==len(self.operation_list): nl ='\n'
                        else: nl =''
                        
                        debug_print('Operation N°{:d} > {:s}'.format(sr_op, operation_string(operation))+nl)
                        self.setLabelText(_('Book {:d} of {:d}. Search/Replace {:d} on {:d}.').format(num, self.book_count, sr_op, self.search_replaces_count))
                        
                        if self.total_operation_count < 100:
                            self.hide()
                        else:
                            self.show()
                        
                        if self.wasCanceled():
                            self.close()
                            self.db.clean()
                            sr_close()
                            return
                        
                        sr_search_replace(book_id)
                        
                
            
            lst_id= []
            for field, book_id_val_map in sr_updated_fields.items():
                lst_id += book_id_val_map.keys()
            self.fields_update = len(lst_id)
            
            lst_id = list(dict.fromkeys(lst_id));
            self.books_update = len(lst_id)
            
            if self.books_update > 0:
                
                debug_print('Update the database for {:d} books...\n'.format(self.books_update))
                self.setLabelText(_('Update the library for {:d} books...').format(self.books_update))
                
                for field, book_id_val_map in sr_updated_fields.items():
                    self.dbA.set_field(field, book_id_val_map)
                
                self.gui.iactions['Edit Metadata'].refresh_gui(lst_id, covers_changed=False)
            
        except Exception as e:
            self.exception = e;
        
        sr_close()
        self.time_execut = round(time.time() - start, 3)
        self.db.clean()
        self.hide()
        return
