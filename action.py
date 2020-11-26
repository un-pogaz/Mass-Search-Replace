#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2020, un_pogaz <>'
__docformat__ = 'restructuredtext en'

import os, sys, time

try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9

from functools import partial
from datetime import datetime
try:
    from PyQt5.Qt import QToolButton, QMenu, QProgressDialog, QTimer
except ImportError:
    from PyQt4.Qt import QToolButton, QMenu, QProgressDialog, QTimer

from calibre.ebooks.metadata.book.base import Metadata
from calibre.gui2 import error_dialog
from calibre.gui2.actions import InterfaceAction
from calibre.library import current_library_name

from calibre_plugins.mass_search_replace.config import PLUGIN_ICONS, PREFS, KEY
from calibre_plugins.mass_search_replace.common_utils import set_plugin_icon_resources, get_icon, create_menu_action_unique, debug_print
from calibre_plugins.mass_search_replace.SearchReplace import SearchReplaceAction, KEY_QUERY


class MassSearchReplaceAction(InterfaceAction):
    
    name = 'Mass Search/Replace'
    # Create our top-level menu/toolbar action (text, icon_path, tooltip, keyboard shortcut)
    action_spec = ('Mass Search/Replace', None, _('Applie a list of saved Search/Replace operations'), None)
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
        chain_items = PREFS[KEY.MASS_SEARCH_REPLACE]
        self.menu.clear()
        self.chain_menu = []
        sub_menus = {}
        
        for action in self.menu_actions:
            self.gui.keyboard.unregister_shortcut(action.calibre_shortcut_unique_name)
            # starting in calibre 2.10.0, actions are registers at
            # the top gui level for OSX' benefit.
            if calibre_version >= (2,10,0):
                self.gui.removeAction(action)
        self.menu_actions = []
        
        for chain in chain_items:
            debug_print('Rebuilding menu for ({})'.format(chain[KEY.MENU_TEXT]))
            ## check chains for errors
            ## Note: this is commented out, we are going to defer checking the chain
            ## to just before we run them, because chains that contain calibre actions
            ## return invalid settings status when this method runs at initialization
            ## as the menu entries of the some plugin are not yet available
            
            if chain[KEY.MENU_ACTIVE]:
                self.append_menu_item_ex(self.menu, sub_menus, chain[KEY.MENU_TEXT], chain[KEY.MENU_SUBMENU], chain[KEY.MENU_IMAGE], chain)
        
        self.menu.addSeparator()
        
        ac = create_menu_action_unique(self, self.menu, _('&Customize plugin...'), 'config.png',
                                             triggered=self.show_configuration,
                                             shortcut=False)
        self.menu_actions.append(ac)
        self.gui.keyboard.finalize()
    
    def append_menu_item_ex(self, m, sub_menus, menu_text, sub_menu_text, image_name, chain):
        parent_menu = m
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
            ac = parent_menu.addSeparator()
        else:
            ac = create_menu_action_unique(self, parent_menu, menu_text, image_name,
                           unique_name=menu_text,
                           triggered=partial(self.run_SearchReplace, chain))
            # Maintain our list of menus by chain references so we can easily enable/disable menus when user right-clicks.
            self.menu_actions.append(ac)
            self.chain_menu.append((chain, ac))
        return ac
    
    def set_enabled_for_all_menu_actions(self, is_enabled):
        for chain_data, menu_action in self.chain_menu:
            chain_settings = chain_data['chain_settings']
            menu_action.setEnabled(is_enabled)
    
    def is_menu_enabled(self, chain_settings):
        '''
        Determine whether menu item for the chain is enabled or not
        '''
#        chain_links = chain_settings.get('chain_links', [])
#        for chain_link in chain_links:
#            action_name = chain_link['action_name']
#            action_settings = chain_link['action_settings']
#            action = self.all_actions[action_name]
#            pass
        return True
    
    def run_SearchReplace(self, chain):
        
        # check chains for errors
        chain_chk = check_chain(chain)
        if chain_chk is not True:
            return error_dialog(self.gui, _('Chain Error'), _('Validating the chain settings before running failed. You can see the detailed errors by opening the chain in the config dialog'),
                show=True)
        
        
        if not self.is_library_selected:
            return error_dialog(self.gui, _('No selected book'), _('No book selected for cleaning comments'), show=True)
            return
        
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows or len(rows) == 0:
            return error_dialog(self.gui, _('No selected book'), _('No book selected for cleaning comments'), show=True)
        book_ids = self.gui.library_view.get_selected_ids()
        
        srpg = SearchReplacesProgressDialog(self, book_ids, chain)
        srpg.close()
        del srpg
    
    def show_configuration(self):
        self.interface_action_base_plugin.do_user_config(self.gui)
        

def check_chain(chain):
    #try:
    chain_name = chain[KEY.MENU_TEXT]
    for search_replace in chain[KEY.MENU_SEARCH_REPLACES]:
        for key in KEY_QUERY.ALL:
            if key not in search_replace.keys():
                debug_print('chain "{}": settings are not valide, the {} is missing'.format(chain_name, key))
                return False
    #except Exception as e:
    #    debug_print('Exception when checking chain: {}'.format(e))
    #    return False
    return True

class SearchReplacesProgressDialog(QProgressDialog):
    
    def __init__(self, plugin_action, book_ids, chain):
        
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
        self.menu_text = chain[KEY.MENU_TEXT]
        
        # name of the search/replace
        self.search_replaces = chain[KEY.MENU_SEARCH_REPLACES]
        # Count of search/replace
        self.search_replaces_count = len(self.search_replaces)
        
        # Count of search/replace
        self.total_operation_count = self.book_count*self.search_replaces_count
        
        # Exception
        self.exception = None
        
        QProgressDialog.__init__(self, '', _('Aborting...'), 0, self.book_count, self.gui)
        
        self.setWindowTitle(_('Mass Search/Replace Progress'))
        self.setWindowIcon(get_icon(PLUGIN_ICONS[0]))
        
        self.setValue(0)
        self.setMinimumWidth(500)
        self.setMinimumDuration(100)
        
        self.setAutoClose(True)
        self.setAutoReset(False)
        
        self.hide()
        debug_print('Launch Search/Replace for {0} books.'.format(self.book_count))
        debug_print(str(self.search_replaces)+'\n')
        
        QTimer.singleShot(0, self._run_search_replaces)
        self.exec_()
        
        if self.wasCanceled():
            debug_print('Mass Search/Replace as cancelled. No change.')
        elif self.exception:
            debug_print('Mass Search/Replace as cancelled. An exception has occurred:')
            debug_print(self.exception)
        else:
            debug_print('Search/Replace launched for {0} books.'.format(self.book_count))
            debug_print('Search/Replace performed for {0} books with a total of {1} fields modify.'.format(self.books_update, self.fields_update))
            debug_print('{0}\n'.format(self.search_replaces))
        
    def _run_search_replaces(self):
        
        try:
            self.setValue(0)
            lst_id= []
            
            for num, book_id in enumerate(self.book_ids, start=1):
                for sr_op, search_replace in enumerate(self.search_replaces, start=1):
                    
                    # update Progress
                    self.setValue(num)
                    self.setLabelText(_('Book {0} of {1}. Search/Replace {2} of {3}').format(num, self.book_count, sr_op, self.search_replaces_count))
                    
                    if self.total_operation_count < 100:
                        self.hide()
                    else:
                        self.show()
                    
                    if self.wasCanceled():
                        self.close()
                        return
                    
                    action = SearchReplaceAction(self.plugin_action)
                    action.run(self.gui, search_replace, self.book_ids, self)
                    
                    for field, book_id_val_map in action.set_field_calls.items():
                        self.dbA.set_field(field, book_id_val_map)
                        self.fields_update += len(book_id_val_map)
                        lst_id += book_id_val_map.keys()
                    
                
            self.books_update = len(list(dict.fromkeys(lst_id)))
            
            #self.dbA.set_field('comments', {id:self.books_dic[id] for id in self.books_dic.keys()})
            self.gui.iactions['Edit Metadata'].refresh_gui(self.book_ids, covers_changed=False)
            
        except Exception as e:
            self.exception = e;
            
        self.db.clean()
        self.hide()
        return
