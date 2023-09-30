#!/usr/bin/env python
# ~*~ coding: utf-8 ~*~

__license__   = 'GPL v3'
__copyright__ = '2020, Ahmed Zaki <azaki00.dev@gmail.com> ; adjustment 2020, un_pogaz <un.pogaz@gmail.com>'
__docformat__ = 'restructuredtext en'


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
from .calibre import MetadataBulkWidget, KEY_QUERY, S_R_FUNCTIONS, S_R_REPLACE_MODES, S_R_MATCH_MODES
from . import text as CalibreText


class Operation(dict):
    
    _default_operation = None
    _s_r = None
    
    def __init__(self, src=None):
        dict.__init__(self)
        if not src:
            if not Operation._s_r or Operation._s_r.db != GUI.current_db:
                _s_r = Operation._s_r = SearchReplaceWidget([0])
            if not Operation._default_operation:
                Operation._default_operation = _s_r.save_settings()
                Operation._default_operation[KEY_QUERY.ACTIVE] = True
            
            src = copy.copy(Operation._default_operation)
        
        self.update(src)
    
    
    def get_error(self):
        
        if not self:
            return TypeError
        
        if KEY_QUERY.S_R_ERROR in self:
            return self[KEY_QUERY.S_R_ERROR]
        
        difference = set(KEY_QUERY.ALL).difference(self.keys())
        for key in difference:
            return OperationError(_('Invalid operation, the "{:s}" key is missing.').format(key))
        
        if self[KEY_QUERY.REPLACE_FUNC] not in S_R_FUNCTIONS:
            return OperationError(CalibreText.get_for_localized_field(CalibreText.FIELD_NAME.REPLACE_FUNC, self[KEY_QUERY.REPLACE_FUNC]))
            
        if self[KEY_QUERY.REPLACE_MODE] not in S_R_REPLACE_MODES:
            return OperationError(CalibreText.get_for_localized_field(CalibreText.FIELD_NAME.REPLACE_MODE, self[KEY_QUERY.REPLACE_MODE]))
            
        if self[KEY_QUERY.SEARCH_MODE] not in S_R_MATCH_MODES:
            return OperationError(CalibreText.get_for_localized_field(CalibreText.FIELD_NAME.SEARCH_MODE, self[KEY_QUERY.SEARCH_MODE]))
        
        #Field test
        all_fields, writable_fields = get_possible_fields()
        
        search_field = self[KEY_QUERY.SEARCH_FIELD]
        dest_field = self[KEY_QUERY.DESTINATION_FIELD]
        
        if search_field not in all_fields:
            return OperationError(_('Search field "{:s}" is not available for this library').format(search_field))
            
        if dest_field and (dest_field not in writable_fields):
            return OperationError(_('Destination field "{:s}" is not available for this library').format(dest_field))
        
        possible_idents = get_possible_idents()
        
        if search_field == 'identifiers':
            src_ident = self[KEY_QUERY.S_R_SRC_IDENT]
            if src_ident not in possible_idents:
                return OperationError(_('Identifier type "{:s}" is not available for this library').format(src_ident))
        
        return None
    
    def test_full_error(self):
        err = self.get_error()
        if err:
            return err
        Operation()
        Operation._s_r.load_settings(self)
        return Operation._s_r.get_error()
        
    def is_full_valid(self):
        return self.test_full_error() == None
        
    def get_para_list(self):
        name = self.get(KEY_QUERY.NAME, '')
        column = self.get(KEY_QUERY.SEARCH_FIELD, '')
        field = self.get(KEY_QUERY.DESTINATION_FIELD, '')
        if (field and field != column):
            column += ' => '+ field
        
        search_mode = self.get(KEY_QUERY.SEARCH_MODE, '')
        template = self.get(KEY_QUERY.S_R_TEMPLATE, '')
        search_for = ''
        if search_mode == CalibreText.S_R_REPLACE:
            search_for = '*'
        else:
            search_for = self.get(KEY_QUERY.SEARCH_FOR, '')
        replace_with = self.get(KEY_QUERY.REPLACE_WITH, '')
        
        if column == 'identifiers':
            src_ident = self.get(KEY_QUERY.S_R_SRC_IDENT, '')
            search_for = src_ident+':'+search_for
            
            dst_ident = self.get(KEY_QUERY.S_R_DST_IDENT, src_ident)
            replace_with = dst_ident+':'+replace_with.strip()
        
        return [ name, column, template, search_mode, search_for, replace_with ]
        
    def string_info(self):
        tbl = self.get_para_list()
        if not tbl[2]: del tbl[2]
        
        return ('name:"'+tbl[0]+'" => ' if tbl[0] else '') + '"'+ '" | "'.join(tbl[1:])+'"'

class OperationError(ValueError):
    pass


def clean_empty_operation(operation_list):
    operation_list = operation_list or []
    default = Operation()
    rlst = []
    for operation in operation_list:
        for key in KEY_QUERY.ALL:
            if operation[key] != default[key]:
                rlst.append(Operation(operation))
                break
    
    return rlst

def operation_list_active(operation_list):
    rlst = []
    for operation in clean_empty_operation(operation_list):
        if operation.get(KEY_QUERY.ACTIVE, True):
            rlst.append(operation)
    
    return rlst


class SearchReplaceWidget(MetadataBulkWidget):
    def __init__(self, book_ids=[], refresh_books=set([])):
        MetadataBulkWidget.__init__(self, book_ids, refresh_books)
        self.updated_fields = self.set_field_calls
    
    def load_settings(self, operation):
        self.load_query(operation)
    
    def save_settings(self):
        return Operation(self.get_query())
    
    def get_error(self):
        return Operation(self.get_query()).get_error()
    
    def search_replace(self, book_id, operation=None):
        if operation:
            self.load_settings(operation)
        
        err = self.get_error()
        if not err:
           err = self.do_search_replace(book_id)
        return err


class SearchReplaceDialog(Dialog):
    def __init__(self, operation=None, book_ids=[]):
        self.operation = operation or Operation()
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
        
        err = self.widget.get_error()
        
        if err:
            if question_dialog(self, _('Invalid operation'),
                             _('The registering of Find/Replace operation has failed.\n{:s}\nDo you want discard the changes?').format(str(err)),
                             default_yes=True, show_copy_button=False, override_icon=get_icon('dialog_warning.png')):
                
                Dialog.reject(self)
                return
            else:
                return
        
        new_operation = self.widget.save_settings()
        new_operation_name = new_operation.get(KEY_QUERY.NAME, None)
        if new_operation_name and new_operation_name == self.operation.get(KEY_QUERY.NAME, None):
            different = False
            for k in new_operation:
                if k in self.operation and new_operation[k] != self.operation[k]:
                    different = True
                    break
            
            if different:
                new_operation[KEY_QUERY.NAME] = ''
                self.operation = new_operation
            
        else:
            self.operation = new_operation
        
        debug_print('Saved operation >', self.operation.string_info())
        debug_print(self.operation)
        Dialog.accept(self)
