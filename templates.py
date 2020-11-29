#!/usr/bin/env python
# ~*~ coding: utf-8 ~*~
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__ = 'GPL v3'
__copyright__ = '2020, Ahmed Zaki <azaki00.dev@gmail.com>'
__docformat__ = 'restructuredtext en'

from functools import partial
from collections import OrderedDict, defaultdict
import re
import traceback
import copy
import json

# python3 compatibility
from six.moves import range
from six import text_type as unicode, string_types as basestring

try:
    from PyQt5 import QtWidgets as QtGui
    from PyQt5.Qt import (Qt, QGridLayout, QHBoxLayout, QVBoxLayout, QToolButton,
                          QDialog, QSizePolicy, QSize)

except ImportError:
    from PyQt4 import QtGui
    from PyQt4.Qt import (Qt, QGridLayout, QHBoxLayout, QVBoxLayout, QToolButton,
                          QDialog, QSizePolicy, QSize)

from calibre import prints
from calibre.constants import DEBUG
from calibre.ebooks.metadata import MetaInformation
from calibre.ebooks.metadata.book.formatter import SafeFormat
from calibre.gui2 import error_dialog
from calibre.gui2.dialogs.template_dialog import TemplateDialog

from calibre_plugins.action_chains.common_utils import get_icon

TEMPLATE_PREFIX = 'TEMPLATE: '
TEMPLATE_ERROR = 'TEMPLATE_ERROR: '

try:
    load_translations()
except NameError:
    prints("ActionsChain/templates.py - exception when loading translations")

def check_template(template, plugin_action, print_error=True):
    gui = plugin_action.gui
    db = gui.current_db
    error_msgs = [
        TEMPLATE_ERROR,
        'unknown function',
        'unknown identifier',
        'unknown field',
        'assign requires the first parameter be an id',
        'missing closing parenthesis',
        'incorrect number of arguments for function',
        'expression is not function or constant'
    ]
    try:
        book_id = list(db.all_ids())[0]
        mi = db.get_metadata(book_id, index_is_id=True, get_user_categories=True)
    except:
        mi = MetaInformation(_('Unknown'))
    # add any extra fields by actions that define update_metadata
    plugin_action.update_metadata(mi)
    #
    output = SafeFormat().safe_format(template, mi, TEMPLATE_ERROR, mi)
    for msg in error_msgs:
        if output.lower().find(msg.lower()) != -1:
            error = _('Running the template: {} returned an error:\n{}').format(template, output.lstrip(TEMPLATE_ERROR))
            if print_error:
                return error_dialog(gui, _('Template Error'), error, show=True)
            return _('Template Error'), error
    return True

class TemplateBox(TemplateDialog):
    def __init__(
        self,
        parent,
        plugin_action,
        template_text=''
    ):
        self.plugin_action = plugin_action
        self.gui = plugin_action.gui
        self.db = self.gui.current_db
        rows = self.gui.current_view().selectionModel().selectedRows()
        if rows:
            index = rows[0]
            mi = self.db.get_metadata(index.row(), index_is_id=False, get_cover=False)
        else:
            try:
                book_id = list(self.db.all_ids())[0]
                mi = self.db.get_metadata(book_id, index_is_id=True, get_user_categories=True)
            except:
                mi = MetaInformation(_('Unknown'))
        # add any extra fields by actions that define update_metadata
        plugin_action.update_metadata(mi)
        #
        if not template_text:
            text = _('Enter a template to test using data from the selected book')
            text_is_placeholder = True
            window_title = _('Add template')
        else:
            text = None
            text_is_placeholder = False
            window_title = _('Edit Template')
        TemplateDialog.__init__(
            self,
            parent,
            text,
            mi=mi,
            text_is_placeholder=text_is_placeholder
        )
        self.setWindowTitle(window_title)
        if template_text:
            self.textbox.insertPlainText(template_text)
    
    def accept(self):
        self.template = unicode(self.textbox.toPlainText()).rstrip()
        chk = check_template(self.template, self.plugin_action)
        if chk is True:
            QDialog.accept(self)

