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
from calibre_plugins.mass_search_replace.templates import TemplateBox, check_template
import calibre_plugins.mass_search_replace.SearchReplaceCalibreText as CalibreText


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
    if KEY_OPERATION.S_R_ERROR in operation:
        return operation[KEY_OPERATION.S_R_ERROR]
    
    difference = set(KEY_OPERATION.ALL).difference(operation.keys())
    for key in difference:
        return Exception(_('Invalid operation, the "{:s}" key is missing.').format(key))
    
    if operation[KEY_OPERATION.REPLACE_FUNC] not in S_R_FUNCTIONS:
        return Exception(CalibreText.getForLocalizedField(CalibreText.FIELD_NAME.REPLACE_FUNC, operation[KEY_OPERATION.REPLACE_FUNC]))
        
    if operation[KEY_OPERATION.REPLACE_MODE] not in S_R_REPLACE_MODES:
        return Exception(CalibreText.getForLocalizedField(CalibreText.FIELD_NAME.REPLACE_MODE, operation[KEY_OPERATION.REPLACE_MODE]))
        
    if operation[KEY_OPERATION.SEARCH_MODE] not in S_R_MATCH_MODES:
        return Exception(CalibreText.getForLocalizedField(CalibreText.FIELD_NAME.SEARCH_MODE, operation[KEY_OPERATION.SEARCH_MODE]))
    
    return None

def operation_isValid(operation):
    return operation_testGetError(operation) == None

def operation_testFullError(operation, plugin_action):
    err = operation_testGetError(operation)
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
        
        err = self.widget.testGetError()
        
        if err:
            if question_dialog(self.parent, _('Invalid operation'),
                             _('The registering of Find/Replace operation has failed.\n{0}\nDo you want discard the changes?').format(err),
                             default_yes=True, show_copy_button=True, override_icon=get_icon('images/warning.png')):
                
                Dialog.reject(self)
                return
            else:
                return
        
        self.operation = self.widget.save_settings()
        debug_print('Saved operation > {0:s}\n{1}\n'.format(operation_string(self.operation), self.operation))
        Dialog.accept(self)



    def validate(self, settings):
        
        if not settings:
            return (_('Settings Error'), _('You must configure this action before running it'))
        if settings.get('s_r_error'):
            return (_('Wrong Expression'), error_message(settings['s_r_error']))
        
        all_fields, writable_fields = self.get_possible_fields()
        
        search_field = settings['search_field']
        dest_field = settings['destination_field']
        if not search_field:
            return (_('Search field unavailable'), _('You must choose a search field'))
        if search_field not in all_fields:
            return (_('Search field unavailable'), _('Search field "{}" is not available for this library'.format(search_field)))
        if search_field == '{template}':
            dest_field = settings['destination_field']
            if not dest_field:
                return (_('Destination field empty'), _('Destination field cannot be empty if the search field is a template'))
            if not dest_field in writable_fields:
                return (_('Destination field unavailable'), _('Destination field "{}" is not available for this library'.format(dest_field)))
            is_template_valid = check_template(settings['s_r_template'], self.plugin_action, print_error=False)
            if is_template_valid is not True:
                return is_template_valid
        if dest_field == 'identifiers' or (search_field == 'identifiers' and dest_field == ''):
            dest_ident = settings['s_r_dst_ident']
            if not dest_ident or ( dest_ident == '*'):
                return (_('Invalid identifier'), _('You must enter a valid destination identifier (not empty or *)'))
        if dest_field and not ( dest_field in writable_fields ):
            return (_('Destination field unavailable'), _('Destination field "{}" not available for this library'.format(dest_field)))
        return True

class TestField:
    
    def get_possible_fields(db):
        all_fields = []
        writable_fields = []
        fm = db.field_metadata
        for f in fm:
            if (f in ['author_sort'] or
                    (fm[f]['datatype'] in ['text', 'series', 'enumeration', 'comments', 'rating'] and
                    fm[f].get('search_terms', None) and
                    f not in ['formats', 'ondevice', 'series_sort']) or
                    (fm[f]['datatype'] in ['int', 'float', 'bool', 'datetime'] and
                    f not in ['id', 'timestamp'])):
                all_fields.append(f)
                writable_fields.append(f)
            if fm[f]['datatype'] == 'composite':
                all_fields.append(f)
        all_fields.sort()
        all_fields.insert(1, '{template}')
        writable_fields.sort()
        return all_fields, writable_fields
    
    
    def get_possible_cols(db):
        standard = [
            'title',
            'authors',
            'tags',
            'series',
            'publisher',
            'pubdate',
            'rating',
            'languages',
            'last_modified',
            'timestamp',
            'comments',
            'author_sort',
            'sort',
            'marked'
        ]                
        custom = sorted([ k for k,v in db.field_metadata.custom_field_metadata().items() if v['datatype'] not in [None,'composite'] ])
        return standard + custom
    
    
    def is_enum(db, col_name, val):
        col_metadata = db.field_metadata.all_metadata()
        col_type = col_metadata['datatype']
        if not col_type == 'enumeration':
            raise ValueError
        vals = col_metadata['display']['enum_values'] + ['']
        if not val in vals:
            raise ValueError
        else:
            return val
    
    def is_bool(val):
        if unicode(val).lower() in ['yes','y','true','1']:
            return True
        elif unicode(val).lower() in ['no','n','false','0']:
            return False
        elif unicode(val).strip() == '':
            return ''
        else:
            raise ValueError
