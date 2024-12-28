"""
WeekViewer, ProfListWidget, CourseListWidget, and ProfessorViewer Classes

Description: Set of classes for displaying the schedule of a professor.  The professor can be
selected from a list on the right.  Once the professor is selected their weekly schedule will
be displayed in the main area.  Their course list and workload will be listed at the bottom.
There is no drag and drop in this viewer unlike the room viewer, but the course list has a context
menu for course properties, tentative selection, and removal of the course form timeslots or
the schedule.

@author: Don Spickler
Last Revision: 8/23/2022

"""

from PySide6.QtCore import (Qt, QMimeData, QPoint, QDir, QMarginsF, QSize)
from PySide6.QtGui import (QIcon, QColor, QBrush, QDrag, QPixmap, QPainter,
                           QFont, QFontMetrics, QMouseEvent, QCursor, QPageSize, QPageLayout, QAction, QActionGroup)
from PySide6.QtWidgets import (QWidget, QAbstractItemView, QMdiSubWindow, QListWidget, QGroupBox,
                               QTreeWidget, QVBoxLayout, QHBoxLayout, QListView, QMenuBar,
                               QLabel, QSplitter, QFrame, QFileDialog, QDialog, QMessageBox,
                               QRadioButton, QButtonGroup, QMenu, QApplication)
from PySide6.QtPrintSupport import (QPrintDialog, QPrinter, QPrintPreviewDialog)

import math
import datetime

from TimeSlot import TimeSlot
from FacultyList import FacultyList, FacultyTreeWidget
from Dialogs import *


class WeekViewer(QWidget):
    """
    Graphical widget that is derived off of the general QWidget.  It takes the information
    for the course list for the professor paints it onto the widget.
    """

    def __init__(self, parent=None, ma=None):
        """
        Sets up minimum size, turns on the mouse tracking, and sets a few variable defaults.

        :param parent: Pointer to the subwindow object,  CoursePositionViewer.
        :param ma: Pointer to the main Application, AcademicScheduler.
        """

        super(WeekViewer, self).__init__(parent)
        self.Parent = parent
        self.mainapp = ma

        self.setMouseTracking(True)
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        self.headerHeight = 0
        self.numberDays = 5
        self.timecolwidth = 0
        self.displaysize = QPoint(1, 1)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.mouseDown = False

        self.mousePosition = QPoint(0, 0)
        self.daysofweek = "MTWRFSU"

    def paintCourseRect(self, qp: QPainter, day: str, sh: int, sm: int, eh: int, em: int,
                        text: str, bordercol: QColor, backcol: QColor, textcol: QColor):
        """
        This function paints a single course/item rectangle to the display widget given the text,
        times, days, and colors.

        :param qp:  The QPainter object to be painted to.  Having this as a parameter allows
                    the same code to paint to a screen widget or to paint to the printer.
        :param day: The day of the week the rectangle is in, determines the horizontal position
                    of the rectangle.
        :param sh: The start hour for the rectangle.
        :param sm: The start minute for the rectangle.
        :param eh: The end hour for the rectangle.
        :param em: The end minute for the rectangle.
        :param text: The text to be drawn inside the rectangle.
        :param bordercol: The color of the border for the rectangle.
        :param backcol: The background color for the rectangle.
        :param textcol: The text color for the text inside the rectangle.
        """

        # Set positioning.
        stvpos = self.vertPositionAtTime(sh, sm)
        endvpos = self.vertPositionAtTime(eh, em)
        colindex = self.daysofweek.find(day)
        colwidth = self.displaysize.x() / self.numberDays

        hpos = int(colindex * colwidth + self.timecolwidth)
        nexthpos = int((colindex + 1) * colwidth + self.timecolwidth)

        # Draw in background color for rectangle.
        if backcol is not None:
            qp.fillRect(hpos, stvpos, nexthpos - hpos, endvpos - stvpos, backcol)

        # Draw in text for rectangle.  Text is split over new line characters and centered
        # in the box both horizontally and vertically.
        text = text.rstrip().lstrip()
        if text != "" and textcol is not None:
            qp.setPen(textcol)
            textlines = text.split("\n")
            textlines = [item.rstrip().lstrip() for item in textlines]
            divwidth = (endvpos - stvpos) / len(textlines)

            for line in textlines:
                linenum = textlines.index(line)
                topofspace = stvpos + linenum * divwidth
                fm = QFontMetrics(qp.font())
                fontheight = fm.height()
                baseline = topofspace + divwidth / 2 + fontheight / 2 - fm.descent()
                htextstart = (hpos + nexthpos - fm.horizontalAdvance(line)) / 2
                qp.drawText(QPoint(htextstart, baseline), line)

        # Draw in border color for rectangle.
        if bordercol is not None:
            qp.setPen(bordercol)
            qp.drawRect(hpos, stvpos, nexthpos - hpos, endvpos - stvpos)

    def paintTimeslot(self, qp: QPainter, timeslot: TimeSlot, text: str,
                      bordercol: QColor, backcol: QColor, textcol: QColor):
        """
        Paints a timeslot with given colors and text.  Uses the paintCourseRect to draw
        each individual rectangle.

        :param qp:  The QPainter object to be painted to.  Having this as a parameter allows
                    the same code to paint to a screen widget or to paint to the printer.
        :param timeslot: Timeslot object for the item.
        :param text: The text to be drawn inside the rectangle.
        :param bordercol: The color of the border for the rectangle.
        :param backcol: The background color for the rectangle.
        :param textcol: The text color for the text inside the rectangle.
        """
        for daychar in timeslot.Days:
            self.paintCourseRect(qp, daychar, timeslot.StartHour, timeslot.StartMinute,
                                 timeslot.EndHour, timeslot.EndMinute, text, bordercol,
                                 backcol, textcol)

    def paintEvent(self, event):
        """
        Paint event override for the widget.  Draws the days and hours on the border of the view.
        Puts the standard timeslots on the view and the display items which is a list of course
        information for the selected professor.

        :param event: Event object for painting.
        """

        # Set some preliminary values and lists.
        ww = self.width()
        wh = self.height()
        days = ["Time", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        headingColor = QColor()
        headingColor.setRgb(240, 240, 240)

        qp = QPainter()
        qp.begin(self)
        font = QFont('Arial', 10)
        fm = QFontMetrics(font)

        self.numberDays = 5

        for stdslot in self.Parent.standardtimeslots:
            if "S" in stdslot.Days:
                self.numberDays = 6
            if "U" in stdslot.Days:
                self.numberDays = 7

        if len(self.Parent.professorcourseslist) > 0:
            for course in self.Parent.professorcourseslist:
                if "S" in course[2].Days:
                    self.numberDays = 6
                if "U" in course[2].Days:
                    self.numberDays = 7

        ###################################
        # Find correct font size.
        ###################################

        # This block of code will start the font size at the minimum font size specified
        # in the options, then it will check if the text will fit inside the designated
        # areas at that size.  If it does the process is repeated with a font that is one
        # point higher.  This continues until the text is too large at the current font size.
        # Then the previous font size is used for the rendering of the image.

        starttime = self.Parent.starttime
        endtime = self.Parent.endtime
        divisions = endtime - starttime
        self.displaysize = QPoint(0, 0)

        if len(self.Parent.professorcourseslist) > 0:
            fontsize = self.mainapp.minimumGraphicFontSize
            fontfits = True
            while fontfits:
                fontsize += 1
                font = QFont('Arial', fontsize)
                fm = QFontMetrics(font)
                fontheight = fm.height()

                daycolwidth = 0
                self.headerHeight = int(1.5 * fontheight)
                timecolwidth = fm.horizontalAdvance("12:0000")
                self.displaysize = QPoint(ww - timecolwidth, wh - self.headerHeight)
                daycolwidth = int(self.displaysize.x() / self.numberDays)

                if fontheight > int(self.displaysize.y() / divisions):
                    fontfits = False

                for daytext in days[:self.numberDays + 1]:
                    if fm.horizontalAdvance(daytext + "00") > daycolwidth:
                        fontfits = False

                if fontfits:
                    for displayitem in self.Parent.professorcourseslist:
                        tw = max([fm.horizontalAdvance(displayitem[0] + "0"),
                                  fm.horizontalAdvance(displayitem[1] + "0")])

                        if tw > daycolwidth:
                            fontfits = False

                        timeslot = displayitem[2]
                        stvpos = self.vertPositionAtTime(timeslot.StartHour, timeslot.StartMinute)
                        endvpos = self.vertPositionAtTime(timeslot.EndHour, timeslot.EndMinute)
                        if fontheight * 2 > endvpos - stvpos:
                            fontfits = False

            fontsize -= 1
            font = QFont('Arial', fontsize)

        ###################################
        # Render the weekly image.
        ###################################

        # Set the font, create the font metrics, and set some positioning variables.
        qp.setFont(font)
        fm = QFontMetrics(font)
        fontheight = fm.height()
        self.headerHeight = int(1.5 * fontheight)
        self.timecolwidth = fm.horizontalAdvance(days[0] + "00")
        if self.timecolwidth < fm.horizontalAdvance("12:0000"):
            self.timecolwidth = fm.horizontalAdvance("12:0000")
        starttime = self.Parent.starttime
        endtime = self.Parent.endtime
        divisions = endtime - starttime

        self.displaysize = QPoint(ww - self.timecolwidth, wh - self.headerHeight)
        colwidth = self.displaysize.x() / self.numberDays

        # Clear the widget by drawing a white rectangle over the entire area.
        qp.fillRect(0, 0, ww, wh, QColor(Qt.white))

        # if no prof selected stop drawing.
        if self.Parent.getSelectedProf() == "":
            return

        # Draw header backgrounds
        qp.fillRect(0, 0, ww, self.headerHeight, headingColor)
        qp.fillRect(0, 0, self.timecolwidth, wh, headingColor)
        qp.setPen(QColor(Qt.black))

        # Draw in header.
        text = days[0]
        w = fm.horizontalAdvance(text)
        hpos = int(0.5 * (self.timecolwidth - w))
        qp.drawText(QPoint(hpos, fontheight), text)

        for i in range(1, self.numberDays + 1):
            text = days[i]
            w = fm.horizontalAdvance(text)
            hpos = int(self.timecolwidth + (i - 1) * colwidth + 0.5 * (colwidth - w))
            qp.drawText(QPoint(hpos, fontheight), text)

        qp.setPen(QColor(Qt.black))
        for i in range(1, self.numberDays + 1):
            qp.drawLine(self.timecolwidth + i * colwidth, 0, self.timecolwidth + i * colwidth, self.headerHeight)

        # Draw in times on the left.
        if starttime < endtime:
            for i in range(1, divisions):
                vpos = int(self.headerHeight + i * self.displaysize.y() / divisions)
                qp.setPen(QColor(Qt.black))
                qp.drawLine(0, vpos, self.timecolwidth, vpos)

            qp.setPen(QColor(Qt.black))
            for i in range(divisions):
                text = str(starttime + i) + ":00"
                if starttime + i > 12:
                    text = str(starttime + i - 12) + ":00"

                w = fm.horizontalAdvance(text)
                vpos = int(self.headerHeight + fontheight + i * self.displaysize.y() / divisions)  # - fm.descent()
                hpos = int(0.5 * (self.timecolwidth - w))
                qp.drawText(QPoint(hpos, vpos), text)

        # Draw in timeslots.
        for stdslot in self.Parent.standardtimeslots:
            self.paintTimeslot(qp, stdslot, "", QColor(Qt.lightGray), None, None)

        # Draw in classes.
        for displayitem in self.Parent.professorcourseslist:
            text = displayitem[0] + "\n" + displayitem[1]
            backcolor = self.mainapp.getChartBackgroundColor(displayitem[3])
            boarderColor = QColor(Qt.black)
            textcolor = QColor(Qt.black)

            oldfont = font
            if displayitem[4]:
                font.setItalic(True)
                qp.setFont(font)
                textcolor = QColor(Qt.darkGray)

            d, h, m = self.timeAtPosition(self.mousePosition.x(), self.mousePosition.y())
            highlightcoursestr = ""
            for highlightdisplayitem in self.Parent.professorcourseslist:
                if highlightdisplayitem[2].timeInSlot(d, h, m):
                    highlightcoursestr = highlightdisplayitem[0]

            if displayitem[0] == highlightcoursestr:
                backcolor = self.mainapp.getChartBackgroundHighlightColor(displayitem[3])
                boarderColor = QColor(Qt.red)

            self.paintTimeslot(qp, displayitem[2], text, boarderColor, backcolor, textcolor)
            oldfont.setItalic(False)
            qp.setFont(oldfont)

        # Draw header outlines.
        qp.setPen(QColor(Qt.black))
        qp.drawRect(0, 0, ww - 1, wh - 1)
        qp.drawRect(0, 0, ww - 1, self.headerHeight)
        qp.drawLine(self.timecolwidth, 0, self.timecolwidth, wh)
        for i in range(self.numberDays + 1):
            qp.drawLine(self.timecolwidth + i * colwidth, 0, self.timecolwidth + i * colwidth, wh)

        qp.end()

    def vertPositionAtTime(self, h: int, m: int) -> int:
        """
        Calculates the vertical position, in pixels, of the given hour and minute on the week
        viewer.

        :param h: Hour for position.
        :param m: Minute for position.
        :return: pixel position of the given time on the week viewer.
        """
        starttime = self.Parent.starttime
        endtime = self.Parent.endtime
        daylength = endtime - starttime
        vposdec = ((h - starttime) * 60 + m) / (daylength * 60)
        vpos = int(vposdec * self.displaysize.y() + self.headerHeight)
        return vpos

    def createEndTime(self, bh, bm, minutes):
        """
        Given a start time and number of minutes this will return the ending time of the slot.

        :param bh: Beginning hour.
        :param bm: Beginning minute.
        :param minutes: Length of time in minutes.
        :return: Ending hour and ending minute.
        """
        em = bm + minutes
        eh = bh
        while em > 60:
            em -= 60
            eh += 1
        return int(eh), int(em)

    def contextMenuEvent(self, e):
        """
        Cretaes a context menu for course options that mouse id currently over.

        :param e: Context menu event.
        """
        self.mousePosition = QPoint(e.x(), e.y())
        self.repaint()

        if len(self.Parent.professorcourseslist) == 0:
            return

        schedItem = None
        for displayitem in self.Parent.professorcourseslist:
            d, h, m = self.timeAtPosition(e.x(), e.y())
            if displayitem[2].timeInSlot(d, h, m):
                schedItem = self.mainapp.findScheduleItemFromString(displayitem[0])

        if not schedItem:
            return

        item = self.mainapp.courseNameAndSection(schedItem)

        # Create the context menu.
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
        courseTentative_act.triggered.connect(
            lambda: self.mainapp.makeCourseTentative(schedItem.InternalID, courseTentative_act.isChecked()))

        menu.addAction(courseProperties_act)
        menu.addAction(courseTentative_act)
        menu.addSeparator()
        menu.addAction(removeRooms_act)
        menu.addAction(removeSchedule_act)

        menu.exec_(self.mapToGlobal(e.pos()))

        self.mousePosition = self.mapFromGlobal(QCursor().pos())
        self.repaint()

    def timeAtPosition(self, x: int, y: int):
        """
        Calculates the time and day in the week schedule viewer for the current (x, y) mouse
        position.

        :param x: X position of the mouse.
        :param y: Y position of the mouse.
        :return: D, H, M of the position.
        """
        vpos = y - self.headerHeight
        hpos = x - self.timecolwidth
        starttime = self.Parent.starttime
        endtime = self.Parent.endtime
        daylength = endtime - starttime

        timedec = vpos / self.displaysize.y() * daylength
        hour = int(timedec) + starttime
        minute = (timedec - int(timedec)) * 60

        daypos = int(hpos / self.displaysize.x() * self.numberDays)
        if daypos < 0:
            daypos = 0
        elif daypos >= self.numberDays:
            daypos = self.numberDays - 1
        days = ["M", "T", "W", "R", "F", "S", "U"]

        return days[daypos], hour, minute

    def findCourseStringFromCurrentPosition(self) -> str:
        """
        Gets the course name and section for the class that the mouse is hovering over.

        :return: String representation of the course being hovered over.
        """
        firstFound = False
        coursestring = ""
        d, h, m = self.timeAtPosition(self.mousePosition.x(), self.mousePosition.y())
        for displayitem in self.Parent.professorcourseslist:
            if displayitem[2].timeInSlot(d, h, m) and (not firstFound):
                schedItem = self.mainapp.findScheduleItemFromString(displayitem[0])
                coursestring = self.mainapp.courseNameAndSection(schedItem)
                firstFound = True

        return coursestring

    def mouseDoubleClickEvent(self, e):
        """
        On a double click on a course in the viewer open up the course properties for that course.

        :param e: Mouse event.
        """
        self.mousePosition = QPoint(e.x(), e.y())
        coursestring = self.findCourseStringFromCurrentPosition()
        if coursestring == "":
            return
        self.mainapp.updateCourseProperties(coursestring)

    def mousePressEvent(self, e):
        """
        On a control-click bring up the course properties dialog and on a right click bring up
        the context menu for that course.

        :param e: Mouse event.
        """
        self.mousePosition = QPoint(e.x(), e.y())
        self.repaint()

        if e.button() == Qt.LeftButton:
            self.mouseDown = True
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.ControlModifier:
                coursestring = self.findCourseStringFromCurrentPosition()
                if coursestring == "":
                    return

                self.mouseDown = False
                self.mainapp.updateCourseProperties(coursestring)
        elif e.button() == Qt.RightButton:
            self.contextMenuEvent(e)

    def mouseReleaseEvent(self, e):
        """
        When mouse released set the mouseDown to false.

        :param e: Mouse event
        """
        self.mouseDown = False

    def mouseMoveEvent(self, e: QMouseEvent):
        """
        Mouse move event, update the position and repaint.

        :param e: Mouse event
        """
        self.mousePosition = QPoint(e.x(), e.y())
        self.repaint()

    def leaveEvent(self, e: QMouseEvent):
        """
        On a leave, set position off-screen and repaint.

        :param e: Mouse event
        """
        self.mousePosition = QPoint(-1, -1)
        self.repaint()
        self.mouseDown = False


class ProfListWidget(QListWidget):
    """
    Small derived class for the list of professors on the right.  If a change is made to the
    selected professor this notifies the viewer to make the appropriate updates.
    """
    def __init__(self, parent=None):
        """
        Sets the parent and minimum width.

        :param parent: Pointer to the professor viewer.
        """
        super(ProfListWidget, self).__init__(parent)
        self.Parent = parent
        self.setMinimumWidth(150)

    def selectionChanged(self, sel, des):
        """
        If change is made notify the parent of new selection.

        :param sel: Dummy variable for the selected.
        :param des: Dummy variable for the deselected.
        """
        items = self.selectedItems()
        if len(items) > 0:
            item = items[0].text()
            self.Parent.professorUpdated()

    def keyPressEvent(self, event):
        """ On enter, invoke the professor editor. """
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.Parent.editItem()
        QListWidget.keyPressEvent(self, event)

    def mouseDoubleClickEvent(self, event) -> None:
        """ On double-click, invoke the professor editor. """
        self.Parent.editItem()

class CourseListWidget(QListWidget):
    """
    Small derived class of QListWidget to add some functionality to the course list for
    the professor.  Enter or double-click on a course will open the course properties dialog.
    Right click will invoke the contect menu for the course.
    """
    def __init__(self, parent=None, ma=None):
        """
        Sets the context menu and mouse tracking.

        :param parent: Pointer to the parent object.
        :param ma: Pointer to the main app object.
        """
        super(CourseListWidget, self).__init__(parent)
        self.Parent = parent
        self.mainapp = ma
        self.customContextMenuRequested.connect(self.contextMenuEvent)
        self.setMouseTracking(True)

    def mouseDoubleClickEvent(self, e):
        """
        On a double click open up the course properties dialog.

        :param e: Mouse event
        """
        items = self.selectedItems()
        if len(items) > 0:
            item = items[0].text()
            coursestr = item.split(":")[0]
            self.mainapp.updateCourseProperties(coursestr)

    def keyPressEvent(self, event):
        """
        If key is return/enter open the course properties dialog for the class.

        :param event: Key pressed event.
        """
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            items = self.selectedItems()
            if len(items) > 0:
                item = items[0].text()
                coursestr = item.split(":")[0]
                self.mainapp.updateCourseProperties(coursestr)
        QListWidget.keyPressEvent(self, event)

    def contextMenuEvent(self, e):
        """
        Creates and displays the context menu for the currently selected class in the clss list.

        :param e: Context menu event.
        """
        items = self.selectedItems()
        if len(items) > 0:
            item = items[0].text()
            coursestr = item.split(":")[0]
            schedItem = self.mainapp.findScheduleItemFromString(coursestr)

            if not schedItem:
                return

            # Create the context menu.
            menu = QMenu(self)

            removeRooms_act = QAction("Remove Course from Rooms...", self)
            removeRooms_act.triggered.connect(lambda: self.mainapp.removeCourseRoomsAndTimes(coursestr))

            removeSchedule_act = QAction("Remove Course from Schedule...", self)
            removeSchedule_act.triggered.connect(lambda: self.mainapp.removeCourseFromSchedule(coursestr))

            courseProperties_act = QAction("Course Properties...", self)
            courseProperties_act.triggered.connect(lambda: self.mainapp.updateCourseProperties(coursestr))

            courseTentative_act = QAction("Tentative", self)
            courseTentative_act.setCheckable(True)
            courseTentative_act.setChecked(schedItem.Tentative)
            courseTentative_act.triggered.connect(
                lambda: self.mainapp.makeCourseTentative(schedItem.InternalID, courseTentative_act.isChecked()))

            menu.addAction(courseProperties_act)
            menu.addAction(courseTentative_act)
            menu.addSeparator()
            menu.addAction(removeRooms_act)
            menu.addAction(removeSchedule_act)

            menu.exec_(self.mapToGlobal(e.pos()))


class ProfessorViewer(QMdiSubWindow):
    """
    Subwindow for viewing the professor's schedule.  Window has a week viewer as the central
    widget displaying the professor's schedule, a list of professors on the right and
    a list of courses the professor is assigned at the bottom.
    """
    def __init__(self, parent):
        """
        Sets up the UI for the subwindow.

        :param parent: Pointer to the parent which must be the main app.
        """
        super(ProfessorViewer, self).__init__(parent)
        self.Parent = parent
        self.mainapp = parent
        self.setWindowIcon(QIcon(self.mainapp.resource_path('icons/ProgramIcon.png')))

        self.setWindowTitle("Professor Schedule Viewer")
        self.proflist = ProfListWidget(self)
        self.courselist = CourseListWidget(self, self.mainapp)
        self.weekviewer = WeekViewer(self, self.mainapp)
        self.starttime = 24
        self.endtime = 0

        self.professors = self.mainapp.faculty
        self.standardtimeslots = self.mainapp.standardtimeslots
        self.schedule = self.mainapp.schedule
        self.professorcourseslist = []

        self.workloadtitlelabel = QLabel("Workload: ")
        self.workloadlabel = QLabel()

        weekcourselistview = QSplitter(Qt.Vertical)
        weekcourselistview.setHandleWidth(5)
        weekcourselistview.addWidget(self.weekviewer)

        workloadline = QHBoxLayout()
        workloadline.setContentsMargins(0,0,0,0)
        workloadline.addWidget(self.workloadtitlelabel)
        workloadline.addWidget(self.workloadlabel)
        workloadline.addStretch(0)
        workloadlinewidget = QWidget()
        workloadlinewidget.setLayout(workloadline)

        workloadandcourselist = QVBoxLayout()
        workloadandcourselist.setContentsMargins(0,0,0,0)
        workloadandcourselist.addWidget(workloadlinewidget)
        workloadandcourselist.addWidget(self.courselist)
        workloadandcourselistwidget = QWidget()
        workloadandcourselistwidget.setLayout(workloadandcourselist)

        weekcourselistview.addWidget(workloadandcourselistwidget)

        mainview = QSplitter(Qt.Horizontal)
        mainview.setHandleWidth(5)
        mainview.addWidget(weekcourselistview)

        profswidget = QWidget()
        vbox = QVBoxLayout(profswidget)
        listlabel = QLabel("Faculty")
        vbox.setContentsMargins(0,0,0,0)
        vbox.addWidget(listlabel)
        vbox.addWidget(self.proflist)
        mainview.addWidget(profswidget)
        mainview.setCollapsible(0, False)
        mainview.setCollapsible(1, False)

        menu_bar = self.createMenu()
        menu_bar.setNativeMenuBar(False)

        mainarea = QWidget()
        mainlayout = QVBoxLayout(mainarea)
        mainlayout.setMenuBar(menu_bar)
        mainlayout.addWidget(mainview)
        mainlayout.setContentsMargins(0,0,0,0)

        self.setWidget(mainarea)
        self.updateData()
        self.getStartAndEndTimes()

    def createMenu(self):
        """ Set up the menu bar. """
        new_faculty_act = QAction(QIcon(self.Parent.resource_path('icons/NewFaculty.png')), "Add New Faculty...", self)
        new_faculty_act.setShortcut('Shift+Ctrl+N')
        new_faculty_act.triggered.connect(self.Parent.AddNewFaculty)

        edit_faculty_act = QAction(QIcon(self.Parent.resource_path('icons/Preferences.png')), "Edit Faculty...", self)
        edit_faculty_act.setShortcut('Shift+Ctrl+E')
        edit_faculty_act.triggered.connect(self.editItem)

        delete_faculty_act = QAction(QIcon(self.Parent.resource_path('icons/Delete.png')), "Delete Faculty Member...",
                                     self)
        delete_faculty_act.triggered.connect(self.deleteItem)

        saveImage_act = QAction(QIcon(self.Parent.resource_path('icons/FileSave.png')), "Save Image...", self)
        saveImage_act.triggered.connect(self.saveAsImage)

        copyImage_act = QAction(QIcon(self.Parent.resource_path('icons/CopyImage2.png')), "Copy Image", self)
        copyImage_act.triggered.connect(self.copyImageToClipboard)

        printImage_act = QAction(QIcon(self.Parent.resource_path('icons/print.png')), "Print...", self)
        printImage_act.triggered.connect(self.printImage)

        printPreviewImage_act = QAction(QIcon(self.Parent.resource_path('icons/preview.png')), "Print Preview...", self)
        printPreviewImage_act.triggered.connect(self.printPreviewImage)

        # Create the menu bar
        menu_bar = QMenuBar(self)

        main_menu = menu_bar.addMenu("Options")
        main_menu.addAction(new_faculty_act)
        main_menu.addAction(edit_faculty_act)
        main_menu.addSeparator()
        main_menu.addAction(delete_faculty_act)
        main_menu.addSeparator()
        main_menu.addAction(saveImage_act)
        main_menu.addAction(copyImage_act)
        main_menu.addSeparator()
        main_menu.addAction(printImage_act)
        main_menu.addAction(printPreviewImage_act)

        return menu_bar

    def getStartAndEndTimes(self):
        """
        This function goes through the list of standard timeslots and the list of courses
        assigned to the selected professor and determines the start and end times to
        view the schedule.  This is use by the week viewer to display the schedule.
        """
        self.starttime = 24
        self.endtime = 0
        for standardtimes in self.mainapp.standardtimeslots:
            if standardtimes.StartHour < self.starttime:
                self.starttime = standardtimes.StartHour
            if standardtimes.EndHour >= self.endtime:
                self.endtime = standardtimes.EndHour
                if standardtimes.EndMinute > 0:
                    self.endtime += 1

        for times in self.professorcourseslist:
            coursetime = times[2]
            if coursetime.StartHour < self.starttime:
                self.starttime = coursetime.StartHour
            if coursetime.EndHour >= self.endtime:
                self.endtime = coursetime.EndHour
                if coursetime.EndMinute > 0:
                    self.endtime += 1

    def updateProfessorList(self):
        """
        Updates the professor list.
        """
        profstr = self.getSelectedProf()

        self.proflist.clear()
        for prof in self.professors:
            self.proflist.addItem(prof.getName())

        if profstr != "":
            for i in range(self.proflist.count()):
                if self.proflist.item(i).text() == profstr:
                    self.proflist.setCurrentRow(i)

            self.repaint()

    def updateData(self):
        """
        Updates the data for the view.
        """
        self.professors = self.mainapp.faculty
        self.standardtimeslots = self.mainapp.standardtimeslots
        self.schedule = self.mainapp.schedule
        self.courselist.clear()
        self.workloadlabel.setText("")
        self.updateProfessorList()

    def getSelectedProf(self) -> str:
        """
        Returns the name of the professor that is selected.

        :return: String of the name of the professor that is selected.
        """
        items = self.proflist.selectedItems()
        if len(items) > 0:
            item = items[0].text()
            return item
        return ""

    def editItem(self):
        """
        Edit the currently selected professor.
        """
        profname = self.getSelectedProf()
        if profname != "":
            self.Parent.EditFaculty(profname)

    def deleteItem(self):
        """
        Delete the currently selected professor.
        """
        profname = self.getSelectedProf()
        if profname != "":
            self.Parent.DeleteFacultyMember(profname)

    def saveAsImage(self):
        """
        Saves the current week display to an image file.
        """
        dialog = QFileDialog()
        dialog.setFilter(dialog.filter() | QDir.Hidden)
        dialog.setDefaultSuffix('png')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters(['PNG Files (*.png)', 'JPEG Files (*.jpg)', 'Bitmap Files (*.bmp)'])
        dialog.setWindowTitle('Save Image As')

        if dialog.exec() == QDialog.Accepted:
            filelist = dialog.selectedFiles()
            if len(filelist) > 0:
                file_name = filelist[0]
                try:
                    pixmap = QPixmap(self.weekviewer.size())
                    self.weekviewer.render(pixmap)
                    pixmap.save(file_name)
                except:
                    QMessageBox.warning(self, "File Not Saved", "The file " + file_name + " could not be saved.",
                                        QMessageBox.Ok)

    def copyImageToClipboard(self):
        """
        Copies the current week display to the clipboard.
        """
        pixmap = QPixmap(self.weekviewer.size())
        self.weekviewer.render(pixmap)
        self.mainapp.clipboard.setPixmap(pixmap)

    def professorUpdated(self):
        """
        Updates the course list, workload, and weekly schedule image when the professor
        selection is changed.
        """
        profstr = self.getSelectedProf()
        profiid = -1
        if profstr != "":
            prof = self.mainapp.findProfessorFromString(profstr)
            profiid = prof.InternalID
            displaystr = profstr
            if not prof.Real:
                displaystr += "*"
            displaystr += "  (" + str(prof.ShortDes) + ")"
            self.setWindowTitle("Professor Schedule Viewer  -  " + displaystr)

            profdetails = ""
            wl, wlf, twl, twlf = self.mainapp.calculateProfessorWorkload(prof)
            profdetails += str(wl)
            if self.mainapp.options[1] > 1:
                profdetails += " / " + "{:.4f}".format(wlf)
            if twl > 0:
                profdetails += "     Tentative: " + str(twl)
                if self.mainapp.options[1] > 1:
                    profdetails += " / " + "{:.4f}".format(twlf)

            self.workloadlabel.setText(profdetails)

        # Get list of classes for display.
        self.professorcourseslist = []
        self.courselist.clear()

        schedule = self.mainapp.schedule
        for scheduleitem in schedule:
            coursename = self.mainapp.courseNameAndSection(scheduleitem)
            timeamountdes = self.mainapp.ScheduleItemTimeCheck(scheduleitem)
            isTentative = scheduleitem.Tentative

            if profiid in scheduleitem.ProfessorIID:
                for roomtimeslots in scheduleitem.RoomsAndTimes:
                    roomiid = roomtimeslots[0]
                    roomstr = self.mainapp.findRoomFromIID(roomiid).getName()
                    self.professorcourseslist.append([coursename, roomstr, roomtimeslots[1],
                                                      timeamountdes, isTentative])

                courseInfoString = coursename + ": " + self.mainapp.createTimeslotStringFromScheduleItem(scheduleitem)
                self.courselist.addItem(courseInfoString)
                font = self.courselist.item(self.courselist.count() - 1).font()
                if isTentative:
                    font.setItalic(True)
                    self.courselist.item(self.courselist.count() - 1).foreground().setColor(QColor(Qt.darkGray))
                    # self.courselist.item(self.courselist.count() - 1).setTextColor(QColor(Qt.darkGray))
                else:
                    font.setItalic(False)
                    self.courselist.item(self.courselist.count() - 1).foreground().setColor(QColor(Qt.black))
                    # self.courselist.item(self.courselist.count() - 1).setTextColor(QColor(Qt.black))
                self.courselist.item(self.courselist.count() - 1).setFont(font)

        self.courselist.sortItems()
        self.getStartAndEndTimes()
        self.weekviewer.repaint()

    def printImage(self):
        """
        Prints the weekly schedule image to the selected printer.
        """
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        printer.setDocName("ProfessorScheduleImage")
        printer.setResolution(300)
        pl = QPageLayout(QPageSize(QPageSize.Letter), QPageLayout.Landscape,
                         QMarginsF(36, 36, 36, 36))
        printer.setPageLayout(pl)
        if dialog.exec() == QDialog.Accepted:
            self.printPreview(printer)

    def printPreviewImage(self):
        """
        Invokes the print preview dialog for the schedule image.
        """
        printer = QPrinter()
        dialog = QPrintPreviewDialog(printer)
        printer.setDocName("ProfessorScheduleImage")
        printer.setResolution(300)
        pl = QPageLayout(QPageSize(QPageSize.Letter), QPageLayout.Portrait,
                         QMarginsF(36, 36, 36, 36))
        printer.setPageLayout(pl)

        dialog.paintRequested.connect(self.printPreview)
        dialog.exec()

    def printPreview(self, printer):
        """
        This handles the printing of the image to the printer.  The function creates an internal,
        off-screen, weekly viewer, sets its size to the image width and height times the resolution
        of the printer, renders the image to the off-screen viewer and then to a pixmap, finally
        prints the pixmap to the printer object.

        :param printer: Pointer to a printer object.
        """

        # Create off-screen viewer.
        printviewer = WeekViewer(self, self.mainapp)
        printres = printer.resolution()

        # Set width and height by resolution and scaling options.
        wid = self.mainapp.ImagePrintWidth * printres
        hei = self.mainapp.ImagePrintHeight * printres

        if self.mainapp.ImagePrintScaleMode == 0:
            hei = wid * self.weekviewer.height() / self.weekviewer.width()
        elif self.mainapp.ImagePrintScaleMode == 1:
            wid = hei * self.weekviewer.width() / self.weekviewer.height()

        # Set pixmap size, render, and send to printer.
        printviewer.setFixedSize(QSize(round(wid), round(hei)))
        pixmap = QPixmap(printviewer.size())
        printviewer.render(pixmap)
        painter = QPainter(printer)

        # Create description string.
        profstr = self.getSelectedProf()
        if self.mainapp.options[0] != "":
            profstr += "  /  " + self.mainapp.options[0]
        profstr += "  /  " + str(datetime.datetime.now())

        font = QFont("Arial", 12)
        fm = QFontMetrics(font)
        h = fm.height()
        painter.setFont(font)
        painter.setPen(QColor(Qt.black))
        painter.drawText(QPoint(0, h), profstr)

        painter.drawPixmap(QPoint(0, 2 * h), pixmap)
        painter.end()

    def printPreviewAll(self, profstrs):
        """
        Invokes the print preview dialog on all schedule inages.

        :param profstrs:  List of professor names to create weekly images for.
        """
        printer = QPrinter()
        dialog = QPrintPreviewDialog(printer)
        printer.setDocName("ProfessorViewerImage")
        printer.setResolution(300)
        pl = QPageLayout(QPageSize(QPageSize.Letter), QPageLayout.Portrait,
                         QMarginsF(36, 36, 36, 36))
        printer.setPageLayout(pl)

        self.profstringstoprint = profstrs

        dialog.paintRequested.connect(self.printAllImages)
        dialog.exec()
        self.profstringstoprint = None

    def printAllImages(self, printer):
        """
        This handles the printing of the image to the printer.  The function creates an internal,
        off-screen, weekly viewer and professor viewer sub-window, sets its size to the image width
        and height times the resolution of the printer, renders the image to the off-screen viewer
        and then to a pixmap, finally prints the pixmap to the printer object.

        :param printer: Pointer to a printer object.
        """

        # Create off-screen viewer.
        offscreenprofviewer = ProfessorViewer(self.mainapp)
        printviewer = offscreenprofviewer.weekviewer
        printres = printer.resolution()

        # Set width and height by resolution and scaling options.
        wid = self.mainapp.ImagePrintWidth * printres
        hei = self.mainapp.ImagePrintHeight * printres

        if self.mainapp.ImagePrintScaleMode == 0:
            hei = wid * self.weekviewer.height() / self.weekviewer.width()
        elif self.mainapp.ImagePrintScaleMode == 1:
            wid = hei * self.weekviewer.width() / self.weekviewer.height()

        painter = QPainter(printer)

        # Run through the professors, paint the image and description to a page and
        # advance to the next page.
        count = 0
        for i in range(offscreenprofviewer.proflist.count()):
            offscreenprofviewer.proflist.setCurrentRow(i)
            profstr = offscreenprofviewer.getSelectedProf()
            if profstr in self.profstringstoprint:
                printviewer.setFixedSize(QSize(round(wid), round(hei)))
                pixmap = QPixmap(printviewer.size())
                printviewer.render(pixmap)

                if self.mainapp.options[0] != "":
                    profstr += "  /  " + self.mainapp.options[0]
                profstr += "  /  " + str(datetime.datetime.now())

                font = QFont("Arial", 12)
                fm = QFontMetrics(font)
                h = fm.height()
                painter.setFont(font)
                painter.setPen(QColor(Qt.black))
                painter.drawText(QPoint(0, h), profstr)
                painter.drawPixmap(QPoint(0, 2 * h), pixmap)
                if count < len(self.profstringstoprint) - 1:
                    printer.newPage()
                count += 1

        painter.end()
