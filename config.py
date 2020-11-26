#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2011, Grant Drake <grant.drake@gmail.com>'
__docformat__ = 'restructuredtext en'

import copy, os

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
                          QPushButton)
except:
    from PyQt4 import QtGui, QtCore
    from PyQt4.Qt import (Qt, QToolButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                          QIcon, QFormLayout, QAction, QFileDialog, QDialog, QTableWidget,
                          QTableWidgetItem, QAbstractItemView, QComboBox,
                          QGroupBox, QGridLayout, QRadioButton, QDialogButtonBox,
                          QPushButton)

from calibre.utils.config import JSONConfig
from calibre.gui2 import error_dialog, question_dialog, info_dialog, choose_files, open_local_file, FileDialog
from calibre.gui2.widgets2 import Dialog

from calibre_plugins.mass_search_replace.common_utils import NoWheelComboBox, KeyboardConfigDialog, ImageTitleLayout, get_library_uuid, debug_print, CSS_CleanRules

PLUGIN_ICONS = ['images/plugin.png', 'images/image_add.png']

COL_NAMES = ['', _('Title'), _('Submenu'), _('Image'), _('Settings'), 'chain_settings']

COMBO_IMAGE_ADD = _('Add New Image...')

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
PREFS.defaults[KEY.MASS_SEARCH_REPLACE] = None

class ConfigWidget(QWidget):
    
    def __init__(self, plugin_action):
        QWidget.__init__(self)
        
        self.plugin_action = plugin_action
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        heading_layout = QHBoxLayout()
        layout.addLayout(heading_layout)
        heading_label = QLabel(_('Select and configure the menu items to display:'), self)
        heading_layout.addWidget(heading_label)
        
        # Add a horizontal layout containing the table and the buttons next to it
        table_layout = QHBoxLayout()
        layout.addLayout(table_layout)
        
        # Create a table the user can edit the data values in
        self._table = MenuTableWidget(PREFS[KEY.MASS_SEARCH_REPLACE], self)
        heading_label.setBuddy(self._table)
        table_layout.addWidget(self._table)
        
        # Add a vertical layout containing the the buttons to move up/down etc.
        button_layout = QtGui.QVBoxLayout()
        table_layout.addLayout(button_layout)
        move_up_button = QtGui.QToolButton(self)
        move_up_button.setToolTip(_('Move row up'))
        move_up_button.setIcon(QIcon(I('arrow-up.png')))
        button_layout.addWidget(move_up_button)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        button_layout.addItem(spacerItem)
        
        add_button = QtGui.QToolButton(self)
        add_button.setToolTip(_('Add menu item row'))
        add_button.setIcon(QIcon(I('plus.png')))
        button_layout.addWidget(add_button)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        button_layout.addItem(spacerItem2)
        
        delete_button = QtGui.QToolButton(self)
        delete_button.setToolTip(_('Delete menu item row'))
        delete_button.setIcon(QIcon(I('minus.png')))
        button_layout.addWidget(delete_button)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        button_layout.addItem(spacerItem1)
        
        spacerItem3 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        button_layout.addItem(spacerItem3)
        
        move_down_button = QtGui.QToolButton(self)
        move_down_button.setToolTip(_('Move row down'))
        move_down_button.setIcon(QIcon(I('arrow-down.png')))
        button_layout.addWidget(move_down_button)
        
        move_up_button.clicked.connect(self._table.move_rows_up)
        move_down_button.clicked.connect(self._table.move_rows_down)
        add_button.clicked.connect(self._table.add_row)
        delete_button.clicked.connect(self._table.delete_rows)
        
        # --- Keyboard shortcuts ---
        keyboard_layout = QHBoxLayout()
        layout.addLayout(keyboard_layout)
        keyboard_shortcuts_button = QPushButton(_('Keyboard shortcuts...'), self)
        keyboard_shortcuts_button.setToolTip(_('Edit the keyboard shortcuts associated with this plugin'))
        keyboard_shortcuts_button.clicked.connect(self.edit_shortcuts)
        keyboard_layout.addWidget(keyboard_shortcuts_button)
        keyboard_layout.insertStretch(-1)
        
    
    def save_settings(self):
        
        names = []
        for r in self._table.get_data():
            name = r[self._table.header_labels[0]]
            if len(name)>0:
                names.append(name)
        if len(names) == 0:
            names = None
        PREFS[KEY.MASS_SEARCH_REPLACE] = names
        
        debug_print('Save settings: {0}\n'.format(PREFS))
        
    
    def edit_shortcuts(self):
        self.save_settings()
        self.plugin_action.build_menus()
        d = KeyboardConfigDialog(self.plugin_action.gui, self.plugin_action.action_spec[0])
        if d.exec_() == d.Accepted:
            self.plugin_action.gui.keyboard.finalize()
    
    
    def checkBox_click(self, num):
        
        b = not self.checkBoxDEL_FORMATTING.isChecked()
        
        self.comboBoxKEEP_URL.setEnabled(b)
        self.comboBoxHEADINGS.setEnabled(b)
        self.comboBoxFONT_WEIGHT.setEnabled(b)
        self.checkBoxDEL_ITALIC.setEnabled(b)
        self.checkBoxDEL_UNDER.setEnabled(b)
        self.checkBoxDEL_STRIKE.setEnabled(b)
        self.comboBoxFORCE_JUSTIFY.setEnabled(b)
        self.comboBoxLIST_ALIGN.setEnabled(b)
        self.comboBoxID_CLASS.setEnabled(b)
        self.lineEditCSS_KEEP.setEnabled(b)



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
        for i, image in enumerate(get_image_names(image_map)):
            self.insertItem(i, image_map.get(image, image), image)
        idx = self.findText(selected_text)
        self.setCurrentIndex(idx)
        #self.setItemData(0, QVariant(idx))
        self.setItemData(0, idx)

class SettingsButton(QToolButton):
    def __init__(self, parent, plugin_action, table_item):
        QToolButton.__init__(self)
        self.config_dialog = parent
        self.plugin_action = plugin_action
        self.table_item = table_item
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.setMaximumWidth(30)
        self.setIcon(get_icon('gear.png'))
        self.setToolTip(_('Change settings'))
        self.clicked.connect(self._clicked)
    
    def _clicked(self):
        chain = self.config_dialog.convert_row_to_data(self.table_item.row())
        d = ChainDialog(self, self.plugin_action, chain)
        if d.exec_() == d.Accepted:
            settings_string = json.dumps(d.chain_settings, default=to_json)
            self.table_item.setText(settings_string)

class MenuTableWidget(QTableWidget):

    def __init__(self, plugin_action, data_items, *args):
        QTableWidget.__init__(self, *args)
        self.plugin_action = plugin_action
        self.gui = plugin_action.gui
        self.populate_table(data_items)
        self.cellChanged.connect(self.cell_changed)

    def populate_table(self, data_items):
        self.clear()
        self.image_map = self.get_image_map()
        self.setAlternatingRowColors(True)
        self.setRowCount(len(data_items))

        self.setColumnCount(len(header_labels))
        self.setHorizontalHeaderLabels(COL_NAMES)
        self.verticalHeader().setDefaultSectionSize(24)

        # hide columns
        #hidden_cols = ['chain_settings','uuid']
        hidden_cols = ['chain_settings']
        for col in hidden_cols:
            idx = COL_NAMES.index(col)
            self.setColumnHidden(idx, True)

        for row, data in enumerate(data_items):
            self.populate_table_row(row, data)

        self.resizeColumnsToContents()
        self.setSortingEnabled(False)
        self.setMinimumSize(800, 0)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.selectRow(0)

    def populate_table_row(self, row, data):
        self.blockSignals(True)
        icon_name = data['image']
        menu_text = data['menuText']
        self.setItem(row, 0, CheckableTableWidgetItem(data['active']))
        self.setItem(row, 1, TextIconWidgetItem(menu_text, get_icon(icon_name)))
        self.setItem(row, 2, QTableWidgetItem(data['subMenu']))
        if menu_text:
            self.set_editable_cells_in_row(row, image=icon_name, chain_settings=data['chain_settings'])
        else:
            # Make all the later column cells non-editable
            self.set_noneditable_cells_in_row(row)
        self.blockSignals(False)

    def append_data(self, data_items):
        for data in reversed(data_items):
            row = self.currentRow() + 1
            self.insertRow(row)
            self.populate_table_row(row, data)

    def get_data(self):
        data_items = []
        for row in range(self.rowCount()):
            data_items.append(self.convert_row_to_data(row))
        # Remove any blank separator row items from the end as unneeded.
        while len(data_items) > 0 and len(data_items[-1]['menuText']) == 0:
            data_items.pop()
        return data_items

    def get_selected_data(self):
        data_items = []
        for row in self.selectionModel().selectedRows():
            data_items.append(self.convert_row_to_data(row.row()))
        return data_items

    def convert_row_to_data(self, row):
        data = self.create_blank_row_data()
        data['active'] = self.item(row, 0).checkState() == Qt.Checked
        data['menuText'] = unicode(self.item(row, 1).text()).strip()
        data['subMenu'] = unicode(self.item(row, 2).text()).strip()
        #data['uuid'] = unicode(self.item(row, 6).text()).strip()
        if data['menuText']:
            data['image'] = unicode(self.cellWidget(row, 3).currentText()).strip()
            data['chain_settings'] = json.loads(unicode(self.item(row, 5).text()).strip(), object_hook=from_json)
        return data

    def cell_changed(self, row, col):
        if col == 1:
            menu_text = unicode(self.item(row, col).text()).strip()
            self.blockSignals(True)
            if menu_text:
                # Make sure that the other columns in this row are enabled if not already.
                if not self.cellWidget(row, 4):
                    # We need to make later columns in this row editable
                    self.set_editable_cells_in_row(row)
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

    def set_editable_cells_in_row(self, row, image='', chain_settings={}):
        image_combo = ImageComboBox(self, self.image_map, image)
        image_combo.currentIndexChanged.connect(partial(self.image_combo_index_changed, image_combo, row))
        self.setCellWidget(row, 3, image_combo)
        chain_settings_item = QTableWidgetItem(json.dumps(chain_settings, default=to_json))
        self.setItem(row, 5, chain_settings_item)
        settings_button = SettingsButton(self, self.plugin_action, chain_settings_item)
        self.setCellWidget(row, 4, settings_button)

    def set_noneditable_cells_in_row(self, row):
        for col in range(3,6):
            if self.cellWidget(row, col):
                self.removeCellWidget(row, col)
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
            self.setItem(row, col, item)
        self.item(row, 1).setIcon(QIcon())

    def create_blank_row_data(self):
        data = {}
        data['active'] = True
        data['menuText'] = ''
        data['subMenu'] = ''
        data['image'] = ''
        data['chain_settings'] = '{}'
        #data['uuid'] = unicode(uuid4())
        return data

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
        # change name and uuid
        row_data['menuText'] = row_data['menuText'] + '(copy)'
        #row_data['uuid'] = unicode(uuid4())
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
        message = _('Are you sure you want to delete this menu item?')
        if len(rows) > 1:
            message = _('Are you sure you want to delete the selected %d menu items?'%len(rows))
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
            for col in range(3,6):
                if col == 3:
                    # Image column has a combobox we have to recreate as cannot move widget (Qt crap)
                    icon_name = self.cellWidget(src_row, col).currentText()
                    image_combo = ImageComboBox(self, self.image_map, icon_name)
                    image_combo.currentIndexChanged.connect(partial(self.image_combo_index_changed, image_combo, dest_row))
                    self.setCellWidget(dest_row, col, image_combo)
                elif col == 4:
                    settings_button = SettingsButton(self, self.plugin_action, self.item(src_row, 5))
                    self.setCellWidget(dest_row, col, settings_button)
                else:
                    # Any other column we transfer the TableWidgetItem
                    self.setItem(dest_row, col, self.takeItem(src_row, col))
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
        # Now read any images from the config\resources\images directory if any
        self.resources_dir = os.path.join(config_dir, 'resources/images')
        if iswindows:
            self.resources_dir = os.path.normpath(self.resources_dir)

        if os.path.exists(self.resources_dir):
            # Get the names of any .png images in this directory
            for f in os.listdir(self.resources_dir):
                if f.lower().endswith('.png'):
                    image_name = os.path.basename(f)
                    image_map[image_name] = get_icon(image_name)

        return image_map

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
        self._radio_file = QRadioButton('From .png &file', self)
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
            return error_dialog(self, 'Cannot select image', 'Source image must be a .png file.', show=True)
        self._input_file_edit.setText(f)
        self._save_as_edit.setText(os.path.splitext(os.path.basename(f))[0])

    def ok_clicked(self):
        # Validate all the inputs
        save_name = unicode(self._save_as_edit.text()).strip()
        if not save_name:
            return error_dialog(self, _('Cannot import image'), _('You must specify a filename to save as.'), show=True)
        self.new_image_name = os.path.splitext(save_name)[0] + '.png'
        if save_name.find('\\') > -1 or save_name.find('/') > -1:
            return error_dialog(self, 'Cannot import image', _('The save as filename should consist of a filename only.'), show=True)
        if not os.path.exists(self.resources_dir):
            os.makedirs(self.resources_dir)
        dest_path = os.path.join(self.resources_dir, self.new_image_name)
        if save_name in self.image_names or os.path.exists(dest_path):
            if not question_dialog(self, _('Are you sure?'), '<p>'+
                    _('An image with this name already exists - overwrite it?'),
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
                return error_dialog(self, 'Cannot import image', _('Source image must be a .png file.'), show=True)
            if not os.path.exists(source_file_path):
                return error_dialog(self, 'Cannot import image', _('Source image does not exist!'), show=True)
            shutil.copyfile(source_file_path, dest_path)
            return self.accept()



COL_CONFIG = [_('Columns'), _('Search mode'), _('Search'), _('Replace')]

class ConfigTableWidget(Dialog):
    
    def __init__(self, name, parent, data_items, title=_('Settings')):
        self.data_items = data_items
        self.widget_cls = ConfigTableWidget
        Dialog.__init__(self, title, name, parent)

    def setup_ui(self):
        self.widget = self.widget_cls(self.data_items)
        l = QVBoxLayout()
        self.setLayout(l)
        l.addWidget(self.widget)
        l.addWidget(self.bb)
    
    def accept(self):
        self.settings = self.widget.save_settings()
        # validate settings
        is_valid = self.action.validate(self.settings)
        if is_valid is not True:
            msg, details = is_valid
            error_dialog(self, msg, details, show=True)
            return
        Dialog.accept(self)


class ConfigTableWidget(QTableWidget):
    
    def __init__(self, data_items=None, *args):
        QTableWidget.__init__(self, *args)
        if data_items == None: data_items = []
        self.populate_table(data_items)
        self.cellChanged.connect(self.cell_changed)
    
    def populate_table(self, data_items):
        self.clear()
        
        self.setAlternatingRowColors(True)
        self.setColumnCount(len(COL_CONFIG))
        self.setHorizontalHeaderLabels(COL_CONFIG)
        self.verticalHeader().setDefaultSectionSize(24)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setRowCount(len(data_items))
        for row, data in enumerate(data_items):
            self.populate_table_row(row, data)
        
        self.resizeColumnsToContents()
        self.setSortingEnabled(False)
        self.setMinimumSize(800, 0)
        self.selectRow(0)
    
    def populate_table_row(self, row, data):
        self.blockSignals(True)
        
        item = TableComboBox(self, data)
        item.currentIndexChanged.connect(self._comboBoxIndexChanged)
        self.setCellWidget(row, 0, item)
        
        for i in range(1, len(COL_CONFIG)):
            item = QTableWidgetItem('', QtGui.QTableWidgetItem.UserType)
            item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
            self.setItem(row, i, item)
        
        self.update_row(row)
        
        self.blockSignals(False)
    
    def get_data(self):
        data_items = []
        for row in range(self.rowCount()):
            data_items.append(self.convert_row_to_data(row))
        return data_items
    
    def convert_row_to_data(self, row):
        data = self.create_blank_row_data()
        for col, name in enumerate(COL_CONFIG, 0) :
            if col==0:
                data[name] = self.cellWidget(row, col).currentText()
            else:
                data[name] = self.item(row, col).text()
        return data
    
    def cell_changed(self, row, col):
        if col==0:
            self.update_row(row)
    
    def _comboBoxIndexChanged(self, index):
        for selectedRow in self.selectionModel().selectedRows():
            self.update_row(selectedRow.row())
    
    def update_row(self, row):
        data = None
        if self.cellWidget(row, 0).currentIndex() != 0:
            current_data = self.cellWidget(row, 0).currentText()
            for key, value in QUERY_DIC.items():
                if value == current_data:
                    data = key
            querie = QUERIES[data]
        
        for i in range(1, len(COL_CONFIG)):
            txt = ''
            if data:
                if i==1:
                    txt = querie['search_field']
                    field = querie['destination_field']
                    if field != None and len(field)>0:
                        txt +=' => '+field
                     
                elif i==2:
                    txt = querie['search_mode']
                elif i==3:
                    txt = querie['search_for']
                elif i==4:
                    txt = querie['replace_with']
            
            self.item(row, i).setText(txt)
            
    
    def create_blank_row_data(self):
        data = {}
        for name in COL_CONFIG:
            data[name] = ''
        return data
    
    def add_row(self):
        self.setFocus()
        # We will insert a blank row below the currently selected row
        row = self.currentRow() + 1
        self.insertRow(row)
        self.populate_table_row(row, '')
        self.select_and_scroll_to_row(row)
    
    def delete_rows(self):
        self.setFocus()
        rows = self.selectionModel().selectedRows()
        if len(rows) == 0:
            return
        message = _('Are you sure you want to delete this item?')
        if len(rows) > 1:
            message = _('Are you sure you want to delete the selected {0} items?').format(len(rows))
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
            if col==0:
                self.setCellWidget(dest_row, col, self.cellWidget(src_row, col))
            else:
                self.setItem(dest_row, col, self.takeItem(src_row, col))
        self.removeRow(src_row)
        self.blockSignals(False)
    
    def select_and_scroll_to_row(self, row):
        self.selectRow(row)
        self.scrollToItem(self.currentItem())
    
    def move_active_to_top(self):
        # Select all of the inactive items and move them to the bottom of the list
        if self.rowCount() == 0:
            return
        self.setUpdatesEnabled(False)
        last_row = self.rowCount()
        row = 0
        for count in range(last_row):
            active = self.item(row, 0).checkState() == Qt.Checked
            if active:
                # Move on to the next row
                row = row + 1
            else:
                # Move this row to the bottom of the grid
                self.swap_row_widgets(row, last_row)
        self.setUpdatesEnabled(True)
    
    
    def _settings_button_clicked(self):
        action_name = self.action_combo_box.currentText()
        config_widget = SearchReplaceWidget(self.plugin_action, [], set())
        name = 'ActionsChain::{}'.format(action_name)
        title = '{}'.format(action_name)
        d = SettingsWidgetDialog(name, self, self.plugin_action, config_widget, title)
        # inject copy of chain data into the settings dialog, for internal use only
        d._chain = copy.deepcopy(self.chain)
        if self.action_settings:
            d.load_settings(self.action_settings)
        if d.exec_() == d.Accepted:
            self.action_settings = d.settings
            # reset any previous error if present
            self.error_w.reset_error()

class SettingsWidgetDialog(Dialog):
    def __init__(self, name, parent, plugin_action, widget_cls, title=_('Settings')):
        self.plugin_action = plugin_action
        self.widget_cls = widget_cls
        Dialog.__init__(self, title, name, parent)

    def setup_ui(self):
        self.widget = self.widget_cls(self.plugin_action)
        l = QVBoxLayout()
        self.setLayout(l)
        l.addWidget(self.widget)
        l.addWidget(self.bb)
    
    def load_settings(self, settings):
        self.widget.load_settings(settings)
    
    def accept(self):
        self.settings = self.widget.save_settings()
        # validate settings
        is_valid = self.action.validate(self.settings)
        if is_valid is not True:
            msg, details = is_valid
            error_dialog(self, msg, details, show=True)
            return
        Dialog.accept(self)
