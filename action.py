#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2020, un_pogaz <un.pogaz@gmail.com>'
__docformat__ = 'restructuredtext en'

import copy, time
# python3 compatibility
from six.moves import range
from six import text_type as unicode

try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9

from datetime import datetime
from collections import defaultdict, OrderedDict
from functools import partial
from polyglot.builtins import iteritems, itervalues

try:
    from qt.core import QToolButton, QMenu, QProgressDialog, QTimer, QSize
except ImportError:
    from PyQt5.Qt import QToolButton, QMenu, QProgressDialog, QTimer, QSize

from calibre import prints
from calibre.ebooks.metadata.book.base import Metadata
from calibre.gui2 import error_dialog, warning_dialog, question_dialog, info_dialog
from calibre.gui2.actions import InterfaceAction
from calibre.gui2.ui import get_gui
from calibre.library import current_library_name

from .config import ICON, PREFS, KEY_MENU, KEY_ERROR, ERROR_UPDATE, ERROR_OPERATION, ConfigOperationListDialog, get_default_menu
from .common_utils import (debug_print, get_icon, PLUGIN_NAME, current_db, load_plugin_resources, calibre_version,
                            get_BookIds_selected, get_BookIds_all, get_BookIds_virtual, get_BookIds_search, get_curent_virtual, set_marked,
                            create_menu_item, create_menu_action_unique, CustomExceptionErrorDialog)
from .SearchReplace import SearchReplaceWidget_NoWindows, operation_list_active, operation_string, operation_testGetError
from . import SearchReplaceCalibreText as CalibreText

GUI = get_gui()

class MassSearchReplaceAction(InterfaceAction):
    
    name = 'Mass Search/Replace'
    
    # Create our top-level menu/toolbar action (text, icon_path, tooltip, keyboard shortcut)
    action_spec = (name, None, _('Apply a list of multiple saved Find and Replace operations'), None)
    popup_type = QToolButton.InstantPopup
    action_type = 'current'
    dont_add_to = frozenset(['context-menu-device'])
    
    def genesis(self):
        self.is_library_selected = True
        self.menu = QMenu(GUI)
        
        load_plugin_resources(self.plugin_path, ICON.ALL)
        
        error_operation = PREFS[KEY_ERROR.ERROR][KEY_ERROR.OPERATION]
        if error_operation not in ERROR_OPERATION.LIST.keys():
            PREFS[KEY_ERROR.ERROR][KEY_ERROR.OPERATION] = ERROR_OPERATION.DEFAULT
        
        error_update = PREFS[KEY_ERROR.ERROR][KEY_ERROR.UPDATE]
        if error_update not in ERROR_UPDATE.LIST.keys():
            PREFS[KEY_ERROR.ERROR][KEY_ERROR.UPDATE] = ERROR_UPDATE.DEFAULT
        
        
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
        menu_list = PREFS[KEY_MENU.MENU]
        self.menu.clear()
        sub_menus = {}
        
        
        for i, action in enumerate(self.menu_actions, 0):
            if hasattr(action, 'calibre_shortcut_unique_name'):
                GUI.keyboard.unregister_shortcut(action.calibre_shortcut_unique_name)
            # starting in calibre 2.10.0, actions are registers at the top gui level for OSX' benefit.
            if calibre_version >= (2,10,0) :
                GUI.removeAction(action)
        
        self.menu_actions = []
        
        debug_print('Rebuilding menu')
        for menu in menu_list:
            if not menu_testGetError(menu) and menu[KEY_MENU.ACTIVE]:
                self.append_menu_item_ex(self.menu, sub_menus, menu)
        
        self.menu.addSeparator()
        
        ac = create_menu_item(self, self.menu, _('&Quick Search/Replace...'), ICON.PLUGIN)
        mn_books = QMenu()
        ac.setMenu(mn_books)
        
        ac = create_menu_action_unique(self, mn_books, _('&Selection'), 'highlight_only_on.png',
                                             triggered=self.quick_selected,
                                             unique_name='&Quick Search/Replace in all books>&Selection')
        self.menu_actions.append(ac)
        
        ac = create_menu_action_unique(self, mn_books, _('&Current search'), 'search.png',
                                             triggered=self.quick_search,
                                             unique_name='&Quick Search/Replace in all books>&Current search')
        self.menu_actions.append(ac)
        
        ac = create_menu_action_unique(self, mn_books, _('&Virtual library'), 'vl.png',
                                             triggered=self.quick_virtual,
                                             unique_name='&Quick Search/Replace in all books>&Virtual library')
        self.menu_actions.append(ac)
        
        ac = create_menu_action_unique(self, mn_books, _('&Library'), 'library.png',
                                             triggered=self.quick_library,
                                             unique_name='&Quick Search/Replace in all books>&Library')
        self.menu_actions.append(ac)
        
        self.menu.addSeparator()
        
        ac = create_menu_action_unique(self, self.menu, _('&Customize plugin...'), 'config.png',
                                             triggered=self.show_configuration,
                                             unique_name='&Customize plugin')
        self.menu_actions.append(ac)
        GUI.keyboard.finalize()
    
    def append_menu_item_ex(self, parent_menu, sub_menus, menu):
        
        menu_text = menu[KEY_MENU.TEXT]
        sub_menu_text = menu[KEY_MENU.SUBMENU]
        image_name = menu[KEY_MENU.IMAGE]
        
        ac = None
        if sub_menu_text:
            # Create the sub-menu if it does not exist
            if sub_menu_text not in sub_menus:
                ac = create_menu_item(self, parent_menu, sub_menu_text, image=None, shortcut=None)
                sm = QMenu()
                ac.setMenu(sm)
                sub_menus[sub_menu_text] = sm
            # Now set our menu variable so the parent menu item will be the sub-menu
            parent_menu = sub_menus[sub_menu_text]
        
        if not menu_text:
            parent_menu.addSeparator()
        elif len(menu[KEY_MENU.OPERATIONS])>0:
            if sub_menu_text:
                name = '{:s} > {:s}'.format(sub_menu_text, menu_text)
            else:
                name = '{:s}'.format(menu_text)
            
            name = name.replace('&','')
            debug_print('Rebuilding menu for:', name)
            
            ac = create_menu_action_unique(self, parent_menu, menu_text, image_name,
                           triggered=partial(self.run_SearchReplace, menu, None),
                           unique_name=name, shortcut_name=name)
        
        if ac:
            # Maintain our list of menus by query references so we can easily enable/disable menus when user right-clicks.
            self.menu_actions.append(ac)
    
    
    def quick_selected(self):
        self.quickSearchReplace(get_BookIds_selected(), _('the selected books'))
    
    def quick_library(self):
        self.quickSearchReplace(get_BookIds_all(), _('all books in the library {:s}').format(GUI.iactions['Choose Library'].library_name()))
    
    def quick_virtual(self):
        vl = get_curent_virtual()
        if vl[0]:
            self.quickSearchReplace(get_BookIds_virtual(), _('the virtual library {:s}').format(vl[0]))
        else:
            self.quick_library()
    
    def quick_search(self):
        self.quickSearchReplace(get_BookIds_search(), _('the current search'))
    
    def quickSearchReplace(self, book_ids, text):
        
        menu = get_default_menu()
        menu[KEY_MENU.TEXT] = text +' '+ _('({:d} books)').format(len(book_ids))
        menu[KEY_MENU.OPERATIONS] = PREFS[KEY_MENU.QUICK]
        
        d = ConfigOperationListDialog(self, menu=menu, book_ids=book_ids)
        
        if len(d.operation_list)==0:
            d.add_empty_operation()
        
        if d.exec_() == d.Accepted:
            
            if len(d.operation_list)>0:
                menu[KEY_MENU.OPERATIONS] = d.operation_list
                
                self.run_SearchReplace(menu, book_ids)
        
        PREFS[KEY_MENU.QUICK] = d.operation_list
    
    
    def run_SearchReplace(self, menu, book_ids):
        if book_ids == None:
            book_ids = get_BookIds_selected(show_error=True)
        
        srpg = SearchReplacesProgressDialog(book_ids, menu)
        srpg.close()
        del srpg
    
    def show_configuration(self):
        self.interface_action_base_plugin.do_user_config(GUI)


def menu_testGetError(menu):
    
    difference = set(KEY_MENU.ALL).difference(menu)
    for key in difference:
        return Exception(_('Invalide menu configuration, the "{:s}" key is missing.').format(key))
    
    return None


class SearchReplacesProgressDialog(QProgressDialog):
    def __init__(self, book_ids, menu):
        
        # DB
        self.db = current_db()
        # DB API
        self.dbAPI = self.db.new_api
        
        # liste of book id
        self.book_ids = book_ids
        # Count book
        self.book_count = len(self.book_ids)
        
        # Count update
        self.books_update = 0
        self.fields_update = 0
        
        # is a quick Search/Replace
        self.quickSearchReplace = menu[KEY_MENU.TEXT] == None
        
        
        # operation list of Search/Replace
        self.operation_list = operation_list_active(menu[KEY_MENU.OPERATIONS])
        
        # Count of Search/Replace
        self.operation_count = len(self.operation_list)
        
        # Count of Search/Replace
        self.total_operation_count = self.book_count*self.operation_count
        
        # Search/Replace Widget
        self.s_r = SearchReplaceWidget_NoWindows(self.book_ids)
        
        # operation error
        self.operationStrategy = PREFS[KEY_ERROR.ERROR][KEY_ERROR.OPERATION]
        self.operationErrorList = []
        
        # use mark
        self.useMark = PREFS[KEY_MENU.USE_MARK]
        
        # show Update Report
        self.showUpdateReport = PREFS[KEY_MENU.UPDATE_REPORT]
        
        # Exception
        self.exceptionStrategy = PREFS[KEY_ERROR.ERROR][KEY_ERROR.UPDATE]
        self.exception = []
        self.exception_unhandled = False
        self.exception_update = False
        self.exception_safely = False
        
        self.time_execut = 0
        
        
        QProgressDialog.__init__(self, '', _('Cancel'), 0, self.total_operation_count, GUI)
        
        self.setWindowTitle(_('Mass Search/Replace progress'))
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
            debug_print('Mass Search/Replace was cancelled. No change.\n')
        
        elif self.exception_unhandled:
            debug_print('Mass Search/Replace was interupted. An exception has occurred:\n'+str(self.exception))
            CustomExceptionErrorDialog(self.exception)
        
        elif self.operationErrorList and self.operationStrategy == ERROR_OPERATION.ABORT:
            debug_print('Mass Search/Replace was interupted. An invalid operation has detected:\n'+str(self.operationErrorList[0][1]))
            warning_dialog(GUI, _('Invalid operation'),
                        _('A invalid operations has detected:\n{:s}\n\n'
                          'Mass Search/Replace was canceled.').format(str(self.operationErrorList[0][1])),
                          show=True, show_copy_button=False)
        
        else:
            
            #info debug
            debug_print('Search/Replace launched for {:d} books with {:d} operation.'.format(self.book_count, self.operation_count))
            
            if self.operationErrorList:
                debug_print('!! {:d} invalid operation was detected.'.format(len(self.operationErrorList)))
            
            if self.exception_update:
                id, book_info, field, e = self.exception[0]
                debug_print('!! Mass Search/Replace was interupted. An exception has occurred during the library update:\n'+str(e))
            elif self.exception_safely:
                debug_print('!! {:d} exceptions have occurred during the library update.'.format(len(self.exception)))
            
            if self.exception_update and self.exceptionStrategy == ERROR_UPDATE.RESTORE:
                debug_print('The library a was restored to its original state.')
            else:
                debug_print('Search/Replace performed for {:d} books with a total of {:d} fields modify.'.format(self.books_update, self.fields_update))
            debug_print('Search/Replace execute in {:0.3f} seconds.\n'.format(self.time_execut))
            
            #info dialog
            if self.exception_update:
                
                msg = _('Mass Search/Replace encountered an error during the library update.')
                if self.exceptionStrategy == ERROR_UPDATE.RESTORE:
                    msg += '\n' + _('The library a was restored to its original state.')
                
                id, book_info, field, e = self.exception[0]
                CustomExceptionErrorDialog(e, custome_msg=msg, custome_title=_('Cannot update the library'))
            
            elif self.exception_safely:
                
                det_msg= '\n'.join('Book {:s} | {:s} > {:}'.format(book_info, field, e.__class__.__name__ +': '+ str(e)) for id, book_info, field, e in self.exception)
                
                warning_dialog(GUI, _('Exceptions during the library update'),
                            _('{:d} exceptions have occurred during the library update.\nSome fields may not have been updated.').format(len(self.exception)),
                              det_msg='-- Mass Search/Replace: Library update exceptions --\n\n'+det_msg, show=True, show_copy_button=True)
            
            if self.operationErrorList:
                det_msg= '\n'.join( 'Operation {:d}/{:d} > {:s}'.format(n, self.operation_count, err) for n, err in self.operationErrorList)
                
                warning_dialog(GUI, _('Invalid operation'),
                            _('{:d} invalid operations has detected and have been ignored.').format(len(self.operationErrorList)),
                            det_msg='-- Mass Search/Replace: Invalid operations --\n\n'+det_msg, show=True, show_copy_button=True)
            
            if self.showUpdateReport and not (self.exception_update and self.exceptionStrategy == ERROR_UPDATE.RESTORE):
                info_dialog(GUI, _('Update Report'),
                        _('Mass Search/Replace performed for {:d} books with a total of {:d} fields modify.').format(self.books_update, self.fields_update)
                        , show=True, show_copy_button=False)
            
        
        self.close()
    
    def close(self):
        self.s_r.close()
        QProgressDialog.close(self)
    
    
    def _run_search_replaces(self):
        lst_id = []
        book_id_update = defaultdict(dict)
        start = time.time()
        alreadyOperationError = False
        
        try:
            self.setValue(0)
            self.hide()
            
            for op, operation in enumerate(self.operation_list, 1):
                
                debug_print('Operation {:d}/{:d} > {:s}'.format(op, self.operation_count, operation_string(operation)))
                
                err = operation_testGetError(operation)
                if not err:
                    self.s_r.load_settings(operation)
                    err = self.s_r.testGetError()
                
                if err:
                    debug_print('!! Invalide operation: {0}\n'.format(err))
                    self.operationErrorList.append([op, str(err)])
                
                
                if len(self.operationErrorList) == 1 and self.operationStrategy == ERROR_OPERATION.ABORT:
                    return
                elif not alreadyOperationError and len(self.operationErrorList) == 1 and self.operationStrategy == ERROR_OPERATION.ASK:
                    alreadyOperationError = True
                    start_dialog =  time.time()
                    rslt = question_dialog(GUI, _('Invalid operation'),
                            _('A invalid operations has detected:\n{:s}\n\n'
                              'Continue the execution of Mass Search/Replace?\n'
                              'Other errors may exist and will be ignored.').format(str(self.operationErrorList[0][1])),
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
                        
                        miA = self.dbAPI.get_proxy_metadata(book_id)
                        
                        #Book num/book_count > "title" (author & author) {id: book_id}
                        book_info = 'Book '+str(num)+'/'+str(self.book_count)+ ' > "'+miA.get('title')+'" ('+' & '.join(miA.get('authors'))+') {id: '+str(book_id)+'}'
                        
                        if num==self.book_count: nl ='\n'
                        else: nl =''
                        
                        debug_print(book_info+nl)
                        
                        if self.wasCanceled():
                            self.close()
                            return
                        
                        err = self.s_r.search_replace(book_id)
                        if err:
                            if type(err) is Exception:
                                if str(err) == CalibreText.EXCEPTION_Invalid_identifier:
                                    book_info = '"'+miA.get('title')+'" ('+' & '.join(miA.get('authors'))+')'
                                    self.exception.append( (book_id, book_info, 'identifier', err) )
                                else:
                                    raise err
                            else:
                                raise Exception(err)
        
        
        except Exception as e:
            self.exception_unhandled = True
            self.exception = e
        
        else:
            
            lst_id = []
            for field, book_id_val_map in iteritems(self.s_r.updated_fields):
                lst_id += book_id_val_map.keys()
            
            self.fields_update = len(lst_id)
            lst_id = list(dict.fromkeys(lst_id))
            self.books_update = len(lst_id)
            
            book_id_update = defaultdict(dict)
            
            if self.books_update > 0:
                
                debug_print('Update the database for {:d} books with a total of {:d} fields...\n'.format(self.books_update, self.fields_update))
                self.setLabelText(_('Update the library for {:d} books with a total of {:d} fields...').format(self.books_update, self.fields_update))
                self.setValue(self.total_operation_count)
                
                if self.exceptionStrategy == ERROR_UPDATE.SAFELY or self.exceptionStrategy == ERROR_UPDATE.DONT_STOP:
                    
                    dont_stop = self.exceptionStrategy == ERROR_UPDATE.DONT_STOP
                    
                    if self.exception:
                        self.exception_safely = True
                    
                    for id in iter(lst_id):
                        if self.exception and not dont_stop:
                            break
                        for field, book_id_val_map in iteritems(self.s_r.updated_fields):
                            if self.exception and not dont_stop:
                                break
                            if id in book_id_val_map:
                                try:
                                    val = self.s_r.updated_fields[field][id]
                                    self.dbAPI.set_field(field, {id:val})
                                    book_id_update[field][id] = ''
                                except Exception as e:
                                    self.exception_safely = True
                                    
                                    miA = self.dbAPI.get_proxy_metadata(id)
                                    #title (author & author)
                                    book_info = '"'+miA.get('title')+'" ('+' & '.join(miA.get('authors'))+')'
                                    self.exception.append( (id, book_info, field, e) )
                    
                else:
                    try:
                        
                        backup_fields = None
                        is_restore = self.exceptionStrategy == ERROR_UPDATE.RESTORE
                        if is_restore:
                            backup_fields = defaultdict(dict)
                        
                        if self.exception:
                            raise Exception('raise')
                        
                        for field, book_id_val_map in iteritems(self.s_r.updated_fields):
                            if is_restore:
                                src_field = self.dbAPI.all_field_for(field, book_id_val_map.keys())
                                backup_fields[field] = src_field
                            
                            self.dbAPI.set_field(field, book_id_val_map)
                            book_id_update[field] = {id:'' for id in book_id_val_map.keys()}
                        
                    except Exception as e:
                        self.exception_update = True
                        self.exception.append( (None, None, None, e) )
                        
                        if is_restore:
                            for field, book_id_val_map in iteritems(backup_fields):
                               self.dbAPI.set_field(field, book_id_val_map)
                            book_id_update = {}
                
                GUI.iactions['Edit Metadata'].refresh_gui(lst_id, covers_changed=False)
                
            
        
        finally:
            
            lst_id = []
            for field, book_id_map in iteritems(book_id_update):
                lst_id += book_id_map.keys()
            self.fields_update = len(lst_id)
            
            lst_id = list(dict.fromkeys(lst_id))
            self.books_update = len(lst_id)
            
            if calibre_version >= (5, 41,0) and self.useMark and self.fields_update:
                set_marked('mass_search_replace_updated', lst_id)
            
            self.time_execut = round(time.time() - start, 3)
            self.db.clean()
            self.hide()
