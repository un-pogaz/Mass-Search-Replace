#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2020, un_pogaz <un.pogaz@gmail.com>'
__docformat__ = 'restructuredtext en'

import copy, time, os, shutil
# python3 compatibility
from six.moves import range
from six import text_type as unicode

try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9

from datetime import datetime
from collections import defaultdict, OrderedDict
from functools import partial
from polyglot.builtins import iteritems, itervalues

try:
    from qt.core import (Qt, QToolButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
                            QFormLayout, QAction, QFileDialog, QDialog, QTableWidget,
                            QTableWidgetItem, QAbstractItemView, QComboBox, QCheckBox,
                            QGroupBox, QGridLayout, QRadioButton, QDialogButtonBox,
                            QPushButton, QSpacerItem, QSizePolicy)
except ImportError:
    from PyQt5.Qt import (Qt, QToolButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
                            QFormLayout, QAction, QFileDialog, QDialog, QTableWidget,
                            QTableWidgetItem, QAbstractItemView, QComboBox, QCheckBox,
                            QGroupBox, QGridLayout, QRadioButton, QDialogButtonBox,
                            QPushButton, QSpacerItem, QSizePolicy)

try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

from calibre import prints
from calibre.constants import iswindows
from calibre.utils.config import config_dir, JSONConfig
from calibre.gui2 import error_dialog, question_dialog, info_dialog, choose_files, open_local_file, FileDialog
from calibre.gui2.ui import get_gui
from calibre.gui2.widgets2 import Dialog
from calibre.utils.zipfile import ZipFile

from .SearchReplace import SearchReplaceDialog, KEY_OPERATION, TEMPLATE_FIELD, operation_is_active, get_default_operation, operation_ConvertError, operation_string, operation_para_list, operation_isFullValid, operation_testFullError, operation_testGetError, clean_empty_operation
from .common_utils import (debug_print, get_icon, PREFS_json, KeyboardConfigDialog, get_selected_BookIds,
                            NoWheelComboBox, CheckableTableWidgetItem, TextIconWidgetItem, ReadOnlyTextIconWidgetItem, ReadOnlyTableWidgetItem, KeyValueComboBox)

GUI = get_gui()

class ICON:
    PLUGIN    = 'images/plugin.png'
    ADD_IMAGE = 'images/image_add.png'
    EXPORT    = 'images/export.png'
    IMPORT    = 'images/import.png'
    WARNING   = 'images/warning.png'
    
    ALL = [
        PLUGIN,
        ADD_IMAGE,
        EXPORT,
        IMPORT,
        WARNING,
    ]

class KEY_MENU:
    MENU = 'Menu'
    ACTIVE = 'Active'
    IMAGE = 'Image'
    TEXT = 'Text'
    SUBMENU = 'SubMenu'
    OPERATIONS = 'Operations'
    
    ALL = [
        ACTIVE,
        TEXT,
        SUBMENU,
        IMAGE,
        OPERATIONS,
    ]
    
    QUICK = 'Quick'
    UPDATE_REPORT = 'UpdateReport'

class KEY_ERROR:
    ERROR = 'ErrorStrategy'
    UPDATE = 'Update'
    OPERATION = 'Operation'

class ERROR_UPDATE:
    
    INTERRUPT = 'interrupt'
    INTERRUPT_NAME = _('Interrupt execution')
    INTERRUPT_DESC = _('Stop Mass Search/Replace and display the error normally without further action.')
    
    RESTORE = 'restore'
    RESTORE_NAME = _('Restore the library')
    RESTORE_DESC = _('Stop Mass Search/Replace and restore the library to its original state.')
    
    
    safely_txt = _('Updates the fields one by one. This operation can be slower than other strategies.')
    
    SAFELY = 'safely stop'
    SAFELY_NAME = _('Carefully executed (slower)')
    SAFELY_DESC = safely_txt+'\n'+ _('When a error occurs, stop Mass Search/Replace and display the error normally without further action.')
    
    DONT_STOP = 'don\'t stop'
    DONT_STOP_NAME = _('Don\'t stop (slower, not recomanded)')
    DONT_STOP_DESC = safely_txt+'\n'+_('Update the library, no matter how many errors are encountered. The problematics fields will not be updated.')
    
    LIST = {
            INTERRUPT: [INTERRUPT_NAME, INTERRUPT_DESC],
            RESTORE: [RESTORE_NAME, RESTORE_DESC],
            SAFELY: [SAFELY_NAME, SAFELY_DESC],
            DONT_STOP: [DONT_STOP_NAME, DONT_STOP_DESC],
    }
    
    DEFAULT = INTERRUPT

class ERROR_OPERATION:
    
    ABORT = 'abort'
    ABORT_NAME = _('Abbort')
    ABORT_DESC = _('If an invalid operation is detected, abort the changes.')
    
    ASK = 'ask'
    ASK_NAME = _('Asked')
    ASK_DESC = _('If an invalid operation is detected, asked whether to continue or abort the changes.')
    
    HIDE = 'hide'
    HIDE_NAME = _('Hidden')
    HIDE_DESC = _('Ignore all invalid operations.')
    
    LIST = {
            ABORT: [ABORT_NAME, ABORT_DESC],
            ASK: [ASK_NAME, ASK_DESC],
            HIDE: [HIDE_NAME, HIDE_DESC],
    }
    
    DEFAULT = ASK

# This is where all preferences for this plugin are stored
PREFS = PREFS_json()
# Set defaults
PREFS.defaults[KEY_MENU.MENU] = []
PREFS.defaults[KEY_MENU.QUICK] = []
PREFS.defaults[KEY_MENU.UPDATE_REPORT] = False

PREFS.defaults[KEY_ERROR.ERROR] = {
    KEY_ERROR.OPERATION : ERROR_UPDATE.DEFAULT,
    KEY_ERROR.UPDATE : ERROR_OPERATION.DEFAULT
}

OWIP = 'owip'


def get_default_menu():
    menu = {}
    menu[KEY_MENU.ACTIVE] = True
    menu[KEY_MENU.TEXT] = ''
    menu[KEY_MENU.SUBMENU] = ''
    menu[KEY_MENU.IMAGE] = ''
    menu[KEY_MENU.OPERATIONS] = []
    return menu

class ConfigWidget(QWidget):
    def __init__(self, plugin_action):
        QWidget.__init__(self)
        
        self.plugin_action = plugin_action
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        menu_list = PREFS[KEY_MENU.MENU]
        
        heading_layout = QHBoxLayout()
        layout.addLayout(heading_layout)
        heading_label = QLabel(_('Select and configure the menu items to display:'), self)
        heading_layout.addWidget(heading_label)
        
        # Add a horizontal layout containing the table and the buttons next to it
        table_layout = QHBoxLayout()
        layout.addLayout(table_layout)
        
        # Create a table the user can edit the menu list
        self._table = MenuTableWidget(menu_list, self)
        heading_label.setBuddy(self._table)
        table_layout.addWidget(self._table)
        
        # Add a vertical layout containing the the buttons to move up/down etc.
        button_layout = QVBoxLayout()
        table_layout.addLayout(button_layout)
        move_up_button = QToolButton(self)
        move_up_button.setToolTip(_('Move menu item up'))
        move_up_button.setIcon(get_icon('arrow-up.png'))
        button_layout.addWidget(move_up_button)
        spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        button_layout.addItem(spacerItem)
        
        add_button = QToolButton(self)
        add_button.setToolTip(_('Add menu item'))
        add_button.setIcon(get_icon('plus.png'))
        button_layout.addWidget(add_button)
        spacerItem1 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        button_layout.addItem(spacerItem1)
        
        copy_button = QToolButton(self)
        copy_button.setToolTip(_('Copy menu item'))
        copy_button.setIcon(get_icon('edit-copy.png'))
        button_layout.addWidget(copy_button)
        spacerItem2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        button_layout.addItem(spacerItem2)
        
        delete_button = QToolButton(self)
        delete_button.setToolTip(_('Delete menu item'))
        delete_button.setIcon(get_icon('minus.png'))
        button_layout.addWidget(delete_button)
        spacerItem3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        button_layout.addItem(spacerItem3)
        
        move_down_button = QToolButton(self)
        move_down_button.setToolTip(_('Move menu item down'))
        move_down_button.setIcon(get_icon('arrow-down.png'))
        button_layout.addWidget(move_down_button)
        
        move_up_button.clicked.connect(self._table.move_rows_up)
        move_down_button.clicked.connect(self._table.move_rows_down)
        add_button.clicked.connect(self._table.add_row)
        delete_button.clicked.connect(self._table.delete_rows)
        copy_button.clicked.connect(self._table.copy_row)
        
        # Define a context menu for the table widget
        self.create_context_menu(self._table)
        
        
        # --- Keyboard shortcuts ---
        keyboard_layout = QHBoxLayout()
        layout.addLayout(keyboard_layout)
        keyboard_shortcuts_button = QPushButton(_('Keyboard shortcuts...'), self)
        keyboard_shortcuts_button.setToolTip(_('Edit the keyboard shortcuts associated with this plugin'))
        keyboard_shortcuts_button.clicked.connect(self.edit_shortcuts)
        keyboard_layout.addWidget(keyboard_shortcuts_button)
        keyboard_layout.insertStretch(-1)
        
        self.updateReport = QCheckBox(_('Display a update report'), self)
        self.updateReport.setChecked(PREFS[KEY_MENU.UPDATE_REPORT])
        
        keyboard_layout.addWidget(self.updateReport)
        
        error_button = QPushButton(_('Error strategy...'), self)
        error_button.setToolTip(_('Define the strategy when a error occurs during the library update'))
        error_button.clicked.connect(self.edit_error_strategy)
        keyboard_layout.addWidget(error_button)
    
    def edit_shortcuts(self):
        KeyboardConfigDialog.edit_shortcuts(self.plugin_action)
    
    def save_settings(self):
        PREFS[KEY_MENU.MENU] = self._table.get_menu_list()
        PREFS[KEY_MENU.UPDATE_REPORT] = self.updateReport.checkState() == Qt.Checked
        #debug_print('Save settings:\n{0}\n'.format(PREFS))
    
    def edit_error_strategy(self):
        d = ErrorStrategyDialog(GUI)
        if d.exec_() == d.Accepted:
            PREFS[KEY_ERROR.ERROR] = {
                KEY_ERROR.OPERATION : d.error_operation,
                KEY_ERROR.UPDATE : d.error_update
            }
            
            debug_print('Error Strategy settings: {0}\n'.format(PREFS[KEY_ERROR.ERROR]))
    
    def create_context_menu(self, table):
        table.setContextMenuPolicy(Qt.ActionsContextMenu)
        act_add_image = QAction(get_icon(ICON.ADD_IMAGE), _('&Add image...'), table)
        act_add_image.triggered.connect(table.display_add_new_image_dialog)
        table.addAction(act_add_image)
        act_open = QAction(get_icon('document_open.png'), _('&Open images folder'), table)
        act_open.triggered.connect(partial(self.open_images_folder, table.resources_dir))
        table.addAction(act_open)
        sep2 = QAction(table)
        sep2.setSeparator(True)
        table.addAction(sep2)
        act_import = QAction(get_icon(ICON.IMPORT), _('&Import...'), table)
        act_import.triggered.connect(self.import_menus)
        table.addAction(act_import)
        act_export = QAction(get_icon(ICON.EXPORT), _('&Export...'), table)
        act_export.triggered.connect(self.export_menus)
        table.addAction(act_export)
    
    def open_images_folder(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
        open_local_file(path)
    
    def import_menus(self):
        table = self._table
        archive_path = self.pick_archive_to_import()
        if not archive_path:
            return
        
        json = os.path.join(table.resources_dir, OWIP)
        json_path = os.path.join(table.resources_dir, OWIP+'.json')
        
        # Write the whole file contents into the resources\images directory
        if not os.path.exists(table.resources_dir):
            os.makedirs(table.resources_dir)
        with ZipFile(archive_path, 'r') as zf:
            contents = zf.namelist()
            if  os.path.basename(json_path) not in contents:
                return error_dialog(self, _('Import failed'), _('This is not a valid OWIP export archive'), show=True)
            for resource in contents:
                fs = os.path.join(table.resources_dir,resource)
                with open(fs,'wb') as f:
                    f.write(zf.read(resource))
        
        try:
            # Read the .JSON file to add to the menus then delete it.
            import_config = JSONConfig(json)
            menu_list = import_config[KEY_MENU.MENU]
            # Now insert the menus into the table
            table.append_menu_list(menu_list)
            info_dialog(self, _('Import completed'), _('{:d} menu items imported').format(len(menu_list)),
                        show=True, show_copy_button=False)
        except Exception as e:
            return error_dialog(self, _('Import failed'), e, show=True)
        finally:
            if os.path.exists(json_path):
                os.remove(json_path)
    
    def pick_archive_to_import(self):
        archives = choose_files(self, 'owp archive dialog', _('Select a menu file archive to import...'),
                             filters=[('OWIP Files', ['owip','owip.zip']),('ZIP Files', ['owip','zip'])], all_files=False, select_only_single_file=True)
        if not archives:
            return
        f = archives[0]
        return f
    
    def export_menus(self):
        table = self._table
        menu_list = table.get_selected_menu()
        if len(menu_list) == 0:
            return error_dialog(self, _('Export failed'), _('No menu items selected to export'), show=True)
        archive_path = self.pick_archive_to_export()
        if not archive_path:
            return
        
        # Build our unique list of images that need to be exported
        image_names = {}
        for menu in menu_list:
            image_name = menu[KEY_MENU.IMAGE]
            if image_name and image_name not in image_names:
                image_path = os.path.join(table.resources_dir, image_name)
                if os.path.exists(image_path):
                    image_names[image_name] = image_path
        
        # Write our menu items out to a json file
        if not os.path.exists(table.resources_dir):
            os.makedirs(table.resources_dir)
        
        json = os.path.join(table.resources_dir, OWIP)
        export_config = JSONConfig(json)
        export_config[KEY_MENU.MENU] = menu_list
        json_path = os.path.join(table.resources_dir, OWIP+'.json')
        
        try:
            # Create the zip file archive
            with ZipFile(archive_path, 'w') as archive_zip:
                archive_zip.write(json_path, os.path.basename(json_path))
                # Add any images referred to in those menu items that are local resources
                for image_name, image_path in iteritems(image_names):
                    archive_zip.write(image_path, os.path.basename(image_path))
            info_dialog(self, _('Export completed'), _('{:d} menu items exported to\n{:s}').format(len(menu_list), archive_path),
                        show=True, show_copy_button=False)
        except Exception as e:
            return error_dialog(self, _('Export failed'), e, show=True)
        finally:
            if os.path.exists(json_path):
                os.remove(json_path)
    
    def pick_archive_to_export(self):
        fd = FileDialog(name='owp archive dialog', title=_('Save menu archive as...'), filters=[('OWIP Files', ['owip.zip']),('ZIP Files', ['zip'])],
                        parent=self, add_all_files_filter=False, mode=QFileDialog.AnyFile)
        fd.setParent(None)
        if not fd.accepted:
            return None
        return fd.get_files()[0]




COL_NAMES = ['', _('Name'), _('Submenu'), _('Image'), _('Operation')]
class MenuTableWidget(QTableWidget):
    def __init__(self, menu_list=None, *args):
        QTableWidget.__init__(self, *args)
        
        from .columns_metadata import get_possible_idents, get_possible_fields
        self.possible_idents = get_possible_idents()
        self.all_fields, self.writable_fields = get_possible_fields()
        
        self.resources_dir = os.path.join(config_dir, 'resources/images')
        if iswindows:
            self.resources_dir = os.path.normpath(self.resources_dir)
        self.image_map = self.get_image_map()
        
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSortingEnabled(False)
        self.setMinimumSize(600, 0)
        
        self.populate_table(menu_list)
        
        self.cellChanged.connect(self.cell_changed)
    
    def populate_table(self, menu_list=None):
        self.clear()
        self.setColumnCount(len(COL_NAMES))
        self.setHorizontalHeaderLabels(COL_NAMES)
        self.verticalHeader().setDefaultSectionSize(24)
        
        menu_list = menu_list or []
        self.setRowCount(len(menu_list))
        for row, menu in enumerate(menu_list, 0):
            self.populate_table_row(row, menu)
        
        self.selectRow(0)
    
    def populate_table_row(self, row, menu):
        self.blockSignals(True)
        icon_name = menu[KEY_MENU.IMAGE]
        menu_text = menu[KEY_MENU.TEXT]
        
        self.setItem(row, 0, CheckableTableWidgetItem(menu[KEY_MENU.ACTIVE]))
        self.setItem(row, 1, TextIconWidgetItem(menu_text, get_icon(icon_name)))
        self.setItem(row, 2, QTableWidgetItem(menu[KEY_MENU.SUBMENU]))
        if menu_text:
            self.set_editable_cells_in_row(row, image=icon_name, menu=menu)
        else:
            # Make all the later column cells non-editable
            self.set_noneditable_cells_in_row(row)
        
        self.resizeColumnsToContents()
        self.blockSignals(False)
    
    def cell_changed(self, row, col):
        self.blockSignals(True)
        
        if col == 1 or col == 2:
            menu_text = unicode(self.item(row, col).text()).strip()
            self.item(row, col).setText(menu_text)
        
        
        if unicode(self.item(row, 1).text()):
            # Make sure that the other columns in this row are enabled if not already.
            if not self.cellWidget(row, len(COL_NAMES)-1):
                self.set_editable_cells_in_row(row)
            self.cellWidget(row, 4).setMenu(self.convert_row_to_menu(row))
        else:
            # Blank menu text so treat it as a separator row
            self.set_noneditable_cells_in_row(row)
        
        self.resizeColumnsToContents()
        self.blockSignals(False)
    
    def image_combo_index_changed(self, combo, row):
        if combo.currentText() == COMBO_IMAGE_ADD:
            # Special item in the combo for choosing a new image to add to Calibre
            self.display_add_new_image_dialog(select_in_combo=True, combo=combo)
        # Regardless of new or existing item, update image on the title column
        title_item = self.item(row, 1)
        title_item.setIcon(combo.itemIcon(combo.currentIndex()))
        # Store the current index as item data in index 0 in case user cancels dialog in future
        combo.setItemData(0, combo.currentIndex())
    
    def set_editable_cells_in_row(self, row, image='', menu=None):
        image_combo = ImageComboBox(self, self.image_map, image)
        image_combo.currentIndexChanged.connect(partial(self.image_combo_index_changed, image_combo, row))
        self.setCellWidget(row, 3, image_combo)
        menu = menu or self.create_blank_row_menu()
        self.setCellWidget(row, 4, SettingsButton(self, menu))
    
    def set_noneditable_cells_in_row(self, row):
        for col in range(3, len(COL_NAMES)):
            if self.cellWidget(row, col):
                self.removeCellWidget(row, col)
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
            self.setItem(row, col, item)
        self.item(row, 1).setIcon(get_icon())
    
    def display_add_new_image_dialog(self, select_in_combo=False, combo=None):
        add_image_dialog = ImageDialog(self, self.resources_dir, get_image_names(self.image_map))
        add_image_dialog.exec_()
        if add_image_dialog.result() == QDialog.Rejected:
            # User cancelled the add operation or an error - set to previous value
            if select_in_combo and combo:
                prevIndex = combo.itemData(0)
                combo.blockSignals(True)
                combo.setCurrentIndex(prevIndex)
                combo.blockSignals(False)
            return
        # User has added a new image so we need to repopulate every combo with new sorted list
        self.image_map[add_image_dialog.image_name] = get_icon(add_image_dialog.image_name)
        for update_row in range(self.rowCount()):
            cellCombo = self.cellWidget(update_row, 3)
            if cellCombo:
                cellCombo.blockSignals(True)
                cellCombo.populate_combo(self.image_map, cellCombo.currentText())
                cellCombo.blockSignals(False)
        # Now select the newly added item in this row if required
        if select_in_combo and combo:
            idx = combo.findText(add_image_dialog.image_name)
            combo.blockSignals(True)
            combo.setCurrentIndex(idx)
            combo.blockSignals(False)
    
    def add_row(self):
        self.setFocus()
        # We will insert a blank row below the currently selected row
        row = self.currentRow() + 1
        self.insertRow(row)
        self.populate_table_row(row, self.create_blank_row_menu())
        self.select_and_scroll_to_row(row)
    
    def copy_row(self):
        self.setFocus()
        currentRow = self.currentRow()
        if currentRow < 0:
            return
        menu = self.convert_row_to_menu(currentRow)
        menu[KEY_MENU.TEXT] += ' ' + _('(copy)')
        # We will insert a blank row below the currently selected row
        row = self.currentRow() + 1
        self.insertRow(row)
        self.populate_table_row(row, menu)
        self.select_and_scroll_to_row(row)
        self.resizeColumnsToContents()
    
    def delete_rows(self):
        self.setFocus()
        rows = self.selectionModel().selectedRows()
        if len(rows) == 0:
            return
        message = _('Are you sure you want to delete this menu item?')
        if len(rows) > 1:
            message = _('Are you sure you want to delete the selected {:d} menu items?').format(len(rows))
        if not question_dialog(self, _('Are you sure?'), message, show_copy_button=False):
            return
        first_sel_row = self.currentRow()
        for selrow in reversed(rows):
            self.removeRow(selrow.row())
        if first_sel_row < self.rowCount():
            self.select_and_scroll_to_row(first_sel_row)
        elif self.rowCount() > 0:
            self.select_and_scroll_to_row(first_sel_row - 1)
    
    def move_rows_up(self):
        self.setFocus()
        rows = self.selectionModel().selectedRows()
        if len(rows) == 0:
            return
        first_sel_row = rows[0].row()
        if first_sel_row <= 0:
            return
        for selrow in rows:
            self.swap_row_widgets(selrow.row() - 1, selrow.row() + 1)
        scroll_to_row = first_sel_row - 1
        if scroll_to_row > 0:
            scroll_to_row = scroll_to_row - 1
        self.scrollToItem(self.item(scroll_to_row, 0))
    
    def move_rows_down(self):
        self.setFocus()
        rows = self.selectionModel().selectedRows()
        if len(rows) == 0:
            return
        last_sel_row = rows[-1].row()
        if last_sel_row == self.rowCount() - 1:
            return
        for selrow in reversed(rows):
            self.swap_row_widgets(selrow.row() + 2, selrow.row())
        scroll_to_row = last_sel_row + 1
        if scroll_to_row < self.rowCount() - 1:
            scroll_to_row = scroll_to_row + 1
        self.scrollToItem(self.item(scroll_to_row, 0))
    
    def swap_row_widgets(self, src_row, dest_row):
        self.blockSignals(True)
        self.insertRow(dest_row)
        
        for col in range(0,3):
            self.setItem(dest_row, col, self.takeItem(src_row, col))
        
        menu_text = unicode(self.item(dest_row, 1).text()).strip()
        if menu_text:
            for col in range(3, len(COL_NAMES)):
                if col == 3:
                    # Image column has a combobox we have to recreate as cannot move widget (Qt crap)
                    icon_name = self.cellWidget(src_row, col).currentText()
                    image_combo = ImageComboBox(self, self.image_map, icon_name)
                    image_combo.currentIndexChanged.connect(partial(self.image_combo_index_changed, image_combo, dest_row))
                    self.setCellWidget(dest_row, col, image_combo)
                elif col == 4:
                    self.setCellWidget(dest_row, col, self.cellWidget(src_row, col))
        else:
            # This is a separator row
            self.set_noneditable_cells_in_row(dest_row)
        
        self.removeRow(src_row)
        self.blockSignals(False)
    
    def select_and_scroll_to_row(self, row):
        self.selectRow(row)
        self.scrollToItem(self.currentItem())
    
    def get_image_map(self):
        image_map = {}
        
        if os.path.exists(self.resources_dir):
            # Get the names of any .png images in this directory
            for f in os.listdir(self.resources_dir):
                if f.lower().endswith('.png'):
                    image_name = os.path.basename(f)
                    image_map[image_name] = get_icon(image_name)
        
        return image_map
    
    
    def create_blank_row_menu(self):
        return get_default_menu()
    
    def get_menu_list(self):
        menu_list = []
        for row in range(self.rowCount()):
            menu_list.append(self.convert_row_to_menu(row))
        
        # Remove any blank separator row items from at the start and the end
        while len(menu_list) > 0 and not menu_list[-1][KEY_MENU.TEXT]:
            menu_list.pop()
        while len(menu_list) > 0 and not menu_list[0][KEY_MENU.TEXT]:
            menu_list.pop(0)
        return menu_list
    
    def convert_row_to_menu(self, row):
        menu = self.create_blank_row_menu()
        menu[KEY_MENU.ACTIVE] = self.item(row, 0).checkState() == Qt.Checked
        menu[KEY_MENU.TEXT] = unicode(self.item(row, 1).text()).strip()
        menu[KEY_MENU.SUBMENU] = unicode(self.item(row, 2).text()).strip()
        if menu[KEY_MENU.TEXT]:
            menu[KEY_MENU.IMAGE] = unicode(self.cellWidget(row, 3).currentText()).strip()
            menu[KEY_MENU.OPERATIONS] = self.cellWidget(row, 4).getOperationList()
        return menu
    
    def get_selected_menu(self):
        menu_list = []
        for row in self.selectionModel().selectedRows():
            menu_list.append(self.convert_row_to_menu(row.row()))
        return menu_list
    
    def append_menu_list(self, menu_list):
        for menu in reversed(menu_list):
            row = self.currentRow() + 1
            self.insertRow(row)
            self.populate_table_row(row, menu)

class SettingsButton(QToolButton):
    def __init__(self, table, menu):
        QToolButton.__init__(self)
        
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.clicked.connect(self._clicked)
        
        self.table = table
        self._initial_menu = copy.deepcopy(menu)
        self.setMenu(menu)
    
    def setMenu(self, menu):
        self._menu = menu
        self.updateText()
        self.hasError()
    
    def getMenu(self):
        return copy.copy(self._menu)
    
    def updateText(self):
        count = len(self.getOperationList())
        active = 0
        for operation in self.getOperationList():
            if operation_is_active(operation):
                active += 1
        
        txt = ''
        if active < count:
            txt = _('{:d}/{:d} operations').format(active, count)
        else:
            txt = _('{:d} operations').format(count)
        
        if self.getHasChanged():
            txt+='*'
        self.setText(txt)
    
    def hasError(self):
        hasError = False
        
        for operation in self.getOperationList():
            if operation_testGetError(operation,
                    all_fields=self.table.all_fields, writable_fields=self.table.writable_fields,
                    possible_idents=self.table.possible_idents):
                hasError = True
                break
        
        if hasError:
            self.setIcon(get_icon(ICON.WARNING))
            self.setToolTip(_('This operations list contain a error'))
        else:
            self.setIcon(get_icon('gear.png'))
            self.setToolTip(_('Edit the operations list'))
        
        return hasError
    
    def getHasChanged(self):
        op_lst = self.getOperationList()
        initial_op_lst = self._initial_menu[KEY_MENU.OPERATIONS]
        if len(op_lst) != len(initial_op_lst):
            return True
        
        for i in range(0, len(op_lst)):
            if operation_is_active(op_lst[i]) != operation_is_active(initial_op_lst[i]):
                return True
            
            for key in KEY_OPERATION.ALL:
                if op_lst[i][key] != initial_op_lst[i][key]:
                    return True
        
        return False
    
    def setOperationList(self, operation_list):
        self._menu[KEY_MENU.OPERATIONS] = operation_list
        self.setMenu(self._menu)
    
    def getOperationList(self):
        return copy.copy(self._menu[KEY_MENU.OPERATIONS])
    
    def _clicked(self):
        d = ConfigOperationListDialog(self, menu=self.getMenu())
        if d.exec_() == d.Accepted:
            self.setOperationList(d.operation_list)

COMBO_IMAGE_ADD = _('Add New Image...')
def get_image_names(image_map):
    image_names = sorted(image_map.keys())
    # Add a blank item at the beginning of the list, and a blank then special 'Add" item at end
    image_names.insert(0, '')
    image_names.append('')
    image_names.append(COMBO_IMAGE_ADD)
    return image_names

class ImageComboBox(NoWheelComboBox):
    def __init__(self, parent, image_map, selected_text):
        NoWheelComboBox.__init__(self, parent)
        self.populate_combo(image_map, selected_text)
    
    def populate_combo(self, image_map, selected_text):
        self.clear()
        for i, image in enumerate(get_image_names(image_map), 0):
            self.insertItem(i, image_map.get(image, image), image)
        idx = self.findText(selected_text)
        self.setCurrentIndex(idx)
        self.setItemData(0, idx)

class ImageDialog(QDialog):
    def __init__(self, parent=None, resources_dir='', image_names=[]):
        QDialog.__init__(self, parent)
        self.resources_dir = resources_dir
        self.image_names = image_names
        self.setWindowTitle(_('Add New Image'))
        v = QVBoxLayout(self)
        
        group_box = QGroupBox(_('&Select image source'), self)
        v.addWidget(group_box)
        grid = QGridLayout()
        self._radio_web = QRadioButton(_('From &web domain favicon'), self)
        self._radio_web.setChecked(True)
        self._web_domain_edit = QLineEdit(self)
        self._radio_web.setFocusProxy(self._web_domain_edit)
        grid.addWidget(self._radio_web, 0, 0)
        grid.addWidget(self._web_domain_edit, 0, 1)
        grid.addWidget(QLabel('e.g. www.amazon.com'), 0, 2)
        self._radio_file = QRadioButton(_('From .png &file'), self)
        self._input_file_edit = QLineEdit(self)
        self._input_file_edit.setMinimumSize(200, 0)
        self._radio_file.setFocusProxy(self._input_file_edit)
        pick_button = QPushButton('...', self)
        pick_button.setMaximumSize(24, 20)
        pick_button.clicked.connect(self.pick_file_to_import)
        grid.addWidget(self._radio_file, 1, 0)
        grid.addWidget(self._input_file_edit, 1, 1)
        grid.addWidget(pick_button, 1, 2)
        group_box.setLayout(grid)
        
        save_layout = QHBoxLayout()
        lbl_filename = QLabel(_('&Save as filename:'), self)
        lbl_filename.setMinimumSize(155, 0)
        self._save_as_edit = QLineEdit('', self)
        self._save_as_edit.setMinimumSize(200, 0)
        lbl_filename.setBuddy(self._save_as_edit)
        lbl_ext = QLabel('.png', self)
        save_layout.addWidget(lbl_filename, 0, Qt.AlignLeft)
        save_layout.addWidget(self._save_as_edit, 0, Qt.AlignLeft)
        save_layout.addWidget(lbl_ext, 1, Qt.AlignLeft)
        v.addLayout(save_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.ok_clicked)
        button_box.rejected.connect(self.reject)
        v.addWidget(button_box)
        self.resize(self.sizeHint())
        self._web_domain_edit.setFocus()
        self.new_image_name = None
    
    @property
    def image_name(self):
        return self.new_image_name
    
    def pick_file_to_import(self):
        images = choose_files(None, _('menu icon dialog'), _('Select a .png file for the menu icon'),
                             filters=[('PNG Image Files', ['png'])], all_files=False, select_only_single_file=True)
        if not images:
            return
        f = images[0]
        if not f.lower().endswith('.png'):
            return error_dialog(self, _('Cannot import image'), _('Source image must be a .png file.'), show=True)
        self._input_file_edit.setText(f)
        self._save_as_edit.setText(os.path.splitext(os.path.basename(f))[0])
    
    def ok_clicked(self):
        # Validate all the inputs
        save_name = unicode(self._save_as_edit.text()).strip()
        if not save_name:
            return error_dialog(self, _('Cannot import image'), _('You must specify a filename to save as.'), show=True)
        self.new_image_name = os.path.splitext(save_name)[0] + '.png'
        if save_name.find('\\') > -1 or save_name.find('/') > -1:
            return error_dialog(self, _('Cannot import image'), _('The save as filename should consist of a filename only.'), show=True)
        if not os.path.exists(self.resources_dir):
            os.makedirs(self.resources_dir)
        dest_path = os.path.join(self.resources_dir, self.new_image_name)
        if save_name in self.image_names or os.path.exists(dest_path):
            if not question_dialog(self, _('Are you sure?'), _('An image with this name already exists - overwrite it?'), show_copy_button=False):
                return
        
        if self._radio_web.isChecked():
            try:
                from urllib.request import urlretrieve
            except ImportError:
                from urllib import urlretrieve
            domain = unicode(self._web_domain_edit.text()).strip()
            if not domain:
                return error_dialog(self, _('Cannot import image'), _('You must specify a web domain url'), show=True)
            url = 'http://www.google.com/s2/favicons?domain=' + domain
            urlretrieve(url, dest_path)
            return self.accept()
        else:
            source_file_path = unicode(self._input_file_edit.text()).strip()
            if not source_file_path:
                return error_dialog(self, _('Cannot import image'), _('You must specify a source file.'), show=True)
            if not source_file_path.lower().endswith('.png'):
                return error_dialog(self, _('Cannot import image'), _('Source image must be a .png file.'), show=True)
            if not os.path.exists(source_file_path):
                return error_dialog(self, _('Cannot import image'), _('Source image does not exist!'), show=True)
            shutil.copyfile(source_file_path, dest_path)
            return self.accept()



COL_CONFIG = ['', _('Columns'), _('Template'), _('Search mode'), _('Search'), _('Replace')]
class ConfigOperationListDialog(Dialog):
    def __init__(self, parent, menu):
        menu = menu or get_default_menu()
        name = menu[KEY_MENU.TEXT]
        sub_menu = menu[KEY_MENU.SUBMENU]
        self.operation_list = menu[KEY_MENU.OPERATIONS]
        
        title = ''
        if not name:
            title = _('List of operations for a quick Search/Replaces')
        else:
            if sub_menu:
                name = '{:s} > {:s}'.format(sub_menu, name)
            else:
                name = '{:s}'.format(name)
            
            title = _('List of Search/Replace operations for {:s}').format(name)
        
        
        Dialog.__init__(self, title, 'config_list_SearchReplace')
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        heading_layout = QHBoxLayout()
        layout.addLayout(heading_layout)
        heading_label = QLabel(_('Select and configure the order of execution of the operations of Search/Replace operations:'), self)
        heading_layout.addWidget(heading_label)
        #help_label = QLabel(' ', self)
        #help_label.setTextInteractionFlags(Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)
        #help_label.setAlignment(Qt.AlignRight)
        #heading_layout.addWidget(help_label)
        
        # Add a horizontal layout containing the table and the buttons next to it
        table_layout = QHBoxLayout()
        layout.addLayout(table_layout)
        
        # Create a table the user can edit the operation list
        self._table = OperationListTableWidget(self.operation_list, self)
        heading_label.setBuddy(self._table)
        table_layout.addWidget(self._table)
        
        # Add a vertical layout containing the the buttons to move up/down etc.
        button_layout = QVBoxLayout()
        table_layout.addLayout(button_layout)
        move_up_button = QToolButton(self)
        move_up_button.setToolTip(_('Move operation up'))
        move_up_button.setIcon(get_icon('arrow-up.png'))
        button_layout.addWidget(move_up_button)
        spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        button_layout.addItem(spacerItem)
        
        add_button = QToolButton(self)
        add_button.setToolTip(_('Add operation'))
        add_button.setIcon(get_icon('plus.png'))
        button_layout.addWidget(add_button)
        spacerItem1 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        button_layout.addItem(spacerItem1)
        
        copy_button = QToolButton(self)
        copy_button.setToolTip(_('Copy operation'))
        copy_button.setIcon(get_icon('edit-copy.png'))
        button_layout.addWidget(copy_button)
        spacerItem2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        button_layout.addItem(spacerItem2)
        
        delete_button = QToolButton(self)
        delete_button.setToolTip(_('Delete operation'))
        delete_button.setIcon(get_icon('minus.png'))
        button_layout.addWidget(delete_button)
        spacerItem3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        button_layout.addItem(spacerItem3)
        
        move_down_button = QToolButton(self)
        move_down_button.setToolTip(_('Move operation down'))
        move_down_button.setIcon(get_icon('arrow-down.png'))
        button_layout.addWidget(move_down_button)
        
        move_up_button.clicked.connect(self._table.move_rows_up)
        move_down_button.clicked.connect(self._table.move_rows_down)
        add_button.clicked.connect(self._table.add_row)
        delete_button.clicked.connect(self._table.delete_rows)
        copy_button.clicked.connect(self._table.copy_row)
        
        # Define a context menu for the table widget
        self.create_context_menu(self._table)
        
        # -- Accept/Reject buttons --
        layout.addWidget(self.bb)
    
    def accept(self):
        self.operation_list = self._table.get_operation_list()
        
        if len(self.operation_list)==0:
            debug_print('Saving a empty list')
        else:
            txt = 'Saved operation list:'
            for i, operation in enumerate(self.operation_list, 1):
                txt += '\nOperation {:d} > {:s}'.format(i, operation_string(operation))
            txt += '\n[  '+ ',\n'.join( [str(operation) for operation in self.operation_list] ) +'  ]\n'
            debug_print(txt)
        
        Dialog.accept(self)
    
    def add_empty_operation(self):
        self._table.add_row()
    
    def create_context_menu(self, table):
        table.setContextMenuPolicy(Qt.ActionsContextMenu)
        act_import = QAction(get_icon(ICON.IMPORT), _('&Import...'), table)
        act_import.triggered.connect(self.import_operations)
        table.addAction(act_import)
        act_export = QAction(get_icon(ICON.EXPORT), _('&Export...'), table)
        act_export.triggered.connect(self.export_operations)
        table.addAction(act_export)
    
    def import_operations(self):
        table = self._table
        json_path = self.pick_json_to_import()
        if not json_path:
            return
        
        json_name = 'zz_import_temp'
        json_temp = os.path.join(config_dir, json_name+'.json')
        if iswindows:
            json_temp = os.path.normpath(json_temp)
        
        try:
            
            shutil.copyfile(json_path, json_temp)
            import_config = JSONConfig(json_name)
            
            if KEY_MENU.OPERATIONS not in import_config:
                return error_dialog(self, _('Import failed'), _('This is not a valid JSON file'), show=True)
            operation_list = import_config[KEY_MENU.OPERATIONS]
            table.append_operation_list(operation_list)
            
            info_dialog(self, _('Import completed'), _('{:d} menu items imported').format(len(operation_list), json_path),
                        show=True, show_copy_button=False)
        except Exception as e:
            return error_dialog(self, _('Export failed'), e, show=True)
        finally:
            if os.path.exists(json_temp):
                os.remove(json_temp)
    
    def pick_json_to_import(self):
        archives = choose_files(self, 'json dialog', _('Select a JSON file to import...'),
                             filters=[('JSON List Files', ['list.json']),('JSON Files', ['json'])], all_files=False, select_only_single_file=True)
        if not archives:
            return
        f = archives[0]
        return f
    
    def export_operations(self):
        table = self._table
        operation_list = table.get_selected_operation()
        if len(operation_list) == 0:
            return error_dialog(self, _('Export failed'), _('No operations selected to export'), show=True)
        json_path = self.pick_json_to_export()
        if not json_path:
            return
        
        json_name = 'zz_export_temp'
        json_temp = os.path.join(config_dir, json_name+'.json')
        if iswindows:
            json_temp = os.path.normpath(json_temp)
        
        try:
            
            export_config = JSONConfig(json_name)
            export_config[KEY_MENU.OPERATIONS] = operation_list
            shutil.copyfile(json_temp, json_path)
            info_dialog(self, _('Export completed'), _('{:d} operations exported to\n{:s}').format(len(operation_list), json_path),
                        show=True, show_copy_button=False)
        except Exception as e:
            return error_dialog(self, _('Export failed'), e, show=True)
        finally:
            if os.path.exists(json_temp):
                os.remove(json_temp)
    
    def pick_json_to_export(self):
        fd = FileDialog(name='json dialog', title=_('Save the operations as...'), filters=[('JSON List Files', ['list.json']),('JSON Files', ['json'])],
                        parent=self, add_all_files_filter=False, mode=QFileDialog.AnyFile)
        fd.setParent(None)
        if not fd.accepted:
            return None
        return fd.get_files()[0]

class OperationListTableWidget(QTableWidget):
    def __init__(self, operation_list=None, *args):
        QTableWidget.__init__(self, *args)
        
        from .columns_metadata import get_possible_idents, get_possible_fields
        self.possible_idents = get_possible_idents()
        self.all_fields, self.writable_fields = get_possible_fields()
        
        self.book_ids = get_selected_BookIds(show_error=False)[:10]
        
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSortingEnabled(False)
        self.setMinimumSize(800, 0)
        
        self.populate_table(operation_list)
        
        self.itemDoubleClicked.connect(self.settingsDoubleClicked)
    
    def populate_table(self, operation_list=None):
        self.clear()
        self.setColumnCount(len(COL_CONFIG))
        self.setHorizontalHeaderLabels(COL_CONFIG)
        self.verticalHeader().setDefaultSectionSize(24)
        
        operation_list = clean_empty_operation(operation_list)
        self.setRowCount(len(operation_list))
        for row, operation in enumerate(operation_list):
            self.populate_table_row(row, operation)
        
        self.selectRow(0)
    
    def populate_table_row(self, row, operation):
        self.blockSignals(True)
        
        self.setItem(row, 0, OperationWidgetItem(self, operation))
        
        for i in range(1, len(COL_CONFIG)):
            item = ReadOnlyTableWidgetItem('')
            self.setItem(row, i, item)
        
        as_template = False
        for i_row in range(self.rowCount()):
            item = self.item(i_row, 0)
            if item and item.getOperation()[KEY_OPERATION.SEARCH_FIELD] == TEMPLATE_FIELD:
                as_template = True
                break
        
        self.setColumnHidden(2, not as_template)
        
        self.update_row(row)
        
        self.resizeColumnsToContents()
        self.blockSignals(False)
    
    def update_row(self, row):
        operation = self.convert_row_to_operation(row)
        
        for col, val in enumerate(operation_para_list(operation), 1):
            self.item(row, col).setText(val)
    
    def add_row(self):
        self.setFocus()
        # We will insert a blank row below the currently selected row
        row = self.currentRow() + 1
        self.insertRow(row)
        
        self.populate_table_row(row, self.create_blank_row_operation())
        self.select_and_scroll_to_row(row)
    
    def copy_row(self):
        self.setFocus()
        currentRow = self.currentRow()
        if currentRow < 0:
            return
        operation = self.convert_row_to_operation(currentRow)
        # We will insert a blank row below the currently selected row
        row = self.currentRow() + 1
        self.insertRow(row)
        self.populate_table_row(row, operation)
        self.select_and_scroll_to_row(row)
    
    def delete_rows(self):
        self.setFocus()
        rows = self.selectionModel().selectedRows()
        if len(rows) == 0:
            return
        message = _('Are you sure you want to delete this operation?')
        if len(rows) > 1:
            message = _('Are you sure you want to delete the selected {:d} operations?').format(len(rows))
        if not question_dialog(self, _('Are you sure?'), message, show_copy_button=False):
            return
        first_sel_row = self.currentRow()
        for selrow in reversed(rows):
            self.removeRow(selrow.row())
        if first_sel_row < self.rowCount():
            self.select_and_scroll_to_row(first_sel_row)
        elif self.rowCount() > 0:
            self.select_and_scroll_to_row(first_sel_row - 1)
        
        if self.rowCount():
            self.update_row(0)
    
    def move_rows_up(self):
        self.setFocus()
        rows = self.selectionModel().selectedRows()
        if len(rows) == 0:
            return
        first_sel_row = rows[0].row()
        if first_sel_row <= 0:
            return
        # Workaround for strange selection bug in Qt which "alters" the selection
        # in certain circumstances which meant move down only worked properly "once"
        selrows = []
        for row in rows:
            selrows.append(row.row())
        selrows.sort()
        for selrow in selrows:
            self.swap_row_widgets(selrow - 1, selrow + 1)
        scroll_to_row = first_sel_row - 1
        if scroll_to_row > 0:
            scroll_to_row = scroll_to_row - 1
        self.scrollToItem(self.item(scroll_to_row, 0))
    
    def move_rows_down(self):
        self.setFocus()
        rows = self.selectionModel().selectedRows()
        if len(rows) == 0:
            return
        last_sel_row = rows[-1].row()
        if last_sel_row == self.rowCount() - 1:
            return
        # Workaround for strange selection bug in Qt which "alters" the selection
        # in certain circumstances which meant move down only worked properly "once"
        selrows = []
        for row in rows:
            selrows.append(row.row())
        selrows.sort()
        for selrow in reversed(selrows):
            self.swap_row_widgets(selrow + 2, selrow)
        scroll_to_row = last_sel_row + 1
        if scroll_to_row < self.rowCount() - 1:
            scroll_to_row = scroll_to_row + 1
        self.scrollToItem(self.item(scroll_to_row, 0))
    
    def swap_row_widgets(self, src_row, dest_row):
        self.blockSignals(True)
        self.insertRow(dest_row)
        
        for col in range(0, len(COL_CONFIG)):
            self.setItem(dest_row, col, self.takeItem(src_row, col))
        
        self.update_row(dest_row)
        self.removeRow(src_row)
        self.blockSignals(False)
    
    def select_and_scroll_to_row(self, row):
        self.selectRow(row)
        self.scrollToItem(self.currentItem())
    
    
    def create_blank_row_operation(self):
        return get_default_operation()
    
    def get_operation_list(self):
        operation_list = []
        for row in range(self.rowCount()):
            operation = self.convert_row_to_operation(row)
            operation_list.append(operation)
       
        return clean_empty_operation(operation_list)
    
    def convert_row_to_operation(self, row):
        return self.item(row, 0).getOperation()
    
    def get_selected_operation(self):
        operation_list = []
        for row in self.selectionModel().selectedRows():
            operation_list.append(self.convert_row_to_operation(row.row()))
        return clean_empty_operation(operation_list)
    
    def append_operation_list(self, operation_list):
        for operation in reversed(clean_empty_operation(operation_list)):
            row = self.currentRow() + 1
            self.insertRow(row)
            self.populate_table_row(row, operation)
    
    
    def settingsDoubleClicked(self):
        self.setFocus()
        row = self.currentRow()
        
        src_operation = self.convert_row_to_operation(row)
        d = SearchReplaceDialog(src_operation, self.book_ids)
        if d.exec_() == d.Accepted:
            d.operation[KEY_OPERATION.ACTIVE] = operation_is_active(src_operation)
            self.populate_table_row(row, d.operation)

class OperationWidgetItem(QTableWidgetItem):
    def __init__(self, table, operation):
        QTableWidgetItem.__init__(self, '')
        self.setFlags(Qt.ItemFlag(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled ))
        
        self.table = table
        self._operation = operation
        self._hasError = False
        self.setOperation(operation)
    
    def setOperation(self, operation):
        operation = operation or get_default_operation()
        self._operation = operation
        
        checked = operation_is_active(self._operation)
        if checked:
            self.setCheckState(Qt.Checked)
        else:
            self.setCheckState(Qt.Unchecked)
        
        self.hasError()
    
    def getOperation(self):
        self._operation[KEY_OPERATION.ACTIVE] = Qt.Checked == self.checkState()
        self._operation = operation_ConvertError(self._operation)
        return copy.copy(self._operation)
    
    def hasError(self):
        err = operation_testFullError(self._operation,
                    all_fields=self.table.all_fields, writable_fields=self.table.writable_fields,
                    possible_idents=self.table.possible_idents)
        
        if err:
            self.setIcon(get_icon(ICON.WARNING))
            self.setToolTip(str(err))
            return True
        else:
            self.setIcon(get_icon())
            self.setToolTip('')
            return False


class ErrorStrategyDialog(Dialog):
    def __init__(self, parent):
        self.error_update = PREFS[KEY_ERROR.ERROR][KEY_ERROR.UPDATE]
        self.error_operation = PREFS[KEY_ERROR.ERROR][KEY_ERROR.OPERATION]
        
        if self.error_operation not in ERROR_OPERATION.LIST.keys():
            self.error_operation = ERROR_OPERATION.DEFAULT
        
        if self.error_update not in ERROR_UPDATE.LIST.keys():
            self.error_update = ERROR_UPDATE.DEFAULT
        
        title = _('Error Strategy')
        Dialog.__init__(self, title, 'config_ErrorStrategy', parent)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        operation_label = QLabel(_('Set the strategy when an invalid operation has detected:'), self)
        layout.addWidget(operation_label)
        
        self.operationStrategy = KeyValueComboBox(self, {key:value[0] for key, value in iteritems(ERROR_OPERATION.LIST)}, self.error_operation)
        self.operationStrategy.currentIndexChanged[int].connect(self.operationStrategyIndexChanged)
        layout.addWidget(self.operationStrategy)
        
        operation_label.setBuddy(self.operationStrategy)
        
        layout.addWidget(QLabel (' ', self))
        
        update_label = QLabel(_('Define the strategy when a error occurs during the library update:'), self)
        layout.addWidget(update_label)
        
        self.updateStrategy = KeyValueComboBox(self, {key:value[0] for key, value in iteritems(ERROR_UPDATE.LIST)}, self.error_update)
        self.updateStrategy.currentIndexChanged[int].connect(self.updateStrategyIndexChanged)
        layout.addWidget(self.updateStrategy)
        
        update_label.setBuddy(self.updateStrategy)
        
        self.desc = QTextEdit (' ', self)
        self.desc.setReadOnly(True)
        layout.addWidget(self.desc)
        
        layout.insertStretch(-1)
        
        # -- Accept/Reject buttons --
        layout.addWidget(self.bb)
    
    
    def operationStrategyIndexChanged(self, idx):
        error_operation = self.operationStrategy.selected_key()
        self.desc.setText(ERROR_OPERATION.LIST[error_operation][1])
    
    def updateStrategyIndexChanged(self, idx):
        error_update = self.updateStrategy.selected_key()
        self.desc.setText(ERROR_UPDATE.LIST[error_update][1])
    
    def accept(self):
        self.error_operation = self.operationStrategy.selected_key()
        if self.error_operation not in ERROR_OPERATION.LIST.keys():
            self.error_operation = ERROR_OPERATION.DEFAULT
        
        self.error_update = self.updateStrategy.selected_key()
        if self.error_update not in ERROR_UPDATE.LIST.keys():
            self.error_update = ERROR_UPDATE.DEFAULT
        
        Dialog.accept(self)