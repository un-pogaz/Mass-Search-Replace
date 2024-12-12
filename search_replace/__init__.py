#!/usr/bin/env python

__license__   = 'GPL v3'
__copyright__ = '2020, Ahmed Zaki <azaki00.dev@gmail.com> ; adjustment 2020, un_pogaz <un.pogaz@gmail.com>'


try:
    load_translations()
except NameError:
    pass  # load_translations() added in calibre 1.9

import copy
from typing import Any, List

try:
    from qt.core import QVBoxLayout
except ImportError:
    from PyQt5.Qt import QVBoxLayout

from calibre.gui2 import question_dialog
from calibre.gui2.widgets2 import Dialog

from . import text as CalibreText
from .calibre import KEY_QUERY, S_R_FUNCTIONS, S_R_MATCH_MODES, S_R_REPLACE_MODES, MetadataBulkWidget
from ..common_utils import GUI, current_db, debug_print, get_icon
from ..common_utils.columns import get_all_identifiers, get_possible_fields


class Operation(dict):
    
    _default_operation = None
    _s_r = None
    
    def __init__(self, src=None):
        dict.__init__(self)
        if not src:
            if not Operation._s_r or Operation._s_r.db != current_db():
                _s_r = Operation._s_r = SearchReplaceWidget([0])
            if not Operation._default_operation:
                Operation._default_operation = _s_r.get_operation()
                Operation._default_operation[KEY_QUERY.ACTIVE] = True
            
            src = copy.copy(Operation._default_operation)
        
        self.update(src)
    
    def get_error(self) -> Any:
        
        if not self:
            return TypeError
        
        if KEY_QUERY.S_R_ERROR in self:
            return self[KEY_QUERY.S_R_ERROR]
        
        difference = set(KEY_QUERY.ALL).difference(self.keys())
        for key in difference:
            return OperationError(_('Invalid operation, the "{:s}" key is missing.').format(key))
        
        if self[KEY_QUERY.REPLACE_FUNC] not in S_R_FUNCTIONS:
            return OperationError(CalibreText.get_for_localized_field(
                CalibreText.FIELD_NAME.REPLACE_FUNC, self[KEY_QUERY.REPLACE_FUNC]
            ))
            
        if self[KEY_QUERY.REPLACE_MODE] not in S_R_REPLACE_MODES:
            return OperationError(CalibreText.get_for_localized_field(
                CalibreText.FIELD_NAME.REPLACE_MODE, self[KEY_QUERY.REPLACE_MODE]
            ))
            
        if self[KEY_QUERY.SEARCH_MODE] not in S_R_MATCH_MODES:
            return OperationError(CalibreText.get_for_localized_field(
                CalibreText.FIELD_NAME.SEARCH_MODE, self[KEY_QUERY.SEARCH_MODE]
            ))
        
        #Field test
        all_fields, writable_fields = get_possible_fields()
        
        search_field = self[KEY_QUERY.SEARCH_FIELD]
        dest_field = self[KEY_QUERY.DESTINATION_FIELD]
        
        if search_field not in all_fields:
            return OperationError(_('Search field "{:s}" is not available for this library').format(search_field))
            
        if dest_field and (dest_field not in writable_fields):
            return OperationError(_('Destination field "{:s}" is not available for this library').format(dest_field))
        
        possible_idents = get_all_identifiers()
        
        if search_field == 'identifiers':
            src_ident = self[KEY_QUERY.S_R_SRC_IDENT]
            if src_ident not in possible_idents:
                return OperationError(_('Identifier type "{:s}" is not available for this library').format(src_ident))
        
        return None
    
    def test_full_error(self) -> Any:
        err = self.get_error()
        if err:
            return err
        Operation()
        Operation._s_r.load_operation(self)
        return Operation._s_r.get_error()
        
    def is_full_valid(self) -> bool:
        return self.test_full_error() is None
        
    def get_para_list(self) -> List[str]:
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
        
    def string_info(self) -> str:
        tbl = self.get_para_list()
        if not tbl[2]:
            del tbl[2]
        
        return ('name:"'+tbl[0]+'" => ' if tbl[0] else '') + '"'+ '" | "'.join(tbl[1:])+'"'

class OperationError(ValueError):
    pass


def clean_empty_operation(operation_list) -> List[Operation]:
    operation_list = operation_list or []
    default = Operation()
    rlst = []
    for operation in operation_list:
        for key in KEY_QUERY.ALL:
            if operation[key] != default[key]:
                rlst.append(Operation(operation))
                break
    
    return rlst

def operation_list_active(operation_list) -> List[Operation]:
    rlst = []
    for operation in clean_empty_operation(operation_list):
        if operation.get(KEY_QUERY.ACTIVE, True):
            rlst.append(operation)
    
    return rlst


class SearchReplaceWidget(MetadataBulkWidget):
    def __init__(self, book_ids=[], refresh_books=set()):
        self.original_operation = None
        MetadataBulkWidget.__init__(self, book_ids, refresh_books)
        self.updated_fields = self.set_field_calls
        self.load_query = self.load_operation
    
    def load_operation(self, operation):
        self.original_operation = Operation(operation)
        MetadataBulkWidget.load_query(self, operation)
    
    def get_operation(self) -> Operation:
        return Operation(self.get_query())
    
    def get_error(self) -> Any:
        return Operation(self.get_query()).get_error()
    
    def search_replace(self, book_id, operation=None) -> Any:
        if operation:
            self.load_operation(operation)
        
        err = self.get_error()
        if not err:
           err = self.do_search_replace(book_id)
        return err


class SearchReplaceDialog(Dialog):
    def __init__(self, operation=None, book_ids=[]):
        self.operation = operation or Operation()
        self.widget = SearchReplaceWidget(book_ids[:10])
        Dialog.__init__(self,
            title=_('Configuration of a Search/Replace operation'),
            name='plugin.MassSearchReplace:config_query_SearchReplace',
            parent=GUI,
        )
    
    def setup_ui(self):
        l = QVBoxLayout()
        self.setLayout(l)
        l.addWidget(self.widget)
        l.addWidget(self.bb)
        
        if self.operation:
            self.widget.load_operation(self.operation)
    
    def accept(self):
        err = self.widget.get_error()
        
        if err:
            if question_dialog(self, _('Invalid operation'),
                             _('The registering of Find/Replace operation has failed.\n{:s}\n'
                               'Do you want discard the changes?').format(str(err)),
                               default_yes=True, show_copy_button=False, override_icon=get_icon('dialog_warning.png')):
                
                Dialog.reject(self)
                return
            else:
                return
        
        new_operation = self.widget.get_operation()
        original_operation = self.widget.original_operation
        new_operation_name = new_operation.get(KEY_QUERY.NAME, None)
        original_operation_name = original_operation.get(KEY_QUERY.NAME, None)
        if new_operation_name and new_operation_name == original_operation_name:
            different = False
            for k in new_operation:
                if k in original_operation and new_operation[k] != original_operation[k]:
                    if k == KEY_QUERY.S_R_SRC_IDENT and not KEY_QUERY.SEARCH_FIELD == 'identifiers':
                        continue
                    if k == KEY_QUERY.S_R_DST_IDENT and not KEY_QUERY.DESTINATION_FIELD == 'identifiers':
                        continue
                    different = True
                    break
            
            if different:
                if question_dialog(self, _('Changed operation'),
                _('The content of the Find/Replace operation "{:s}" was edited after being loaded into the editor.\n'
                    'The operation will be saved has it and not as a shared named operation!\n'
                    'Do you want continue?').format(new_operation_name),
                    default_yes=True, show_copy_button=False, override_icon=get_icon('dialog_warning.png')):
                    
                    new_operation[KEY_QUERY.NAME] = ''
                else:
                    return
        
        self.operation = new_operation
        
        debug_print('Saved operation >', self.operation.string_info())
        debug_print(self.operation)
        Dialog.accept(self)
