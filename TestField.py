#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2020, un_pogaz <un.pogaz@gmail.com>'
__docformat__ = 'restructuredtext en'

import os, time
# calibre Python 3 compatibility.
from six import text_type as unicode

try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9

from .SearchReplaceCalibre import TEMPLATE_FIELD

def get_possible_fields(db):
    all_fields = []
    writable_fields = []
    fm = db.field_metadata
    for f in fm:
        if (f in ['author_sort'] or
                (fm[f]['datatype'] in ['text', 'series', 'enumeration', 'comments', 'rating'] and fm[f].get('search_terms', None) and f not in ['formats', 'ondevice', 'series_sort']) or
                (fm[f]['datatype'] in ['int', 'float', 'bool', 'datetime'] and f not in ['id', 'timestamp'])):
            all_fields.append(f)
            writable_fields.append(f)
        if fm[f]['datatype'] == 'composite':
            all_fields.append(f)
    all_fields.sort()
    all_fields.insert(1, TEMPLATE_FIELD)
    writable_fields.sort()
    return all_fields, writable_fields

def get_possible_idents(db):
    return db.get_all_identifier_types()

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
