"""
LC_Table Class

Description: Extension of a QTableWidget to add some basic functionality as well as
undo and redo capabilities.

@author: Don Spickler
Revised: 8/10/2021

"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QTableWidget, QTableWidgetItem, QAbstractItemView, QApplication,
                               QDialog)
from PySide6.QtPrintSupport import (QPrintDialog, QPrinter, QPrintPreviewDialog)
from PySide6.QtGui import (QTextCursor, QTextDocument)


class LC_Table(QTableWidget):
    """
    Extension of a QTableWidget to add some basic functionality as well as
    undo and redo capabilities.
    """

    def __init__(self, parent=None):
        """
        Sets up the options and history list.

        :param parent: Object that has this embedded.
        """
        super(LC_Table, self).__init__(parent)
        self.setRowCount(3)
        self.setColumnCount(3)
        self.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.setCurrentCell(0, 0)
        self.cellChanged.connect(self.onCellChanged)
        self.tableHistory = []
        self.historyPos = 0
        self.addToHistory()
        self.clipboard = QApplication.clipboard()
        self.undoredoon = False

    def keyPressEvent(self, event):
        """
        Overrides the key event processing.  Sends untracked keys to parent.
        """
        key = event.key()
        modifiers = event.modifiers()

        if self.editTriggers() == QAbstractItemView.NoEditTriggers:
            if modifiers == Qt.ControlModifier:
                if key == Qt.Key_C:
                    items = self.getSelectedTableContents()
                    cbstr = self.itemsToTabString(items)
                    self.clipboard.setText(cbstr)
                elif key == Qt.Key_R:
                    self.resizeAllCells()
            elif key == Qt.Key_Return or key == Qt.Key_Enter:
                row = self.currentRow()
                col = self.currentColumn()
                row = row + 1
                if row >= self.rowCount():
                    row = 0
                    col = col + 1

                if col >= self.columnCount():
                    col = 0

                self.setCurrentCell(row, col)
            else:
                super(LC_Table, self).keyPressEvent(event)

            return

        if modifiers == Qt.ShiftModifier | Qt.ControlModifier:
            if key == Qt.Key_Z:
                self.redo()
        elif modifiers == Qt.ControlModifier:
            if key == Qt.Key_Z:
                self.undo()
            elif key == Qt.Key_C:
                items = self.getSelectedTableContents()
                cbstr = self.itemsToTabString(items)
                self.clipboard.setText(cbstr)
            elif key == Qt.Key_V:
                cbstr = self.clipboard.text()
                items = self.tabStringToItems(cbstr)
                self.pasteNoResize(items)
            elif key == Qt.Key_R:
                self.resizeAllCells()

        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            row = self.currentRow()
            col = self.currentColumn()
            row = row + 1
            if row >= self.rowCount():
                row = 0
                col = col + 1

            if col >= self.columnCount():
                col = 0

            self.setCurrentCell(row, col)
        elif key == Qt.Key_Delete:
            self.blockSignals(True)
            rng = self.selectedCellRanges()
            if len(rng) > 0:
                for i in range(rng[0][0], rng[0][1] + 1):
                    for j in range(rng[1][0], rng[1][1] + 1):
                        self.setItem(i, j, QTableWidgetItem(''))

            self.addToHistory()
            self.blockSignals(False)
        else:
            super(LC_Table, self).keyPressEvent(event)

    def addToHistory(self):
        """
        Adds the curent table to the undo/redo history.  Removes stored tables
        from the current table position to the end of the list.
        """
        currentTable = self.getTableContents()

        if len(self.tableHistory) > 0:
            while self.historyPos != len(self.tableHistory) - 1:
                self.tableHistory.pop(len(self.tableHistory) - 1)

        self.tableHistory.append(currentTable)
        self.historyPos = len(self.tableHistory) - 1
        self.setFocus()

    def setLables(self, lablelist: [], vertLableList: [] = None):
        """ Sets the horizontal and vertical labels on the grid. """
        self.setHorizontalHeaderLabels(lablelist)
        if vertLableList:
            self.setVerticalHeaderLabels(vertLableList)

    def onCellChanged(self):
        """ If a cell is changed the new table is stored. """
        self.addToHistory()

    def resizeAllCells(self):
        """ Resizes the entire grid to the cell contents. """
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def selectedCellRanges(self) -> []:
        """
        Returns a lit of the upper left and lower right positions of the selected
        block of cells.
        """
        selitems = self.selectedIndexes()
        returnList = []
        if len(selitems) > 0:
            minrow = selitems[0].row()
            maxrow = selitems[0].row()
            mincol = selitems[0].column()
            maxcol = selitems[0].column()
            for i in selitems:
                if i.row() < minrow:
                    minrow = i.row()
                if i.row() > maxrow:
                    maxrow = i.row()
                if i.column() < mincol:
                    mincol = i.column()
                if i.column() > maxcol:
                    maxcol = i.column()

            returnList.append([minrow, maxrow])
            returnList.append([mincol, maxcol])
        return returnList

    def resizeTable(self, r: int, c: int):
        """ Resizes the table to r rows and c columns. """
        self.blockSignals(True)
        self.setColumnCount(c)
        self.setRowCount(r)
        self.addToHistory()
        self.blockSignals(False)

    def closeEditing(self):
        """
        Stops the editing of a cell and takes the current edit as its contents.
        """
        # Trick to end editing of all cells, probably a better way to do this.
        self.setEnabled(False)
        self.setEnabled(True)

    def getTableContents(self) -> []:
        """
        Returns a list of row lists of table contents for the entire table.
        """
        self.closeEditing()
        tablelist = []
        for i in range(self.rowCount()):
            rowlist = []
            for j in range(self.columnCount()):
                item = self.item(i, j)
                if item is None:
                    rowlist.append('')
                else:
                    rowlist.append(item.text())

            tablelist.append(rowlist)

        return tablelist

    def getSelectedTableContents(self) -> []:
        """
        Returns a list of row lists of selected table contents.
        """
        self.closeEditing()
        tablelist = []
        rng = self.selectedCellRanges()
        if len(rng) > 0:
            for i in range(rng[0][0], rng[0][1] + 1):
                rowlist = []
                for j in range(rng[1][0], rng[1][1] + 1):
                    item = self.item(i, j)
                    if item is None:
                        rowlist.append('')
                    else:
                        rowlist.append(item.text())

                tablelist.append(rowlist)

        return tablelist

    def paste(self, items: []):
        """
        Pastes the list of row lists to the table, expanding the table size if
        necessary.
        """
        self.blockSignals(True)
        rows = len(items)
        cols = 0
        for i in range(rows):
            if len(items[i]) > cols:
                cols = len(items[i])

        rng = self.selectedCellRanges()
        if len(rng) > 0:
            startrow = rng[0][0]
            startcol = rng[1][0]

            if rows + startrow > self.rowCount():
                if rows + startrow > 10000:
                    rows = 10000 - startrow
                self.setRowCount(rows + startrow)

            if cols + startcol > self.columnCount():
                if cols + startcol > 1000:
                    cols = 1000 - startcol
                self.setColumnCount(cols + startcol)

            for i in range(startrow, rows + startrow):
                for j in range(startcol, cols + startcol):
                    self.setItem(i, j, QTableWidgetItem(items[i - startrow][j - startcol]))

        self.addToHistory()
        self.blockSignals(False)

    def pasteNoResize(self, items: []):
        """
        Pastes the list of row lists to the table.
        """
        self.blockSignals(True)
        rows = len(items)
        cols = 0
        for i in range(rows):
            if len(items[i]) > cols:
                cols = len(items[i])

        rng = self.selectedCellRanges()
        if len(rng) > 0:
            startrow = rng[0][0]
            startcol = rng[1][0]

            for i in range(startrow, rows + startrow):
                for j in range(startcol, cols + startcol):
                    if i < self.rowCount() and j < self.columnCount():
                        self.setItem(i, j, QTableWidgetItem(items[i - startrow][j - startcol]))

        self.addToHistory()
        self.blockSignals(False)

    def getUpperLeftSelectedCell(self) -> []:
        """
        Returns the index of the upper left selected cell.
        """
        rng = self.selectedCellRanges()
        if len(rng) > 0:
            return [rng[0][0], rng[1][0]]
        else:
            return []

    def getLowerRightSelectedCell(self) -> []:
        """
        Returns the index of the lower right selected cell.
        """
        rng = self.selectedCellRanges()
        if len(rng) > 0:
            return [rng[0][1], rng[1][1]]
        else:
            return []

    def addRowAbove(self):
        """
        Adds a row above the selected cells.
        """
        start = self.getUpperLeftSelectedCell()
        if len(start) > 0:
            self.insertRow(start[0])

        self.addToHistory()

    def addRowBelow(self):
        """
        Adds a row below the selected cells.
        """
        start = self.getLowerRightSelectedCell()
        if len(start) > 0:
            self.insertRow(start[0] + 1)

        self.addToHistory()

    def addColumnBefore(self):
        """
        Adds a column before the selected cells.
        """
        start = self.getUpperLeftSelectedCell()
        if len(start) > 0:
            self.insertColumn(start[1])

        self.addToHistory()

    def addColumnAfter(self):
        """
        Adds a column after the selected cells.
        """
        start = self.getLowerRightSelectedCell()
        if len(start) > 0:
            self.insertColumn(start[1] + 1)

        self.addToHistory()

    def deleteRows(self):
        """
        Deletes the selected rows.
        """
        rng = self.selectedCellRanges()
        if len(rng) > 0:
            start = rng[0][0]
            end = rng[0][1]
            for i in range(end - start + 1):
                self.removeRow(start)

        if self.rowCount() == 0:
            self.insertRow(0)

        self.addToHistory()

    def deleteColumns(self):
        """
        Deletes the selected columns.
        """
        rng = self.selectedCellRanges()
        if len(rng) > 0:
            start = rng[1][0]
            end = rng[1][1]
            for i in range(end - start + 1):
                self.removeColumn(start)

        if self.columnCount() == 0:
            self.insertColumn(0)

        self.addToHistory()

    def deleteRowsColumns(self):
        """
        Deletes the selected rows and columns.
        """
        rng = self.selectedCellRanges()
        if len(rng) > 0:
            startr = rng[0][0]
            endr = rng[0][1]
            startc = rng[1][0]
            endc = rng[1][1]
            for i in range(endr - startr + 1):
                self.removeRow(startr)

            if self.rowCount() == 0:
                self.insertRow(0)

            for i in range(endc - startc + 1):
                self.removeColumn(startc)

            if self.columnCount() == 0:
                self.insertColumn(0)

        self.addToHistory()

    def transpose(self):
        """
        Transposes the grid.
        """
        self.blockSignals(True)

        items = self.getTableContents()
        rows = self.rowCount()
        cols = self.columnCount()

        tablelist = []
        for j in range(cols):
            collist = []
            for i in range(rows):
                item = items[i][j]
                if item is None:
                    collist.append('')
                else:
                    collist.append(item)

            tablelist.append(collist)

        self.setRowCount(cols)
        self.setColumnCount(rows)
        self.paste(tablelist)
        self.setCurrentCell(0, 0)
        self.addToHistory()
        self.blockSignals(False)

    def trimcells(self):
        """
        Trims the entries in each cell.
        """
        self.blockSignals(True)
        for i in range(self.rowCount()):
            for j in range(self.columnCount()):
                item = self.item(i, j)

                if item is None:
                    item = ''
                else:
                    item = item.text()

                item = item.lstrip()
                item = item.rstrip()
                self.setItem(i, j, QTableWidgetItem(item))

        self.addToHistory()
        self.blockSignals(False)

    def fillcells(self, fill_text):
        """
        Fills the cells with the given text.
        """
        self.blockSignals(True)
        for i in range(self.rowCount()):
            for j in range(self.columnCount()):
                self.setItem(i, j, QTableWidgetItem(fill_text))

        self.addToHistory()
        self.blockSignals(False)

    def clearTable(self):
        """
        Clears the table contents.
        """
        self.clear()
        self.addToHistory()

    def newtable(self):
        """
        Clears the table contents and resets the size to 3 X 3.
        """
        self.setRowCount(3)
        self.setColumnCount(3)
        self.clear()
        self.setCurrentCell(0, 0)
        self.addToHistory()

    def loadItems(self, currentTable):
        """
        Loads the items (list of row lists) into the table.
        """
        self.blockSignals(True)
        rows = len(currentTable)
        cols = len(currentTable[0])
        self.setRowCount(rows)
        self.setColumnCount(cols)

        for i in range(self.rowCount()):
            for j in range(self.columnCount()):
                self.setItem(i, j, QTableWidgetItem(currentTable[i][j]))
        self.blockSignals(False)

    def undo(self):
        """
        Processes an undo.
        """
        if not self.undoredoon:
            return

        self.historyPos = self.historyPos - 1
        if self.historyPos < 0:
            self.historyPos = 0

        currentTable = self.tableHistory[self.historyPos]
        self.loadItems(currentTable)

    def redo(self):
        """
        Processes a redo.
        """
        if not self.undoredoon:
            return

        self.historyPos = self.historyPos + 1
        if self.historyPos >= len(self.tableHistory):
            self.historyPos = len(self.tableHistory) - 1

        currentTable = self.tableHistory[self.historyPos]
        self.loadItems(currentTable)

    def itemsToTabString(self, items: []):
        """
        Converts a list of row lists of table elements to a tab delimited string.
        """
        retstr = ''
        for i in range(len(items)):
            row = items[i]
            for j in range(len(row)):
                retstr = retstr + row[j]
                if (j == len(row) - 1):
                    retstr = retstr + '\n'
                else:
                    retstr = retstr + '\t'

        return retstr

    def tabStringToItems(self, tdstr: str) -> []:
        """
        Converts a tab delimited string to a list of row lists of table elements.
        """
        retitems = []
        strobj = str(tdstr)
        strlist = strobj.split('\n')
        for line in strlist:
            if len(line) > 0:
                splitline = line.split('\t')
                retitems.append(splitline)

        return retitems
