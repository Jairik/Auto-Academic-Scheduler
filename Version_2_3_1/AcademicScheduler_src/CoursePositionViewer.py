"""
CoursePositionViewer Class and WeekViewer Class

Description: The CoursePositionViewer is a viewer for course placement and overlaps during the week.  It is
useful for finding possible scheduling issues such as course conbflicts and course offerings not being
spread out sufficiently.  The WeekViewer is a custom-built tool, derived from the base QWidget to display positioning
and overlaps in courses.

The subwindow consists of the WeekViewer and course/class selection list along with a menu and status bar.  When the
selection in the course list is changed the tally functions find positioning and overlaps which is then rendered
in the WeekViewer.

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

from PySide6.QtPrintSupport import QPrintDialog, QPrinter, QPrintPreviewDialog

import math
import datetime

from TimeSlot import TimeSlot
from FacultyList import FacultyList, FacultyTreeWidget
from Dialogs import *


class WeekViewer(QWidget):
    """
    Graphical widget that is derived off of the general QWidget.  It takes the information
    for the course positions and overlaps and paints them onto the widget.
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
        self.daysofweek = "MTWRFSU"
        self.mousePosition = QPoint(0, 0)

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
        Puts the standard timeslots on the view and the display items which is a list of overlap
        information.  The end of the function creates a string of all scheduled classes at the
        position of the mouse.  These are displayed in the status bar if the status bar is
        visible.

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

        if self.Parent.includeSaturday:
            self.numberDays = 6
        if self.Parent.includeSunday:
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

            stvpos = self.vertPositionAtTime(8, 0)
            endvpos = self.vertPositionAtTime(9, 0)
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

        # If nothing to draw return.
        if len(self.Parent.timeslottally) == 0:
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

        # Draw in classes/items really color rectangles for overlap tracking.
        for displayitem in self.Parent.timeslottally:
            if displayitem[1] > 0:
                backcolor = QColor(Qt.green)
                if displayitem[1] < 6:
                    backcolor = self.Parent.colorlist[displayitem[1] - 1]

                if displayitem[1] > self.Parent.maxoverlap:
                    backcolor = QColor(Qt.red)

                self.paintTimeslot(qp, displayitem[0], "", None, backcolor, None)

        # Draw header outlines.
        qp.setPen(QColor(Qt.black))
        qp.drawRect(0, 0, ww - 1, wh - 1)
        qp.drawRect(0, 0, ww - 1, self.headerHeight)
        qp.drawLine(self.timecolwidth, 0, self.timecolwidth, wh)
        for i in range(self.numberDays + 1):
            qp.drawLine(self.timecolwidth + i * colwidth, 0, self.timecolwidth + i * colwidth, wh)

        qp.end()

        # Create the status bar string of all courses that are scheduled in the position of
        # the mouse.

        # Get day, hour, and minute for the current mouse position.
        d, h, m = self.timeAtPosition(self.mousePosition.x(), self.mousePosition.y())

        # Create a list of all courses at the mouse position time.
        hoverlist = []
        if self.Parent.viewCourseMode:
            for coursestr in self.Parent.classselectedlist:
                course = self.mainapp.findCourseFromString(coursestr)
                for scheditem in self.mainapp.schedule:
                    if scheditem.CourseIID == course.InternalID:
                        if self.Parent.includeTentativeClasses or (not scheditem.Tentative):
                            for slot in scheditem.RoomsAndTimes:
                                if slot[1].timeInSlot(d, h, m):
                                    namesec = self.mainapp.courseNameAndSection(scheditem)
                                    hoverlist.append(namesec)
        else:
            for scheditem in self.mainapp.schedule:
                namesec = self.mainapp.courseNameAndSection(scheditem)
                if namesec in self.Parent.classselectedlist:
                    if self.Parent.includeTentativeClasses or (not scheditem.Tentative):
                        for slot in scheditem.RoomsAndTimes:
                            if slot[1].timeInSlot(d, h, m):
                                hoverlist.append(namesec)

        # Remove duplicates, sort, separate multiple listings with / and call the status bar
        # update function.
        hoverlist = list(set(hoverlist))
        hoverlist.sort()
        hoverliststr = ""
        for i in range(len(hoverlist)):
            hoverliststr += hoverlist[i]
            if i < len(hoverlist) - 1:
                hoverliststr += " / "

        self.Parent.updateStatusBar(hoverliststr)

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

    def mouseMoveEvent(self, e: QMouseEvent):
        """ Mouse move override that updates the mouse position variable and repaints. """
        self.mousePosition = QPoint(e.x(), e.y())
        self.repaint()

    def leaveEvent(self, e: QMouseEvent):
        """ Mouse leave override that sets the mouse position variable to (-1, -1) and repaints. """
        self.mousePosition = QPoint(-1, -1)
        self.repaint()


class CoursePositionViewer(QMdiSubWindow):
    """
    MDI child window derived off of a general QMdiSubWindow.  This window consists of a week viewer object
    for displaying the course positions, a course/class list on the right for selecting the courses to view,
    and a menu and status bar.
    """

    def __init__(self, parent):
        """
        Sets up the UI for the window and sets some variables used by the weekly viewer for rendering.

        :param parent: Pointer to the main application.
        """
        super(CoursePositionViewer, self).__init__(parent)
        self.Parent = parent
        self.mainapp = parent
        self.setWindowIcon(QIcon(self.mainapp.resource_path('icons/ProgramIcon.png')))

        # Set up UI
        self.setWindowTitle("Course Position Viewer")
        self.classlist = QListWidget()
        self.classlist.setMinimumWidth(100)
        self.classlist.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.classlist.selectionModel().selectionChanged.connect(self.coursesUpdated)

        self.weekviewer = WeekViewer(self, self.mainapp)
        self.starttime = 24
        self.endtime = 0

        # Set pointers to the schedule and timeslots in the main.  Also initialize data lists
        # and variables used for rendering.
        self.standardtimeslots = self.mainapp.standardtimeslots
        self.schedule = self.mainapp.schedule
        self.coursetimeslotlist = []
        self.timeslottally = []
        self.classselectedlist = []
        self.includeSaturday = False
        self.includeSunday = False
        self.includeTentativeClasses = False
        self.viewCourseMode = True

        # Set the colors used for different amounts of course overlap.
        self.colorlist = []
        self.maxoverlap = 1

        color = QColor(Qt.green)
        self.colorlist.append(color)
        color = QColor(Qt.darkCyan)
        self.colorlist.append(color)
        color = QColor(Qt.magenta)
        self.colorlist.append(color)
        color = QColor(Qt.cyan)
        self.colorlist.append(color)
        color = QColor(Qt.yellow)
        self.colorlist.append(color)
        color = QColor(Qt.gray)
        self.colorlist.append(color)

        # Finalize UI for the main window.
        mainview = QSplitter(Qt.Horizontal)
        mainview.setHandleWidth(5)

        coursesswidget = QWidget()
        vbox = QVBoxLayout(coursesswidget)
        listlabel = QLabel("Courses")
        vbox.setContentsMargins(0,0,0,0)
        vbox.addWidget(listlabel)
        vbox.addWidget(self.classlist)
        mainview.addWidget(self.weekviewer)
        mainview.addWidget(coursesswidget)
        mainview.setCollapsible(0, False)
        mainview.setCollapsible(1, False)

        self.statusText = QLabel()
        sttextfont = self.statusText.font()
        fm = QFontMetrics(sttextfont)
        sttextheight = fm.height()
        self.statusText.setMaximumHeight(sttextheight)

        menu_bar = self.createMenu()
        menu_bar.setNativeMenuBar(False)

        mainarea = QWidget()
        mainlayout = QVBoxLayout(mainarea)
        mainlayout.setMenuBar(menu_bar)
        mainlayout.addWidget(mainview)
        mainlayout.addWidget(self.statusText)
        mainlayout.setContentsMargins(0,0,0,0)

        self.setWidget(mainarea)
        self.updateData()
        self.getStartAndEndTimes()

    def createMenu(self):
        """ Set up the menu bar. """

        # Create actions.
        saveImage_act = QAction(QIcon(self.Parent.resource_path('icons/FileSave.png')), "Save Image...", self)
        saveImage_act.triggered.connect(self.saveAsImage)

        copyImage_act = QAction(QIcon(self.Parent.resource_path('icons/CopyImage2.png')), "Copy Image", self)
        copyImage_act.triggered.connect(self.copyImageToClipboard)

        printImage_act = QAction(QIcon(self.Parent.resource_path('icons/print.png')), "Print...", self)
        printImage_act.triggered.connect(self.printImage)

        printPreviewImage_act = QAction(QIcon(self.Parent.resource_path('icons/preview.png')), "Print Preview...", self)
        printPreviewImage_act.triggered.connect(self.printPreviewImage)

        self.showStatusBar_act = QAction("Show Status Bar", self)
        self.showStatusBar_act.triggered.connect(self.toggleStatusBar)
        self.showStatusBar_act.setCheckable(True)
        self.showStatusBar_act.setChecked(True)

        # Course or Class view selections and groups.
        courseView_act = QAction("Courses", self)
        courseView_act.triggered.connect(self.courseView)

        classesView_act = QAction("Individual Classes", self)
        classesView_act.triggered.connect(self.classesView)

        courseView_act.setCheckable(True)
        classesView_act.setCheckable(True)

        viewtypegroup = QActionGroup(self)
        viewtypegroup.addAction(courseView_act)
        viewtypegroup.addAction(classesView_act)
        courseView_act.setChecked(True)
        viewtypegroup.triggered.connect(self.setOverlapModeChange)

        # Highlighting amount selections and group.
        overlap2_act = QAction("Highlight Any Overlap", self)
        overlap2_act.triggered.connect(self.overlapset1)

        overlap3_act = QAction("Highlight up to 3 Overlaps", self)
        overlap3_act.triggered.connect(self.overlapset2)

        overlap4_act = QAction("Highlight up to 4 Overlaps", self)
        overlap4_act.triggered.connect(self.overlapset3)

        overlap5_act = QAction("Highlight up to 5 Overlaps", self)
        overlap5_act.triggered.connect(self.overlapset4)

        overlap6_act = QAction("Highlight up to 6 Overlaps", self)
        overlap6_act.triggered.connect(self.overlapset5)

        overlap2_act.setCheckable(True)
        overlap3_act.setCheckable(True)
        overlap4_act.setCheckable(True)
        overlap5_act.setCheckable(True)
        overlap6_act.setCheckable(True)

        overlapgroup = QActionGroup(self)
        overlapgroup.addAction(overlap2_act)
        overlapgroup.addAction(overlap3_act)
        overlapgroup.addAction(overlap4_act)
        overlapgroup.addAction(overlap5_act)
        overlapgroup.addAction(overlap6_act)
        overlap2_act.setChecked(True)
        overlapgroup.triggered.connect(self.setOverlapModeChange)

        # Tentative inclusion check box action.
        self.includeTentative_act = QAction("Include Tentative Classes", self)
        self.includeTentative_act.triggered.connect(self.includeTentative)
        self.includeTentative_act.setCheckable(True)
        self.includeTentative_act.setChecked(False)

        # Create the menu bar
        menu_bar = QMenuBar(self)

        main_menu = menu_bar.addMenu("Options")
        main_menu.addSeparator()
        main_menu.addAction(saveImage_act)
        main_menu.addAction(copyImage_act)
        main_menu.addSeparator()
        main_menu.addAction(printImage_act)
        main_menu.addAction(printPreviewImage_act)
        main_menu.addSeparator()
        main_menu.addAction(self.showStatusBar_act)

        view_menu = menu_bar.addMenu("View")
        view_menu.addAction(courseView_act)
        view_menu.addAction(classesView_act)
        view_menu.addSeparator()
        view_menu.addAction(overlap2_act)
        view_menu.addAction(overlap3_act)
        view_menu.addAction(overlap4_act)
        view_menu.addAction(overlap5_act)
        view_menu.addAction(overlap6_act)
        view_menu.addSeparator()
        view_menu.addAction(self.includeTentative_act)

        return menu_bar

    def courseView(self):
        """ Set to course view mode. """
        self.viewCourseMode = True
        self.updateCourseList()

    def classesView(self):
        """ Set to class view mode. """
        self.viewCourseMode = False
        self.updateCourseList()

    def setOverlapModeChange(self):
        """ Called if the overlap mode is changed. """
        self.weekviewer.repaint()

    def overlapset1(self):
        """ Set overlap mode to any overlap. """
        self.maxoverlap = 1

    def overlapset2(self):
        """ Set overlap mode to track 3 overlaps. """
        self.maxoverlap = 2

    def overlapset3(self):
        """ Set overlap mode to track 4 overlaps. """
        self.maxoverlap = 3

    def overlapset4(self):
        """ Set overlap mode to track 5 overlaps. """
        self.maxoverlap = 4

    def overlapset5(self):
        """ Set overlap mode to track 6 overlaps. """
        self.maxoverlap = 5

    def includeTentative(self):
        """ Toggle tentative course inclusion. """
        self.includeTentativeClasses = self.includeTentative_act.isChecked()
        self.coursesUpdated()

    def toggleStatusBar(self):
        """ Toggle the visibility of the status bar. """
        self.statusText.setVisible(self.showStatusBar_act.isChecked())

    def updateStatusBar(self, text):
        """
        Update status bar with input text.

        :param text: Text to place in the status bar.  This is created in the weekly viewer class since
                    it depends on the position of the mouse over the widget.
        """
        self.statusText.setText(text)

    def getStartAndEndTimes(self):
        """
        Finds the start and end times for rendering the weekly overlap image.  It finds the start and end
        times that incorporate all the standard timeslots from the main app and does the same for the
        list of timeslots of the selected courses from the course selection list.  The selected course list
        is created in the coursesUpdated function.
        """
        self.starttime = 24
        self.endtime = 0
        self.includeSaturday = False
        self.includeSunday = False

        # Process times in the standard timeslots.
        for standardtimes in self.mainapp.standardtimeslots:
            if "S" in standardtimes.Days:
                self.includeSaturday = True
            if "U" in standardtimes.Days:
                self.includeSaturday = True
                self.includeSunday = True

            if standardtimes.StartHour < self.starttime:
                self.starttime = standardtimes.StartHour
            if standardtimes.EndHour >= self.endtime:
                self.endtime = standardtimes.EndHour
                if standardtimes.EndMinute > 0:
                    self.endtime += 1

        # Process times in the list of selected courses.
        for coursetime in self.coursetimeslotlist:
            if "S" in coursetime.Days:
                self.includeSaturday = True
            if "U" in coursetime.Days:
                self.includeSaturday = True
                self.includeSunday = True

            if coursetime.StartHour < self.starttime:
                self.starttime = coursetime.StartHour
            if coursetime.EndHour >= self.endtime:
                self.endtime = coursetime.EndHour
                if coursetime.EndMinute > 0:
                    self.endtime += 1

    def updateCourseList(self):
        """
        Updates the course list when the window is opened and when there is a change to the course database.
        If in class mode the tentative courses are gray and italics.
        """

        # Create course/class list.
        courseslist = []
        if self.viewCourseMode:
            for scheduleitem in self.schedule:
                course = self.mainapp.findCourseFromIID(scheduleitem.CourseIID)
                if course.getName() not in courseslist:
                    courseslist.append(course.getName())
        else:
            for scheduleitem in self.schedule:
                courseslist.append([self.mainapp.courseNameAndSection(scheduleitem), scheduleitem.Tentative])

        # Add data items to the displayed list.
        self.classlist.clear()
        courseslist.sort()
        for item in courseslist:
            if self.viewCourseMode:
                self.classlist.addItem(item)
            else:
                self.classlist.addItem(item[0])
                font = self.classlist.item(self.classlist.count() - 1).font()
                if item[1]:
                    font.setItalic(True)
                    # self.classlist.item(self.classlist.count() - 1).setTextColor(QColor(Qt.darkGray))
                    self.classlist.item(self.classlist.count() - 1).foreground().setColor(QColor(Qt.darkGray))
                else:
                    font.setItalic(False)
                    # self.classlist.item(self.classlist.count() - 1).setTextColor(QColor(Qt.black))
                    self.classlist.item(self.classlist.count() - 1).foreground().setColor(QColor(Qt.black))
                self.classlist.item(self.classlist.count() - 1).setFont(font)

        self.coursesUpdated()

    def updateData(self):
        """
        Updates the course list but retains the selections that were current.  So if there were selections and
        a course is added to the database this will update the course list and reselect the courses before the
        update.
        """
        self.standardtimeslots = self.mainapp.standardtimeslots
        self.schedule = self.mainapp.schedule
        classselectedlist = self.getSelectedClasses()
        self.classlist.clear()
        self.updateCourseList()

        for i in range(self.classlist.count()):
            item = self.classlist.item(i)
            if item.text() in classselectedlist:
                item.setSelected(True)

    def getSelectedClasses(self) -> []:
        """
        Simply constructs and returns the list of currently selected classes/courses from the list.

        :return: A list of selected courses/classes from the list.
        """
        items = self.classlist.selectedItems()
        itemlist = []
        for item in items:
            itemlist.append(item.text())

        return itemlist

    def saveAsImage(self):
        """
        Saves the weekly viewer image to an image file.  File types are determined by the extension on
        the selected filename and is open to any type that the system supports.  The default is PNG and
        the filters are PNG, JPG, and BMP, the types supported by the three main OSs, according to the
        documentation.
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
        """ Copies the image to the clipboard. """
        pixmap = QPixmap(self.weekviewer.size())
        self.weekviewer.render(pixmap)
        self.mainapp.clipboard.setPixmap(pixmap)

    def coursesUpdated(self):
        """
        This is called when there is a change in the course selection list.  The function determines the
        days of the week to use and the timespan of each day.  It creates a list of timeslots each 5 minutes
        in length, adjacent to each other, and covers the entire week.  It then tallies the number of selected
        courses in each of these 5 minute slots for rendering.   The tally is stored in self.timeslottally.
        """

        # If no selected courses return.
        self.classselectedlist = []
        self.classselectedlist = self.getSelectedClasses()
        if self.classselectedlist == []:
            self.timeslottally = []
            self.weekviewer.repaint()
            return

        # Create a list of timeslots used by the courses that are selected.
        self.coursetimeslotlist = []
        if self.viewCourseMode:
            for coursestr in self.classselectedlist:
                course = self.mainapp.findCourseFromString(coursestr)
                for scheditem in self.schedule:
                    if scheditem.CourseIID == course.InternalID:
                        if self.includeTentativeClasses or (not scheditem.Tentative):
                            for slot in scheditem.RoomsAndTimes:
                                self.coursetimeslotlist.append(slot[1])
        else:
            for scheditem in self.schedule:
                if self.mainapp.courseNameAndSection(scheditem) in self.classselectedlist:
                    if self.includeTentativeClasses or (not scheditem.Tentative):
                        for slot in scheditem.RoomsAndTimes:
                            self.coursetimeslotlist.append(slot[1])

        # Get days and timespan to cover.
        self.getStartAndEndTimes()
        self.timeslottally = []
        dayendhour = self.endtime
        daylist = ["M", "T", "W", "R", "F"]
        if self.includeSaturday:
            daylist.append("S")
        if self.includeSunday:
            daylist.append("U")

        for day in daylist:
            hour = self.starttime
            minute = 0
            while hour < dayendhour:
                slot = TimeSlot()
                endminute = minute + 5
                endhour = hour
                if endminute >= 60:
                    endhour += 1
                    endminute = 0
                slot.setData(day, hour, minute, endhour, endminute)
                self.timeslottally.append([slot, 0])
                minute += 5
                if minute >= 60:
                    hour += 1
                    minute = 0

        # Tally up the 5-minute slot counts.
        for slotcount in self.timeslottally:
            slot = slotcount[0]
            for courseslot in self.coursetimeslotlist:
                if courseslot.timeStrictlyInSlot(slot.Days, slot.StartHour, slot.StartMinute) or \
                        courseslot.timeStrictlyInSlot(slot.Days, slot.EndHour, slot.EndMinute):
                    slotcount[1] += 1

        self.weekviewer.repaint()

    def printImage(self):
        """ Prints the overlap image.  The printPreview function does the printing.  """
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        printer.setDocName("CoursePositionImage")
        printer.setResolution(300)
        pl = QPageLayout(QPageSize(QPageSize.Letter), QPageLayout.Landscape,
                         QMarginsF(36, 36, 36, 36))
        printer.setPageLayout(pl)
        if dialog.exec() == QDialog.Accepted:
            self.printPreview(printer)

    def printPreviewImage(self):
        """
        Invokes the print preview dialog for previewing the printed overlap image. The dialog is connected to the
        printPreview function for the rendering to the preview.
        """
        printer = QPrinter()
        dialog = QPrintPreviewDialog(printer)
        printer.setDocName("CoursePositionImage")
        printer.setResolution(300)
        pl = QPageLayout(QPageSize(QPageSize.Letter), QPageLayout.Portrait,
                         QMarginsF(36, 36, 36, 36))
        printer.setPageLayout(pl)

        dialog.paintRequested.connect(self.printPreview)
        dialog.exec()

    def printPreview(self, printer):
        """
        This handles the printing of the image to the printer.  The function creates an internal, off-screen,
        weekly viewer, sets its size to the image width and height times the resolution of the printer, renders
        the image to the off-screen viewer and then to a pixmap, finally prints the pixmap to the printer
        object.

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
        painter.drawPixmap(QPoint(0, 0), pixmap)
        painter.end()
