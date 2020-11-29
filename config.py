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

from six import text_type as unicode
from collections import OrderedDict
try:
    from PyQt5 import Qt as QtGui
    from PyQt5 import QtCore
    from PyQt5.Qt import (Qt, QToolButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                          QIcon, QFormLayout, QAction, QFileDialog, QDialog, QTableWidget,
                          QTableWidgetItem, QAbstractItemView, QComboBox,
                          QGroupBox, QGridLayout, QRadioButton, QDialogButtonBox,
                          QPushButton, QSizePolicy)
except:
    from PyQt4 import QtGui, QtCore
    from PyQt4.Qt import (Qt, QToolButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                          QIcon, QFormLayout, QAction, QFileDialog, QDialog, QTableWidget,
                          QTableWidgetItem, QAbstractItemView, QComboBox,
                          QGroupBox, QGridLayout, QRadioButton, QDialogButtonBox,
                          QPushButton, QSizePolicy)

try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

from functools import partial
from calibre.constants import iswindows
from calibre.utils.config import config_dir, JSONConfig
from calibre.gui2 import error_dialog, question_dialog, info_dialog, choose_files, open_local_file, FileDialog
from calibre.gui2.widgets2 import Dialog
from calibre.utils.zipfile import ZipFile

from calibre_plugins.mass_search_replace.SearchReplace import SearchReplaceDialog, get_default_query, query_isValid, query_string, KEY_QUERY
from calibre_plugins.mass_search_replace.common_utils import (NoWheelComboBox, CheckableTableWidgetItem , TextIconWidgetItem, KeyboardConfigDialog, ReadOnlyTableWidgetItem,
                                                              get_icon, debug_print)

PLUGIN_ICONS = ['images/plugin.png', 'images/image_add.png', 'images/export.png', 'images/import.png']


class KEY:
    MASS_SEARCH_REPLACE = 'MassSearch-Replace'
    MENU_ACTIVE = 'Active'
    MENU_IMAGE = 'Image'
    MENU_TEXT = 'Text'
    MENU_SUBMENU = 'SubMenu'
    MENU_SEARCH_REPLACES = 'Search-Replaces'


# This is where all preferences for this plugin are stored
PREFS = JSONConfig('plugins/Mass Search-Replace')
# Set defaults
PREFS.defaults[KEY.MASS_SEARCH_REPLACE] = []

OWIP = 'owip'

class ConfigWidget(QWidget):
    def __init__(self, plugin_action):
        QWidget.__init__(self)
        self.plugin_action = plugin_action
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        data_items = PREFS[KEY.MASS_SEARCH_REPLACE]
        
        heading_layout = QHBoxLayout()
        layout.addLayout(heading_layout)
        heading_label = QLabel(_('Select and configure the menu items to display:'), self)
        heading_layout.addWidget(heading_label)
        
        # Add a horizontal layout containing the table and the buttons next to it
        table_layout = QHBoxLayout()
        layout.addLayout(table_layout)
        
        # Create a table the user can edit the data values in
        self._table = MenuTableWidget(plugin_action, data_items, self)
        heading_label.setBuddy(self._table)
        table_layout.addWidget(self._table)
        
        # Add a vertical layout containing the the buttons to move up/down etc.
        button_layout = QtGui.QVBoxLayout()
        table_layout.addLayout(button_layout)
        move_up_button = QtGui.QToolButton(self)
        move_up_button.setToolTip(_('Move menu item up'))
        move_up_button.setIcon(QIcon(I('arrow-up.png')))
        button_layout.addWidget(move_up_button)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        button_layout.addItem(spacerItem)
        
        add_button = QtGui.QToolButton(self)
        add_button.setToolTip(_('Add menu item'))
        add_button.setIcon(QIcon(I('plus.png')))
        button_layout.addWidget(add_button)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        button_layout.addItem(spacerItem1)
        
        copy_button = QtGui.QToolButton(self)
        copy_button.setToolTip(_('Copy menu item'))
        copy_button.setIcon(QIcon(I('edit-copy.png')))
        button_layout.addWidget(copy_button)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        button_layout.addItem(spacerItem2)
        
        delete_button = QtGui.QToolButton(self)
        delete_button.setToolTip(_('Delete menu item'))
        delete_button.setIcon(QIcon(I('minus.png')))
        button_layout.addWidget(delete_button)
        spacerItem3 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        button_layout.addItem(spacerItem3)
        
        move_down_button = QtGui.QToolButton(self)
        move_down_button.setToolTip(_('Move menu item down'))
        move_down_button.setIcon(QIcon(I('arrow-down.png')))
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
        
    
    def save_settings(self):
        
        PREFS[KEY.MASS_SEARCH_REPLACE] = self._table.get_data()
        debug_print('Save settings:\n{0}\n'.format(PREFS))
        
    
    def edit_shortcuts(self):
        self.save_settings()
        self.plugin_action.rebuild_menus()
        d = KeyboardConfigDialog(self.plugin_action.gui, self.plugin_action.action_spec[0])
        if d.exec_() == d.Accepted:
            self.plugin_action.gui.keyboard.finalize()
        
    def create_context_menu(self, table):
        table.setContextMenuPolicy(Qt.ActionsContextMenu)
        act_add_image = QAction(get_icon(PLUGIN_ICONS[1]), _('&Add image...'), table)
        act_add_image.triggered.connect(table.display_add_new_image_dialog)
        table.addAction(act_add_image)
        act_open = QAction(get_icon('document_open.png'), _('&Open images folder'), table)
        act_open.triggered.connect(partial(self.open_images_folder, table.resources_dir))
        table.addAction(act_open)
        sep2 = QAction(table)
        sep2.setSeparator(True)
        table.addAction(sep2)
        act_import = QAction(get_icon(PLUGIN_ICONS[2]), _('&Import...'), table)
        act_import.triggered.connect(self.import_menus)
        table.addAction(act_import)
        act_export = QAction(get_icon(PLUGIN_ICONS[3]), _('&Export...'), table)
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
            data_items = import_config[KEY.MASS_SEARCH_REPLACE]
            # Now insert the menus into the table
            table.append_data(data_items)
            info_dialog(self, _('Import completed'), _('{:d} menu items imported').format(len(data_items)),
                        show=True, show_copy_button=False)
        except Exception as e:
            return error_dialog(self, _('Import failed'), e, show=True)
        finally:
            if os.path.exists(json_path):
                os.remove(json_path)
    
    def pick_archive_to_import(self):
        archives = choose_files(self, 'owp archive dialog', _('Select a menu file archive to import...'),
                             filters=[('OWIP Files', ['owip','zip'])], all_files=False, select_only_single_file=True)
        if not archives:
            return
        f = archives[0]
        return f
    
    def export_menus(self):
        table = self._table
        data_items = table.get_selected_data()
        if len(data_items) == 0:
            return error_dialog(self, _('Export failed'), _('No menu items selected to export'), show=True)
        archive_path = self.pick_archive_to_export()
        if not archive_path:
            return
        
        # Build our unique list of images that need to be exported
        image_names = {}
        for data in data_items:
            image_name = data[KEY.MENU_IMAGE]
            if image_name and image_name not in image_names:
                image_path = os.path.join(table.resources_dir, image_name)
                if os.path.exists(image_path):
                    image_names[image_name] = image_path
        
        # Write our menu items out to a json file
        if not os.path.exists(table.resources_dir):
            os.makedirs(table.resources_dir)
        
        json = os.path.join(table.resources_dir, OWIP)
        export_config = JSONConfig(json)
        export_config[KEY.MASS_SEARCH_REPLACE] = data_items
        json_path = os.path.join(table.resources_dir, OWIP+'.json')
        
        try:
            # Create the zip file archive
            with ZipFile(archive_path, 'w') as archive_zip:
                archive_zip.write(json_path, os.path.basename(json_path))
                # Add any images referred to in those menu items that are local resources
                for image_name, image_path in list(image_names.items()):
                    archive_zip.write(image_path, os.path.basename(image_path))
            info_dialog(self, _('Export completed'), _('{:d} menu items exported to\n{:s}').format(len(data_items), archive_path),
                        show=True, show_copy_button=False)
        except Exception as e:
            return error_dialog(self, _('Export failed'), e, show=True)
        finally:
            if os.path.exists(json_path):
                os.remove(json_path)
    
    def pick_archive_to_export(self):
        fd = FileDialog(name='owp archive dialog', title=_('Save menu archive as...'), filters=[('OWIP Files', ['zip'])],
                        parent=self, add_all_files_filter=False, mode=QFileDialog.AnyFile)
        fd.setParent(None)
        if not fd.accepted:
            return None
        return fd.get_files()[0]


COMBO_IMAGE_ADD = _('Add New Image...')

def get_image_names(image_map):
    image_names = sorted(image_map.keys())
    # Add a blank item at the beginning of the list, and a blank then special 'Add" item at end
    image_names.insert(0, '')
    image_names.append('')
    image_names.append(COMBO_IMAGE_ADD)
    return image_names


COL_NAMES = ['', _('Name'), _('Submenu'), _('Image'), _('Operation')]

class MenuTableWidget(QTableWidget):
    def __init__(self, plugin_action, data_items=None, *args):
        QTableWidget.__init__(self, *args)
        self.plugin_action = plugin_action
        self.gui = plugin_action.gui
        
        self.resources_dir = os.path.join(config_dir, 'resources/images')
        if iswindows:
            self.resources_dir = os.path.normpath(self.resources_dir)
        
        self.populate_table(data_items)
        self.cellChanged.connect(self.cell_changed)
        
        
    def populate_table(self, data_items=None):
        self.image_map = self.get_image_map()
        self.clear()
        self.setAlternatingRowColors(True)
        if data_items == None: data_items = []
        self.setRowCount(len(data_items))
        
        self.setColumnCount(len(COL_NAMES))
        self.setHorizontalHeaderLabels(COL_NAMES)
        self.verticalHeader().setDefaultSectionSize(24)
        
        for row, data in enumerate(data_items, 0):
            self.populate_table_row(row, data)
        
        self.resizeColumnsToContents()
        self.setSortingEnabled(False)
        self.setMinimumSize(800, 0)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.selectRow(0)
    
    def populate_table_row(self, row, data):
        self.blockSignals(True)
        icon_name = data[KEY.MENU_IMAGE]
        menu_text = data[KEY.MENU_TEXT]
        
        self.setItem(row, 0, CheckableTableWidgetItem(data[KEY.MENU_ACTIVE]))
        self.setItem(row, 1, TextIconWidgetItem(menu_text, get_icon(icon_name)))
        self.setItem(row, 2, QTableWidgetItem(data[KEY.MENU_SUBMENU]))
        if menu_text:
            self.set_editable_cells_in_row(row, image=icon_name, query=data)
        else:
            # Make all the later column cells non-editable
            self.set_noneditable_cells_in_row(row)
        
        self.blockSignals(False)
    
    def cell_changed(self, row, col):
        self.blockSignals(True)
        
        if col == 1 or col == 2:
            menu_text = unicode(self.item(row, col).text()).strip()
            self.item(row, col).setText(menu_text)
        
        
        if unicode(self.item(row, 1).text()):
            # Make sure that the other columns in this row are enabled if not already.
            if not self.cellWidget(row, len(COL_NAMES)-1):
                debug_print('dswdsdfsfsdfdfs')
                self.set_editable_cells_in_row(row)
            self.cellWidget(row, 4).query = self.convert_row_to_data(row)
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
    
    def set_editable_cells_in_row(self, row, image='', query=None):
        image_combo = ImageComboBox(self, self.image_map, image)
        image_combo.currentIndexChanged.connect(partial(self.image_combo_index_changed, image_combo, row))
        self.setCellWidget(row, 3, image_combo)
        if query==None: query = self.create_blank_row_data()
        self.setCellWidget(row, 4, SettingsButton(self, self.plugin_action, query))
    
    def set_noneditable_cells_in_row(self, row):
        for col in range(3, len(COL_NAMES)):
            if self.cellWidget(row, col):
                self.removeCellWidget(row, col)
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
            self.setItem(row, col, item)
        self.item(row, 1).setIcon(QIcon())
    
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
        self.populate_table_row(row, self.create_blank_row_data())
        self.select_and_scroll_to_row(row)
    
    def copy_row(self):
        self.setFocus()
        row_data = self.convert_row_to_data(self.currentRow())
        row_data[KEY.MENU_TEXT] += ' ' + _('(copy)')
        # We will insert a blank row below the currently selected row
        row = self.currentRow() + 1
        self.insertRow(row)
        self.populate_table_row(row, row_data)
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
                    self.setCellWidget(dest_row, col, SettingsButton(self, self.plugin_action, self.cellWidget(src_row, col).query))
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
    
    
    def create_blank_row_data(self):
        data = {}
        data[KEY.MENU_ACTIVE] = True
        data[KEY.MENU_TEXT] = ''
        data[KEY.MENU_SUBMENU] = ''
        data[KEY.MENU_IMAGE] = ''
        data[KEY.MENU_SEARCH_REPLACES] = []
        return data
    
    def get_data(self):
        data_items = []
        for row in range(self.rowCount()):
            data_items.append(self.convert_row_to_data(row))
        # Remove any blank separator row items from the end as unneeded.
        
        while len(data_items) > 0 and len(data_items[-1][KEY.MENU_TEXT]) == 0:
            data_items.pop()
        return data_items
    
    def convert_row_to_data(self, row):
        data = self.create_blank_row_data()
        data[KEY.MENU_ACTIVE] = self.item(row, 0).checkState() == Qt.Checked
        data[KEY.MENU_TEXT] = unicode(self.item(row, 1).text()).strip()
        data[KEY.MENU_SUBMENU] = unicode(self.item(row, 2).text()).strip()
        if data[KEY.MENU_TEXT]:
            data[KEY.MENU_IMAGE] = unicode(self.cellWidget(row, 3).currentText()).strip()
            data[KEY.MENU_SEARCH_REPLACES] = self.cellWidget(row, 4).query[KEY.MENU_SEARCH_REPLACES]
        return data
    
    def get_selected_data(self):
        data_items = []
        for row in self.selectionModel().selectedRows():
            data_items.append(self.convert_row_to_data(row.row()))
        return data_items
    
    def append_data(self, data_items):
        for data in reversed(data_items):
            row = self.currentRow() + 1
            self.insertRow(row)
            self.populate_table_row(row, data)

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

class SettingsButton(QToolButton):
    def __init__(self, parent, plugin_action, query=None):
        QToolButton.__init__(self)
        self.config_dialog = parent
        self.plugin_action = plugin_action
        
        query_list_clean = []
        for qu in query[KEY.MENU_SEARCH_REPLACES]:
            if query_isValid(qu):
                query_list_clean.append(qu)
        
        query[KEY.MENU_SEARCH_REPLACES] = query_list_clean
        
        self.query = query
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setIcon(get_icon('gear.png'))
        self.update_text()
        self.setToolTip(_('Change operation list'))
        self.clicked.connect(self._clicked)
    
    def _clicked(self):
        d = ConfigSearchReplaceWidget(self, self.plugin_action, query=self.query)
        if d.exec_() == d.Accepted:
            self.query[KEY.MENU_SEARCH_REPLACES] = d.query_list
            self.update_text()
            
            if len(d.query_list)==0:
                debug_print('Saving a empty list')
            else:
                txt = 'Saved operation list:'
                for i, query in enumerate(d.query_list, 1):
                    txt += '\nOperation {:d} > {:s}'.format(i, query_string(query))
                txt += '\n[  '+ ',\n'.join( [str(query) for query in d.query_list] ) +'  ]\n'
                debug_print(txt)
                
            
    
    def update_text(self):
        self.setText(_('{:d} operations').format(len(self.query[KEY.MENU_SEARCH_REPLACES])))

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
            if not question_dialog(self, _('Are you sure?'), _('An image with this name already exists - overwrite it?'),
                    show_copy_button=False):
                return
        
        if self._radio_web.isChecked():
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


COL_CONFIG = [_('Columns'), _('Search mode'), _('Search'), _('Replace')]

class ConfigSearchReplaceWidget(Dialog):
    def __init__(self, parent, plugin_action, query=None):
        self.plugin_action = plugin_action
        name = query[KEY.MENU_TEXT]
        self.query_list = query[KEY.MENU_SEARCH_REPLACES]
        if self.query_list == None: self.query_list = []
        title = _('List of Search/Replace operations')
        if name:
            title = _('List of Search/Replace operations for {:s}').format(name)
        
        Dialog.__init__(self, title, 'config_list_SearchReplace', parent)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        heading_layout = QHBoxLayout()
        layout.addLayout(heading_layout)
        heading_label = QLabel(_('Select and configure the order of execution of the operations of Search/Replace operations:'), self)
        heading_layout.addWidget(heading_label)
        help_label = QLabel(' ', self)
        help_label.setTextInteractionFlags(Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)
        help_label.setAlignment(Qt.AlignRight)
        heading_layout.addWidget(help_label)
        
        # Add a horizontal layout containing the table and the buttons next to it
        table_layout = QHBoxLayout()
        layout.addLayout(table_layout)
        
        # Create a table the user can edit the data values in
        self._table = SearchReplaceTableWidget(self.plugin_action, self.query_list, self)
        heading_label.setBuddy(self._table)
        table_layout.addWidget(self._table)
        
        # Add a vertical layout containing the the buttons to move up/down etc.
        button_layout = QtGui.QVBoxLayout()
        table_layout.addLayout(button_layout)
        move_up_button = QtGui.QToolButton(self)
        move_up_button.setToolTip(_('Move operation up'))
        move_up_button.setIcon(QIcon(I('arrow-up.png')))
        button_layout.addWidget(move_up_button)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        button_layout.addItem(spacerItem)
        
        add_button = QtGui.QToolButton(self)
        add_button.setToolTip(_('Add operation'))
        add_button.setIcon(QIcon(I('plus.png')))
        button_layout.addWidget(add_button)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        button_layout.addItem(spacerItem1)
        
        copy_button = QtGui.QToolButton(self)
        copy_button.setToolTip(_('Copy operation'))
        copy_button.setIcon(QIcon(I('edit-copy.png')))
        button_layout.addWidget(copy_button)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        button_layout.addItem(spacerItem2)
        
        delete_button = QtGui.QToolButton(self)
        delete_button.setToolTip(_('Delete operation'))
        delete_button.setIcon(QIcon(I('minus.png')))
        button_layout.addWidget(delete_button)
        spacerItem3 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        button_layout.addItem(spacerItem3)
        
        move_down_button = QtGui.QToolButton(self)
        move_down_button.setToolTip(_('Move operation down'))
        move_down_button.setIcon(QIcon(I('arrow-down.png')))
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
        self.query_list = self._table.get_data()
        Dialog.accept(self)
        
    
    
    def create_context_menu(self, table):
        table.setContextMenuPolicy(Qt.ActionsContextMenu)
        act_import = QAction(get_icon(PLUGIN_ICONS[2]), _('&Import...'), table)
        act_import.triggered.connect(self.import_operations)
        table.addAction(act_import)
        act_export = QAction(get_icon(PLUGIN_ICONS[3]), _('&Export...'), table)
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
            
            if KEY.MENU_SEARCH_REPLACES not in import_config:
                return error_dialog(self, _('Import failed'), _('This is not a valid JSON file'), show=True)
            data_items = import_config[KEY.MENU_SEARCH_REPLACES]
            table.append_data(data_items)
            
            info_dialog(self, _('Import completed'), _('{:d} menu items imported').format(len(data_items), json_path),
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
        data_items = table.get_selected_data()
        if len(data_items) == 0:
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
            export_config[KEY.MENU_SEARCH_REPLACES] = data_items
            shutil.copyfile(json_temp, json_path)
            info_dialog(self, _('Export completed'), _('{:d} operations exported to\n{:s}').format(len(data_items), json_path),
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


class ReadOnlySearchReplaceTableWidgetItem(ReadOnlyTableWidgetItem):
    def __init__(self, text, query):
        ReadOnlyTableWidgetItem.__init__(self, text)
        self.query = query

class SearchReplaceTableWidget(QTableWidget):
    def __init__(self, plugin_action, query_list=None, *args):
        QTableWidget.__init__(self, *args)
        self.plugin_action = plugin_action
        self.populate_table(query_list)
        self.itemDoubleClicked.connect(self.settingsDoubleClicked)
    
    def populate_table(self, query_list=None):
        self.clear()
        if query_list == None: query_list = []
        self.setAlternatingRowColors(True)
        self.setColumnCount(len(COL_CONFIG))
        self.setHorizontalHeaderLabels(COL_CONFIG)
        self.verticalHeader().setDefaultSectionSize(24)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        query_list_clean = []
        for query in query_list:
            if query_isValid(query):
                query_list_clean.append(query)
            
        self.setRowCount(len(query_list_clean))
        for row, query in enumerate(query_list_clean):
            self.populate_table_row(row, query)
        
        self.resizeColumnsToContents()
        self.setSortingEnabled(False)
        self.setMinimumSize(800, 0)
        self.selectRow(0)
    
    def populate_table_row(self, row, query):
        self.blockSignals(True)
        
        self.setItem(row, 0, ReadOnlySearchReplaceTableWidgetItem('', query))
        
        for i in range(1, len(COL_CONFIG)):
            item = ReadOnlyTableWidgetItem('')
            self.setItem(row, i, item)
        
        self.update_row(row)
        
        self.blockSignals(False)
    
    def update_row(self, row):
        query = self.item(row, 0).query
        column = query[KEY_QUERY.SEARCH_FIELD]
        field = query[KEY_QUERY.DESTINATION_FIELD]
        if field and field != column:
            column += ' => '+ field
            
        self.item(row, 0).setText(column)
         
        self.item(row, 1).setText(query[KEY_QUERY.SEARCH_MODE])
        self.item(row, 2).setText(query[KEY_QUERY.SEARCH_FOR])
        self.item(row, 3).setText(query[KEY_QUERY.REPLACE_WITH])
        self.resizeColumnsToContents()
    
    def add_row(self):
        self.setFocus()
        # We will insert a blank row below the currently selected row
        row = self.currentRow() + 1
        self.insertRow(row)
        
        self.populate_table_row(row, self.create_blank_row_data())
        self.select_and_scroll_to_row(row)
    
    def copy_row(self):
        self.setFocus()
        row_data = self.convert_row_to_data(self.currentRow())
        # We will insert a blank row below the currently selected row
        row = self.currentRow() + 1
        self.insertRow(row)
        self.populate_table_row(row, row_data)
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
            self.item(dest_row, col, self.cellItem(src_row, col))
            
        self.removeRow(src_row)
        self.blockSignals(False)
    
    def select_and_scroll_to_row(self, row):
        self.selectRow(row)
        self.scrollToItem(self.currentItem())
    
    
    def create_blank_row_data(self):
        return get_default_query(self.plugin_action)
    
    def get_data(self):
        data_items = []
        for row in range(self.rowCount()):
            query = self.convert_row_to_data(row)
            if query_isValid(query):
                data_items.append(query)
                
        return data_items
    
    def convert_row_to_data(self, row):
        return self.item(row, 0).query
    
    def get_selected_data(self):
        data_items = []
        for row in self.selectionModel().selectedRows():
            data_items.append(self.convert_row_to_data(row.row()))
        return data_items
    
    def append_data(self, data_items):
        for data in reversed(data_items):
            row = self.currentRow() + 1
            self.insertRow(row)
            self.populate_table_row(row, data)
    
    
    def settingsDoubleClicked(self):
        self.setFocus()
        row = self.currentRow()
        
        query = self.item(row, 0).query
        
        d = SearchReplaceDialog(self, self.plugin_action, query)
        if d.exec_() == d.Accepted:
            self.item(row, 0).query = d.query
            self.update_row(row)

