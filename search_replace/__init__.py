#!/usr/bin/env python
# ~*~ coding: utf-8 ~*~
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2020, Ahmed Zaki <azaki00.dev@gmail.com> ; adjustment 2020, un_pogaz <un.pogaz@gmail.com>'
__docformat__ = 'restructuredtext en'


# python3 compatibility
from six.moves import range
from six import text_type as unicode
from polyglot.builtins import iteritems, itervalues

try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9

from collections import defaultdict, OrderedDict
from functools import partial

import copy

try:
    from qt.core import (
        QSize, QVBoxLayout,
    )
except ImportError:
    from PyQt5.Qt import (
        QSize, QVBoxLayout,
    )

from calibre.gui2 import error_dialog, question_dialog
from calibre.gui2.widgets2 import Dialog

from ..common_utils import debug_print, get_icon, GUI
from ..common_utils.columns import get_possible_idents, get_possible_fields
from .calibre import MetadataBulkWidget, KEY as KEY_QUERY, S_R_FUNCTIONS, S_R_REPLACE_MODES, S_R_MATCH_MODES
from . import text as CalibreText


class KEY_OPERATION:
    locals().update(vars(KEY_QUERY))
    ACTIVE = '_MSR:Active'

_default_operation = None
_s_r = None

def get_default_operation():
    global _default_operation
    global _s_r
    
    if not _s_r or _s_r.db != GUI.current_db:
        _s_r = SearchReplaceWidget_NoWindows([0])
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

def clean_empty_operation(operation_list):
    operation_list = operation_list or []
    default = get_default_operation()
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

class OperationError(ValueError):
    pass

def operation_testGetError(operation):
    
    if not operation:
        return TypeError
    
    if KEY_OPERATION.S_R_ERROR in operation:
        return OperationError(str(operation[KEY_OPERATION.S_R_ERROR]))
            
    
    difference = set(KEY_OPERATION.ALL).difference(operation.keys())
    for key in difference:
        return OperationError(_('Invalid operation, the "{:s}" key is missing.').format(key))
    
    if operation[KEY_OPERATION.REPLACE_FUNC] not in S_R_FUNCTIONS:
        return OperationError(CalibreText.getForLocalizedField(CalibreText.FIELD_NAME.REPLACE_FUNC, operation[KEY_OPERATION.REPLACE_FUNC]))
        
    if operation[KEY_OPERATION.REPLACE_MODE] not in S_R_REPLACE_MODES:
        return OperationError(CalibreText.getForLocalizedField(CalibreText.FIELD_NAME.REPLACE_MODE, operation[KEY_OPERATION.REPLACE_MODE]))
        
    if operation[KEY_OPERATION.SEARCH_MODE] not in S_R_MATCH_MODES:
        return OperationError(CalibreText.getForLocalizedField(CalibreText.FIELD_NAME.SEARCH_MODE, operation[KEY_OPERATION.SEARCH_MODE]))
    
    #Field test
    all_fields, writable_fields = get_possible_fields()
    
    search_field = operation[KEY_OPERATION.SEARCH_FIELD]
    dest_field = operation[KEY_OPERATION.DESTINATION_FIELD]
    
    if search_field not in all_fields:
        return OperationError(_('Search field "{:s}" is not available for this library').format(search_field))
        
    if dest_field and (dest_field not in writable_fields):
        return OperationError(_('Destination field "{:s}" is not available for this library').format(dest_field))
    
    possible_idents = get_possible_idents()
    
    if search_field == 'identifiers':
        src_ident = operation[KEY_OPERATION.S_R_SRC_IDENT]
        if src_ident not in possible_idents:
            return OperationError(_('Identifier type "{:s}" is not available for this library').format(src_ident))
    
    return None

def operation_testFullError(operation):
    err = operation_testGetError(operation)
    if err:
        return err
    get_default_operation()
    global _s_r
    _s_r.load_settings(operation)
    return _s_r.testGetError()

def operation_isFullValid(operation):
    return operation_testFullError(operation) == None


def operation_para_list(operation):
    name = operation.get(KEY_OPERATION.NAME, '')
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
    
    if column == 'identifiers':
        src_ident = operation.get(KEY_OPERATION.S_R_SRC_IDENT, '')
        search_for = src_ident+':'+search_for
        
        dst_ident = operation.get(KEY_OPERATION.S_R_DST_IDENT, src_ident)
        replace_with = dst_ident+':'+replace_with.strip()
    
    return [ name, column, template, search_mode, search_for, replace_with ]

def operation_string(operation):
    tbl = operation_para_list(operation)
    if not tbl[2]: del tbl[2]
    
    return ('name:"'+tbl[0]+'" => ' if tbl[0] else '') + '"'+ '" | "'.join(tbl[1:])+'"'


def SearchReplaceWidget_NoWindows(book_ids=[]):
    rslt = SearchReplaceWidget(book_ids)
    rslt.resize(QSize(0, 0))
    return rslt

class SearchReplaceWidget(MetadataBulkWidget):
    def __init__(self, book_ids=[], refresh_books=set([])):
        
        if not book_ids or len(book_ids) == 0:
            book_ids = GUI.library_view.get_selected_ids()
        
        MetadataBulkWidget.__init__(self, book_ids, refresh_books)
        self.updated_fields = self.set_field_calls
    
    def load_settings(self, operation):
        self.load_query(operation)
    
    def save_settings(self):
        return self.get_query()
    
    def testGetError(self):
        return operation_testGetError(self.get_query())
    
    def search_replace(self, book_id, operation=None):
        if operation:
            self.load_settings(operation)
        
        err = self.testGetError()
        if not err:
           err = self.do_search_replace(book_id)
        return err


class SearchReplaceDialog(Dialog):
    def __init__(self, operation=None, book_ids=[]):
        self.operation = operation or get_default_operation()
        self.widget = SearchReplaceWidget(book_ids[:10])
        Dialog.__init__(self, _('Configuration of a Search/Replace operation'), 'config_query_SearchReplace')
    
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
        
        new_operation = self.widget.save_settings()
        new_operation_name = new_operation.get(KEY_OPERATION.NAME, None)
        if new_operation_name and new_operation_name == self.operation.get(KEY_OPERATION.NAME, None):
            different = False
            for k in new_operation:
                if k in self.operation and new_operation[k] != self.operation[k]:
                    different = True
                    break
            
            if different:
                new_operation[KEY_OPERATION.NAME] = ''
                self.operation = new_operation
            
        else:
            self.operation = new_operation
        
        debug_print('Saved operation >', operation_string(self.operation))
        debug_print(self.operation)
        Dialog.accept(self)
