#!/usr/bin/env python
# ~*~ coding: utf-8 ~*~
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__ = 'GPL v3'
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
from PyQt5.Qt import Qt, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QSize
                      
from calibre import prints
from calibre.gui2 import error_dialog, question_dialog, warning_dialog
from calibre.gui2.widgets2 import Dialog

from calibre_plugins.mass_search_replace.common_utils import debug_print
from calibre_plugins.mass_search_replace.SearchReplaceCalibre import MetadataBulkWidget, KEY_QUERY as CALIBRE_KEY_QUERY, TEMPLATE_FIELD

class KEY_QUERY():
    locals().update(vars(CALIBRE_KEY_QUERY))

_default_query = None

def get_default_query(plugin_action):
        global _default_query
        if not _default_query:
            s_r = SearchReplaceWidget(plugin_action)
            s_r.resize(QSize(0, 0))
            _default_query = s_r.save_settings()
            s_r.close()
            del s_r
        
        return _default_query

def query_hasSearchField(query):
    return len(query[KEY_QUERY.SEARCH_FIELD])>0
def query_hasError(query):
    return KEY_QUERY.S_R_ERROR in query
def query_hasAllKey(query):
    for key in KEY_QUERY.ALL:
        if key not in query.keys():
            return False
    return True

def query_isValid(query):
    return query_hasSearchField(query) and query_hasAllKey(query) and not query_hasError(query)


def query_string(query):
    column = query[KEY_QUERY.SEARCH_FIELD]
    field = query[KEY_QUERY.DESTINATION_FIELD]
    if (field and field != column):
        column += ' => '+ field
    
    return '"'+ '" | "'.join([column, query[KEY_QUERY.SEARCH_MODE], query[KEY_QUERY.SEARCH_FOR], query[KEY_QUERY.REPLACE_WITH]])+'"'


class SearchReplaceWidget(MetadataBulkWidget):
    def __init__(self, plugin_action, book_ids=[], refresh_books=set([])):
        
        if not book_ids or len(book_ids)==0:
            book_ids = plugin_action.gui.library_view.get_selected_ids();
        
        MetadataBulkWidget.__init__(self, plugin_action, book_ids, refresh_books)
        self.updated_fields = self.set_field_calls
    
    def load_settings(self, query):
        self.load_query(query)
        
    def save_settings(self):
        return self.get_query()
    
    def search_replace(self, book_id, query):
        self.load_settings(query)
        self.do_search_replace(book_id)

class SearchReplaceDialog(Dialog):
    def __init__(self, parent, plugin_action, query, book_ids=[]):
        self.plugin_action = plugin_action
        self.parent = parent
        self.query = query
        self.widget = SearchReplaceWidget(self.plugin_action, book_ids)
        Dialog.__init__(self, _('Search/Replace configuration'), 'config_query_SearchReplace', parent)

    def setup_ui(self):
        l = QVBoxLayout()
        self.setLayout(l)
        l.addWidget(self.widget)
        l.addWidget(self.bb)
        
        self.widget.load_settings(self.query)
        
    
    def accept(self):
        self.query = self.widget.save_settings()
        
        msg_error = None
        if not query_hasSearchField(self.query):
            msg_error = _('You must specify the target "Search field".')
        
        if query_hasError(self.query):
            msg_error = str(self.query[KEY_QUERY.S_R_ERROR])
        
        if msg_error:
            if question_dialog(self.parent, _('Invalid operation'),
                             _('The registering of Find/Replace operation has failed.\n{:s}\nResume to the editing?\nElse, the changes will be discard.').format(msg_error),
                             default_yes=True, show_copy_button=False):
                
                return
            else:
                Dialog.reject(self)
                return
        
        debug_print('Saved operation > {0:s}\n{1}\n'.format(query_string(self.query), self.query))
        Dialog.accept(self)

