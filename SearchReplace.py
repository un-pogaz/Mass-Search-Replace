#!/usr/bin/env python
# ~*~ coding: utf-8 ~*~
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2020, Ahmed Zaki <azaki00.dev@gmail.com> ; adjustment 2020, un_pogaz <un.pogaz@gmail.com>'
__docformat__ = 'restructuredtext en'

import os, copy
# calibre Python 3 compatibility.
from six import text_type as unicode

try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.Qt import Qt, QIcon, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QSize
                      
from calibre import prints
from calibre.gui2 import error_dialog, question_dialog
from calibre.gui2.widgets2 import Dialog

from calibre_plugins.mass_search_replace.common_utils import debug_print, get_icon
from calibre_plugins.mass_search_replace.SearchReplaceCalibre import MetadataBulkWidget, KEY as KEY_QUERY, S_R_FUNCTIONS, S_R_REPLACE_MODES, S_R_MATCH_MODES, TEMPLATE_FIELD as TEMPLATE
from calibre_plugins.mass_search_replace.templates import TemplateBox, check_template
from calibre_plugins.mass_search_replace.TestField import get_possible_fields, get_possible_idents
import calibre_plugins.mass_search_replace.SearchReplaceCalibreText as CalibreText

TEMPLATE_FIELD = TEMPLATE

class KEY_OPERATION:
    locals().update(vars(KEY_QUERY))
    ACTIVE = '_MSR:Active'

_default_operation = None
_s_r = None

def get_default_operation(plugin_action):
        global _default_operation
        global _s_r
        
        if not _s_r or _s_r.db != plugin_action.gui.current_db:
            _s_r = SearchReplaceWidget_NoWindows(plugin_action, [0])
        if not _default_operation:
            _default_operation = _s_r.save_settings()
            _default_operation[KEY_OPERATION.ACTIVE] = True
        
        return copy.copy(_default_operation)

def operation_ConvertError(operation):
    err = operation.get(KEY_OPERATION.S_R_ERROR, None)
    if err:
        operation[KEY_OPERATION.S_R_ERROR] = str(err)
    return operation

def operation_list_ConvertError(operation_list):
    rlst = []
    for operation in operation_list:
        rlst.append(operation_ConvertError(operation))
    return rlst

def clean_empty_operation(operation_list, plugin_action):
    if not operation_list: operation_list = []
    default = get_default_operation(plugin_action)
    operation_list = operation_list_ConvertError(operation_list)
    rlst = []
    for operation in operation_list:
        for key in KEY_OPERATION.ALL:
            if operation[key] != default[key]:
                rlst.append(operation)
                break
    
    return rlst

def operation_is_active(operation):
    return operation.get(KEY_OPERATION.ACTIVE, True)

def operation_list_active(operation_list):
    rlst = []
    for operation in operation_list:
        if operation_is_active(operation):
            rlst.append(operation)
    
    return rlst


def operation_testGetError(operation, plugin_action):
    
    db = plugin_action.gui.current_db
    
    if not operation:
        return TypeError
    
    if KEY_OPERATION.S_R_ERROR in operation:
        return Exception(str(operation[KEY_OPERATION.S_R_ERROR]))
            
    
    difference = set(KEY_OPERATION.ALL).difference(operation.keys())
    for key in difference:
        return Exception(_('Invalid operation, the "{:s}" key is missing.').format(key))
    
    if operation[KEY_OPERATION.REPLACE_FUNC] not in S_R_FUNCTIONS:
        return Exception(CalibreText.getForLocalizedField(CalibreText.FIELD_NAME.REPLACE_FUNC, operation[KEY_OPERATION.REPLACE_FUNC]))
        
    if operation[KEY_OPERATION.REPLACE_MODE] not in S_R_REPLACE_MODES:
        return Exception(CalibreText.getForLocalizedField(CalibreText.FIELD_NAME.REPLACE_MODE, operation[KEY_OPERATION.REPLACE_MODE]))
        
    if operation[KEY_OPERATION.SEARCH_MODE] not in S_R_MATCH_MODES:
        return Exception(CalibreText.getForLocalizedField(CalibreText.FIELD_NAME.SEARCH_MODE, operation[KEY_OPERATION.SEARCH_MODE]))
    
    
    #Field test
    all_fields, writable_fields = get_possible_fields(db)
    
    search_field = operation[KEY_OPERATION.SEARCH_FIELD]
    dest_field = operation[KEY_OPERATION.DESTINATION_FIELD]
    
    if search_field not in all_fields:
        return Exception(_('Search field "{:s}" is not available for this library').format(search_field))
        
    if dest_field and (dest_field not in writable_fields):
        return Exception(_('Destination field "{:s}" is not available for this library').format(dest_field))
    
    if search_field == 'identifiers':
        src_ident = operation[KEY_OPERATION.S_R_SRC_IDENT]
        if src_ident not in get_possible_idents(db):
            return Exception(_('Identifier type "{:s}" is not available for this library').format(src_ident))
    
    return None

def operation_testFullError(operation, plugin_action):
    err = operation_testGetError(operation, plugin_action)
    if err:
        return err
    get_default_operation(plugin_action)
    global _s_r
    _s_r.load_settings(operation)
    return _s_r.testGetError()

def operation_isFullValid(operation, plugin_action):
    return operation_testFullError(operation, plugin_action) == None


def operation_para_list(operation):
    column = operation.get(KEY_OPERATION.SEARCH_FIELD, '')
    field = operation.get(KEY_OPERATION.DESTINATION_FIELD, '')
    if (field and field != column):
        column += ' => '+ field
    
    search_mode = operation.get(KEY_OPERATION.SEARCH_MODE, '')
    template = operation.get(KEY_OPERATION.S_R_TEMPLATE, '')
    search_for = ''
    if search_mode == CalibreText.S_R_REPLACE:
        search_for = '*'
    else:
        search_for = operation.get(KEY_OPERATION.SEARCH_FOR, '')
    replace_with = operation.get(KEY_OPERATION.REPLACE_WITH, '')
    
    return [ column, template, search_mode, search_for, replace_with ]

def operation_string(operation):
    val = [operation_para_list(operation)[0]]
    temp = operation_para_list(operation)[1]
    if temp:
        val.append(temp)
    val = val + operation_para_list(operation)[2:]
    
    return '"'+ '" | "'.join(val)+'"'


def SearchReplaceWidget_NoWindows(plugin_action, book_ids=[]):
    rslt = SearchReplaceWidget(plugin_action, book_ids)
    rslt.resize(QSize(0, 0))
    return rslt;

class SearchReplaceWidget(MetadataBulkWidget):
    def __init__(self, plugin_action, book_ids=[], refresh_books=set([])):
        
        if not book_ids or len(book_ids) == 0:
            book_ids = plugin_action.gui.library_view.get_selected_ids();
        
        MetadataBulkWidget.__init__(self, plugin_action, book_ids, refresh_books)
        self.updated_fields = self.set_field_calls
        self.plugin_action = plugin_action
    
    def load_settings(self, operation):
        self.load_query(operation)
    
    def save_settings(self):
        return self.get_query()
    
    def testGetError(self):
        return operation_testGetError(self.get_query(), self.plugin_action)
    
    def search_replace(self, book_id, operation=None):
        if operation:
            self.load_settings(operation)
        
        err = self.testGetError()
        if not err:
           err = self.do_search_replace(book_id)
        return err


class SearchReplaceDialog(Dialog):
    def __init__(self, parent, plugin_action, operation=None, book_ids=[]):
        self.plugin_action = plugin_action
        self.parent = parent
        if not operation:
            operation = get_default_operation(plugin_action)
        self.operation = operation
        self.widget = SearchReplaceWidget(self.plugin_action, book_ids[:10])
        Dialog.__init__(self, _('Configuration of a Search/Replace operation'), 'config_query_SearchReplace', parent)
    
    def setup_ui(self):
        l = QVBoxLayout()
        self.setLayout(l)
        l.addWidget(self.widget)
        l.addWidget(self.bb)
        
        if self.operation:
            self.widget.load_settings(self.operation)
    
    def accept(self):
        
        err = self.widget.testGetError()
        
        if err:
            if question_dialog(self, _('Invalid operation'),
                             _('The registering of Find/Replace operation has failed.\n{:s}\nDo you want discard the changes?').format(str(err)),
                             default_yes=True, show_copy_button=False, override_icon=get_icon('dialog_warning.png')):
                
                Dialog.reject(self)
                return
            else:
                return
        
        self.operation = self.widget.save_settings()
        debug_print('Saved operation > {0}\n{1}\n'.format(operation_string(self.operation), self.operation))
        Dialog.accept(self)
