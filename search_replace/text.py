#!/usr/bin/env python

__license__   = 'GPL v3'
__copyright__ = '2020, un_pogaz <un.pogaz@gmail.com>'


try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9


SEARCH_FIELD = _('You must specify a "Search field"')

class FIELD_NAME:
    REPLACE_FUNC = _('Case to be applied')
    REPLACE_MODE = _('Replace mode')
    SEARCH_MODE = _('Search mode')
    IDENTIFIER_TYPE = _('Identifier type')

S_R_REPLACE = _('Replace field')
REPLACE_REGEX = '(?msi)^.*$'
REPLACE_HEADING = _(
                 'In field replacement mode, the specified field is set '
                 'to the text and all previous values are erased. After '
                 'replacement is finished, the text can be changed to '
                 'upper-case, lower-case, or title-case.')

TEMPLATE_BUTTON_ToolTip = _('Open the template editor')

EXCEPTION_Invalid_identifier = _('Invalid identifier string. It must be a comma-separated list of pairs of strings separated by a colon.')

def get_empty_field(field):
    return _('The field "{:s}" is not defined').format(field)

def get_for_invalid_value(field, value):
    return _('The operation field "{:s}" contains a invalid value ({:s}).').format(field, value)

def get_for_localized_field(field, value):
    return get_for_invalid_value(field, value)+'\n'+_('The value of this field is localized (translated). This can cause problems when using settings shared on internet or when changing the user interface language.')
