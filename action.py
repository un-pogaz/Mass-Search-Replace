#!/usr/bin/env python

__license__   = 'GPL v3'
__copyright__ = '2020, un_pogaz <un.pogaz@gmail.com>'


try:
    load_translations()
except NameError:
    pass  # load_translations() added in calibre 1.9

import time
from collections import defaultdict
from functools import partial
from typing import Union

try:
    from qt.core import QMenu, QToolButton
except ImportError:
    from PyQt5.Qt import QMenu, QToolButton

from calibre.gui2 import info_dialog, question_dialog, warning_dialog
from calibre.gui2.actions import InterfaceAction

from .common_utils import CALIBRE_VERSION, GUI, debug_print, get_icon
from .common_utils.dialogs import ProgressDialog, custom_exception_dialog
from .common_utils.librarys import (
    get_BookIds_all,
    get_BookIds_search,
    get_BookIds_selected,
    get_BookIds_virtual,
    get_curent_virtual,
    set_marked,
)
from .common_utils.menus import create_menu_action_unique, create_menu_item, unregister_menu_actions
from .config import (
    ERROR_OPERATION,
    ERROR_UPDATE,
    ICON,
    KEY_ERROR,
    KEY_MENU,
    PREFS,
    ConfigOperationListDialog,
    get_default_menu,
)
from .search_replace import Operation, SearchReplaceWidget, operation_list_active
from .search_replace import text as CalibreText


class MassSearchReplaceAction(InterfaceAction):
    
    name = 'Mass Search/Replace'
    
    # Create our top-level menu/toolbar action (text, icon_path, tooltip, keyboard shortcut)
    action_spec = (name, None, _('Apply a list of multiple saved Find and Replace operations'), None)
    popup_type = QToolButton.InstantPopup
    action_type = 'current'
    dont_add_to = frozenset(['context-menu-device'])
    
    def genesis(self):
        self.menu = QMenu(GUI)
        self.qaction.setMenu(self.menu)
        self.qaction.setIcon(get_icon(ICON.PLUGIN))
        
        error_operation = PREFS[KEY_ERROR.ERROR][KEY_ERROR.OPERATION]
        if error_operation not in ERROR_OPERATION.LIST.keys():
            PREFS[KEY_ERROR.ERROR][KEY_ERROR.OPERATION] = ERROR_OPERATION.DEFAULT
        
        error_update = PREFS[KEY_ERROR.ERROR][KEY_ERROR.UPDATE]
        if error_update not in ERROR_UPDATE.LIST.keys():
            PREFS[KEY_ERROR.ERROR][KEY_ERROR.UPDATE] = ERROR_UPDATE.DEFAULT
    
    def initialization_complete(self):
        self.rebuild_menus()
    
    def rebuild_menus(self):
        self.menu.clear()
        sub_menus = {}
        
        unregister_menu_actions()
        
        for menu in PREFS[KEY_MENU.MENU]:
            if not menu_get_error(menu) and menu[KEY_MENU.ACTIVE]:
                self.append_menu_item_ex(self.menu, sub_menus, menu)
        
        self.menu.addSeparator()
        
        ac = create_menu_item(self, self.menu, _('&Quick Search/Replace…'), ICON.PLUGIN)
        mn_books = QMenu()
        ac.setMenu(mn_books)
        
        create_menu_action_unique(self, mn_books, _('&Selection'), 'highlight_only_on.png',
                                        triggered=self.quick_selected,
                                        unique_name='&Quick Search/Replace in all books>&Selection')
    
        create_menu_action_unique(self, mn_books, _('&Current search'), 'search.png',
                                        triggered=self.quick_search,
                                        unique_name='&Quick Search/Replace in all books>&Current search')
    
        create_menu_action_unique(self, mn_books, _('&Virtual library'), 'vl.png',
                                        triggered=self.quick_virtual,
                                        unique_name='&Quick Search/Replace in all books>&Virtual library')
    
        create_menu_action_unique(self, mn_books, _('&Library'), 'library.png',
                                        triggered=self.quick_library,
                                        unique_name='&Quick Search/Replace in all books>&Library')
        
        self.menu.addSeparator()
        
        create_menu_action_unique(self, self.menu, _('&Customize plugin…'), 'config.png',
                                        triggered=self.show_configuration,
                                        unique_name='&Customize plugin',
                                        shortcut=False)
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
                unique_name = f'{sub_menu_text} > {menu_text}'
            else:
                unique_name = f'{menu_text}'
            
            unique_name = unique_name.replace('&','')
            debug_print('Rebuilding menu for:', unique_name)
            
            create_menu_action_unique(self, parent_menu, menu_text, image_name,
                        triggered=partial(self.run_SearchReplace, menu, None),
                        unique_name=unique_name,
                        )
    
    
    def quick_selected(self):
        self.quick_search_replace(get_BookIds_selected(), _('the selected books'))
    
    def quick_library(self):
        self.quick_search_replace(
            get_BookIds_all(),
            _('all books in the library {:s}').format(GUI.iactions['Choose Library'].library_name())
        )
    
    def quick_virtual(self):
        vl = get_curent_virtual()
        if vl[0]:
            self.quick_search_replace(get_BookIds_virtual(), _('the virtual library {:s}').format(vl[0]))
        else:
            self.quick_library()
    
    def quick_search(self):
        self.quick_search_replace(get_BookIds_search(), _('the current search'))
    
    def quick_search_replace(self, book_ids, text):
        
        menu = get_default_menu()
        menu[KEY_MENU.TEXT] = text +' '+ _('({:d} books)').format(len(book_ids))
        menu[KEY_MENU.OPERATIONS] = [Operation(o) for o in PREFS[KEY_MENU.QUICK]]
        
        d = ConfigOperationListDialog(menu=menu, book_ids=book_ids)
        
        if len(d.operation_list)==0:
            d.add_empty_operation()
        
        if d.exec():
            if len(d.operation_list)>0:
                menu[KEY_MENU.OPERATIONS] = d.operation_list
                
                self.run_SearchReplace(menu, book_ids)
        
        PREFS[KEY_MENU.QUICK] = d.operation_list
    
    
    def run_SearchReplace(self, menu, book_ids):
        if book_ids is None:
            book_ids = get_BookIds_selected(show_error=True)
        
        SearchReplacesProgressDialog(book_ids, menu=menu)
    
    def show_configuration(self):
        self.interface_action_base_plugin.do_user_config(GUI)


def menu_get_error(menu: QMenu) -> Union[Exception, None]:
    
    difference = set(KEY_MENU.ALL).difference(menu)
    for key in difference:
        return Exception(_('Invalide menu configuration, the "{:s}" key is missing.').format(key))
    
    return None


class SearchReplacesProgressDialog(ProgressDialog):
    
    title = _('{PLUGIN_NAME} progress').format(PLUGIN_NAME=MassSearchReplaceAction.name)
    
    def progress_text(self):
        return _('Search/Replace {:d} of {:d}. Book {:d} of {:d}.').format(
            self.op_num, self.operation_count, self.book_num, self.book_count
        )
    
    def setup_progress(self, **kvargs):
        # Count update
        self.books_update = 0
        self.fields_update = 0
        self.book_num = 0
        
        # is a quick Search/Replace
        self.quick_search_replace = kvargs['menu'][KEY_MENU.TEXT] is None
        
        
        # operation list of Search/Replace
        self.op_num = 0
        self.operation_list = operation_list_active(kvargs['menu'][KEY_MENU.OPERATIONS])
        
        # Count of Search/Replace
        self.operation_count = len(self.operation_list)
        
        # Count of Search/Replace
        self.total_operation_count = self.book_count*self.operation_count
        
        # Search/Replace Widget
        self.s_r = SearchReplaceWidget(self.book_ids)
        
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
        
        return self.total_operation_count
    
    def end_progress(self):
        
        if self.wasCanceled():
            debug_print('Mass Search/Replace was cancelled. No change.\n')
        
        elif self.exception_unhandled:
            debug_print('Mass Search/Replace was interupted. An exception has occurred:\n'+str(self.exception))
            custom_exception_dialog(self.exception)
        
        elif self.operationErrorList and self.operationStrategy == ERROR_OPERATION.ABORT:
            debug_print(
                'Mass Search/Replace was interupted. An invalid operation has detected:',
                str(self.operationErrorList[0][1]),
                sep='\n',
            )
            warning_dialog(GUI, _('Invalid operation'),
                        _('A invalid operations has detected:\n{:s}\n\n'
                          'Mass Search/Replace was canceled.').format(str(self.operationErrorList[0][1])),
                          show=True, show_copy_button=False)
        
        else:
            
            #info debug
            debug_print(f'Search/Replace launched for {self.book_count} books with {self.operation_count} operation.')
            
            if self.operationErrorList:
                debug_print(f'!! {len(self.operationErrorList):d} invalid operation was detected.')
            
            if self.exception_update:
                id, book_info, field, e = self.exception[0]
                debug_print(
                    '!! Mass Search/Replace was interupted. An exception has occurred during the library update:',
                    str(e),
                    sep='\n',
                )
            elif self.exception_safely:
                debug_print(f'!! {len(self.exception):d} exceptions have occurred during the library update.')
            
            if self.exception_update and self.exceptionStrategy == ERROR_UPDATE.RESTORE:
                debug_print('The library a was restored to its original state.')
            else:
                debug_print(
                    f'Search/Replace performed for {self.books_update} books'
                    f'with a total of {self.fields_update} fields modify.'
                )
            debug_print(f'Search/Replace execute in {self.time_execut:0.3f} seconds.\n')
            
            #info dialog
            if self.exception_update:
                
                msg = None
                if self.exceptionStrategy == ERROR_UPDATE.RESTORE:
                    msg = _('The library a was restored to its original state.')
                
                id, book_info, field, e = self.exception[0]
                custom_exception_dialog(e, additional_msg=msg, title=_('Cannot update the library'))
            
            elif self.exception_safely:
                lst = []
                for id, book_info, field, e in self.exception:
                    lst.append(f'Book {book_info} | {field} > ' + e.__class__.__name__ +': '+ str(e))
                det_msg= '\n'.join(lst)
                
                warning_dialog(GUI, _('Exceptions during the library update'),
                    _('{:d} exceptions have occurred during the library update.\n'
                    'Some fields may not have been updated.').format(len(self.exception)),
                    det_msg='-- Mass Search/Replace: Library update exceptions --\n\n'+det_msg,
                    show=True, show_copy_button=True,
                )
            
            if self.operationErrorList:
                lst = []
                for n, err in self.operationErrorList:
                    lst.append(f'Operation {n}/{self.operation_count} > {err}')
                det_msg= '\n'.join(lst)
                
                warning_dialog(GUI, _('Invalid operation'),
                    _('{:d} invalid operations has detected and have been ignored.').format(
                        len(self.operationErrorList)
                    ),
                    det_msg='-- Mass Search/Replace: Invalid operations --\n\n'+det_msg,
                    show=True, show_copy_button=True,
                )
            
            if self.showUpdateReport and not (self.exception_update and self.exceptionStrategy == ERROR_UPDATE.RESTORE):
                books_update, fields_update = self.books_update, self.fields_update
                info_dialog(GUI, _('Update Report'),
                    _('Mass Search/Replace performed for {:d} books with a total of {:d} fields modify.').format(
                        books_update,
                        fields_update,
                    ),
                    show=True, show_copy_button=False,
                )
            
        
        self.s_r.close()
        del self.s_r
    
    def job_progress(self):
        
        debug_print(f'Launch Search/Replace for {self.book_count} books with {self.operation_count} operation.\n')
        
        lst_id = []
        book_id_update = defaultdict(dict)
        
        alreadyOperationError = False
        
        try:
            
            for self.op_num, operation in enumerate(self.operation_list, 1):
                
                debug_print(f'Operation {self.op_num}/{self.operation_count} >', operation.string_info())
                
                err = operation.get_error()
                if not err:
                    self.s_r.load_operation(operation)
                    err = self.s_r.get_error()
                
                if err:
                    debug_print('!! Invalide operation:', err, '\n')
                    self.operationErrorList.append([self.op_num, str(err)])
                
                
                if len(self.operationErrorList) == 1 and self.operationStrategy == ERROR_OPERATION.ABORT:
                    return
                elif (not alreadyOperationError
                    and len(self.operationErrorList) == 1
                    and self.operationStrategy == ERROR_OPERATION.ASK
                ):
                    alreadyOperationError = True
                    start_dialog =  time.time()
                    rslt = question_dialog(self, _('Invalid operation'),
                            _('A invalid operations has detected:\n{:s}\n\n'
                              'Continue the execution of Mass Search/Replace?\n'
                              'Other errors may exist and will be ignored.').format(str(self.operationErrorList[0][1])),
                              default_yes=True, override_icon=get_icon('dialog_warning.png'))
                    
                    self.start = self.start + (time.time() - start_dialog)
                    
                    if not rslt:
                        return
                
                if not err:
                    for self.book_num, book_id in enumerate(self.book_ids, 1):
                        
                        #update Progress
                        self.increment()
                        
                        miA = self.dbAPI.get_proxy_metadata(book_id)
                        
                        #Book book_num/book_count > "title" (author & author) {id: book_id}
                        book_info = 'Book {book_num}/{book_count} > "{title}" ({authors}) {{id: {book_id}}}'.format(
                            book_num=self.book_num,
                            book_count=self.book_count,
                            title=miA.get('title'),
                            authors=' & '.join(miA.get('authors')),
                            book_id=book_id,
                        )
                        
                        if self.book_num == self.book_count:
                            nl = '\n'
                        else:
                            nl = ''
                        
                        debug_print(book_info+nl)
                        
                        if self.wasCanceled():
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
            for field, book_id_val_map in self.s_r.updated_fields.items():
                lst_id += book_id_val_map.keys()
            
            self.fields_update = len(lst_id)
            lst_id = list(dict.fromkeys(lst_id))
            self.books_update = len(lst_id)
            
            book_id_update = defaultdict(dict)
            
            if self.books_update > 0:
                books_update, fields_update = self.books_update, self.fields_update
                debug_print(f'Update the database for {books_update} books with a total of {fields_update} fields…\n')
                self.set_value(-1,
                    text=_('Update the library for {:d} books with a total of {:d} fields…').format(
                        books_update, fields_update,
                    ))
                
                if self.exceptionStrategy == ERROR_UPDATE.SAFELY or self.exceptionStrategy == ERROR_UPDATE.DONT_STOP:
                    
                    dont_stop = self.exceptionStrategy == ERROR_UPDATE.DONT_STOP
                    
                    if self.exception:
                        self.exception_safely = True
                    
                    for id in iter(lst_id):
                        if self.exception and not dont_stop:
                            break
                        for field, book_id_val_map in self.s_r.updated_fields.items():
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
                        
                        for field, book_id_val_map in self.s_r.updated_fields.items():
                            if is_restore:
                                src_field = self.dbAPI.all_field_for(field, book_id_val_map.keys())
                                backup_fields[field] = src_field
                            
                            self.dbAPI.set_field(field, book_id_val_map)
                            book_id_update[field] = {id:'' for id in book_id_val_map.keys()}
                    
                    except Exception as e:
                        self.exception_update = True
                        self.exception.append( (None, None, None, e) )
                        
                        if is_restore:
                            for field, book_id_val_map in backup_fields.items():
                               self.dbAPI.set_field(field, book_id_val_map)
                            book_id_update = {}
                
                GUI.iactions['Edit Metadata'].refresh_gui(lst_id, covers_changed=False)
        
        finally:
            
            lst_id = []
            for field, book_id_map in book_id_update.items():
                lst_id += book_id_map.keys()
            self.fields_update = len(lst_id)
            
            lst_id = list(dict.fromkeys(lst_id))
            self.books_update = len(lst_id)
            
            if CALIBRE_VERSION >= (5,41,0) and self.useMark and self.fields_update:
                set_marked('mass_search_replace_updated', lst_id)
