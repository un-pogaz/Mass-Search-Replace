#!/usr/bin/env python
# ~*~ coding: utf-8 ~*~
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2008, Kovid Goyal <kovid at kovidgoyal.net> ; 2020, Ahmed Zaki <azaki00.dev@gmail.com> ; adjustment 2020, un_pogaz <un.pogaz@gmail.com>'
__docformat__ = 'restructuredtext en'

import regex, numbers
from collections import defaultdict

# python 3 compatibility
from six import text_type as unicode
from six.moves import range

try:
    from qt.core import QtCore, QtGui, QtWidgets
except:
    from PyQt5 import QtCore, QtGui, QtWidgets

try:
    QShape = QtWidgets.QFrame.Shape
    QShadow = QtWidgets.QFrame.Shadow
    QSizeConstraint = QtWidgets.QLayout.SizeConstraint
    QPolicy = QtWidgets.QSizePolicy.Policy
except:
    QShape = QtWidgets.QFrame
    QShadow = QtWidgets.QFrame
    QSizeConstraint = QtWidgets.QLayout
    QPolicy = QtWidgets.QSizePolicy

from calibre import prints
from calibre.constants import iswindows, isosx, numeric_version as calibre_version
from calibre.gui2 import error_dialog, FunctionDispatcher, question_dialog
from calibre.ebooks.metadata.book.formatter import SafeFormat
from calibre.gui2.dialogs.template_line_editor import TemplateLineEditor
from calibre.utils.config import JSONConfig, dynamic, prefs, tweaks
from calibre.utils.date import now
from calibre.utils.icu import capitalize, sort_key
from calibre.utils.titlecase import titlecase
from calibre.gui2.widgets import LineEditECM, HistoryLineEdit
from calibre.gui2.widgets2 import Dialog
from polyglot.builtins import error_message, iteritems, itervalues, native_string_type, unicode_type

from calibre_plugins.mass_search_replace.templates import TemplateBox, check_template
import calibre_plugins.mass_search_replace.SearchReplaceCalibreText as CalibreText

TEMPLATE_FIELD = '{template}'

S_R_FUNCTIONS = {
        '' : lambda x: x,
        _('Lower Case') : lambda x: icu_lower(x),
        _('Upper Case') : lambda x: icu_upper(x),
        _('Title Case') : lambda x: titlecase(x),
        _('Capitalize') : lambda x: capitalize(x),
                }

S_R_MATCH_MODES = [
        _('Character match'),
        _('Regular expression'),
        CalibreText.S_R_REPLACE, ##un_pogaz Replace Field
                  ]

S_R_REPLACE_MODES = [
        _('Replace field'),
        _('Prepend to field'),
        _('Append to field'),
                    ]

class KEY:
    CASE_SENSITIVE      = 'case_sensitive'
    COMMA_SEPARATED     = 'comma_separated'
    DESTINATION_FIELD   = 'destination_field'
    MULTIPLE_SEPARATOR  = 'multiple_separator'
    NAME                = 'name'
    REPLACE_FUNC        = 'replace_func'
    REPLACE_MODE        = 'replace_mode'
    REPLACE_WITH        = 'replace_with'
    RESULTS_COUNT       = 'results_count'
    S_R_DST_IDENT       = 's_r_dst_ident'
    S_R_SRC_IDENT       = 's_r_src_ident'
    S_R_TEMPLATE        = 's_r_template'
    SEARCH_FIELD        = 'search_field'
    SEARCH_FOR          = 'search_for'
    SEARCH_MODE         = 'search_mode'
    STARTING_FROM       = 'starting_from'
    
    S_R_ERROR           = 's_r_error'
    
    ALL = [
        NAME,
        CASE_SENSITIVE    ,
        COMMA_SEPARATED   ,
        DESTINATION_FIELD ,
        MULTIPLE_SEPARATOR,
        REPLACE_FUNC      ,
        REPLACE_MODE      ,
        REPLACE_WITH      ,
        RESULTS_COUNT     ,
        S_R_DST_IDENT     ,
        S_R_SRC_IDENT     ,
        S_R_TEMPLATE      ,
        SEARCH_FIELD      ,
        SEARCH_FOR        ,
        SEARCH_MODE       ,
        STARTING_FROM     ,
    ]
    
    LOCALIZED_FIELD = {
        REPLACE_FUNC : S_R_FUNCTIONS.keys(),
        REPLACE_MODE : S_R_REPLACE_MODES,
        SEARCH_MODE  : S_R_MATCH_MODES,
    }
    


# class borrowed from src/calibre/gui2/dialogs/metadata_bulk_ui.py & src/calibre/gui2/dialogs/metadata_bulk.py 
class MetadataBulkWidget(QtWidgets.QWidget):
    def __init__(self, plugin_action, book_ids=[], refresh_books=set([])):
        QtWidgets.QWidget.__init__(self)
        self.plugin_action = plugin_action
        self.gui = plugin_action.gui
        self.db = self.gui.current_db
        self.ids = book_ids
        self.refresh_books = refresh_books
        self.set_field_calls = defaultdict(dict)
        self.changed = False
        self._init_controls()
        self.prepare_search_and_replace()
    
    def _init_controls(self):
        l = QtWidgets.QVBoxLayout()
        self.setLayout(l)
        self.scrollArea3 = QtWidgets.QScrollArea()
        self.scrollArea3.setFrameShape(QShape.NoFrame)
        self.scrollArea3.setWidgetResizable(True)
        self.scrollArea3.setObjectName("scrollArea3")
        self.tabWidgetPage3 = QtWidgets.QWidget()
        self.tabWidgetPage3.setGeometry(QtCore.QRect(0, 0, 804, 388))
        self.tabWidgetPage3.setObjectName("tabWidgetPage3")
        self.vargrid = QtWidgets.QGridLayout(self.tabWidgetPage3)
        self.vargrid.setSizeConstraint(QSizeConstraint.SetMinimumSize)
        self.vargrid.setObjectName("vargrid")
        self.s_r_heading = QtWidgets.QLabel(self.tabWidgetPage3)
        self.s_r_heading.setWordWrap(True)
        self.s_r_heading.setOpenExternalLinks(True)
        self.s_r_heading.setObjectName("s_r_heading")
        self.vargrid.addWidget(self.s_r_heading, 0, 0, 1, 4)
        self.filler = QtWidgets.QLabel(self.tabWidgetPage3)
        self.filler.setText("")
        self.filler.setObjectName("filler")
        self.vargrid.addWidget(self.filler, 1, 0, 1, 1)
        self.line = QtWidgets.QFrame(self.tabWidgetPage3)
        self.line.setFrameShape(QShape.HLine)
        self.line.setFrameShadow(QShadow.Sunken)
        self.line.setObjectName("line")
        self.vargrid.addWidget(self.line, 2, 0, 1, 3)
        self.xlabel_22 = QtWidgets.QLabel(self.tabWidgetPage3)
        self.xlabel_22.setObjectName("xlabel_22")
        self.vargrid.addWidget(self.xlabel_22, 3, 0, 1, 1)
        self.query_field = QtWidgets.QComboBox(self.tabWidgetPage3)
        self.query_field.setObjectName("query_field")
        self.vargrid.addWidget(self.query_field, 3, 1, 1, 1)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        spacerItem4 = QtWidgets.QSpacerItem(20, 20, QPolicy.Fixed, QPolicy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem4)
        self.save_button = QtWidgets.QPushButton(self.tabWidgetPage3)
        self.save_button.setObjectName("save_button")
        self.horizontalLayout_6.addWidget(self.save_button)
        self.remove_button = QtWidgets.QPushButton(self.tabWidgetPage3)
        self.remove_button.setObjectName("remove_button")
        self.horizontalLayout_6.addWidget(self.remove_button)
        spacerItem5 = QtWidgets.QSpacerItem(40, 20, QPolicy.Expanding, QPolicy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem5)
        self.vargrid.addLayout(self.horizontalLayout_6, 3, 2, 1, 1)
        self.source_field_label = QtWidgets.QLabel(self.tabWidgetPage3)
        self.source_field_label.setObjectName("source_field_label")
        self.vargrid.addWidget(self.source_field_label, 4, 0, 1, 1)
        self.search_field = QtWidgets.QComboBox(self.tabWidgetPage3)
        self.search_field.setObjectName("search_field")
        self.vargrid.addWidget(self.search_field, 4, 1, 1, 1)
        self.HLayout_4 = QtWidgets.QHBoxLayout()
        self.HLayout_4.setObjectName("HLayout_4")
        self.xlabel_24 = QtWidgets.QLabel(self.tabWidgetPage3)
        self.xlabel_24.setObjectName("xlabel_24")
        self.HLayout_4.addWidget(self.xlabel_24)
        self.search_mode = QtWidgets.QComboBox(self.tabWidgetPage3)
        self.search_mode.setObjectName("search_mode")
        self.HLayout_4.addWidget(self.search_mode)
        spacerItem6 = QtWidgets.QSpacerItem(20, 10, QPolicy.Expanding, QPolicy.Minimum)
        self.HLayout_4.addItem(spacerItem6)
        self.vargrid.addLayout(self.HLayout_4, 4, 2, 1, 1)
        self.s_r_src_ident_label = QtWidgets.QLabel(self.tabWidgetPage3)
        self.s_r_src_ident_label.setObjectName("s_r_src_ident_label")
        self.vargrid.addWidget(self.s_r_src_ident_label, 5, 0, 1, 1)
        self.s_r_src_ident = QtWidgets.QComboBox(self.tabWidgetPage3)
        sizePolicy = QtWidgets.QSizePolicy(QPolicy.Expanding, QPolicy.Fixed)
        sizePolicy.setHorizontalStretch(100)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.s_r_src_ident.sizePolicy().hasHeightForWidth())
        self.s_r_src_ident.setSizePolicy(sizePolicy)
        self.s_r_src_ident.setObjectName("s_r_src_ident")
        self.vargrid.addWidget(self.s_r_src_ident, 5, 1, 1, 1)
        self.template_label = QtWidgets.QLabel(self.tabWidgetPage3)
        self.template_label.setObjectName("template_label")
        self.vargrid.addWidget(self.template_label, 5, 0, 1, 1)
        self.s_r_template = HistoryLineEdit(self.tabWidgetPage3)
        sizePolicy = QtWidgets.QSizePolicy(QPolicy.Expanding, QPolicy.Fixed)
        sizePolicy.setHorizontalStretch(100)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.s_r_template.sizePolicy().hasHeightForWidth())
        self.s_r_template.setSizePolicy(sizePolicy)
        self.s_r_template.setObjectName("s_r_template")
        self.vargrid.addWidget(self.s_r_template, 5, 1, 1, 1)
        self.search_for_label = QtWidgets.QLabel(self.tabWidgetPage3)
        self.search_for_label.setObjectName("search_for_label")
        self.vargrid.addWidget(self.search_for_label, 6, 0, 1, 1)
        self.search_for = HistoryLineEdit(self.tabWidgetPage3)
        sizePolicy = QtWidgets.QSizePolicy(QPolicy.Expanding, QPolicy.Fixed)
        sizePolicy.setHorizontalStretch(100)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.search_for.sizePolicy().hasHeightForWidth())
        self.search_for.setSizePolicy(sizePolicy)
        self.search_for.setObjectName("search_for")
        self.vargrid.addWidget(self.search_for, 6, 1, 1, 1)
        self.case_sensitive = QtWidgets.QCheckBox(self.tabWidgetPage3)
        self.case_sensitive.setChecked(True)
        self.case_sensitive.setObjectName("case_sensitive")
        self.vargrid.addWidget(self.case_sensitive, 6, 2, 1, 1)
        self.xlabel_4 = QtWidgets.QLabel(self.tabWidgetPage3)
        self.xlabel_4.setObjectName("xlabel_4")
        self.vargrid.addWidget(self.xlabel_4, 7, 0, 1, 1)
        self.replace_with = HistoryLineEdit(self.tabWidgetPage3)
        ##un_pogaz sizePolicy for replace_with
        sizePolicy = QtWidgets.QSizePolicy(QPolicy.Expanding, QPolicy.Fixed)
        sizePolicy.setHorizontalStretch(100)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.replace_with.sizePolicy().hasHeightForWidth())
        self.replace_with.setSizePolicy(sizePolicy)
        ##
        self.replace_with.setObjectName("replace_with")
        self.vargrid.addWidget(self.replace_with, 7, 1, 1, 1)
        self.verticalLayout = QtWidgets.QHBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_41 = QtWidgets.QLabel(self.tabWidgetPage3)
        self.label_41.setObjectName("label_41")
        self.verticalLayout.addWidget(self.label_41)
        self.replace_func = QtWidgets.QComboBox(self.tabWidgetPage3)
        self.replace_func.setObjectName("replace_func")
        self.verticalLayout.addWidget(self.replace_func)
        spacerItem7 = QtWidgets.QSpacerItem(20, 10, QPolicy.Expanding, QPolicy.Minimum)
        self.verticalLayout.addItem(spacerItem7)
        self.vargrid.addLayout(self.verticalLayout, 7, 2, 1, 1)
        self.destination_field_label = QtWidgets.QLabel(self.tabWidgetPage3)
        self.destination_field_label.setObjectName("destination_field_label")
        self.vargrid.addWidget(self.destination_field_label, 8, 0, 1, 1)
        self.destination_field = QtWidgets.QComboBox(self.tabWidgetPage3)
        self.destination_field.setObjectName("destination_field")
        self.vargrid.addWidget(self.destination_field, 8, 1, 1, 1)
        self.verticalLayout_2 = QtWidgets.QHBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.replace_mode_label = QtWidgets.QLabel(self.tabWidgetPage3)
        self.replace_mode_label.setObjectName("replace_mode_label")
        self.verticalLayout_2.addWidget(self.replace_mode_label)
        self.replace_mode = QtWidgets.QComboBox(self.tabWidgetPage3)
        self.replace_mode.setObjectName("replace_mode")
        self.verticalLayout_2.addWidget(self.replace_mode)
        self.comma_separated = QtWidgets.QCheckBox(self.tabWidgetPage3)
        self.comma_separated.setChecked(True)
        self.comma_separated.setObjectName("comma_separated")
        self.verticalLayout_2.addWidget(self.comma_separated)
        spacerItem8 = QtWidgets.QSpacerItem(20, 10, QPolicy.Expanding, QPolicy.Minimum)
        self.verticalLayout_2.addItem(spacerItem8)
        self.vargrid.addLayout(self.verticalLayout_2, 8, 2, 1, 1)
        self.s_r_dst_ident_label = QtWidgets.QLabel(self.tabWidgetPage3)
        self.s_r_dst_ident_label.setObjectName("s_r_dst_ident_label")
        self.vargrid.addWidget(self.s_r_dst_ident_label, 9, 0, 1, 1)
        self.s_r_dst_ident = QtWidgets.QLineEdit(self.tabWidgetPage3)
        sizePolicy = QtWidgets.QSizePolicy(QPolicy.Expanding, QPolicy.Fixed)
        sizePolicy.setHorizontalStretch(100)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.s_r_dst_ident.sizePolicy().hasHeightForWidth())
        self.s_r_dst_ident.setSizePolicy(sizePolicy)
        self.s_r_dst_ident.setObjectName("s_r_dst_ident")
        self.vargrid.addWidget(self.s_r_dst_ident, 9, 1, 1, 1)
        self.horizontalLayout_21 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_21.setObjectName("horizontalLayout_21")
        spacerItem9 = QtWidgets.QSpacerItem(20, 0, QPolicy.Expanding, QPolicy.Minimum)
        self.horizontalLayout_21.addItem(spacerItem9)
        self.xlabel_412 = QtWidgets.QLabel(self.tabWidgetPage3)
        self.xlabel_412.setObjectName("xlabel_412")
        self.horizontalLayout_21.addWidget(self.xlabel_412)
        self.results_count = QtWidgets.QSpinBox(self.tabWidgetPage3)
        self.results_count.setEnabled(True)
        self.results_count.setMinimum(1)
        self.results_count.setMaximum(999)
        self.results_count.setProperty("value", 999)
        self.results_count.setObjectName("results_count")
        self.horizontalLayout_21.addWidget(self.results_count)
        self.xlabel_413 = QtWidgets.QLabel(self.tabWidgetPage3)
        self.xlabel_413.setObjectName("xlabel_413")
        self.horizontalLayout_21.addWidget(self.xlabel_413)
        self.starting_from = QtWidgets.QSpinBox(self.tabWidgetPage3)
        self.starting_from.setEnabled(True)
        self.starting_from.setMinimum(1)
        self.starting_from.setMaximum(999)
        self.starting_from.setProperty("value", 1)
        self.starting_from.setObjectName("starting_from")
        self.horizontalLayout_21.addWidget(self.starting_from)
        self.xlabel_41 = QtWidgets.QLabel(self.tabWidgetPage3)
        self.xlabel_41.setObjectName("xlabel_41")
        self.horizontalLayout_21.addWidget(self.xlabel_41)
        self.multiple_separator = QtWidgets.QLineEdit(self.tabWidgetPage3)
        self.multiple_separator.setObjectName("multiple_separator")
        self.horizontalLayout_21.addWidget(self.multiple_separator)
        self.vargrid.addLayout(self.horizontalLayout_21, 10, 1, 1, 2)
        self.scrollArea11 = QtWidgets.QScrollArea(self.tabWidgetPage3)
        self.scrollArea11.setFrameShape(QShape.NoFrame)
        self.scrollArea11.setWidgetResizable(True)
        self.scrollArea11.setObjectName("scrollArea11")
        self.gridLayoutWidget_2 = QtWidgets.QWidget()
        self.gridLayoutWidget_2.setGeometry(QtCore.QRect(0, 0, 203, 70))
        self.gridLayoutWidget_2.setObjectName("gridLayoutWidget_2")
        self.testgrid = QtWidgets.QGridLayout(self.gridLayoutWidget_2)
        self.testgrid.setObjectName("testgrid")
        self.xlabel_3 = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.xlabel_3.setObjectName("xlabel_3")
        self.testgrid.addWidget(self.xlabel_3, 7, 1, 1, 1)
        self.xlabel_5 = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.xlabel_5.setObjectName("xlabel_5")
        self.testgrid.addWidget(self.xlabel_5, 7, 2, 1, 1)
        self.label_31 = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.label_31.setObjectName("label_31")
        self.testgrid.addWidget(self.label_31, 8, 0, 1, 1)
        self.test_text = HistoryLineEdit(self.gridLayoutWidget_2)
        self.test_text.setObjectName("test_text")
        self.testgrid.addWidget(self.test_text, 8, 1, 1, 1)
        self.test_result = QtWidgets.QLineEdit(self.gridLayoutWidget_2)
        self.test_result.setObjectName("test_result")
        self.testgrid.addWidget(self.test_result, 8, 2, 1, 1)
        spacerItem10 = QtWidgets.QSpacerItem(20, 5, QPolicy.Minimum, QPolicy.Expanding)
        self.testgrid.addItem(spacerItem10, 25, 0, 1, 2)
        self.scrollArea11.setWidget(self.gridLayoutWidget_2)
        self.vargrid.addWidget(self.scrollArea11, 11, 0, 1, 4)
        self.scrollArea3.setWidget(self.tabWidgetPage3)
        
        l.addWidget(self.scrollArea3)
        
        self.xlabel_22.setBuddy(self.query_field)
        self.source_field_label.setBuddy(self.search_field)
        self.xlabel_24.setBuddy(self.search_mode)
        self.s_r_src_ident_label.setBuddy(self.s_r_src_ident)
        self.template_label.setBuddy(self.s_r_template)
        self.search_for_label.setBuddy(self.search_for)
        self.xlabel_4.setBuddy(self.replace_with)
        self.label_41.setBuddy(self.replace_func)
        self.destination_field_label.setBuddy(self.destination_field)
        self.replace_mode_label.setBuddy(self.replace_mode)
        self.s_r_dst_ident_label.setBuddy(self.s_r_dst_ident)
        self.xlabel_412.setBuddy(self.results_count)
        self.xlabel_413.setBuddy(self.starting_from)
        self.xlabel_41.setBuddy(self.multiple_separator)
        self.label_31.setBuddy(self.test_text)
        
        ##un_pogaz template_button
        self.template_button = QtWidgets.QPushButton(self.tabWidgetPage3)
        self.template_button.setObjectName("template_button")
        self.template_button.setIcon(QtGui.QIcon(I('template_funcs.png')))
        self.template_button.setSizePolicy(QPolicy.Maximum, QPolicy.Maximum)
        self.template_button.setToolTip(CalibreText.TEMPLATE_BUTTON_ToolTip)
        self.template_button.clicked.connect(self.openTemplateBox)
        self.vargrid.addWidget(self.template_button, 5, 2, 1, 1)
        ##
        
        self.retranslateUi()
    
    def retranslateUi(self):
        self.xlabel_22.setText(_("&Load search/replace:"))
        self.query_field.setToolTip(_("Select saved search/replace to load."))
        self.save_button.setToolTip(_("Save current search/replace"))
        self.save_button.setText(_("Sa&ve"))
        self.remove_button.setToolTip(_("Delete saved search/replace"))
        self.remove_button.setText(_("Delete"))
        self.source_field_label.setText(_("Search &field:"))
        self.search_field.setToolTip(_("The name of the field that you want to search"))
        self.xlabel_24.setText(_("Search &mode:"))
        self.search_mode.setToolTip(_("Choose whether to use basic text matching or advanced regular expression matching"))
        self.s_r_src_ident_label.setText(_("&Identifier type:"))
        self.s_r_src_ident.setToolTip(_("Choose which identifier type to operate upon"))
        self.template_label.setText(_("&Template:"))
        self.s_r_template.setToolTip(_("Enter a template to be used as the source for the search/replace"))
        self.search_for_label.setText(_("&Search for:"))
        self.search_for.setToolTip(_("Enter what you are looking for, either plain text or a regular expression, depending on the mode"))
        self.case_sensitive.setToolTip(_("Check this box if the search string must match exactly upper and lower case. Uncheck it if case is to be ignored"))
        self.case_sensitive.setText(_("Cas&e sensitive"))
        self.xlabel_4.setText(_("&Replace with:"))
        self.replace_with.setToolTip(_("The replacement text. The matched search text will be replaced with this string"))
        self.label_41.setText(_("&Apply function after replace:"))
        self.replace_func.setToolTip(_("Specify how the text is to be processed after matching and replacement. In character mode, the entire\n"
"field is processed. In regular expression mode, only the matched text is processed"))
        self.destination_field_label.setText(_("&Destination field:"))
        self.destination_field.setToolTip(_("The field that the text will be put into after all replacements.\n"
"If blank, the source field is used if the field is modifiable"))
        self.replace_mode_label.setText(_("M&ode:"))
        self.replace_mode.setToolTip(_("Specify how the text should be copied into the destination."))
        self.comma_separated.setToolTip(_("Specifies whether result items should be split into multiple values or\n"
"left as single values. This option has the most effect when the source field is\n"
"not multiple and the destination field is multiple"))
        self.comma_separated.setText(_("Split &result"))
        self.s_r_dst_ident_label.setText(_("Identifier type:"))
        self.s_r_dst_ident.setToolTip(_("<p>Choose which identifier type to operate upon. When the\n"
"              source field is something other than \'identifiers\' you can enter\n"
"              a * if you want to replace the entire set of identifiers with\n"
"              the result of the search/replace.</p>"))
        self.xlabel_412.setText(_("For multiple-valued fields, sho&w"))
        self.xlabel_413.setText(_("val&ues starting at"))
        self.xlabel_41.setText(_("with values separated b&y"))
        self.multiple_separator.setToolTip(_("Used when displaying test results to separate values in multiple-valued fields"))
        self.xlabel_3.setText(_("Test text"))
        self.xlabel_5.setText(_("Test result"))
        self.label_31.setText(_("Your &test:"))
        #self.central_widget.setTabText(self.central_widget.indexOf(self.scrollArea3), _("&Search and replace"))
        
        ##un_pogaz Search and destination field label swap
        self.source_field_label_text = self.source_field_label.text()
        self.destination_field_label_text = self.destination_field_label.text()
    
    # S&R {{{
    def prepare_search_and_replace(self):
        self.search_for.initialize('bulk_edit_search_for')
        self.replace_with.initialize('bulk_edit_replace_with')
        self.s_r_template.setLineEdit(TemplateLineEditor(self.s_r_template))
        self.s_r_template.initialize('bulk_edit_template')
        self.test_text.initialize('bulk_edit_test_test')
        self.all_fields = ['']
        self.writable_fields = ['']
        fm = self.db.field_metadata
        for f in fm:
            if (f in ['author_sort'] or
                    (fm[f]['datatype'] in ['text', 'series', 'enumeration', 'comments', 'rating'] and
                     fm[f].get('search_terms', None) and
                     f not in ['formats', 'ondevice', 'series_sort']) or
                    (fm[f]['datatype'] in ['int', 'float', 'bool', 'datetime'] and
                     f not in ['id', 'timestamp'])):
                self.all_fields.append(f)
                self.writable_fields.append(f)
            if fm[f]['datatype'] == 'composite':
                self.all_fields.append(f)
        
        ##un_pogaz exclude unsupported cover
        self.all_fields.remove('cover')
        self.writable_fields.remove('cover')
        
        self.all_fields.sort()
        self.all_fields.insert(1, TEMPLATE_FIELD)
        self.writable_fields.sort()
        self.search_field.setMaxVisibleItems(25)
        self.destination_field.setMaxVisibleItems(25)
        self.testgrid.setColumnStretch(1, 1)
        self.testgrid.setColumnStretch(2, 1)
        offset = 10
        self.s_r_number_of_books = min(10, len(self.ids))
        for i in range(1,self.s_r_number_of_books+1):
            w = QtWidgets.QLabel(self.tabWidgetPage3)
            w.setText(_('Book %d:')%i)
            self.testgrid.addWidget(w, i+offset, 0, 1, 1)
            w = QtWidgets.QLineEdit(self.tabWidgetPage3)
            w.setReadOnly(True)
            name = 'book_%d_text'%i
            setattr(self, name, w)
            self.book_1_text.setObjectName(name)
            self.testgrid.addWidget(w, i+offset, 1, 1, 1)
            w = QtWidgets.QLineEdit(self.tabWidgetPage3)
            w.setReadOnly(True)
            name = 'book_%d_result'%i
            setattr(self, name, w)
            self.book_1_text.setObjectName(name)
            self.testgrid.addWidget(w, i+offset, 2, 1, 1)
        
        ident_types = sorted(self.db.get_all_identifier_types(), key=sort_key)
        self.s_r_dst_ident.setCompleter(QtWidgets.QCompleter(ident_types))
        try:
            self.s_r_dst_ident.setPlaceholderText(_('Enter an identifier type'))
        except:
            pass
        self.s_r_src_ident.addItems(ident_types)
        
        self.main_heading = _(
                 '<b>You can destroy your library using this feature.</b> '
                 'Changes are permanent. There is no undo function. '
                 'You are strongly encouraged to back up your library '
                 'before proceeding.<p>'
                 'Search and replace in text fields using character matching '
                 'or regular expressions. ')
        
        ##un_pogaz main_heading_short
        self.main_heading_short = self.main_heading[:self.main_heading.find('<p>')] + '<p>'
        
        self.character_heading = _(
                 'In character mode, the field is searched for the entered '
                 'search text. The text is replaced by the specified replacement '
                 'text everywhere it is found in the specified field. After '
                 'replacement is finished, the text can be changed to '
                 'upper-case, lower-case, or title-case. If the Case-sensitive '
                 'check box is checked, the search text must match exactly. If '
                 'it is unchecked, the search text will match both upper- and '
                 'lower-case letters'
                 )
        
        self.regexp_heading = _(
                 'In regular expression mode, the search text is an '
                 'arbitrary Python-compatible regular expression. The '
                 'replacement text can contain backreferences to parenthesized '
                 'expressions in the pattern. The search is not anchored, '
                 'and can match and replace multiple times on the same string. '
                 'The modification functions (lower-case etc) are applied to the '
                 'matched text, not to the field as a whole. '
                 'The destination box specifies the field where the result after '
                 'matching and replacement is to be assigned. You can replace '
                 'the text in the field, or prepend or append the matched text. '
                 'See <a href="https://docs.python.org/library/re.html">'
                 'this reference</a> for more information on Python\'s regular '
                 'expressions, and in particular the \'sub\' function.'
                 )
        
        self.search_mode.addItems(S_R_MATCH_MODES)
        self.search_mode.setCurrentIndex(dynamic.get('s_r_search_mode', 0))
        self.replace_mode.addItems(S_R_REPLACE_MODES)
        self.replace_mode.setCurrentIndex(0)
        
        self.s_r_search_mode = 0
        self.s_r_error = None
        self.s_r_obj = None
        
        self.replace_func.addItems(sorted(S_R_FUNCTIONS.keys()))
        self.search_mode.currentIndexChanged.connect(self.s_r_search_mode_changed)
        self.search_field.currentIndexChanged.connect(self.s_r_search_field_changed)
        self.destination_field.currentIndexChanged.connect(self.s_r_destination_field_changed)
        
        self.replace_mode.currentIndexChanged.connect(self.s_r_paint_results)
        self.replace_func.currentIndexChanged.connect(self.s_r_paint_results)
        self.search_for.editTextChanged[native_string_type].connect(self.s_r_paint_results)
        self.replace_with.editTextChanged[native_string_type].connect(self.s_r_paint_results)
        self.test_text.editTextChanged[native_string_type].connect(self.s_r_paint_results)
        self.comma_separated.stateChanged.connect(self.s_r_paint_results)
        self.case_sensitive.stateChanged.connect(self.s_r_paint_results)
        self.s_r_src_ident.currentIndexChanged.connect(self.s_r_identifier_type_changed)
        self.s_r_dst_ident.textChanged.connect(self.s_r_paint_results)
        
        self.s_r_template.editTextChanged[native_string_type].connect(self.s_r_template_changed) ##un_pogaz template_button
        #self.s_r_template.lost_focus.connect(self.s_r_template_changed)
        #self.central_widget.setCurrentIndex(0)
        
        self.search_for.completer().setCaseSensitivity(QtCore.Qt.CaseSensitive)
        self.replace_with.completer().setCaseSensitivity(QtCore.Qt.CaseSensitive)
        self.s_r_template.completer().setCaseSensitivity(QtCore.Qt.CaseSensitive)
        
        self.s_r_search_mode_changed(self.search_mode.currentIndex())
        self.multiple_separator.setFixedWidth(30)
        self.multiple_separator.setText(' ::: ')
        self.multiple_separator.textChanged.connect(self.s_r_separator_changed)
        self.results_count.valueChanged[int].connect(self.s_r_display_bounds_changed)
        self.starting_from.valueChanged[int].connect(self.s_r_display_bounds_changed)
        
        self.save_button.clicked.connect(self.s_r_save_query)
        self.remove_button.clicked.connect(self.s_r_remove_query)
        
        self.queries = JSONConfig("search_replace_queries")
        self.saved_search_name = ''
        self.query_field.addItem("")
        self.query_field_values = sorted(self.queries, key=sort_key)
        self.query_field.addItems(self.query_field_values)
        self.query_field.currentIndexChanged.connect(self.s_r_query_change)
        self.query_field.setCurrentIndex(0)
        self.search_field.setCurrentIndex(0)
        self.s_r_search_field_changed(0)
    
    def s_r_sf_itemdata(self, idx):
        if idx is None:
            idx = self.search_field.currentIndex()
        return unicode_type(self.search_field.itemData(idx) or '')
    
    def s_r_df_itemdata(self, idx):
        if idx is None:
            idx = self.destination_field.currentIndex()
        return unicode_type(self.destination_field.itemData(idx) or '')
    
    def s_r_get_field(self, mi, field):
        if field:
            if field == TEMPLATE_FIELD:
                v = SafeFormat().safe_format(
                    unicode_type(self.s_r_template.text()), mi, _('S/R TEMPLATE ERROR'), mi)
                return [v]
            fm = self.db.metadata_for_field(field)
            if field == 'sort':
                val = mi.get('title_sort', None)
            elif fm['datatype'] == 'datetime':
                val = mi.format_field(field)[1]
            else:
                val = mi.get(field, None)
            if isinstance(val, (numbers.Number, bool)):
                val = unicode_type(val)
            elif fm['is_csp']:
                # convert the csp dict into a list
                id_type = unicode_type(self.s_r_src_ident.currentText())
                if id_type:
                    val = [val.get(id_type, '')]
                else:
                    val = ['%s:%s'%(t[0], t[1]) for t in iteritems(val)]
            if val is None:
                val = [] if fm['is_multiple'] else ['']
            elif not fm['is_multiple']:
                val = [val]
            elif fm['datatype'] == 'composite':
                val = [v2.strip() for v2 in val.split(fm['is_multiple']['ui_to_list'])]
            elif field == 'authors':
                val = [v2.replace('|', ',') for v2 in val]
        else:
            val = []
        if not val:
            val = ['']
        return val
    
    def s_r_display_bounds_changed(self, i):
        self.s_r_search_field_changed(self.search_field.currentIndex())
    
    def s_r_template_changed(self, *args):
        #self.s_r_search_field_changed(self.search_field.currentIndex())
        
        ##un_pogaz
        for i in range(0, self.s_r_number_of_books):
            w = getattr(self, 'book_%d_text'%(i+1))
            mi = self.db.get_metadata(self.ids[i], index_is_id=True)
            src = self.s_r_sf_itemdata(None)
            t = self.s_r_get_field(mi, src)
            if len(t) > 1:
                t = t[self.starting_from.value()-1:
                      self.starting_from.value()-1 + self.results_count.value()]
            w.setText(unicode_type(self.multiple_separator.text()).join(t))
        
        self.s_r_paint_results(None)
    
    def s_r_identifier_type_changed(self, idx):
        self.s_r_search_field_changed(self.search_field.currentIndex())
        
        if self.search_mode.currentIndex() == 2: ##un_pogaz Replace Field
            self.s_r_dst_ident.setText(self.s_r_src_ident.currentText())
        
        self.s_r_paint_results(idx)
    
    def s_r_search_field_changed(self, idx):
        self.s_r_template.setVisible(False)
        self.template_label.setVisible(False)
        self.template_button.setVisible(False) ##un_pogaz template_button
        self.s_r_src_ident_label.setVisible(False)
        self.s_r_src_ident.setVisible(False)
        if self.s_r_sf_itemdata(idx) == TEMPLATE_FIELD: ## idx == 1 # Template 
            self.s_r_template.setVisible(True)
            self.template_label.setVisible(True)
            self.template_button.setVisible(True) ##un_pogaz template_button
        elif self.s_r_sf_itemdata(idx) == 'identifiers':
            self.s_r_src_ident_label.setVisible(True)
            self.s_r_src_ident.setVisible(True)
        
        for i in range(0, self.s_r_number_of_books):
            w = getattr(self, 'book_%d_text'%(i+1))
            mi = self.db.get_metadata(self.ids[i], index_is_id=True)
            src = self.s_r_sf_itemdata(idx)
            t = self.s_r_get_field(mi, src)
            if len(t) > 1:
                t = t[self.starting_from.value()-1:
                      self.starting_from.value()-1 + self.results_count.value()]
            w.setText(unicode_type(self.multiple_separator.text()).join(t))
        
        if self.search_mode.currentIndex() == 0:
            self.destination_field.setCurrentIndex(idx)
        else:
            self.s_r_destination_field_changed(self.destination_field.currentIndex())
            self.s_r_paint_results(None)
    
    def s_r_destination_field_changed(self, idx):
        self.s_r_dst_ident_label.setVisible(False)
        self.s_r_dst_ident.setVisible(False)
        txt = self.s_r_df_itemdata(idx)
        if not txt:
            txt = self.s_r_sf_itemdata(None)
        if txt and txt in self.writable_fields:
            if txt == 'identifiers' and self.search_mode.currentIndex() != 2: ##un_pogaz Replace Field
                self.s_r_dst_ident_label.setVisible(True)
                self.s_r_dst_ident.setVisible(True)
            
            self.destination_field_fm = self.db.metadata_for_field(txt)
        self.s_r_paint_results(None)
    
    def s_r_search_mode_changed(self, val):
        search = self.search_field.currentText()
        self.search_field.clear()
        self.destination_field.clear()
        
        if val != 2: ##un_pogaz Replace Field
            self.search_for_label.setVisible(True)
            self.search_for.setVisible(True)
            self.case_sensitive.setVisible(True)
            self.source_field_label.setText(self.source_field_label_text)
            self.destination_field_label.setText(self.destination_field_label_text)
        
        if val == 0:
            for f in self.writable_fields:
                self.search_field.addItem(f if f != 'sort' else 'title_sort', f)
                self.destination_field.addItem(f if f != 'sort' else 'title_sort', f)
            self.destination_field.setCurrentIndex(0)
            self.destination_field.setVisible(False)
            self.destination_field_label.setVisible(False)
            self.replace_mode.setCurrentIndex(0)
            self.replace_mode.setVisible(False)
            self.replace_mode_label.setVisible(False)
            self.comma_separated.setVisible(False)
            self.s_r_heading.setText('<p>'+self.main_heading + self.character_heading)
            
        elif val == 2: ##un_pogaz Replace Field
            self.search_field.blockSignals(True)
            self.destination_field.blockSignals(True)
            for f in self.writable_fields:
                self.search_field.addItem(f if f != 'sort' else 'title_sort', f)
                self.destination_field.addItem(f if f != 'sort' else 'title_sort', f)
            self.destination_field.setCurrentIndex(0)
            self.search_field.blockSignals(False)
            self.destination_field.blockSignals(False)
            self.destination_field.setVisible(False)
            self.destination_field_label.setVisible(False)
            self.replace_mode.setCurrentIndex(0)
            self.replace_mode.setVisible(False)
            self.replace_mode_label.setVisible(False)
            self.comma_separated.setVisible(False)
            self.s_r_heading.setText('<p>'+ self.main_heading_short + CalibreText.REPLACE_HEADING)
            
            self.search_for_label.setVisible(False)
            self.search_for.setVisible(False)
            self.search_for.setText(CalibreText.REPLACE_REGEX)
            self.case_sensitive.setVisible(False)
            self.source_field_label.setText(self.destination_field_label_text)
            self.destination_field_label.setText(self.source_field_label_text)
            
        else:
            self.search_field.blockSignals(True)
            self.destination_field.blockSignals(True)
            for f in self.all_fields:
                self.search_field.addItem(f if f != 'sort' else 'title_sort', f)
            for f in self.writable_fields:
                self.destination_field.addItem(f if f != 'sort' else 'title_sort', f)
            self.search_field.blockSignals(False)
            self.destination_field.blockSignals(False)
            self.destination_field.setVisible(True)
            self.destination_field_label.setVisible(True)
            self.replace_mode.setVisible(True)
            self.replace_mode_label.setVisible(True)
            self.comma_separated.setVisible(True)
            self.s_r_heading.setText('<p>'+self.main_heading + self.regexp_heading)
        
        self.search_field.setCurrentText(search)
        
        self.s_r_paint_results(None)
    
    def s_r_separator_changed(self, txt):
        self.s_r_search_field_changed(self.search_field.currentIndex())
    
    def s_r_set_colors(self):
        if self.s_r_error is not None:
            self.test_result.setText(error_message(self.s_r_error))
            col = 'rgba(255, 0, 0, 20%)'
        else:
            col = 'rgba(0, 255, 0, 20%)'
            
        if calibre_version >= (5,0,0):
            self.test_result.setStyleSheet(QtWidgets.QApplication.instance().stylesheet_for_line_edit(self.s_r_error is not None))
        else:
            self.test_result.setStyleSheet('QLineEdit { color: black; background-color: %s; }'%col)
        
        for i in range(0,self.s_r_number_of_books):
            getattr(self, 'book_%d_result'%(i+1)).setText('')
    
    def s_r_func(self, match):
        rfunc = S_R_FUNCTIONS[unicode_type(self.replace_func.currentText())]
        rtext = unicode_type(self.replace_with.text())
        rtext = match.expand(rtext)
        return rfunc(rtext)
    
    def s_r_do_regexp(self, mi):
        src_field = self.s_r_sf_itemdata(None)
        src = self.s_r_get_field(mi, src_field)
        result = []
        rfunc = S_R_FUNCTIONS[unicode_type(self.replace_func.currentText())]
        for s in src:
            t = self.s_r_obj.sub(self.s_r_func, s)
            if self.search_mode.currentIndex() == 0:
                t = rfunc(t)
            result.append(t)
        return result
    
    def s_r_do_destination(self, mi, val):
        src = self.s_r_sf_itemdata(None)
        if src == '':
            return ''
        dest = self.s_r_df_itemdata(None)
        if dest == '':
            if (src == TEMPLATE_FIELD or
                        self.db.metadata_for_field(src)['datatype'] == 'composite'):
                raise Exception(_('You must specify a destination when source is '
                                  'a composite field or a template'))
            dest = src
        
        if self.destination_field_fm['datatype'] == 'rating' and val[0]:
            ok = True
            try:
                v = int(val[0])
                if v < 0 or v > 10:
                    ok = False
            except:
                ok = False
            if not ok:
                raise Exception(_('The replacement value for a rating column must '
                                  'be empty or an integer between 0 and 10'))
        dest_mode = self.replace_mode.currentIndex()
        
        if self.destination_field_fm['is_csp']:
            dest_ident = unicode_type(self.s_r_dst_ident.text())
            if not dest_ident or (src == 'identifiers' and dest_ident == '*'):
                raise Exception(_('You must specify a destination identifier type'))
        
        if self.destination_field_fm['is_multiple']:
            if self.comma_separated.isChecked():
                splitter = self.destination_field_fm['is_multiple']['ui_to_list']
                res = []
                for v in val:
                    res.extend([x.strip() for x in v.split(splitter) if x.strip()])
                val = res
            else:
                val = [v.replace(',', '') for v in val]
        
        if dest_mode != 0:
            dest_val = mi.get(dest, '')
            if self.db.metadata_for_field(dest)['is_csp']:
                dst_id_type = unicode_type(self.s_r_dst_ident.text())
                if dst_id_type:
                    dest_val = [dest_val.get(dst_id_type, '')]
                else:
                    # convert the csp dict into a list
                    dest_val = ['%s:%s'%(t[0], t[1]) for t in iteritems(dest_val)]
            if dest_val is None:
                dest_val = []
            elif not isinstance(dest_val, list):
                dest_val = [dest_val]
        else:
            dest_val = []
        
        if dest_mode == 1:
            val.extend(dest_val)
        elif dest_mode == 2:
            val[0:0] = dest_val
        return val
    
    def s_r_replace_mode_separator(self):
        if self.comma_separated.isChecked():
            return ','
        return ''
    
    def s_r_paint_results(self, txt):
        self.s_r_error = None
        self.s_r_set_colors()
        flags = regex.FULLCASE | regex.UNICODE
        
        if not self.case_sensitive.isChecked():
            flags |= regex.IGNORECASE
        
        if self.search_mode.currentIndex() == 2: ##un_pogaz Replace Field
            flags |= regex.DOTALL
        
        
        ##un_pogaz extend try catch
        try:
            
            sftxt = unicode_type(self.search_field.currentText())
            if not sftxt:
                raise Exception(CalibreText.SEARCH_FIELD)
            
            smtxt = unicode_type(self.search_mode.currentText())
            if not smtxt:
                raise Exception(CalibreText.getEmptyField(CalibreText.FIELD_NAME.SEARCH_MODE))
            
            rmtxt = unicode_type(self.replace_mode.currentText())
            if not rmtxt:
                raise Exception(CalibreText.getEmptyField(CalibreText.FIELD_NAME.REPLACE_MODE))
            
            if sftxt == 'identifiers':
                if not unicode_type(self.s_r_src_ident.currentText()):
                    raise Exception(CalibreText.getEmptyField(CalibreText.FIELD_NAME.IDENTIFIER_TYPE ))
            
            if sftxt == TEMPLATE_FIELD:
                error = check_template(self.s_r_template.text(), self.plugin_action)
                if error is not True:
                    raise Exception(_('S/R TEMPLATE ERROR')+': '+ str(error))
            
        except Exception as e:
            self.s_r_error = e
            self.s_r_set_colors()
            return
        
        
        try:
            
            stext = unicode_type(self.search_for.text())
            if not stext:
                raise Exception(_('You must specify a search expression in the "Search for" field'))
            if self.search_mode.currentIndex() == 0:
                self.s_r_obj = regex.compile(regex.escape(stext), flags | regex.V1)
            else:
                try:
                    self.s_r_obj = regex.compile(stext, flags | regex.V1)
                except regex.error:
                    self.s_r_obj = regex.compile(stext, flags)
        except Exception as e:
            self.s_r_obj = None
            self.s_r_error = e
            self.s_r_set_colors()
            return
        
        try:
            test_result = self.s_r_obj.sub(self.s_r_func, self.test_text.text())
            if self.search_mode.currentIndex() == 0:
                rfunc = S_R_FUNCTIONS[self.replace_func.currentText()]
                test_result = rfunc(test_result)
            self.test_result.setText(test_result)
        except Exception as e:
            self.s_r_error = e
            self.s_r_set_colors()
            return
        
        
        for i in range(0,self.s_r_number_of_books):
            mi = self.db.get_metadata(self.ids[i], index_is_id=True)
            wr = getattr(self, 'book_%d_result'%(i+1))
            try:
                result = self.s_r_do_regexp(mi)
                t = self.s_r_do_destination(mi, result)
                if len(t) > 1 and self.destination_field_fm['is_multiple']:
                    t = t[self.starting_from.value()-1:
                          self.starting_from.value()-1 + self.results_count.value()]
                    t = unicode_type(self.multiple_separator.text()).join(t)
                else:
                    t = self.s_r_replace_mode_separator().join(t)
                wr.setText(t)
            except Exception as e:
                self.s_r_error = e
                self.s_r_set_colors()
                break
    
    def do_search_replace(self, book_id):
        source = self.s_r_sf_itemdata(None)
        if not source or not self.s_r_obj:
            return
        dest = self.s_r_df_itemdata(None)
        if not dest:
            dest = source
        
        dfm = self.db.field_metadata[dest]
        mi = self.db.new_api.get_proxy_metadata(book_id)
        
        #edit the metadata object with the stored edited field
        if dest in self.set_field_calls:
            if book_id in self.set_field_calls[dest]:
                store = self.set_field_calls[dest][book_id]
                mi.set(dest, store)
        
        original = mi.get(dest)
        
        val = self.s_r_do_regexp(mi)
        val = self.s_r_do_destination(mi, val)
        if dfm['is_multiple']:
            if dfm['is_csp']:
                # convert the colon-separated pair strings back into a dict,
                # which is what set_identifiers wants
                dst_id_type = unicode_type(self.s_r_dst_ident.text())
                if dst_id_type and dst_id_type != '*':
                    v = ''.join(val)
                    ids = mi.get(dest).copy() ##un_pogaz fix ghost identifier with empty value
                    ids[dst_id_type] = v
                    val = ids
                else:
                    try:
                        val = dict([(t.split(':', maxsplit=1)) for t in val])
                    except:
                        #import traceback
                        #ans = question_dialog(self, _('Invalid identifier string'),
                        #       _('The identifier string for book "{0}" (id {1}) is '
                        #         'invalid. It must be a comma-separated list of '
                        #         'pairs of strings separated by a colon.\n\n'
                        #         'Do you want to continue processing books?').format(mi.title, mi.id),
                        #       det_msg='\n'.join([_('Result identifier string: '),
                        #                         ', '.join(val), '-----', traceback.format_exc()]),
                        #       show_copy_button=True)
                        #return ans
                        ##un_pogaz use custom error handling
                        return Exception(CalibreText.EXCEPTION_Invalid_identifier)
        else:
            val = self.s_r_replace_mode_separator().join(val)
            if dest == 'title' and len(val) == 0:
                val = _('Unknown')
        
        if not val and dfm['datatype'] == 'datetime':
            val = None
        if dfm['datatype'] == 'rating':
            if (not val or int(val) == 0):
                val = None
            if dest == 'rating' and val:
                val = (int(val) // 2) * 2
        
        ## add the result value only if different of the original
        ## and if it is not a pair None/''
        if original != val and (self.hasValue(original) or self.hasValue(val)):
            self.set_field_calls[dest][book_id] = val
    # }}}
    
    def hasValue(self, v):
        if v == None: return False
        elif v is True or v is False: return True
        elif v is int() or v is float(): return True
        else:
            try: return len(v) > 0
            except: return True
    
    def s_r_remove_query(self, *args):
        if self.query_field.currentIndex() == 0:
            return
        
        if not question_dialog(self, _("Delete saved search/replace"),
                _("The selected saved search/replace will be deleted. "
                    "Are you sure?")):
            return
        
        item_id = self.query_field.currentIndex()
        item_name = unicode_type(self.query_field.currentText())
        
        self.query_field.blockSignals(True)
        self.query_field.removeItem(item_id)
        self.query_field.blockSignals(False)
        self.query_field.setCurrentIndex(0)
        
        if item_name in list(self.queries.keys()):
            del(self.queries[item_name])
            self.queries.commit()
    
    def s_r_save_query(self, *args):
        names = ['']
        names.extend(self.query_field_values)
        try:
            dex = names.index(self.saved_search_name)
        except:
            dex = 0
        name = ''
        while not name:
            name, ok =  QtWidgets.QInputDialog.getItem(self, _('Save search/replace'),
                    _('Search/replace name:'), names, dex, True)
            if not ok:
                return
            if not name:
                error_dialog(self, _("Save search/replace"),
                        _("You must provide a name."), show=True)
        new = True
        name = unicode_type(name)
        if name in list(self.queries.keys()):
            if not question_dialog(self, _("Save search/replace"),
                    _("That saved search/replace already exists and will be overwritten. "
                        "Are you sure?")):
                return
            new = False
        
        query = self.get_query()
        query[KEY.NAME] = name
        
        self.queries[name] = query
        self.queries.commit()
        
        if new:
            self.query_field.blockSignals(True)
            self.query_field.clear()
            self.query_field.addItem('')
            self.query_field_values = sorted(self.queries, key=sort_key)
            self.query_field.addItems(self.query_field_values)
            self.query_field.blockSignals(False)
        self.query_field.setCurrentIndex(self.query_field.findText(name))
    
    def s_r_query_change(self, item_name):
        if not item_name:
            self.s_r_reset_query_fields()
            self.saved_search_name = ''
            return
        item = self.queries.get(unicode_type(item_name), None)
        if item is None:
            self.s_r_reset_query_fields()
            return
        self.saved_search_name = item_name
        
        self.load_query(item)
    
    def s_r_reset_query_fields(self):
        # Don't reset the search mode. The user will probably want to use it
        # as it was
        self.search_field.setCurrentIndex(0)
        self.s_r_src_ident.setCurrentIndex(0)
        self.s_r_template.setText("")
        self.search_for.setText("")
        self.case_sensitive.setChecked(False)
        self.replace_with.setText("")
        self.replace_func.setCurrentIndex(0)
        self.destination_field.setCurrentIndex(0)
        self.s_r_dst_ident.setText('')
        self.replace_mode.setCurrentIndex(0)
        self.comma_separated.setChecked(True)
        self.results_count.setValue(999)
        self.starting_from.setValue(1)
        self.multiple_separator.setText(" ::: ")
    
    
    def load_query(self, query):
        if query:
            def set_text(attr, key):
                try:
                    attr.setText(query[key])
                except:
                    pass
            
            def set_checked(attr, key):
                try:
                    attr.setChecked(query[key])
                except:
                    attr.setChecked(False)
            
            def set_value(attr, key):
                try:
                    attr.setValue(int(query[key]))
                except:
                    attr.setValue(0)
            
            def set_index(attr, key):
                try:
                    attr.setCurrentIndex(attr.findText(query[key]))
                except:
                    attr.setCurrentIndex(0)
            
            set_index(self.search_mode, KEY.SEARCH_MODE)
            set_index(self.search_field, KEY.SEARCH_FIELD)
            set_text(self.s_r_template, KEY.S_R_TEMPLATE)
            
            self.s_r_template_changed()  # simulate gain/loss of focus
            
            set_index(self.s_r_src_ident, KEY.S_R_SRC_IDENT)
            set_text(self.s_r_dst_ident, KEY.S_R_DST_IDENT)
            set_text(self.search_for, KEY.SEARCH_FOR)
            set_checked(self.case_sensitive, KEY.CASE_SENSITIVE)
            set_text(self.replace_with, KEY.REPLACE_WITH)
            set_index(self.replace_func, KEY.REPLACE_FUNC)
            set_index(self.destination_field, KEY.DESTINATION_FIELD)
            set_index(self.replace_mode, KEY.REPLACE_MODE)
            set_checked(self.comma_separated, KEY.COMMA_SEPARATED)
            set_value(self.results_count, KEY.RESULTS_COUNT)
            set_value(self.starting_from, KEY.STARTING_FROM)
            set_text(self.multiple_separator, KEY.MULTIPLE_SEPARATOR)
    
    def _get_query_without_error(self):
        query = {}
        query[KEY.NAME] = unicode_type(self.query_field.currentText())
        query[KEY.SEARCH_FIELD] = unicode_type(self.search_field.currentText())
        query[KEY.SEARCH_MODE] = unicode_type(self.search_mode.currentText())
        query[KEY.S_R_TEMPLATE] = unicode_type(self.s_r_template.text())
        query[KEY.S_R_SRC_IDENT] = unicode_type(self.s_r_src_ident.currentText())
        query[KEY.SEARCH_FOR] = unicode_type(self.search_for.text())
        query[KEY.CASE_SENSITIVE] = self.case_sensitive.isChecked()
        query[KEY.REPLACE_WITH] = unicode_type(self.replace_with.text())
        query[KEY.REPLACE_FUNC] = unicode_type(self.replace_func.currentText())
        query[KEY.DESTINATION_FIELD] = unicode_type(self.destination_field.currentText())
        query[KEY.S_R_DST_IDENT] = unicode_type(self.s_r_dst_ident.text())
        query[KEY.REPLACE_MODE] = unicode_type(self.replace_mode.currentText())
        query[KEY.COMMA_SEPARATED] = self.comma_separated.isChecked()
        query[KEY.RESULTS_COUNT] = self.results_count.value()
        query[KEY.STARTING_FROM] = self.starting_from.value()
        query[KEY.MULTIPLE_SEPARATOR] = unicode_type(self.multiple_separator.text())
        
        return query
    
    def get_query(self):
        query = self._get_query_without_error()
        
        if query[KEY.SEARCH_FIELD] != TEMPLATE_FIELD:
            query[KEY.S_R_TEMPLATE] = ''
        
        # to be used in validate method
        if self.s_r_error != None:
            query[KEY.S_R_ERROR] = self.s_r_error
        
        return query
    
    def do_it(self):
        if len(self.ids) < 1:
            return
        try:
            source = self.s_r_sf_itemdata(None)
        except:
            source = ''
        do_sr = source and self.s_r_obj
        
        if self.s_r_error is not None and do_sr:
            error_dialog(self, _('Search/replace invalid'),
                    _('Search/replace is invalid: %s')%error_message(self.s_r_error),
                    show=True)
            return False
        self.changed = bool(self.ids)
                
        self.set_field_calls = defaultdict(dict)
        
        if do_sr:
            for book_id in self.ids:
                self.do_search_replace(book_id)
            if self.set_field_calls:
                for field, book_id_val_map in iteritems(self.set_field_calls):
                    self.refresh_books.update(self.db.new_api.set_field(field, book_id_val_map))
        
        self.db.clean()
        return
    
    
    def openTemplateBox(self):
        
        temp = TemplateBox(self, self.plugin_action, template_text=unicode_type(self.s_r_template.text()))
        temp.exec_()
        if temp.template:
            self.s_r_template.setText(temp.template)
        
        self.s_r_template_changed()  # simulate gain/loss of focus