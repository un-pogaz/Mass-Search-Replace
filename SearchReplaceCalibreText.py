#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2020, un_pogaz <un.pogaz@gmail.com>'
__docformat__ = 'restructuredtext en'

import os, time, shutil
# calibre Python 3 compatibility.
from six import text_type as unicode

try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9


SEARCH_FIELD = _('You must specify a "Search field"')

EMPTY_FIELD = _('The field "{:s}" is not defined')

class FIELD_NAME:
    REPLACE_FUNC = _('Case to be applied')
    REPLACE_MODE = _('Replace mode')
    SEARCH_MODE = _('Search mode')

TEMPLATE_BUTTON_ToolTip = _('template button ToolTip')

def getForInvalidValue(field, value):
    return _('The operation field "{0:s}" contains a invalid value ({1}).').format(field, value)

def getForLocalizedField(field, value):
    return getForInvalidValue(field, value)+'\n'+_('The value of this field is localized (translated). This can cause problems when using settings shared on internet or when changing the user interface language.')
