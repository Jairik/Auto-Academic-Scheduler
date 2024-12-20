"""
NoteEditor Class

Description: Simple note editor that allows the user to type any noted for the schedule they wish.
The editor also has options for opening, saving, and printing the editor contents as well as a
popup menu for cut/copy/paste operations and undo/redo.

@author: Don Spickler
Last Revision: 8/14/2022

"""

from PySide6.QtCore import (Qt, QMimeData, QDir, QMarginsF)
from PySide6.QtGui import (QIcon, QColor, QBrush, QDrag, QPageSize, QPageLayout, QAction)
from PySide6.QtWidgets import (QWidget, QAbstractItemView, QMdiSubWindow, QListWidget,
                               QTreeWidget, QVBoxLayout, QListView, QMenuBar, QTextEdit,
                               QFileDialog, QDialog, QMenu)
from PySide6.QtPrintSupport import (QPrintDialog, QPrinter, QPrintPreviewDialog)


class NoteEditor(QMdiSubWindow):
    """
    Subwindow with a simple text editor.
    """

    def __init__(self, parent):
        """
        Sets up the UI.

        :param parent: Pointer to calling application, which must be the main app.
        """
        super(NoteEditor, self).__init__(parent)
        self.Parent = parent
        self.mainapp = parent
        self.setWindowIcon(QIcon(self.mainapp.resource_path('icons/ProgramIcon.png')))

        self.setWindowTitle("Notes")
        self.editor = QTextEdit()
        self.editor.setMinimumWidth(300)
        self.editor.setMinimumHeight(300)
        self.editor.textChanged.connect(self.onTextChange)

        menu_bar = self.createMenu()
        menu_bar.setNativeMenuBar(False)
        mainarea = QWidget()
        mainlayout = QVBoxLayout(mainarea)
        mainlayout.setMenuBar(menu_bar)
        mainlayout.addWidget(self.editor)
        mainlayout.setContentsMargins(0,0,0,0)

        self.setWidget(mainarea)

    def closeEvent(self, event):
        """ Close event to close the window in the main app.  """
        self.Parent.closeSubWindow(self)

    def onTextChange(self):
        """ Alert parent (main app) that there was editing to the notes. """
        self.Parent.ChangeMade()

    def createMenu(self):
        """ Set up the menu bar. """

        file_open_act = QAction(QIcon(self.mainapp.resource_path('icons/FileOpen.png')), "Open...", self)
        file_open_act.triggered.connect(self.openFile)

        file_save_act = QAction(QIcon(self.mainapp.resource_path('icons/FileSave.png')), "Save As...", self)
        file_save_act.triggered.connect(self.saveFile)

        print_act = QAction(QIcon(self.mainapp.resource_path('icons/print.png')), "Print...", self)
        print_act.triggered.connect(self.print)

        printPreview_act = QAction(QIcon(self.mainapp.resource_path('icons/preview.png')), "Print Preview...", self)
        printPreview_act.triggered.connect(self.printPreview)

        # Create the menu bar and add actions
        menu_bar = QMenuBar(self)
        menu_bar.setNativeMenuBar(False)

        main_menu = menu_bar.addMenu("Options")
        main_menu.addAction(file_open_act)
        main_menu.addAction(file_save_act)
        main_menu.addSeparator()
        main_menu.addAction(print_act)
        main_menu.addAction(printPreview_act)

        return menu_bar

    def openFile(self):
        """ Open and loads a text file. """
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text Files (*.txt);;All Files (*.*)")
        try:
            f = open(file_name, 'r')
            self.editor.setText(f.read())
        except:
            pass

    def saveFile(self):
        """ Saves the contents of the editor to a text file. """
        dialog = QFileDialog()
        dialog.setFilter(dialog.filter() | QDir.Hidden)
        dialog.setDefaultSuffix('txt')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters(['Text Files (*.txt)', 'All Files (*.*)'])
        dialog.setWindowTitle('Save As')

        if dialog.exec() == QDialog.Accepted:
            filelist = dialog.selectedFiles()
            if len(filelist) > 0:
                file_name = filelist[0]
                f = open(file_name, 'w')
                f.write(self.editor.toPlainText())

    def print(self):
        """ Prints the contents of the editor to the selected printer. """
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        printer.setDocName("ScheduleNotes")
        printer.setResolution(300)
        if dialog.exec() == QDialog.Accepted:
            self.editor.print_(printer)

    def printPreview(self):
        """ Prints the contents of the editor to a print preview dialog. """
        printer = QPrinter()
        dialog = QPrintPreviewDialog(printer)
        printer.setDocName("ScheduleNotes")
        printer.setResolution(300)
        dialog.paintRequested.connect(self.printPreviewDoc)
        dialog.exec()

    def printPreviewDoc(self, printer):
        """ Print function to link to preview system. """
        self.editor.print_(printer)
