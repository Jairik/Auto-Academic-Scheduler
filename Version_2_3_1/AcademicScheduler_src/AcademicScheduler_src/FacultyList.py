"""
FacultyList Class and FacultyTreeWidget Class

Description: This is the main hub to the program, courses are droped here to establish a course
assignment  to a professor and then courses are dragged from here to the room viewers to place
th course in a room and time.

The FacultyTreeWidget handles the majority of the functionality with drag and drop.  The
FacultyList is a subwindow that includes the FacultyTreeWidget and a menu.

@author: Don Spickler
Last Revision: 8/23/2022

"""

from PySide6.QtCore import (Qt, QMimeData, QAbstractItemModel, QPoint)
from PySide6.QtGui import (QIcon, QColor, QBrush, QDrag, QFont, QFontMetrics, QPixmap, QPainter, QAction)
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QAbstractItemView, QMdiSubWindow, QListWidget,
                               QTreeWidget, QTreeWidgetItem, QMenuBar, QTreeView, QHeaderView,
                               QMenu)

from ScheduleItem import ScheduleItem
from Professor import Professor
from CourseList import CoursesListWidget


class FacultyTreeWidget(QTreeWidget):
    """
    The professor/course assignment list.  Using a tree widget here so that the professor's name is
    at the top level and bold with their assigned courses listed below their name.
    """

    def __init__(self, parent=None, ma=None):
        """
        Sets up the UI and enables the drag and drop interface.

        :param parent: Pointer to calling object.
        :param ma: Pointer to main app.
        """
        super(FacultyTreeWidget, self).__init__(parent)
        self.Parent = parent
        self.mainapp = ma

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)
        self.setMouseTracking(True)

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setColumnCount(3)

        self.setHeaderLabels(["Name", "Status", "Details"])
        self.header().setMinimumSectionSize(30)
        self.header().resizeSection(1, 10)
        self.header().resizeSection(0, 200)
        self.header().setSectionsMovable(False)
        self.header().setSectionResizeMode(QHeaderView.ResizeToContents)

    def mouseDoubleClickEvent(self, e):
        """
        On a double-click if a course is selected the function invokes the course properties
        editor for that class (i.e. schedule item).  If a professor is selected it will not
        have a parent and hence not invoke the editor.  Finally, the function sends the event
        to the widget base class.

        :param e: Mouse click event.
        """
        items = self.selectedItems()
        if len(items) > 0:
            item = items[0].text(0)
            if items[0].parent():
                self.mainapp.updateCourseProperties(item)

        QTreeWidget.mouseDoubleClickEvent(self, e)

    def keyPressEvent(self, e):
        """
        If the pressed key is return/enter the function invokes the course properties if a course is
        selected and the professor editor if a professor is selected.  Finally, the event is sent to
        the widget base class.

        :param e: Key pressed event.
        """
        if e.key() == Qt.Key_Return or e.key() == Qt.Key_Enter:
            items = self.selectedItems()
            if len(items) > 0:
                item = items[0].text(0)
                if items[0].parent():
                    self.mainapp.updateCourseProperties(item)
                else:
                    self.Parent.editItem()

        QTreeWidget.keyPressEvent(self, e)

    def contextMenuEvent(self, e):
        """
        If the user right-clicks on a course this context menu will appear.  It has options for
        invoking the course properties dialog, toggling the tentative mode, removing the class
        from the schedule and just removing the class from its scheduled rooms and times.

        :param e: Context menu event
        """
        items = self.selectedItems()
        if len(items) > 0:
            item = items[0].text(0)
            if items[0].parent():
                schedItem = self.mainapp.findScheduleItemFromString(item)

                if not schedItem:
                    return

                # Create the context menu actions.
                menu = QMenu(self)

                removeRooms_act = QAction("Remove Course from Rooms...", self)
                removeRooms_act.triggered.connect(lambda: self.mainapp.removeCourseRoomsAndTimes(item))

                removeSchedule_act = QAction("Remove Course from Schedule...", self)
                removeSchedule_act.triggered.connect(lambda: self.mainapp.removeCourseFromSchedule(item))

                courseProperties_act = QAction("Course Properties...", self)
                courseProperties_act.triggered.connect(lambda: self.mainapp.updateCourseProperties(item))

                courseTentative_act = QAction("Tentative", self)
                courseTentative_act.setCheckable(True)
                courseTentative_act.setChecked(schedItem.Tentative)
                courseTentative_act.triggered.connect(self.Parent.makeCourseTentative)

                # Create menu.
                menu.addAction(courseProperties_act)
                menu.addAction(courseTentative_act)
                menu.addSeparator()
                menu.addAction(removeRooms_act)
                menu.addAction(removeSchedule_act)

                # Display at cursor location.
                menu.exec(self.viewport().mapToGlobal(e))

    def startDrag(self, allowableActions):
        """
        This is called when dragging a course from the list to the room viewer for placement
        into rooms and times.

        :param allowableActions: System drag actions list.
        """

        # Only one item is selectable at a time, so self.selectedItems() should have a length of 1 only.
        # In case not we will exit the function and not invoke the drag.
        selectedItems = self.selectedItems()
        if len(selectedItems) < 1:
            return

        selectedTreeWidgetItem = selectedItems[0]

        # If the selected item is a professor it will not have a parent and in that case we
        # exit the program.
        if not selectedTreeWidgetItem.parent():
            return

        # Create drag object and get name of course that is being dragged.
        drag = QDrag(self)
        dragAndDropName = selectedTreeWidgetItem.text(0)

        # Set the mime data to be transferred for the drag event.
        mimedata = QMimeData()
        mimedata.setText(dragAndDropName)

        # Create a pixmap image to attach to the cursor during the drag.
        cursorText = dragAndDropName
        font = QFont("Arial")
        fm = QFontMetrics(font)
        w = fm.horizontalAdvance(cursorText)
        h = fm.height()
        self.pix = QPixmap(w, h)
        self.pix.fill(Qt.transparent)
        painter = QPainter(self.pix)
        painter.setFont(font)
        painter.drawText(QPoint(0, h), cursorText)
        painter.end()
        drag.setPixmap(self.pix)

        # Attach the data and invoke the drag.
        drag.setMimeData(mimedata)
        drag.exec_(allowableActions)

    def dragMoveEvent(self, e):
        """
        This is called when a course is being dragged from the course list into this
        widget.  It is for highlighting the professor that will be assigned to the
        dragged class.

        :param e: Drag event
        """

        # Check to see that the course is not being dragged from this list, if so return.
        if e.source() == self:
            return

        e.accept()

        # From the position of the cursor find the professor that the position is in and
        # highlight that professor. Helps the user with a more prominent visual.
        dropat = self.itemAt(e.pos())
        if dropat:
            dropparent = dropat.parent()
            parent = dropparent
            if not parent:
                dropParentIndex = self.indexOfTopLevelItem(self.itemAt(e.pos()))
                parent = self.topLevelItem(dropParentIndex)

            if not parent:
                return

            self.clearSelection()
            if parent:
                parent.setSelected(True)

    def dragEnterEvent(self, e):
        """
        On a drag entering the widget if the drag is not from a CoursesListWidget object or if
        it is from this object return, otherwise accept the drag.

        :param e: Drag event
        """
        if e.source() == self:
            return

        if not isinstance(e.source(), CoursesListWidget):
            return

        e.accept()

    def dropEvent(self, e):
        """
        This is invoked if a drag object is dropped into the widget.  If the drop does not come
        from CoursesListWidget or if it does not contain text the function exits.  If so, the
        function finds the professor associated with the position of the drop.  As long as the
        professor is valid the course is dropped and added to the professor's schedule.

        :param e: Drop event
        """

        # If the drop is not coming from a CoursesListWidget return.
        if not isinstance(e.source(), CoursesListWidget):
            return

        # Check to see if the mime data is text, otherwise abort.
        if e.mimeData().hasText():
            e.accept()
        else:
            e.ignore()

        # From the position of the cursor find the professor that the position is in and
        # add the course to their course assignments on the drop.
        dropParentIndex = -1
        dropat = self.itemAt(e.pos())
        if dropat:
            dropparent = dropat.parent()
            dropParentIndex = self.indexOfTopLevelItem(dropparent)
            if dropParentIndex == -1:
                dropParentIndex = self.indexOfTopLevelItem(self.itemAt(e.pos()))

        passedData = e.mimeData().text()

        if dropParentIndex != -1:
            self.Parent.AddScheduleItem(dropParentIndex, passedData)


class FacultyList(QMdiSubWindow):
    """
    Subwindow for the faculty course assignments.  This window is the hub of the program.
    The courses are dropped he to establish a course assignment and courses are dragged
    from here to rooms for schedule placement.
    """

    def __init__(self, parent=None):
        """
        Sets up the UI for the program.

        :param parent: Pointer to the calling object which must be the main app.
        """
        super(FacultyList, self).__init__(parent)
        self.Parent = parent
        self.mainapp = parent
        self.setWindowIcon(QIcon(self.mainapp.resource_path('icons/ProgramIcon.png')))

        self.setWindowTitle("Course/Faculty Assignments")
        self.listitems = FacultyTreeWidget(self, self.mainapp)
        self.blocktext = "  \u2586\u2586  "  # Unicode for a block, used to make a rectangle of color.

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

    def createMenu(self):
        """ Set up the menu bar. """

        # Set up the actions.
        new_faculty_act = QAction(QIcon(self.Parent.resource_path('icons/NewFaculty.png')), "Add New Faculty...", self)
        new_faculty_act.setShortcut('Shift+Ctrl+N')
        new_faculty_act.triggered.connect(self.Parent.AddNewFaculty)

        edit_faculty_act = QAction(QIcon(self.Parent.resource_path('icons/Preferences.png')), "Edit Faculty...", self)
        edit_faculty_act.setShortcut('Shift+Ctrl+E')
        edit_faculty_act.triggered.connect(self.editItem)

        delete_faculty_act = QAction(QIcon(self.Parent.resource_path('icons/Delete.png')), "Delete Faculty Member...",
                                     self)
        delete_faculty_act.triggered.connect(self.deleteItem)

        view_expand_act = QAction(QIcon(self.Parent.resource_path('icons/Expand.png')), "Expand All", self)
        view_expand_act.triggered.connect(self.listitems.expandAll)

        view_collapse_act = QAction(QIcon(self.Parent.resource_path('icons/Collapse.png')), "Collapse All", self)
        view_collapse_act.triggered.connect(self.listitems.collapseAll)

        removeRooms_act = QAction("Remove Course from Rooms...", self)
        removeRooms_act.triggered.connect(self.removeCourseRoomsAndTimes)

        removeSchedule_act = QAction("Remove Course from Schedule...", self)
        removeSchedule_act.triggered.connect(self.removeCourseFromSchedule)

        courseProperties_act = QAction("Course Properties...", self)
        courseProperties_act.triggered.connect(self.updateCourseProperties)

        self.courseTentative_act = QAction("Toggle Tentative", self)
        self.courseTentative_act.triggered.connect(self.makeCourseTentative)

        # Create the menu bar
        menu_bar = QMenuBar(self)
        main_menu = menu_bar.addMenu("Options")
        main_menu.addAction(new_faculty_act)
        main_menu.addAction(edit_faculty_act)
        main_menu.addSeparator()
        main_menu.addAction(delete_faculty_act)
        main_menu.addSeparator()
        main_menu.addAction(courseProperties_act)
        main_menu.addAction(self.courseTentative_act)
        main_menu.addSeparator()
        main_menu.addAction(removeRooms_act)
        main_menu.addAction(removeSchedule_act)
        main_menu.addSeparator()
        main_menu.addAction(view_expand_act)
        main_menu.addAction(view_collapse_act)
        return menu_bar

    def getSelectedScheduleItem(self) -> str:
        """
        Gets the string of the course if one is selected, returns None if not.

        :return: String of the course if one is selected, returns None if not.
        """
        items = self.listitems.selectedItems()
        if len(items) > 0:
            item = items[0].text(0)
            if items[0].parent():
                schedItem = self.mainapp.findScheduleItemFromString(item)

                if not schedItem:
                    return None
            return item
        else:
            return None

    def removeCourseRoomsAndTimes(self):
        """ Has the main app remove the course's days and times but keeps the course in the schedule. """
        item = self.getSelectedScheduleItem()
        if item:
            self.mainapp.removeCourseRoomsAndTimes(item)

    def removeCourseFromSchedule(self):
        """ Has the main app remove the course from the schedule. """
        item = self.getSelectedScheduleItem()
        if item:
            self.mainapp.removeCourseFromSchedule(item)

    def updateCourseProperties(self):
        """ Has the main app invoke the course properties dialog. """
        item = self.getSelectedScheduleItem()
        if item:
            self.mainapp.updateCourseProperties(item)

    def makeCourseTentative(self):
        """ Has the main app toggle the tentative state of the class. """
        item = self.getSelectedScheduleItem()
        if item:
            schedItem = self.mainapp.findScheduleItemFromString(item)
            self.mainapp.makeCourseTentative(schedItem.InternalID, not schedItem.Tentative)

    def editItem(self):
        """
        Finds the selected faculty member or the position for the faculty member and invokes
        the editor.
        """
        selectedItems = self.listitems.selectedItems()
        if len(selectedItems) < 1:
            return

        selectedTreeWidgetItem = selectedItems[0]
        if selectedTreeWidgetItem.parent():
            selectedTreeWidgetItem = selectedTreeWidgetItem.parent()

        FacultyName = selectedTreeWidgetItem.text(0)
        self.Parent.EditFaculty(FacultyName)

    def deleteItem(self):
        """
        Finds the selected faculty member or the position for the faculty member and invokes
        the main apps deletion.
        """
        selectedItems = self.listitems.selectedItems()
        if len(selectedItems) < 1:
            return

        selectedTreeWidgetItem = selectedItems[0]
        if selectedTreeWidgetItem.parent():
            selectedTreeWidgetItem = selectedTreeWidgetItem.parent()

        FacultyName = selectedTreeWidgetItem.text(0)
        self.Parent.DeleteFacultyMember(FacultyName)

    def AddScheduleItem(self, dropParentIndex, passedData):
        """
        Adds a schedule item to the professor's (at the drop index) schedule.

        :param dropParentIndex: Index of the professor to receive the class.
        :param passedData: The schedule item to add.
        """
        self.Parent.AddScheduleItem(dropParentIndex, passedData)

    def scheduleItemColor(self, scheditem: ScheduleItem) -> QColor:
        """
        Determines the number of minutes allotted to the course and compares this to the
        number of minutes that the course should have and then determines the color to
        color the designation block in the tree.

        :param scheditem: Schedule item to calculate designation of allotted time.
        :return: QColor of the color designation.
        """
        timedes = self.mainapp.ScheduleItemTimeCheck(scheditem)
        childColor = QColor()

        if timedes == -2:
            childColor.setRgb(255, 0, 0)
        elif timedes == -1:
            childColor.setRgb(230, 230, 0)
        elif timedes == 1:
            childColor.setRgb(0, 230, 0)
        else:
            childColor.setRgb(0, 150, 0)

        return childColor

    def scheduleItemQTreeWidgetItem(self, scheditem: ScheduleItem) -> QTreeWidgetItem:
        """
        Creates a QTreeWidgetItem for displaying in the tree, for the input QTreeWidgetItem.

        :param scheditem: ScheduleItem to be added to the tree.
        :return: QTreeWidgetItem object to display.
        """
        nameandsection = self.mainapp.courseNameAndSection(scheditem)
        timeslotstring = self.mainapp.createTimeslotStringFromScheduleItem(scheditem)

        child = QTreeWidgetItem(None, [nameandsection, self.blocktext, timeslotstring])

        # Determine the color of the entry depending on if the course is tentative or not.
        if scheditem.Tentative:
            child.setForeground(0, QBrush(Qt.black))
            child.setForeground(2, QBrush(Qt.black))
#            child.setTextColor(0, QColor(Qt.darkGray))
#            child.setTextColor(2, QColor(Qt.darkGray))
            font = child.font(0)
            font.setItalic(True)
            child.setFont(0, font)
            child.setFont(2, font)
        else:
            child.setForeground(0, QBrush(Qt.black))
            child.setForeground(2, QBrush(Qt.black))
#            child.setTextColor(0, QColor(Qt.black))
#            child.setTextColor(2, QColor(Qt.black))
            font = child.font(0)
            font.setItalic(False)
            child.setFont(0, font)
            child.setFont(2, font)

        return child

    def profeesorDetailString(self, prof: Professor) -> str:
        """
        Creates and returns a string representing the details to be displayed for the tree view.

        :param prof: The professor to create the detail string for.
        :return: String representing the details to be displayed for the tree view.
        """
        profdetails = ""
        wl, wlf, twl, twlf = self.mainapp.calculateProfessorWorkload(prof)
        profdetails += str(wl)
        if self.mainapp.options[1] > 1:
            profdetails += " / " + "{:.4f}".format(wlf)
        if twl > 0:
            profdetails += "     Tentative: " + str(twl)
            if self.mainapp.options[1] > 1:
                profdetails += " / " + "{:.4f}".format(twlf)

        profdetails += "  (" + prof.ShortDes + ")"
        if prof.ID != "":
            profdetails += "   (" + prof.ID + ")"

        return profdetails

    def UpdateSingleFacultyList(self, profIndex: int):
        """
        Updates the professor detail string at the index given.

        :param profIndex: Index of professor to update.
        """
        prof = self.mainapp.faculty[profIndex]
        item = self.listitems.topLevelItem(profIndex)
        item.setText(0, prof.getName())
        item.setText(2, self.profeesorDetailString(prof))

    def UpdateFacultyCourseList(self, profIndex: int, scheditem: ScheduleItem, overright: bool = False):
        """
        Updates the course list for the professor at the given index.

        :param profIndex: Index of professor to update.
        :param scheditem: Schedule item to add/update into their schedule.
        :param overright: Boolean on whether to update a schedule item that already exists or to add a new one.
        """
        proftreeitem = self.listitems.topLevelItem(profIndex)
        if overright:
            for childindex in range(proftreeitem.childCount()):
                coursestring = proftreeitem.child(childindex).text(0)
                scheditemcoursestring = self.mainapp.courseNameAndSection(scheditem)
                if coursestring == scheditemcoursestring:
                    timeslotstring = self.mainapp.createTimeslotStringFromScheduleItem(scheditem)
                    proftreeitem.child(childindex).setText(2, timeslotstring)
                    proftreeitem.child(childindex).setTextColor(1, self.scheduleItemColor(scheditem))
        else:
            child = self.scheduleItemQTreeWidgetItem(scheditem)
            child.setTextColor(1, self.scheduleItemColor(scheditem))
            proftreeitem.addChild(child)
        proftreeitem.sortChildren(0, Qt.AscendingOrder)
        self.UpdateSingleFacultyList(profIndex)

    def UpdateFacultyList(self):
        """ Updates the entire faculty course assignment list. """
        bar = self.listitems.verticalScrollBar()
        yScroll = bar.value()

        self.listitems.clear()
        for prof in self.mainapp.faculty:
            profdetails = self.profeesorDetailString(prof)
            parent = QTreeWidgetItem(None, [prof.getName(), "", profdetails])
            facnameft = parent.font(0)
            facnameft.setBold(True)
            parent.setFont(0, facnameft)
            self.listitems.addTopLevelItem(parent)

            for scheditem in self.mainapp.schedule:
                for IID in scheditem.ProfessorIID:
                    if IID == prof.InternalID:
                        child = self.scheduleItemQTreeWidgetItem(scheditem)
#                        child.setTextColor(1, self.scheduleItemColor(scheditem))
                        child.setForeground(1, self.scheduleItemColor(scheditem))
                        parent.addChild(child)
                        parent.sortChildren(0, Qt.AscendingOrder)

        self.listitems.expandAll()
        self.listitems.verticalScrollBar().setSliderPosition(yScroll)
