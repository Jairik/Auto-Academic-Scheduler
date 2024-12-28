"""
CourseLinker Class

Description: The CourseLinker is just a view for the linking of main to subsequent classes, such
as a course with a lab or set of labs.  The class itself is an MDI sub window in the main application.
The constructor takes the parameter of a pointer to the main class which does the actual linking.
This is essentially a callback system where the view is handling the UI and the main is doing the
updates to the schedule database.

The window consists of three lists, the main course, the subsequent course, and a list of already
linked courses.  The UpdateLinkerLists function creates the three lists.  It references the
databases, primarily the schedule, from the mainapp and displays the information in the lists.

The three lists are selectable, the main is single selection only, the subsequent list is multiple
selection and the linked list is single selection.

@author: Don Spickler
Last Revision: 8/9/2022

"""

from PySide6.QtCore import (Qt, QMimeData, QPoint)
from PySide6.QtGui import (QIcon, QColor, QBrush, QDrag, QPixmap, QPainter, QFont, QFontMetrics, QAction)
from PySide6.QtWidgets import (QWidget, QAbstractItemView, QMdiSubWindow, QListWidget, QGroupBox,
                               QTreeWidget, QVBoxLayout, QHBoxLayout, QListView, QMenuBar,
                               QLabel)


class CourseLinker(QMdiSubWindow):

    def __init__(self, parent):
        """ Constructor sets up the UI. """
        super(CourseLinker, self).__init__(parent)
        self.Parent = parent
        self.mainapp = parent

        self.setWindowTitle("Course Linker")
        self.setWindowIcon(QIcon(self.mainapp.resource_path('icons/ProgramIcon.png')))

        # Create the three lists and set selection modes.
        self.maincourses = QListWidget()
        self.subcourses = QListWidget()
        self.subcourses.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.linkedcourses = QListWidget()

        menu_bar = self.createMenu()
        menu_bar.setNativeMenuBar(False)
        mainarea = QWidget()

        # Configure the main course list.
        maincoursewidget = QWidget()
        vbox = QVBoxLayout(maincoursewidget)
        listlabel = QLabel("Main/Lecture Course")
        vbox.setContentsMargins(0,0,0,0)
        vbox.addWidget(listlabel)
        vbox.addWidget(self.maincourses)

        # Configure the subsequent course list.
        subcoursewidget = QWidget()
        vbox = QVBoxLayout(subcoursewidget)
        listlabel = QLabel("Subsequent/Lab Course")
        vbox.setContentsMargins(0,0,0,0)
        vbox.addWidget(listlabel)
        vbox.addWidget(self.subcourses)

        # Configure the linked course list.
        linkedcoursewidget = QWidget()
        vbox = QVBoxLayout(linkedcoursewidget)
        listlabel = QLabel("Linked Courses")
        vbox.setContentsMargins(5,5,5,5)
        vbox.addWidget(listlabel)
        vbox.addWidget(self.linkedcourses)

        # Position lists and menu in the layout.
        upperLists = QWidget()
        toplayout = QHBoxLayout(upperLists)
        toplayout.setContentsMargins(5,5,5,5)
        toplayout.addWidget(maincoursewidget)
        toplayout.addWidget(subcoursewidget)

        mainlayout = QVBoxLayout(mainarea)
        mainlayout.setMenuBar(menu_bar)
        mainlayout.addWidget(upperLists)
        mainlayout.addWidget(linkedcoursewidget)
        mainlayout.setContentsMargins(0,0,0,0)

        self.setWidget(mainarea)

    def closeEvent(self, event):
        """ Subwindow close in the main MDI. """
        self.Parent.closeSubWindow(self)

    def createMenu(self):
        """ Set up the menu bar. """

        # Define the actions.
        link_act = QAction(QIcon(self.Parent.resource_path('icons/Link2.png')), "Link Courses", self)
        link_act.setShortcut('Ctrl+L')
        link_act.triggered.connect(self.LinkSelectedCourses)

        unlink_act = QAction(QIcon(self.Parent.resource_path('icons/Unlink.png')), "Unlink Courses", self)
        unlink_act.setShortcut('Ctrl+U')
        unlink_act.triggered.connect(self.UnlinkSelectedCourses)

        # Create the menu bar and load the action.
        menu_bar = QMenuBar(self)
        main_menu = menu_bar.addMenu("Options")
        main_menu.addAction(link_act)
        main_menu.addAction(unlink_act)

        return menu_bar

    def LinkSelectedCourses(self):
        """ Take selected courses and call LinkCourses in the main to alter the database. """
        mainselection = self.maincourses.selectedItems()
        subselection = self.subcourses.selectedItems()

        if len(mainselection) == 0 or len(subselection) == 0:
            return

        # Extract name and section of courses.
        mainselection = mainselection[0].text().split(":")[0]
        subitems = [item.text().split(":")[0] for item in subselection]
        self.mainapp.LinkCourses(mainselection, subitems)
        self.UpdateLinkerLists()

    def UnlinkSelectedCourses(self):
        """ Take selected course in the linked list and call UninkCourses in the main
            to alter the database.
        """
        mainselection = self.linkedcourses.selectedItems()
        if len(mainselection) == 0:
            return

        # Extract name and section of course.
        mainselection = mainselection[0].text().split(":")[0]
        self.mainapp.UninkCourses(mainselection)
        self.UpdateLinkerLists()

    def UpdateLinkerLists(self):
        """ Function to update the list views.
        """

        # CLear the three lists for updating.
        self.maincourses.clear()
        self.subcourses.clear()
        self.linkedcourses.clear()

        # List of course ids that are either linked or linked to.
        linkedcourseslist = []

        # Populate linkedcourseslist.
        for scheditem in self.mainapp.schedule:
            if len(scheditem.LinkedCourses) > 0:
                linkedcourseslist.append(scheditem.InternalID)
                linkedcourseslist.extend(scheditem.LinkedCourses)

        # Find all non-linked courses. Create list string and load into both the main and sub lists.
        for scheditem in self.mainapp.schedule:
            if not (scheditem.InternalID in linkedcourseslist):
                coursestr = self.mainapp.courseNameAndSection(scheditem) + ": "
                firstprof = True
                for piid in scheditem.ProfessorIID:
                    prof = self.mainapp.findProfessorFromIID(piid)
                    if not firstprof:
                        coursestr += " / "
                    firstprof = False
                    coursestr += prof.getName()

                self.maincourses.addItem(coursestr)
                self.subcourses.addItem(coursestr)

        self.maincourses.sortItems(Qt.AscendingOrder)
        self.subcourses.sortItems(Qt.AscendingOrder)

        # Find all linked courses. Create list string and load into linked lists.
        for scheditem in self.mainapp.schedule:
            if len(scheditem.LinkedCourses) > 0:
                coursestr = self.mainapp.courseNameAndSection(scheditem) + ": "
                firstprof = True
                for piid in scheditem.ProfessorIID:
                    prof = self.mainapp.findProfessorFromIID(piid)
                    if not firstprof:
                        coursestr += " / "
                    firstprof = False
                    coursestr += prof.getName()

                subcoursestringlist = []
                for sid in scheditem.LinkedCourses:
                    subscheditem = self.mainapp.findScheduleItemFromIID(sid)
                    subcoursestr = self.mainapp.courseNameAndSection(subscheditem) + ": "
                    firstprof = True
                    for piid in subscheditem.ProfessorIID:
                        prof = self.mainapp.findProfessorFromIID(piid)
                        if not firstprof:
                            subcoursestr += " / "
                        firstprof = False
                        subcoursestr += prof.getName()
                    subcoursestringlist.append(subcoursestr)

                subcoursestringlist.sort()
                for subcoursestr in subcoursestringlist:
                    coursestr += "\n      ==>  " + subcoursestr

                self.linkedcourses.addItem(coursestr)
                self.linkedcourses.sortItems(Qt.AscendingOrder)
