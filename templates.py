#!/usr/bin/env python
# ~*~ coding: utf-8 ~*~
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2020, Ahmed Zaki <azaki00.dev@gmail.com>'
__docformat__ = 'restructuredtext en'


# python3 compatibility
from six.moves import range
from six import text_type as unicode
from polyglot.builtins import iteritems, itervalues

from collections import defaultdict, OrderedDict
from functools import partial

from calibre.ebooks.metadata import MetaInformation
from calibre.ebooks.metadata.book.formatter import SafeFormat
from calibre.gui2 import error_dialog, question_dialog
from calibre.gui2.dialogs.template_dialog import TemplateDialog

from .common_utils import get_icon, GUI


TEMPLATE_PREFIX = 'TEMPLATE: '
TEMPLATE_ERROR = 'TEMPLATE_ERROR: '
TEMPLATE_FIELD = '{template}'

try:
    load_translations()
except NameError:
    pass

def check_template(template, show_error=False):
    db = GUI.current_db
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
    
    output = SafeFormat().safe_format(template, mi, TEMPLATE_ERROR, mi)
    for msg in error_msgs:
        if output.lower().find(msg.lower()) != -1:
            error = output.lstrip(TEMPLATE_ERROR)
            if show_error:
                error_dialog(GUI, _('Template Error'),
                        _('Running the template returned an error:') +'\n'+ str(error),
                        show=True)
            return error
    return True


class TemplateBox(TemplateDialog):
    def __init__(self, parent=None, mi=None, fm=None, template_text=''):
        self.db = GUI.current_db
        self.template = template_text
        parent = parent or GUI
        
        if not template_text:
            text = _('Enter a template to test using data from the selected book')
            text_is_placeholder = True
        else:
            text = None
            text_is_placeholder = False
         
        TemplateDialog.__init__(self, parent, text, mi=mi, fm=fm, text_is_placeholder=text_is_placeholder)
        self.setWindowTitle(_('Template editor'))
        self.setWindowIcon(get_icon('template_funcs.png'))
        if template_text:
            self.textbox.insertPlainText(template_text)
    
    def template_is_valide(self):
        return check_template(self.template) is True
    
    def accept(self):
        self.template = unicode(self.textbox.toPlainText()).rstrip()
        TemplateDialog.accept(self)
