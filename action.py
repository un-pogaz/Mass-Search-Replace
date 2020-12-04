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
from collections import defaultdict
try:
    from PyQt5.Qt import QToolButton, QMenu, QProgressDialog, QTimer, QSize
except ImportError:
    from PyQt4.Qt import QToolButton, QMenu, QProgressDialog, QTimer, QSize

from calibre import prints
from calibre.ebooks.metadata.book.base import Metadata
from calibre.constants import numeric_version as calibre_version
from calibre.gui2 import error_dialog, warning_dialog, question_dialog
from calibre.gui2.actions import InterfaceAction
from calibre.library import current_library_name
from polyglot.builtins import iteritems

from calibre_plugins.mass_search_replace.config import ICON, PREFS, KEY, ERROR_UPDATE, ERROR_OPERATION, ConfigOperationListDialog, get_default_query
from calibre_plugins.mass_search_replace.common_utils import set_plugin_icon_resources, get_icon, create_menu_action_unique, create_menu_item, debug_print, CustomExceptionErrorDialog
from calibre_plugins.mass_search_replace.SearchReplace import SearchReplaceWidget_NoWindows, operation_list_active, operation_string, operation_testGetError



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
        
        icon_resources = self.load_resources(ICON.ALL)
        set_plugin_icon_resources(self.name, icon_resources)
        
        error_operation = PREFS[KEY.ERROR_OPERATION]
        if error_operation not in ERROR_OPERATION.LIST.keys():
            PREFS[KEY.ERROR_OPERATION] = PREFS.defaults[KEY.ERROR_OPERATION]
        
        error_update = PREFS[KEY.ERROR_UPDATE]
        if error_update not in ERROR_UPDATE.LIST.keys():
            PREFS[KEY.ERROR_UPDATE] = PREFS.defaults[KEY.ERROR_UPDATE]
        
        
        # Assign our menu to this action and an icon
        self.qaction.setMenu(self.menu)
        self.qaction.setIcon(get_icon(ICON.PLUGIN))
    
    def initialization_complete(self):
        # we implement here to have access to current_db
        # if we try this in genesis() we get the error:
        # AttributeError: 'Main' object has no attribute 'current_db'
        self.menu_actions = []
        self.rebuild_menus()
    
    def rebuild_menus(self):
        query_list = PREFS[KEY.MENU]
        self.menu.clear()
        self.query_menu = []
        sub_menus = {}
        
        
        for i, action in enumerate(self.menu_actions, 0):
            if hasattr(action, 'calibre_shortcut_unique_name'):
                self.gui.keyboard.unregister_shortcut(action.calibre_shortcut_unique_name)
            # starting in calibre 2.10.0, actions are registers at the top gui level for OSX' benefit.
            if calibre_version >= (2,10,0) :
                self.gui.removeAction(action)
        
        self.menu_actions = []
        
        debug_print('Rebuilding menu')
        for query in query_list:
            if not query_testGetError(query) and query[KEY.MENU_ACTIVE]:
                self.append_menu_item_ex(self.menu, sub_menus, query)
        
        self.menu.addSeparator()
        
        ac = create_menu_action_unique(self, self.menu, _('&Quick Search/Replace...'), ICON.PLUGIN,
                                             triggered=self.quickSearchReplace,
                                             unique_name='&Quick Search/Replace')
        self.menu_actions.append(ac)
        
        self.menu.addSeparator()
        
        ac = create_menu_action_unique(self, self.menu, _('&Customize plugin...'), 'config.png',
                                             triggered=self.show_configuration,
                                             unique_name='&Customize plugin')
        self.menu_actions.append(ac)
        self.gui.keyboard.finalize()
    
    def append_menu_item_ex(self, parent_menu, sub_menus, query):
        
        menu_text = query[KEY.MENU_TEXT]
        sub_menu_text = query[KEY.MENU_SUBMENU]
        image_name = query[KEY.MENU_IMAGE]
        
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
                name = '{:s} > {:s}'.format(sub_menu_text, menu_text)
            else:
                name = '{:s}'.format(menu_text)
            
            name = name.replace('&','')
            debug_print('Rebuilding menu for:', name)
            
            ac = create_menu_action_unique(self, parent_menu, menu_text, image_name,
                           triggered=partial(self.run_SearchReplace, query),
                           unique_name=name, shortcut_name=name)
        
        if ac:
            # Maintain our list of menus by query references so we can easily enable/disable menus when user right-clicks.
            self.menu_actions.append(ac)
            self.query_menu.append((query, ac))
    
    def quickSearchReplace(self, parameter_list):
        
        query = get_default_query()
        query[KEY.MENU_TEXT] = None
        query[KEY.MENU_SEARCH_REPLACES] = PREFS[KEY.QUICK]
        
        d = ConfigOperationListDialog(self.menu, self, query=query)
        
        if len(d.operation_list)==0:
            d.add_empty_operation()
        
        if d.exec_() == d.Accepted:
            
            if len(d.operation_list)>0:
                query[KEY.MENU_SEARCH_REPLACES] = d.operation_list
                PREFS[KEY.QUICK] = d.operation_list
                
                self.run_SearchReplace(query)
    
    def run_SearchReplace(self, query):
        
        if not self.is_library_selected:
            return error_dialog(self.gui, _('Could not to launch Mass Search/Replace'), _('No book selected'), show=True, show_copy_button=False)
        
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows or len(rows) == 0:
            return error_dialog(self.gui, _('Could not to launch Mass Search/Replace'), _('No book selected'), show=True, show_copy_button=False)
        book_ids = self.gui.library_view.get_selected_ids()
        
        book_ids = self.gui.library_view.get_selected_ids()
        
        srpg = SearchReplacesProgressDialog(self, book_ids, query)
        srpg.close()
        del srpg
    
    def show_configuration(self):
        self.interface_action_base_plugin.do_user_config(self.gui)


def query_testGetError(query):
    
    difference = set(KEY.ALL_MENU).difference(query)
    for key in difference:
        return Exception(_('Invalide configuration, the "{:s}" key is missing.').format(key))
    
    return None


class SearchReplacesProgressDialog(QProgressDialog):
    def __init__(self, plugin_action, book_ids, query):
        
        # plugin_action
        self.plugin_action = plugin_action
        # gui
        self.gui = plugin_action.gui
        
        # DB
        self.db = plugin_action.gui.current_db
        # DB API
        self.dbA = plugin_action.gui.current_db.new_api
        # liste of book id
        self.book_ids = book_ids
        # Count book
        self.book_count = len(self.book_ids)
        
        # Count update
        self.books_update = 0
        self.fields_update = 0
        
        # is a quick Search/Replace
        self.quickSearchReplace = query[KEY.MENU_TEXT] == None
        
        
        # operation list of search/replace
        self.operation_list = operation_list_active(query[KEY.MENU_SEARCH_REPLACES])
        
        # Count of search/replace
        self.operation_count = len(self.operation_list)
        
        # Count of search/replace
        self.total_operation_count = self.book_count*self.operation_count
        
        # Search/Replace Widget
        self.s_r = SearchReplaceWidget_NoWindows(self.plugin_action)
        
        self.time_execut = 0
        
        # operation error
        self.operationStrategy = PREFS[KEY.ERROR_OPERATION]
        self.operationErrorList = []
        
        # Exception
        self.exceptionStrategy = PREFS[KEY.ERROR_UPDATE]
        self.exception = None
        self.exception_list = False
        self.exception_update = False
        self.exception_safely = False
        
        QProgressDialog.__init__(self, '', _('Cancel'), 0, self.total_operation_count, self.gui)
        
        self.setWindowTitle(_('Mass Search/Replace Progress'))
        self.setWindowIcon(get_icon(ICON.PLUGIN))
        
        self.setValue(0)
        self.setMinimumWidth(500)
        self.setMinimumDuration(10)
        
        self.setAutoClose(True)
        self.setAutoReset(False)
        
        self.hide()
        debug_print('Launch Search/Replace for {:d} books with {:d} operation.\n'.format(self.book_count, self.operation_count))
        
        QTimer.singleShot(0, self._run_search_replaces)
        self.exec_()
        
        
        if self.wasCanceled():
            debug_print('Mass Search/Replace was cancelled. No change.')
        
        elif self.exception_list:
            debug_print('Mass Search/Replace was interupted. An exception has occurred:\n'+str(self.exception))
            CustomExceptionErrorDialog(self.gui ,self.exception, custome_msg=_('Unhandled exception')+'\n')
        
        elif self.operationErrorList and self.operationStrategy == ERROR_OPERATION.ABORT:
            debug_print('Mass Search/Replace was interupted. An invalid operation has detected:\n'+str(self.operationErrorList[0]))
            warning_dialog(self.gui, _('Invalid operation'),
                        _('A invalid operations has detected:\n{:s}\n\n'
                          'Mass Search/Replace was canceled.').format(str(self.operationErrorList[0])),
                          show=True, show_copy_button=False)
            
        elif self.exception_update:
            debug_print('Mass Search/Replace was interupted. An exception has occurred during the library update:\n'+str(self.exception))
            
            msg = _('Mass Search/Replace encountered an error during the library update.')
            if self.exceptionStrategy == ERROR_UPDATE.RESTORE:
                msg += '\n' + _('The library a was restored to its original state.')
                debug_print('The library a was restored to its original state.')
                
            CustomExceptionErrorDialog(self.gui ,self.exception, custome_title=_('Cannot update the library'), custome_msg=msg+'\n')
        
        else:
            
            debug_print('Search/Replace launched for {:d} books with {:d} operation.'.format(self.book_count, self.operation_count))
            debug_print('Search/Replace performed for {:d} books with a total of {:d} fields modify.'.format(self.books_update, self.fields_update))
            if self.operationErrorList:
                debug_print('!! An invalid operation was detected.'.format(self.time_execut))
            debug_print('Search/Replace execute in {:0.3f} seconds.\n'.format(self.time_execut))
            
            if self.exception_safely:
                debug_print('!! {:d} exceptions have occurred.'.format(len(self.exception)))
                
                det_msg= '\n'.join('Book {:s} | {:s} > {:}'.format(book_info, field, e) for id, book_info, field, e in self.exception )
                
                warning_dialog(self.gui, _('Exceptions during the library update'),
                            _('{:d} exceptions have occurred during the library update.\nSome fields may not have been updated.').format(len(self.exception)),
                              det_msg='-- Mass Search/Replace: Library update exceptions --\n\n'+det_msg, show=True, show_copy_button=True)
            
            elif self.operationErrorList:
                det_msg= '\n'.join( 'Operation {:d}/{:d} > {:s}'.format(n, self.operation_count, err) for n, err in self.operationErrorList)
                
                warning_dialog(self.gui, _('Invalid operation'),
                            _('{:d} invalid operations has detected and have been ignored.').format(len(self.operationErrorList)),
                            det_msg='-- Mass Search/Replace: Invalid operations --\n\n'+det_msg, show=True, show_copy_button=True)
            
        
        self.close()
    
    def close(self):
        self.db.clean()
        self.s_r.close()
        QProgressDialog.close(self)
    
    
    def _run_search_replaces(self):
        lst_id = []
        start = time.time()
        alradyOperationError = False
        try:
            self.setValue(0)
            self.show()
            
            for op, operation in enumerate(self.operation_list, 1):
                
                debug_print('Operation {:d}/{:d} > {:s}'.format(op, self.operation_count, operation_string(operation)))
                
                err = operation_testGetError(operation, self.plugin_action)
                if not err:
                    self.s_r.load_settings(operation)
                    err = self.s_r.testGetError()
                
                if err:
                    debug_print('!! Invalide operation: {0}\n'.format(err))
                    self.operationErrorList.append((op, str(err)))
                
                
                if len(self.operationErrorList) == 1 and self.operationStrategy == ERROR_OPERATION.ABORT:
                    return
                elif not alradyOperationError and len(self.operationErrorList) == 1 and self.operationStrategy == ERROR_OPERATION.ASK:
                    alradyOperationError = True
                    start_dialog =  time.time()
                    rslt = question_dialog(self.gui, _('Invalid operation'),
                            _('A invalid operations has detected:\n{:s}\n\n'
                              'Continue the execution of Mass Search/Replace?\n'
                              'Other errors may exist and will be ignored.').format(str(self.operationErrorList[0])),
                              default_yes=True, override_icon=get_icon('dialog_warning.png'))
                    
                    start = start + (time.time() - start_dialog)
                    
                    if not rslt:
                        return
                
                
                if not err:
                    for num, book_id in enumerate(self.book_ids, 1):
                        
                        #update Progress
                        self.setValue( ((op-1)*self.book_count) + num )
                        self.setLabelText(_('Search/Replace {:d} of {:d}. Book {:d} of {:d}.').format(op, self.operation_count, num, self.book_count))
                        
                        if self.total_operation_count < 100:
                            self.hide()
                        else:
                            self.show()
                        
                        miA = self.dbA.get_proxy_metadata(book_id)
                        
                        #Book num/book_count > "title" (author & author) {id: book_id}
                        book_info = 'Book '+str(num)+'/'+str(self.book_count)+ ' > "'+miA.get('title')+'" ('+' & '.join(miA.get('authors'))+') {id: '+str(book_id)+'}'
                        
                        if num==self.book_count: nl ='\n'
                        else: nl =''
                        
                        debug_print(book_info+nl)
                        
                        
                        if self.wasCanceled():
                            self.close()
                            return
                        
                        self.s_r.search_replace(book_id)
        
        except Exception as e:
            self.exception_list = True
            self.exception = e
        
        else:
            
            lst_id = []
            for field, book_id_val_map in iteritems(self.s_r.updated_fields):
                lst_id += book_id_val_map.keys()
            self.fields_update = len(lst_id)
            
            lst_id = list(dict.fromkeys(lst_id));
            self.books_update = len(lst_id)
            
            if self.books_update > 0:
                
                debug_print('Update the database for {:d} books...\n'.format(self.books_update))
                self.setLabelText(_('Update the library for {:d} books...').format(self.books_update))
                self.setValue(self.total_operation_count)
                
                if self.exceptionStrategy == ERROR_UPDATE.SAFELY or self.exceptionStrategy == ERROR_UPDATE.DONT_STOP:
                    
                    self.exception = []
                    dont_stop = self.exceptionStrategy == ERROR_UPDATE.DONT_STOP
                    
                    for id in iter(lst_id):
                        if self.exception and not dont_stop:
                            break
                        for field, book_id_val_map in iteritems(self.s_r.updated_fields):
                            if self.exception and not dont_stop:
                                break
                            if id in book_id_val_map:
                                try:
                                    val = self.s_r.updated_fields[field][id]
                                    self.dbA.set_field(field, {id:val})
                                except Exception as e:
                                    self.exception_safely = True
                                    
                                    miA = self.dbA.get_proxy_metadata(id)
                                    #title (author & author)
                                    book_info = '"'+miA.get('title')+'" ('+' & '.join(miA.get('authors'))+')'
                                    
                                    self.exception.append( (id, book_info, field, e.__class__.__name__ +': '+ str(e)) )
                    
                else:
                    try:
                        
                        backup_fields = None
                        is_restore = self.exceptionStrategy == ERROR_UPDATE.RESTORE
                        if is_restore:
                            backup_fields = defaultdict(dict)
                        
                        for field, book_id_val_map in iteritems(self.s_r.updated_fields):
                            if is_restore:
                                src_field = self.dbA.all_field_for(field, book_id_val_map.keys())
                                backup_fields[field] = src_field
                            
                            self.dbA.set_field(field, book_id_val_map)
                        
                        print(self.s_r.updated_fields)
                        
                    except Exception as e:
                        self.exception_update = True
                        self.exception = e
                        
                        if is_restore:
                            for field, book_id_val_map in iteritems(backup_fields):
                               self.dbA.set_field(field, book_id_val_map)
                
                self.gui.iactions['Edit Metadata'].refresh_gui(lst_id, covers_changed=False)
                
            
        
        finally:
            self.time_execut = round(time.time() - start, 3)
            self.hide()
