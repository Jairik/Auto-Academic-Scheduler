"""
CourseList Class and CoursesListWidget Class

Description: The CourseList is a view and drag start for the courses in your course database.
The CoursesListWidget enables dragging of courses to the course/faculty assignment list which
crates schedule items (professor/course pairs) to be put into rooms.

The subwindow also has options in the menu for adding, editing, and deleting courses.  Each of
these simply do a callback to the main app which handles the changes to the databases. There
is also a menu option to toggle between a single line display and multiple line display (expanded).

@author: Don Spickler
Last Revision: 8/23/2022

"""

from PySide6.QtCore import (Qt, QMimeData, QPoint)
from PySide6.QtGui import (QIcon, QColor, QBrush, QDrag, QPixmap, QPainter, QFont, QFontMetrics, QAction)
from PySide6.QtWidgets import (QWidget, QAbstractItemView, QMdiSubWindow, QListWidget,
                               QTreeWidget, QVBoxLayout, QListView, QMenuBar, QLabel)
import collections
from Course import Course
from Room import Room


class CoursesListWidget(QListWidget):
    """
    The CoursesListWidget is derived off of a general QListWidget so that it can incorporate
    the creation of a drag event to be dropped into the course/faculty assignment list.
    It also links the course in the list to the course editor which is invoked from the main
    application, AcademicScheduler.
    """
    def __init__(self, parent=None, ma=None):
        """
        Takes pointers to the MDI subwindow and main app.  Sets the control to enable a
        drag initiation and sets the QPixmap size for the drag text attached to the cursor.

        :param parent:  Pointer to CourseList(QMdiSubWindow)
        :param ma: Pointer to the main application,  AcademicScheduler.
        """
        super(CoursesListWidget, self).__init__(parent)
        self.setDragEnabled(True)
        self.pix = QPixmap(10, 10)
        self.Parent = parent
        self.mainapp = ma

    # Override of the key pressed event.  If enter/return is pressed the course editor is invoked.
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.mainapp.editItem()
        QListWidget.keyPressEvent(self, event)

    def startDrag(self, allowableActions):
        # If no item is selected, do not proceed with the drag.
        selectedItems = self.selectedItems()
        if len(selectedItems) < 1:
            return

        # The drag information is simply the course name, e.g. MATH 201.
        drag = QDrag(self)
        mimedata = QMimeData()
        dataText = selectedItems[0].data(0).split(":")[0]
        mimedata.setText(dataText)

        # Set text for drag icon.  The drag text is the course name and title.
        cursorText = selectedItems[0].data(0).split('\n')[0]
        font = QFont("Arial")
        fm = QFontMetrics(font)
        w = fm.horizontalAdvance(cursorText)
        h = fm.height()
        self.pix = QPixmap(w, h)
        self.pix.fill(Qt.transparent)
        painter = QPainter(self.pix)
        painter.setFont(font)
        painter.drawText(QPoint(0, h), cursorText)
        drag.setPixmap(self.pix)

        # Initiate the drag.
        drag.setMimeData(mimedata)
        drag.exec_(allowableActions)


class CourseList(QMdiSubWindow):
    """
    MDI child window derived off of a general QMdiSubWindow.  This is simply a list (CoursesListWidget)
    and menu.  The CoursesListWidget allows dragging to the course/faculty assignment list.
    """
    def __init__(self, parent):
        """ Sets up the links to the main application and the UI for the subwindow. """
        super(CourseList, self).__init__(parent)
        self.Parent = parent
        self.mainapp = parent
        self.setWindowIcon(QIcon(self.mainapp.resource_path('icons/ProgramIcon.png')))

        self.setWindowTitle("Courses")
        self.listitems = CoursesListWidget(self, self)
        self.listitems.doubleClicked.connect(self.editItem)

        self.ExpandedDisplay = True

        menu_bar = self.createMenu()
        mainarea = QWidget()
        mainlayout = QVBoxLayout(mainarea)
        mainlayout.setMenuBar(menu_bar)
        mainlayout.addWidget(self.listitems)
        mainlayout.setContentsMargins(0,0,0,0)
        #mainlayout.setMargin(0)
        self.setWidget(mainarea)

    def closeEvent(self, event):
        """ Close event to close the window in the main app.  """
        self.Parent.closeSubWindow(self)

    def editItem(self):
        """ Invokes the course editor on the currently selected item in the list. """
        indexes = self.listitems.selectedIndexes()
        if len(indexes) > 0:
            item = self.listitems.model().itemData(indexes[0])[0]
            coursetoedit = item.split(":")[0]
            self.Parent.EditCourse(coursetoedit)

    def deleteItem(self):
        """ Invokes the course deletion function on the currently selected item in the list. """
        indexes = self.listitems.selectedIndexes()
        if len(indexes) > 0:
            item = self.listitems.model().itemData(indexes[0])[0]
            coursetoedit = item.split(":")[0]
            self.Parent.DeleteCourse(coursetoedit)

    def createMenu(self):
        """ Set up the menu bar. """

        # Set actions.
        new_course_act = QAction(QIcon(self.Parent.resource_path('icons/FileNew.png')), "Add New Courses...", self)
        new_course_act.setShortcut('Shift+Ctrl+N')
        new_course_act.triggered.connect(self.Parent.AddNewCourse)

        edit_course_act = QAction(QIcon(self.Parent.resource_path('icons/Preferences.png')), "Edit Course...", self)
        edit_course_act.setShortcut('Shift+Ctrl+E')
        edit_course_act.triggered.connect(self.editItem)

        delete_course_act = QAction(QIcon(self.Parent.resource_path('icons/Delete.png')), "Delete Course...", self)
        delete_course_act.triggered.connect(self.deleteItem)

        self.showExpanded_act = QAction("Expanded Course Display", self)
        self.showExpanded_act.triggered.connect(self.toggleExpanded)
        self.showExpanded_act.setCheckable(True)
        self.showExpanded_act.setChecked(True)

        # Create the menu bar
        menu_bar = QMenuBar(self)
        menu_bar.setNativeMenuBar(False)

        main_menu = menu_bar.addMenu("Options")
        main_menu.addAction(new_course_act)
        main_menu.addAction(edit_course_act)
        main_menu.addSeparator()
        main_menu.addAction(delete_course_act)
        main_menu.addSeparator()
        main_menu.addAction(self.showExpanded_act)

        return menu_bar

    def toggleExpanded(self):
        # Toggle for the expanded or contracted display of course information.
        self.ExpandedDisplay = self.showExpanded_act.isChecked()
        self.UpdateCourseList()

    def courseString(self, course: Course) -> str:
        """
        Creates and returns a course string for display in the list. For example,

        MATH 201: Calculus I
            Sections: 3/0 Enrollment: 72/0
            Staff: DES, VXH(2)

        :param course: The course object that is to be displayed with scheduling information.
        :return: The display string for that course in the course list.
        """
        coursecount = 0
        coursetentativecount = 0
        totalcap = 0
        totaltentcap = 0
        proflist = []
        profTentativelist = []
        for scheditem in self.mainapp.schedule:
            if course.InternalID == scheditem.CourseIID:
                roomcaps = []
                for roomtime in scheditem.RoomsAndTimes:
                    room = self.mainapp.findRoomFromIID(roomtime[0])
                    roomcaps.append(room.Capacity)
                    if len(scheditem.LinkedCourses) > 0:
                        for linkediid in scheditem.LinkedCourses:
                            scheditemlinked = self.mainapp.findScheduleItemFromIID(linkediid)
                            for linkedroomtime in scheditemlinked.RoomsAndTimes:
                                linkedroom = self.mainapp.findRoomFromIID(linkedroomtime[0])
                                roomcaps.append(linkedroom.Capacity)

                classenroll = 0
                if len(roomcaps) > 0:
                    classenroll = min(roomcaps)

                if scheditem.Tentative:
                    coursetentativecount += 1
                    totaltentcap += classenroll
                    for iid in scheditem.ProfessorIID:
                        profTentativelist.append(self.mainapp.findProfessorFromIID(iid).ShortDes)
                else:
                    coursecount += 1
                    totalcap += classenroll
                    for iid in scheditem.ProfessorIID:
                        proflist.append(self.mainapp.findProfessorFromIID(iid).ShortDes)

        if self.ExpandedDisplay:
            indent = "\n          "
        else:
            indent = "  ---  "

        displaystring = course.getDisplayStringNoLoad()
        if coursecount + coursetentativecount > 0:
            displaystring += indent + "Sections: " + str(coursecount) + " / " + str(coursetentativecount)
            displaystring += "   Enrollment: " + str(totalcap) + " / " + str(totaltentcap)
            proflist.sort()
            frequency = collections.Counter(proflist)
            freqdict = dict(frequency)

            profTentativelist.sort()
            tentfrequency = collections.Counter(profTentativelist)
            tentfreqdict = dict(tentfrequency)

            totelproflist = proflist + profTentativelist
            totelproflist = list(set(totelproflist))
            totelproflist.sort()

            staffstring = ""
            for profdes in totelproflist:
                profcount = 0
                proftentcount = 0
                try:
                    profcount = freqdict[profdes]
                except:
                    pass
                try:
                    proftentcount = tentfreqdict[profdes]
                except:
                    pass

                staffstring += profdes
                if profcount > 1 and proftentcount == 0:
                    staffstring += "(" + str(profcount) + ")"
                elif profcount >= 0 and proftentcount > 0:
                    staffstring += "(" + str(profcount) + "/" + str(proftentcount) + ")"
                staffstring += ", "
            displaystring += indent + "Staff: " + staffstring[:-2]

        return displaystring

    def UpdateSingleCourseList(self, course: Course):
        """
        Updates a single course in the course list.

        :param course: Course object to be updated.
        """
        index = -1
        for i in range(len(self.mainapp.courses)):
            listitemstring = self.mainapp.courses[i].getName()
            if listitemstring == course.getName():
                index = i

        if index != -1:
            self.listitems.item(index).setText(self.courseString(course))

    def UpdateCourseList(self):
        # Clears and updates the course display list.
        self.listitems.clear()
        for course in self.mainapp.courses:
            displaystring = self.courseString(course)
            self.listitems.addItem(displaystring)
