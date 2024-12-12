#!/usr/bin/env python

__license__   = 'GPL v3'
__copyright__ = '2020, un_pogaz <un.pogaz@gmail.com>'


try:
    load_translations()
except NameError:
    pass  # load_translations() added in calibre 1.9

import copy
import json
import os
from functools import partial
from typing import Any, Dict, List

try:
    from qt.core import (
        QAbstractItemView,
        QAction,
        QCheckBox,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSizePolicy,
        QSpacerItem,
        Qt,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PyQt5.Qt import (
        QAbstractItemView,
        QAction,
        QCheckBox,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSizePolicy,
        QSpacerItem,
        Qt,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )

from calibre.gui2 import FileDialog, choose_files, error_dialog, info_dialog, open_local_file, question_dialog
from calibre.gui2.widgets2 import Dialog
from calibre.utils.config import JSONConfig
from calibre.utils.zipfile import ZipFile
from polyglot.builtins import unicode_type

from .common_utils import CALIBRE_VERSION, GUI, PREFS_json, debug_print, get_icon, get_image_map, local_resource
from .common_utils.dialogs import ImageDialog, KeyboardConfigDialogButton
from .common_utils.librarys import get_BookIds_selected
from .common_utils.templates import TEMPLATE_FIELD
from .common_utils.widgets import (
    CheckableTableWidgetItem,
    ImageComboBox,
    KeyValueComboBox,
    ReadOnlyTableWidgetItem,
    TextIconWidgetItem,
)
from .search_replace import KEY_QUERY, Operation, SearchReplaceDialog, clean_empty_operation


class ICON:
    PLUGIN    = 'images/plugin.png'
    ADD_IMAGE = 'images/image_add.png'
    EXPORT    = 'images/export.png'
    IMPORT    = 'images/import.png'
    WARNING   = 'images/warning.png'

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
    USE_MARK = 'UseMark'

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
    SAFELY_DESC = (safely_txt+'\n'+
    _('When a error occurs, stop Mass Search/Replace and display the error normally without further action.'))
    
    DONT_STOP = "don't stop"
    DONT_STOP_NAME = _("Don't stop (slower, not recomanded)")
    DONT_STOP_DESC = (safely_txt+'\n'+
    _('Update the library, no matter how many errors are encountered. The problematics fields will not be updated.'))
    
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
PREFS.defaults[KEY_MENU.USE_MARK] = True

PREFS.defaults[KEY_ERROR.ERROR] = {
    KEY_ERROR.OPERATION : ERROR_UPDATE.DEFAULT,
    KEY_ERROR.UPDATE : ERROR_OPERATION.DEFAULT
}

OWIP = 'owip'


def get_default_menu() -> Dict[str, Any]:
    menu = {}
    menu[KEY_MENU.ACTIVE] = True
    menu[KEY_MENU.TEXT] = ''
    menu[KEY_MENU.SUBMENU] = ''
    menu[KEY_MENU.IMAGE] = ''
    menu[KEY_MENU.OPERATIONS] = []
    return menu

class ConfigWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        menu_list = []
        for menu in PREFS[KEY_MENU.MENU]:
            menu[KEY_MENU.OPERATIONS] = [Operation(o) for o in menu[KEY_MENU.OPERATIONS]]
            menu_list.append(menu)
        
        heading_layout = QHBoxLayout()
        layout.addLayout(heading_layout)
        heading_label = QLabel(_('Select and configure the menu items to display:'), self)
        heading_layout.addWidget(heading_label)
        
        # Add a horizontal layout containing the table and the buttons next to it
        table_layout = QHBoxLayout()
        layout.addLayout(table_layout)
        
        # Create a table the user can edit the menu list
        self.table = MenuTableWidget(menu_list, self)
        heading_label.setBuddy(self.table)
        table_layout.addWidget(self.table)
        
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
        
        move_up_button.clicked.connect(self.table.move_rows_up)
        move_down_button.clicked.connect(self.table.move_rows_down)
        add_button.clicked.connect(self.table.add_row)
        delete_button.clicked.connect(self.table.delete_rows)
        copy_button.clicked.connect(self.table.copy_row)
        
        # --- Keyboard shortcuts ---
        keyboard_layout = QHBoxLayout()
        layout.addLayout(keyboard_layout)
        keyboard_layout.addWidget(KeyboardConfigDialogButton(parent=self))
        keyboard_layout.insertStretch(-1)
        
        if CALIBRE_VERSION >= (5,41,0):
            self.useMark = QCheckBox(_('Mark the updated books'), self)
            self.useMark.setChecked(PREFS[KEY_MENU.USE_MARK])
            keyboard_layout.addWidget(self.useMark)
        
        self.updateReport = QCheckBox(_('Display a update report'), self)
        self.updateReport.setChecked(PREFS[KEY_MENU.UPDATE_REPORT])
        keyboard_layout.addWidget(self.updateReport)
        
        error_button = QPushButton(_('Error strategy')+'…', self)
        error_button.setToolTip(_('Define the strategy when a error occurs during the library update'))
        error_button.clicked.connect(self.edit_error_strategy)
        keyboard_layout.addWidget(error_button)
    
    def save_settings(self):
        PREFS[KEY_MENU.MENU] = self.table.get_menu_list()
        PREFS[KEY_MENU.UPDATE_REPORT] = self.updateReport.checkState() == Qt.Checked
        if CALIBRE_VERSION >= (5,41,0):
            PREFS[KEY_MENU.USE_MARK] = self.useMark.checkState() == Qt.Checked
        debug_print('Save settings: menu operation count:', len(PREFS[KEY_MENU.MENU]), '\n')
        #debug_print('Save settings:\n', PREFS, '\n')
    
    def edit_error_strategy(self):
        d = ErrorStrategyDialog()
        if d.exec():
            PREFS[KEY_ERROR.ERROR] = {
                KEY_ERROR.OPERATION : d.error_operation,
                KEY_ERROR.UPDATE : d.error_update
            }
            
            debug_print('Error Strategy settings:', PREFS[KEY_ERROR.ERROR], '\n')


COL_NAMES = ['', _('Name'), _('Submenu'), _('Image'), _('Operation')]
class MenuTableWidget(QTableWidget):
    def __init__(self, menu_list=None, *args):
        QTableWidget.__init__(self, *args)
        
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSortingEnabled(False)
        self.setMinimumSize(600, 0)
        
        self.append_context_menu(self)
        
        self.image_map = get_image_map()
        
        self.populate_table(menu_list)
        
        self.cellChanged.connect(self.cell_changed)
    
    def append_context_menu(self, parent):
        parent.setContextMenuPolicy(Qt.ActionsContextMenu)
        
        act_add_image = QAction(get_icon(ICON.ADD_IMAGE), _('&Add image…'), parent)
        act_add_image.triggered.connect(self.add_new_image_dialog)
        parent.addAction(act_add_image)
        
        act_open = QAction(get_icon('document_open.png'), _('&Open images folder'), parent)
        act_open.triggered.connect(self.open_images_folder)
        parent.addAction(act_open)
        
        sep2 = QAction(parent)
        sep2.setSeparator(True)
        parent.addAction(sep2)
        
        act_import = QAction(get_icon(ICON.IMPORT), _('&Import…'), parent)
        act_import.triggered.connect(self.import_menus)
        parent.addAction(act_import)
        
        act_export = QAction(get_icon(ICON.EXPORT), _('&Export…'), parent)
        act_export.triggered.connect(self.export_menus)
        parent.addAction(act_export)
    
    
    def open_images_folder(self):
        if not os.path.exists(local_resource.IMAGES):
            os.makedirs(local_resource.IMAGES)
        open_local_file(local_resource.IMAGES)
    
    def import_menus(self):
        archive_path = self.pick_archive_to_import()
        if not archive_path:
            return
        
        json_name = OWIP+'.json'
        
        # Write the whole file contents into the resources\images directory
        if not os.path.exists(local_resource.IMAGES):
            os.makedirs(local_resource.IMAGES)
        with ZipFile(archive_path, 'r') as zf:
            contents = zf.namelist()
            if json_name not in contents:
                return error_dialog(self, _('Import failed'), _('This is not a valid OWIP export archive'), show=True)
            for resource in contents:
                if resource == json_name:
                    json_import = json.loads(zf.read(resource))
                else:
                    fs = os.path.join(local_resource.IMAGES, resource)
                    with open(fs,'wb') as f:
                        f.write(zf.read(resource))
        
        try:
            # Read the .JSON file to add to the menus then delete it.
            menu_list = json_import[KEY_MENU.MENU]
            for idx in range(len(menu_list)):
                menu_list[idx][KEY_MENU.OPERATIONS] = [Operation(e) for e in menu_list[idx][KEY_MENU.OPERATIONS]]
            # Now insert the menus into the table
            self.append_menu_list(menu_list)
            info_dialog(self, _('Import completed'), _('{:d} menu items imported').format(len(menu_list)),
                        show=True, show_copy_button=False)
        except Exception as e:
            return error_dialog(self, _('Import failed'), e, show=True)
    
    def pick_archive_to_import(self) -> str:
        archives = choose_files(self,
            name='owip archive dialog',
            title=_('Select a menu file archive to import…'),
            filters=[('OWIP Files', ['owip','owip.zip']), ('ZIP Files', ['owip','zip'])],
            all_files=False, select_only_single_file=True,
        )
        if not archives:
            return
        f = archives[0]
        return f
    
    def export_menus(self):
        menu_list = [m for m in self.get_selected_menu() if m['Text']]
        if len(menu_list) == 0:
            return error_dialog(self, _('Export failed'), _('No menu items selected to export'), show=True)
        archive_path = self.pick_archive_to_export()
        if not archive_path:
            return
        
        # Build our unique list of images that need to be exported
        image_map = {}
        for menu in menu_list:
            image_name = menu[KEY_MENU.IMAGE]
            if image_name and image_name not in image_map:
                image_path = I(image_name)
                if os.path.exists(image_path):
                    image_map[image_name] = image_path
        
        try:
            # Create the zip file archive
            with ZipFile(archive_path, 'w') as archive_zip:
                archive_zip.writestr(OWIP+'.json', json.dumps({KEY_MENU.MENU: menu_list}))
                # Add any images referred to in those menu items that are local resources
                for image_name, image_path in image_map.items():
                    archive_zip.write(image_path, os.path.basename(image_path))
            
            info_dialog(self,
                _('Export completed'),
                _('{:d} menu items exported to\n{:s}').format(len(menu_list), archive_path),
                show=True, show_copy_button=False,
            )
        except Exception as e:
            return error_dialog(self, _('Export failed'), e, show=True)
    
    def pick_archive_to_export(self) -> str:
        fd = FileDialog(parent=self,
            name='owip archive dialog',
            title=_('Save menu archive as…'),
            filters=[('OWIP Files', ['owip.zip']), ('ZIP Files', ['zip'])],
            add_all_files_filter=False, mode=QFileDialog.FileMode.AnyFile,
        )
        fd.setParent(None)
        if not fd.accepted:
            return None
        return fd.get_files()[0]
    
    
    def populate_table(self, menu_list=None):
        self.clear()
        self.setColumnCount(len(COL_NAMES))
        self.setHorizontalHeaderLabels(COL_NAMES)
        self.verticalHeader().setDefaultSectionSize(24)
        
        menu_list = menu_list or []
        self.setRowCount(len(menu_list))
        for row, menu in enumerate(menu_list, 0):
            self.populate_table_row(row, menu)
        
        self.selectRow(-1)
    
    def populate_table_row(self, row, menu):
        self.blockSignals(True)
        icon_name = menu[KEY_MENU.IMAGE]
        menu_text = menu[KEY_MENU.TEXT]
        
        self.setItem(row, 0, CheckableTableWidgetItem(menu[KEY_MENU.ACTIVE]))
        self.setItem(row, 1, TextIconWidgetItem(menu_text, icon_name))
        self.setItem(row, 2, QTableWidgetItem(menu[KEY_MENU.SUBMENU]))
        if menu_text:
            self.set_editable_cells_in_row(row, icon_name=icon_name, menu=menu)
        else:
            # Make all the later column cells non-editable
            self.set_noneditable_cells_in_row(row)
        
        self.resizeColumnsToContents()
        self.blockSignals(False)
    
    def cell_changed(self, row, col):
        self.blockSignals(True)
        
        if col == 1 or col == 2:
            menu_text = self.item(row, col).text().strip()
            self.item(row, col).setText(menu_text)
        
        if self.item(row, 1).text():
            # Make sure that the other columns in this row are enabled if not already.
            if not self.cellWidget(row, len(COL_NAMES)-1):
                self.set_editable_cells_in_row(row)
            self.cellWidget(row, 4).set_menu(self.convert_row_to_menu(row))
        else:
            # Blank menu text so treat it as a separator row
            self.set_noneditable_cells_in_row(row)
        
        self.resizeColumnsToContents()
        self.blockSignals(False)
    
    def image_combo_index_changed(self, combo, row):
        # Update image on the title column
        title_item = self.item(row, 1)
        title_item.setIcon(combo.itemIcon(combo.currentIndex()))
    
    def create_image_combo_box(self, row, icon_name=None) -> ImageComboBox:
        rslt = ImageComboBox(self.image_map, icon_name)
        rslt.currentIndexChanged.connect(partial(self.image_combo_index_changed, rslt, row))
        rslt.new_image_added.connect(self.update_all_image_combo_box)
        self.append_context_menu(rslt)
        return rslt
    
    def set_editable_cells_in_row(self, row, icon_name=None, menu=None):
        self.setCellWidget(row, 3, self.create_image_combo_box(row, icon_name))
        menu = menu or get_default_menu()
        self.setCellWidget(row, 4, SettingsButton(self, menu))
    
    def set_noneditable_cells_in_row(self, row):
        for col in range(3, len(COL_NAMES)):
            if self.cellWidget(row, col):
                self.removeCellWidget(row, col)
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.setItem(row, col, item)
        self.item(row, 1).setIcon(get_icon(None))
    
    def add_new_image_dialog(self):
        d = ImageDialog(existing_images=self.image_map.keys())
        if d.exec():
            self.update_all_image_combo_box(d.image_name)
    
    def update_all_image_combo_box(self, new_image):
        self.image_map[new_image] = get_icon(new_image)
        self.image_map = {k:self.image_map[k] for k in sorted(self.image_map.keys())}
        for update_row in range(self.rowCount()):
            cellCombo = self.cellWidget(update_row, 3)
            if cellCombo:
                cellCombo.blockSignals(True)
                cellCombo.populate_combo(self.image_map, cellCombo.currentText())
                cellCombo.blockSignals(False)
    
    def add_row(self):
        self.setFocus()
        # We will insert a blank row below the currently selected row
        row = self.currentRow() + 1
        self.insertRow(row)
        self.populate_table_row(row, get_default_menu())
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
            scroll_to_row += 1
        self.scrollToItem(self.item(scroll_to_row, 0))
    
    def swap_row_widgets(self, src_row, dest_row):
        self.blockSignals(True)
        self.insertRow(dest_row)
        
        for col in range(0,3):
            self.setItem(dest_row, col, self.takeItem(src_row, col))
        
        menu_text = self.item(dest_row, 1).text().strip()
        if menu_text:
            for col in range(3, len(COL_NAMES)):
                if col == 3:
                    # Image column has a combobox we have to recreate as cannot move widget (Qt crap)
                    icon_name = self.cellWidget(src_row, col).currentText()
                    self.setCellWidget(dest_row, col, self.create_image_combo_box(dest_row, icon_name))
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
    
    def get_menu_list(self) -> List[Dict[str, Any]]:
        menu_list = []
        for row in range(self.rowCount()):
            menu_list.append(self.convert_row_to_menu(row))
        
        # Remove any blank separator row items from at the start and the end
        while len(menu_list) > 0 and not menu_list[-1][KEY_MENU.TEXT]:
            menu_list.pop()
        while len(menu_list) > 0 and not menu_list[0][KEY_MENU.TEXT]:
            menu_list.pop(0)
        return menu_list
    
    def convert_row_to_menu(self, row) -> Dict[str, Any]:
        menu = get_default_menu()
        menu[KEY_MENU.ACTIVE] = self.item(row, 0).checkState() == Qt.Checked
        menu[KEY_MENU.TEXT] = self.item(row, 1).text().strip()
        menu[KEY_MENU.SUBMENU] = self.item(row, 2).text().strip()
        if menu[KEY_MENU.TEXT]:
            menu[KEY_MENU.IMAGE] = self.cellWidget(row, 3).currentText().strip()
            menu[KEY_MENU.OPERATIONS] = self.cellWidget(row, 4).get_operation_list()
        return menu
    
    def get_selected_menu(self) -> List[Dict[str, Any]]:
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
        self.set_menu(menu)
    
    def set_menu(self, menu):
        self._menu = menu
        self.update_text()
        self.has_error()
    
    def get_menu(self) -> Dict[str, Any]:
        return copy.copy(self._menu)
    
    def update_text(self):
        count = len(self.get_operation_list())
        active = 0
        for operation in self.get_operation_list():
            if operation.get(KEY_QUERY.ACTIVE, True):
                active += 1
        
        txt = ''
        if active < count:
            txt = _('{:d}/{:d} operations').format(active, count)
        else:
            txt = _('{:d} operations').format(count)
        
        if self.get_has_changed():
            txt+='*'
        self.setText(txt)
    
    def has_error(self) -> bool:
        has_error = False
        
        for operation in self.get_operation_list():
            if operation.get_error():
                has_error = True
                break
        
        if has_error:
            self.setIcon(get_icon(ICON.WARNING))
            self.setToolTip(_('This operations list contain a error'))
        else:
            self.setIcon(get_icon('gear.png'))
            self.setToolTip(_('Edit the operations list'))
        
        return has_error
    
    def get_has_changed(self) -> bool:
        op_lst = self.get_operation_list()
        initial_op_lst = self._initial_menu[KEY_MENU.OPERATIONS]
        if len(op_lst) != len(initial_op_lst):
            return True
        
        for i in range(0, len(op_lst)):
            if op_lst[i].get(KEY_QUERY.ACTIVE, True) != initial_op_lst[i].get(KEY_QUERY.ACTIVE, True):
                return True
            
            for key in KEY_QUERY.ALL:
                if op_lst[i][key] != initial_op_lst[i][key]:
                    return True
        
        return False
    
    def set_operation_list(self, operation_list):
        self._menu[KEY_MENU.OPERATIONS] = operation_list
        self.set_menu(self._menu)
    
    def get_operation_list(self) -> List[Operation]:
        return copy.copy(self._menu[KEY_MENU.OPERATIONS])
    
    def _clicked(self):
        d = ConfigOperationListDialog(self.get_menu())
        if d.exec():
            self.set_operation_list(d.operation_list)


COL_CONFIG = ['', _('Name'), _('Columns'), _('Template'), _('Search mode'), _('Search'), _('Replace')]
class ConfigOperationListDialog(Dialog):
    def __init__(self, menu, book_ids=None):
        menu = menu or get_default_menu()
        name = menu[KEY_MENU.TEXT]
        sub_menu = menu[KEY_MENU.SUBMENU]
        self.operation_list = menu[KEY_MENU.OPERATIONS]
        self.book_ids = book_ids
        
        title = ''
        if not name:
            title = _('List of operations for a quick Search/Replaces')
        else:
            if sub_menu:
                name = f'{sub_menu} > {name}'
            
            title = _('List of Search/Replace operations for {:s}').format(name)
        
        Dialog.__init__(self,
            title=title,
            name='plugin.MassSearchReplace:config_list_SearchReplace',
            parent=GUI,
        )
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        heading_layout = QHBoxLayout()
        layout.addLayout(heading_layout)
        heading_label = QLabel(
            _('Select and configure the order of execution of the operations of Search/Replace operations:'),
            self,
        )
        heading_layout.addWidget(heading_label)
        #help_label = QLabel(' ', self)
        #help_label.setTextInteractionFlags(Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)
        #help_label.setAlignment(Qt.AlignRight)
        #heading_layout.addWidget(help_label)
        
        # Add a horizontal layout containing the table and the buttons next to it
        table_layout = QHBoxLayout()
        layout.addLayout(table_layout)
        
        # Create a table the user can edit the operation list
        self.table = OperationListTableWidget(self.operation_list, self.book_ids, self)
        heading_label.setBuddy(self.table)
        table_layout.addWidget(self.table)
        
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
        
        move_up_button.clicked.connect(self.table.move_rows_up)
        move_down_button.clicked.connect(self.table.move_rows_down)
        add_button.clicked.connect(self.table.add_row)
        delete_button.clicked.connect(self.table.delete_rows)
        copy_button.clicked.connect(self.table.copy_row)
        
        # -- Accept/Reject buttons --
        layout.addWidget(self.bb)
    
    def add_empty_operation(self):
        self.table.add_row()
    
    def accept(self):
        self.operation_list = self.table.get_operation_list()
        
        if len(self.operation_list)==0:
            debug_print('Saving a empty list')
        else:
            txt = 'Saved operation list:\n' + '\n'.join(
                (f'Operation {i} > '+ operation.string_info()) for i, operation in enumerate(self.operation_list, 1)
            )
            #txt += '\n[  '+ ',\n'.join( [str(operation) for operation in self.operation_list] ) +'  ]\n'
            debug_print(txt)
        
        Dialog.accept(self)

class OperationListTableWidget(QTableWidget):
    def __init__(self, operation_list=None, book_ids=None, *args):
        QTableWidget.__init__(self, *args)
        
        self.book_ids = (book_ids or get_BookIds_selected(show_error=False))[:10]
        
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSortingEnabled(False)
        self.setMinimumSize(800, 0)
        
        self.append_context_menu()
        
        self.populate_table(operation_list)
        
        self.itemDoubleClicked.connect(self.settings_doubleClick)
    
    def append_context_menu(self):
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        act_import = QAction(get_icon(ICON.IMPORT), _('&Import…'), self)
        act_import.triggered.connect(self.import_operations)
        self.addAction(act_import)
        
        act_export = QAction(get_icon(ICON.EXPORT), _('&Export…'), self)
        act_export.triggered.connect(self.export_operations)
        self.addAction(act_export)
    
    
    def import_operations(self):
        json_path = self.pick_json_to_import()
        if not json_path:
            return
        
        try:
            with open(json_path) as fr:
                json_import = json.load(fr)
            
            if KEY_MENU.OPERATIONS not in json_import:
                return error_dialog(self, _('Import failed'), _('This is not a valid JSON file'), show=True)
            operation_list = [Operation(e) for e in json_import[KEY_MENU.OPERATIONS]]
            self.append_operation_list(operation_list)
            
            info_dialog(self,
                _('Import completed'),
                _('{:d} menu items imported').format(len(operation_list), json_path),
                show=True, show_copy_button=False,
            )
        except Exception as e:
            return error_dialog(self, _('Export failed'), e, show=True)
    
    def pick_json_to_import(self) -> str:
        archives = choose_files(self,
            name='json dialog',
            title=_('Select a JSON file to import…'),
            filters=[('JSON List Files', ['list.json']), ('JSON Files', ['json'])],
            all_files=False, select_only_single_file=True,
        )
        if not archives:
            return
        f = archives[0]
        return f
    
    def export_operations(self):
        operation_list = self.get_selected_operation()
        if len(operation_list) == 0:
            return error_dialog(self, _('Export failed'), _('No operations selected to export'), show=True)
        json_path = self.pick_json_to_export()
        if not json_path:
            return
        
        try:
            with open(json_path, 'w') as fw:
                json.dump({KEY_MENU.OPERATIONS: operation_list}, fw)
            info_dialog(self,
                _('Export completed'),
                _('{:d} operations exported to\n{:s}').format(len(operation_list), json_path),
                show=True, show_copy_button=False,
            )
        except Exception as e:
            return error_dialog(self, _('Export failed'), e, show=True)
    
    def pick_json_to_export(self) -> str:
        fd = FileDialog(parent=self,
            name='json dialog',
            title=_('Save the operations as…'),
            filters=[('JSON List Files', ['list.json']), ('JSON Files', ['json'])],
            add_all_files_filter=False, mode=QFileDialog.FileMode.AnyFile,
        )
        fd.setParent(None)
        if not fd.accepted:
            return None
        return fd.get_files()[0]
    
    
    def populate_table(self, operation_list=None):
        self.clear()
        self.setColumnCount(len(COL_CONFIG))
        self.setHorizontalHeaderLabels(COL_CONFIG)
        self.verticalHeader().setDefaultSectionSize(24)
        
        operation_list = clean_empty_operation(operation_list)
        calibre_queries = JSONConfig("search_replace_queries")
        
        self.setRowCount(len(operation_list))
        for row, operation in enumerate(operation_list):
            is_active = operation[KEY_QUERY.ACTIVE]
            calibre_operation = calibre_queries.get(unicode_type(operation.get(KEY_QUERY.NAME, None)))
            if calibre_operation:
                operation = Operation(calibre_operation)
            operation[KEY_QUERY.ACTIVE] = is_active
            
            self.populate_table_row(row, operation)
        
        self.test_column_hidden()
        
        self.selectRow(-1)
    
    def populate_table_row(self, row, operation):
        self.blockSignals(True)
        
        self.setItem(row, 0, OperationWidgetItem(self, operation))
        
        for i in range(1, len(COL_CONFIG)):
            item = ReadOnlyTableWidgetItem('')
            self.setItem(row, i, item)
        
        self.update_row(row)
        
        self.resizeColumnsToContents()
        self.blockSignals(False)
    
    def test_column_hidden(self):
        no_name = True
        no_template = True
        for i_row in range(self.rowCount()):
            item = self.item(i_row, 0)
            operation = item.get_operation() if item else {}
            if no_name and operation.get(KEY_QUERY.NAME, ''):
                no_name = False
            if no_template and operation.get(KEY_QUERY.SEARCH_FIELD, '') == TEMPLATE_FIELD:
                no_template = False
        
        self.setColumnHidden(1, no_name)
        self.setColumnHidden(3, no_template)
        self.resizeColumnsToContents()
    
    def update_row(self, row):
        operation = self.convert_row_to_operation(row)
        
        for col, val in enumerate(operation.get_para_list(), 1):
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
            scroll_to_row += 1
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
    
    def create_blank_row_operation(self) -> Operation:
        return Operation()
    
    def get_operation_list(self) -> List[Operation]:
        operation_list = []
        for row in range(self.rowCount()):
            operation = self.convert_row_to_operation(row)
            operation_list.append(operation)
       
        return clean_empty_operation(operation_list)
    
    def convert_row_to_operation(self, row) -> Operation:
        return self.item(row, 0).get_operation()
    
    def get_selected_operation(self) -> List[Operation]:
        operation_list = []
        for row in self.selectionModel().selectedRows():
            operation_list.append(self.convert_row_to_operation(row.row()))
        return clean_empty_operation(operation_list)
    
    def append_operation_list(self, operation_list):
        for operation in reversed(clean_empty_operation(operation_list)):
            row = self.currentRow() + 1
            self.insertRow(row)
            self.populate_table_row(row, operation)
        
        self.test_column_hidden()
    
    
    def settings_doubleClick(self):
        self.setFocus()
        row = self.currentRow()
        
        src_operation = self.convert_row_to_operation(row)
        d = SearchReplaceDialog(src_operation, self.book_ids)
        if d.exec():
            d.operation[KEY_QUERY.ACTIVE] = src_operation.get(KEY_QUERY.ACTIVE, True)
            self.populate_table_row(row, d.operation)
        
        self.test_column_hidden()

class OperationWidgetItem(QTableWidgetItem):
    def __init__(self, table, operation):
        QTableWidgetItem.__init__(self, '')
        self.setFlags(Qt.ItemFlag(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled ))
        
        self.table = table
        self._operation = operation
        self._has_error = False
        self.set_operation(operation)
    
    def set_operation(self, operation):
        operation = operation or Operation()
        self._operation = operation
        
        checked = self._operation.get(KEY_QUERY.ACTIVE, True)
        if checked:
            self.setCheckState(Qt.Checked)
        else:
            self.setCheckState(Qt.Unchecked)
        
        self.has_error()
    
    def get_operation(self) -> Operation:
        self._operation[KEY_QUERY.ACTIVE] = Qt.Checked == self.checkState()
        return copy.copy(self._operation)
    
    def has_error(self) -> bool:
        err = self._operation.test_full_error()
        
        if err:
            self.setIcon(get_icon(ICON.WARNING))
            self.setToolTip(str(err))
            return True
        else:
            self.setIcon(get_icon(None))
            self.setToolTip('')
            return False


class ErrorStrategyDialog(Dialog):
    def __init__(self):
        self.error_update = PREFS[KEY_ERROR.ERROR][KEY_ERROR.UPDATE]
        self.error_operation = PREFS[KEY_ERROR.ERROR][KEY_ERROR.OPERATION]
        
        if self.error_operation not in ERROR_OPERATION.LIST.keys():
            self.error_operation = ERROR_OPERATION.DEFAULT
        
        if self.error_update not in ERROR_UPDATE.LIST.keys():
            self.error_update = ERROR_UPDATE.DEFAULT
        
        Dialog.__init__(self,
            title=_('Error Strategy'),
            name='plugin.MassSearchReplace:config_ErrorStrategy',
            parent=GUI,
        )
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        operation_label = QLabel(_('Set the strategy when an invalid operation has detected:'), self)
        layout.addWidget(operation_label)
        
        self.operationStrategy = KeyValueComboBox(
            {key:value[0] for key, value in ERROR_OPERATION.LIST.items()},
            self.error_operation,
            parent=self,
        )
        self.operationStrategy.currentIndexChanged.connect(self.operation_strategy_index_changed)
        layout.addWidget(self.operationStrategy)
        
        operation_label.setBuddy(self.operationStrategy)
        
        layout.addWidget(QLabel (' ', self))
        
        update_label = QLabel(_('Define the strategy when a error occurs during the library update:'), self)
        layout.addWidget(update_label)
        
        self.updateStrategy = KeyValueComboBox(
            {key:value[0] for key, value in ERROR_UPDATE.LIST.items()},
            self.error_update,
            parent=self,
        )
        self.updateStrategy.currentIndexChanged.connect(self.update_strategy_index_changed)
        layout.addWidget(self.updateStrategy)
        
        update_label.setBuddy(self.updateStrategy)
        
        self.desc = QTextEdit (' ', self)
        self.desc.setReadOnly(True)
        layout.addWidget(self.desc)
        
        layout.insertStretch(-1)
        
        # -- Accept/Reject buttons --
        layout.addWidget(self.bb)
    
    def operation_strategy_index_changed(self, idx):
        error_operation = self.operationStrategy.selected_key()
        self.desc.setText(ERROR_OPERATION.LIST[error_operation][1])
    
    def update_strategy_index_changed(self, idx):
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
