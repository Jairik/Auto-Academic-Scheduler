"""
TimeslotListWidget, and TimeclotList Classes

Description: Subwindow that allows the addition and editing of standard timeslots.

@author: Don Spickler
Last Revision: 8/23/2022

"""

from PySide6.QtCore import (Qt, QMimeData)
from PySide6.QtGui import (QIcon, QColor, QBrush, QDrag, QAction)
from PySide6.QtWidgets import (QWidget, QAbstractItemView, QMdiSubWindow, QListWidget,
                               QTreeWidget, QVBoxLayout, QListView, QMenuBar)


class TimeslotListWidget(QListWidget):
    """
    Small enhancement on the QListWidget that envokes the timeslot editor on an enter key.
    """
    def __init__(self, parent=None, ma=None):
        """
        Sets pointers to parent and main app.

        :param parent: Pointer to the parent object, which must be the main app.
        :param ma: Pointer to the main app object.
        """
        super(TimeslotListWidget, self).__init__(parent)
        self.Parent = parent
        self.mainapp = ma

    def keyPressEvent(self, event):
        """
        If enter is pressed edit the selected timeslot.  Pass key to base QListWidget.

        :param event: Key pressed event.
        """
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.mainapp.editItem()
        QListWidget.keyPressEvent(self, event)


class TimeslotList(QMdiSubWindow):
    """
    Subwindow that allows the adding and editing of the standard timeslot database.
    """
    def __init__(self, parent):
        """
        Sets up the UI for the subwindow.

        :param parent: Pointer to the parent object.
        """
        super(TimeslotList, self).__init__(parent)
        self.Parent = parent
        self.mainapp = parent
        self.setWindowIcon(QIcon(self.mainapp.resource_path('icons/ProgramIcon.png')))

        self.setWindowTitle("Standard Timeslots")
        self.listitems = TimeslotListWidget(self, self)
        self.listitems.doubleClicked.connect(self.editItem)

        menu_bar = self.createMenu()
        menu_bar.setNativeMenuBar(False)

        mainarea = QWidget()
        mainlayout = QVBoxLayout(mainarea)
        mainlayout.setMenuBar(menu_bar)
        mainlayout.addWidget(self.listitems)
        mainlayout.setContentsMargins(0,0,0,0)

        self.setWidget(mainarea)

    def closeEvent(self, event):
        """ Close event to close the window in the main app.  """
        self.Parent.closeSubWindow(self)

    def editItem(self):
        """ Invokes the editor for a selected timeslot. """
        indexes = self.listitems.selectedIndexes()
        if len(indexes) > 0:
            item = self.listitems.model().itemData(indexes[0])[0]
            self.Parent.EditTimeslot(item)

    def createMenu(self):
        """ Set up the menu bar. """

        # Create actions.
        new_slots_act = QAction(QIcon(self.Parent.resource_path('icons/NewTimeslots.png')), "Add New Timeslots...", self)
        new_slots_act.setShortcut('Shift+Ctrl+N')
        new_slots_act.triggered.connect(self.Parent.AddNewTimeslots)

        edit_slots_act = QAction(QIcon(self.Parent.resource_path('icons/Preferences.png')), "Edit Timeslot...", self)
        edit_slots_act.setShortcut('Shift+Ctrl+E')
        edit_slots_act.triggered.connect(self.editItem)

        delete_slot_act = QAction(QIcon(self.Parent.resource_path('icons/Delete.png')), "Delete Timeslot...", self)
        delete_slot_act.triggered.connect(self.removeTimeslot)

        # Create the menu bar
        menu_bar = QMenuBar(self)
        main_menu = menu_bar.addMenu("Options")
        main_menu.addAction(new_slots_act)
        main_menu.addAction(edit_slots_act)
        main_menu.addSeparator()
        main_menu.addAction(delete_slot_act)

        return menu_bar

    def UpdateStandardTimeslotsList(self):
        """ Updates the timeslot list. """
        self.listitems.clear()
        for slot in self.mainapp.standardtimeslots:
            self.listitems.addItem(slot.getDescription())

    def removeTimeslot(self):
        """ Removes the selected timeslot.  """
        indexes = self.listitems.selectedIndexes()
        if len(indexes) > 0:
            item = self.listitems.model().itemData(indexes[0])[0]
            self.Parent.DeleteTimeslot(item)
