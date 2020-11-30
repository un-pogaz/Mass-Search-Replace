#!/usr/bin/env python
# ~*~ coding: utf-8 ~*~
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2020, Ahmed Zaki <azaki00.dev@gmail.com> ; adjustment 2020, un_pogaz <un.pogaz@gmail.com>'
__docformat__ = 'restructuredtext en'

import os
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
from calibre_plugins.mass_search_replace.SearchReplaceCalibre import MetadataBulkWidget, KEY_OPERATION as KEY_QUERY, S_R_FUNCTIONS, S_R_REPLACE_MODES, S_R_MATCH_MODES, TEMPLATE_FIELD
from calibre_plugins.mass_search_replace.templates import check_template


class KEY_OPERATION():
    locals().update(vars(KEY_QUERY))

_default_operation = None
_s_r = None

def get_default_operation(plugin_action):
        global _default_operation
        global _s_r
        if not _s_r or not _default_operation:
            _s_r = SearchReplaceWidget_NoWindows(plugin_action)
            _default_operation = _s_r.save_settings()
        
        return _default_operation

def clean_empty_operation(operation_list, plugin_action):
    if not operation_list: operation_list = []
    rlst = []
    for operation in operation_list:
        if operation and operation != get_default_operation(plugin_action):
            rlst.append(operation)
    
    return rlst

def operation_testGetError(operation):
    difference = set(KEY_OPERATION.ALL).difference(operation.keys())
    for key in difference:
        return Exception(_('Invalid operation, the "{:s}" key is missing.').format(key))
    if KEY_OPERATION.S_R_ERROR in operation:
        return operation[KEY_OPERATION.S_R_ERROR]
    if len(operation[KEY_OPERATION.SEARCH_FIELD])==0:
        return Exception(_('You must specify the target "Search field".'))
    return None

def operation_isValid(operation):
    return operation_testGetError(operation) == None

def operation_testGetLocalizedFieldError(operation):
    err = operation_testGetError(operation)
    if err:
        return err
    
    msg = _('The operation field "{0:s}" contains a invalid value ({1}).\n'
            'The value of this field is localized (translated). This can cause problems when using settings shared on internet or when changing the user interface language.')
    if operation[KEY_OPERATION.REPLACE_FUNC] not in S_R_FUNCTIONS:
        return Exception(msg.format(_('Case to be applied'), operation[KEY_OPERATION.REPLACE_FUNC]))
    if operation[KEY_OPERATION.REPLACE_MODE] not in S_R_REPLACE_MODES:
        return Exception(msg.format(_('Replace mode'),operation[KEY_OPERATION.REPLACE_MODE]))
    if operation[KEY_OPERATION.SEARCH_MODE] not in S_R_MATCH_MODES:
        return Exception(msg.format(_('Search mode'),operation[KEY_OPERATION.SEARCH_MODE]))
    
    return None

def operation_isValidLocalizedField(operation):
    return operation_testGetLocalizedFieldError(operation) == None

def operation_testFullError(operation, plugin_action):
    err = operation_testGetLocalizedFieldError(operation)
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
    
    return [ column, operation.get(KEY_OPERATION.SEARCH_MODE, ''), operation.get(KEY_OPERATION.SEARCH_FOR, ''), operation.get(KEY_OPERATION.REPLACE_WITH, '') ]

def operation_string(operation):
    return '"'+ '" | "'.join(operation_para_list(operation))+'"'




def SearchReplaceWidget_NoWindows(plugin_action):
    rslt = SearchReplaceWidget(plugin_action)
    rslt.resize(QSize(0, 0))
    return rslt;

class SearchReplaceWidget(MetadataBulkWidget):
    def __init__(self, plugin_action, book_ids=[], refresh_books=set([])):
        
        if not book_ids or len(book_ids)==0:
            book_ids = plugin_action.gui.library_view.get_selected_ids();
        
        MetadataBulkWidget.__init__(self, plugin_action, book_ids, refresh_books)
        self.updated_fields = self.set_field_calls
    
    def load_settings(self, operation):
        self.load_query(operation)
    
    def save_settings(self):
        return self.get_query()
    
    def testGetError(self):
        return operation_testGetError(self.get_query())
    
    def testGetLocalizedFieldError(self):
        return operation_testGetLocalizedFieldError(self.get_query())
    
    def search_replace(self, book_id, operation=None):
        if operation:
            self.load_settings(operation)
        
        err = self.testGetError()
        if not err:
            self.do_search_replace(book_id)
        return err


class SearchReplaceDialog(Dialog):
    def __init__(self, parent, plugin_action, operation=None, book_ids=[]):
        self.plugin_action = plugin_action
        self.parent = parent
        self.operation = operation
        self.widget = SearchReplaceWidget(self.plugin_action, book_ids)
        Dialog.__init__(self, _('Search/Replace configuration'), 'config_query_SearchReplace', parent)
    
    def setup_ui(self):
        l = QVBoxLayout()
        self.setLayout(l)
        l.addWidget(self.widget)
        l.addWidget(self.bb)
        
        if self.operation:
            self.widget.load_settings(self.operation)
    
    def accept(self):
        
        err = self.widget.testGetLocalizedFieldError()
        
        if err:
            if question_dialog(self.parent, _('Invalid operation'),
                             _('The registering of Find/Replace operation has failed.\n{:s}\nDo you want discard the changes?').format(str(err)),
                             default_yes=True, show_copy_button=True, override_icon=get_icon('images/warning.png')):
                
                Dialog.reject(self)
                return
            else:
                return
        
        self.operation = self.widget.save_settings()
        debug_print('Saved operation > {0:s}\n{1}\n'.format(operation_string(self.operation), self.operation))
        Dialog.accept(self)

