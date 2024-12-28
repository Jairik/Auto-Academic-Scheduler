"""
WeekViewer, RoomListWidget, CourseListWidget, and RoomViewer Classes

Description:  Set of classes for displaying the schedule of a room as well as a drag and drop
framework that allows drops from the assignment window or another room viewer.  The room can be
selected from a list on the right.  Once the room is selected its weekly schedule will
be displayed in the main area.  The course list for the room will be listed at the bottom.
The course list has a context menu for course properties, tentative selection, and removal
of the course form timeslots or the schedule.

@author: Don Spickler
Last Revision: 8/23/2022

"""

from PySide6.QtCore import (Qt, QMimeData, QPoint, QDir, QMarginsF, QSize,
                            QTimer, SIGNAL)
from PySide6.QtGui import (QIcon, QColor, QBrush, QDrag, QPixmap, QPainter,
                           QFont, QFontMetrics, QMouseEvent, QCursor, QPageSize, QPageLayout, QAction, QActionGroup)
from PySide6.QtWidgets import (QWidget, QAbstractItemView, QMdiSubWindow, QListWidget, QGroupBox,
                               QTreeWidget, QVBoxLayout, QHBoxLayout, QListView, QMenuBar,
                               QLabel, QSplitter, QFrame, QFileDialog, QDialog, QMessageBox,
                               QRadioButton, QButtonGroup, QStatusBar, QApplication,
                               QMenu, QListWidgetItem)
from PySide6.QtPrintSupport import (QPrintDialog, QPrinter, QPrintPreviewDialog)

from TimeSlot import TimeSlot
import math
import datetime

from FacultyList import FacultyList, FacultyTreeWidget
from Room import Room
from Dialogs import *


class WeekViewer(QWidget):
    """
    Graphical widget that is derived off of the general QWidget.  It takes the information
    for the course list for the professor paints it onto the widget.
    """

    def __init__(self, parent=None, ma=None):
        """
        Sets up minimum size, turns on the mouse tracking and drag and drop, and
        sets a few variable defaults.

        :param parent: Pointer to the subwindow object,  CoursePositionViewer.
        :param ma: Pointer to the main Application, AcademicScheduler.
        """
        super(WeekViewer, self).__init__(parent)
        self.Parent = parent
        self.mainapp = ma

        self.setMouseTracking(True)
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        self.setAcceptDrops(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.headerHeight = 0
        self.numberDays = 5
        self.timecolwidth = 0
        self.displaysize = QPoint(1, 1)

        self.mousePosition = QPoint(0, 0)
        self.daysofweek = "MTWRFSU"

        self.DnDTimeslot = None
        self.DnDTimeslotList = []
        self.multipleDropIndex = -1

        self.scheditemdragged = None
        self.coursedragged = None
        self.mouseDown = False

        self.professortimeslotlist = []
        self.linkedtimeslotlist = []
        self.roomtimeslotlist = []

        # TimeslotModes
        # 0 - standard timeslot
        # 1 - Single Hour Free Positioning
        # 2 - Single Hour Timeslot starts
        # 3 - Block Timeslot starts
        # 4 - Block Free Positioning
        # 5 - Single Day Contact Hour
        # 6 - Single Day Contact Hour with Contact Hour Truncation
        # 7 - Block with Standard Timeslot Starts and Contact Hour Truncation
        # 8 - Block with Free Positioning and Contact Hour Truncation
        # 9 - 60 Minute Standard Timeslot Starts
        # 10 - 60 Minute Free Positioning
        # 11 - 75 Minute Standard Timeslot Starts
        # 12 - 75 Minute Free Positioning

        self.DnDTimeslotMode = 0

    def contextMenuEvent(self, e):
        """
        Context menu for the weekly viewer, when over a course it gives options for
        properties, tentative, and removal from rooms or the schedule.

        :param e: Context menu event.
        """
        self.mousePosition = QPoint(e.x(), e.y())
        self.repaint()

        if len(self.Parent.roomcourseslist) == 0:
            return

        schedItem = None
        for displayitem in self.Parent.roomcourseslist:
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

        hpos = math.floor(colindex * colwidth + self.timecolwidth)
        nexthpos = math.floor((colindex + 1) * colwidth + self.timecolwidth)

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

        if len(self.Parent.roomcourseslist) > 0:
            for course in self.Parent.roomcourseslist:
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

        if len(self.Parent.roomcourseslist) > 0:
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
                    for displayitem in self.Parent.roomcourseslist:
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

        # If no room selected stop drawing.
        if self.Parent.getSelectedRoom() == "":
            return

        # Draw header backgrounds
        qp.fillRect(0, 0, ww, self.headerHeight, headingColor)
        qp.fillRect(0, 0, self.timecolwidth, wh, headingColor)
        qp.setPen(QColor(Qt.black))

        # Draw in header.
        text = days[0]
        w = fm.horizontalAdvance(text)
        hpos = 0.5 * (self.timecolwidth - w)
        qp.drawText(QPoint(hpos, fontheight), text)

        for i in range(1, self.numberDays + 1):
            text = days[i]
            w = fm.horizontalAdvance(text)
            hpos = self.timecolwidth + (i - 1) * colwidth + 0.5 * (colwidth - w)
            qp.drawText(QPoint(hpos, fontheight), text)

        qp.setPen(QColor(Qt.black))
        for i in range(1, self.numberDays + 1):
            qp.drawLine(self.timecolwidth + i * colwidth, 0, self.timecolwidth + i * colwidth, self.headerHeight)

        # Draw in times on the left.
        if starttime < endtime:
            for i in range(1, divisions):
                vpos = self.headerHeight + i * self.displaysize.y() / divisions
                qp.setPen(QColor(Qt.black))
                qp.drawLine(0, vpos, self.timecolwidth, vpos)

            qp.setPen(QColor(Qt.black))
            for i in range(divisions):
                text = str(starttime + i) + ":00"
                if starttime + i > 12:
                    text = str(starttime + i - 12) + ":00"

                w = fm.horizontalAdvance(text)
                vpos = self.headerHeight + fontheight + i * self.displaysize.y() / divisions
                hpos = 0.5 * (self.timecolwidth - w)
                qp.drawText(QPoint(hpos, vpos), text)

        # Draw in timeslots.
        for stdslot in self.Parent.standardtimeslots:
            self.paintTimeslot(qp, stdslot, "", QColor(Qt.lightGray), None, None)

        self.Parent.updateStatusBar("")
        # Draw in classes.
        for displayitem in self.Parent.roomcourseslist:
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
            for highlightdisplayitem in self.Parent.roomcourseslist:
                if highlightdisplayitem[2].timeInSlot(d, h, m):
                    highlightcoursestr = highlightdisplayitem[0]

            if displayitem[0] == highlightcoursestr:
                backcolor = self.mainapp.getChartBackgroundHighlightColor(displayitem[3])
                boarderColor = QColor(Qt.red)

                schedItem = self.mainapp.findScheduleItemFromString(displayitem[0])
                coursestring = self.mainapp.courseNameAndSection(schedItem)
                roomsandtimesstring = self.mainapp.createTimeslotStringFromScheduleItem(schedItem)
                profstring = ""
                for profiid in schedItem.ProfessorIID:
                    prof = self.mainapp.findProfessorFromIID(profiid)
                    profstring += prof.ShortDes + " "

                profstring = profstring.rstrip().lstrip()
                courseInfoString = coursestring + ": (" + profstring + ")  " + roomsandtimesstring
                self.Parent.updateStatusBar(courseInfoString)

            self.paintTimeslot(qp, displayitem[2], text, boarderColor, backcolor, textcolor)
            oldfont.setItalic(False)
            qp.setFont(oldfont)

        # Draw DnD Timeslot
        if self.DnDTimeslot:
            DnDColor = QColor()
            DnDColor.setRgb(230, 230, 230)
            self.paintTimeslot(qp, self.DnDTimeslot, "", QColor(Qt.red), DnDColor, None)

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
        for displayitem in self.Parent.roomcourseslist:
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

        if self.mouseDown:
            self.processDnDStart()

    def leaveEvent(self, e: QMouseEvent):
        """
        On a leave, set position off-screen and repaint.

        :param e: Mouse event
        """
        self.mousePosition = QPoint(-1, -1)
        self.repaint()
        self.mouseDown = False

    def processDnDStart(self):
        """
        Initiate a drag from this room viewer.
        """
        self.mouseDown = False

        # If no course to drag, return.
        if self.Parent.roomcourseslist == []:
            return

        # If no course at current position, return.
        coursestring = self.findCourseStringFromCurrentPosition()
        if coursestring == "":
            return

        # Create drag object and set mime data.
        drag = QDrag(self)
        mimedata = QMimeData()
        mimedata.setText(coursestring)

        # Create pixmap for cursor attachment during drag.
        cursorText = coursestring
        font = QFont("Arial")
        fm = QFontMetrics(font)
        w = fm.horizontalAdvance(cursorText)
        h = fm.height()
        pix = QPixmap(w, h)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setFont(font)
        painter.drawText(QPoint(0, h), cursorText)
        painter.end()

        # set pixmap, data, and initiate drag.
        drag.setPixmap(pix)
        drag.setMimeData(mimedata)
        drag.exec_()

    def dragEnterEvent(self, e):
        """
        Process when a drag enters the object.

        :param e: Drag event.
        """

        # Establish where the drag is originating and set the addingTimeslot accordingly.
        self.setFocus()
        addingTimeslot = True
        if isinstance(e.source(), FacultyTreeWidget):
            addingTimeslot = True
            e.accept()
        elif isinstance(e.source(), WeekViewer):
            addingTimeslot = False
            e.accept()
        else:
            e.ignore()
            return

        # Get the schedule item, course, and professors.
        self.scheditemdragged = self.mainapp.findScheduleItemFromString(e.mimeData().text())
        self.coursedragged = self.mainapp.findCourseFromIID(self.scheditemdragged.CourseIID)
        profiidlist = self.scheditemdragged.ProfessorIID

        # Set lists for drop and highlighting restrictions.
        self.professortimeslotlist = []
        self.linkedtimeslotlist = []
        self.roomtimeslotlist = []

        # Populate professortimeslotlist with all timeslots currently in the professor's schedule.
        for profiid in profiidlist:
            prof = self.mainapp.findProfessorFromIID(profiid)
            if prof.Real:
                for course in self.mainapp.schedule:
                    if (profiid in course.ProfessorIID) and (
                            addingTimeslot or (self.scheditemdragged.InternalID != course.InternalID)):
                        for roomtime in course.RoomsAndTimes:
                            self.professortimeslotlist.append(roomtime[1])

        # Populate linkedtimeslotlist with all times of linked courses.
        if len(self.scheditemdragged.LinkedCourses) > 0:
            for schediid in self.scheditemdragged.LinkedCourses:
                course = self.mainapp.findScheduleItemFromIID(schediid)
                for roomtime in course.RoomsAndTimes:
                    self.linkedtimeslotlist.append(roomtime[1])

        for course in self.mainapp.schedule:
            if self.scheditemdragged.InternalID in course.LinkedCourses:
                for roomtime in course.RoomsAndTimes:
                    self.linkedtimeslotlist.append(roomtime[1])

        # Populate roomtimeslotlist with all timeslots currently in the room.
        roomstr = self.Parent.getSelectedRoom()
        room = self.mainapp.findRoomFromString(roomstr)

        if room.Real:
            for course in self.mainapp.schedule:
                for roomtime in course.RoomsAndTimes:
                    thisroom = self.mainapp.findRoomFromIID(roomtime[0])
                    if (thisroom.getName() == roomstr) and (
                            addingTimeslot or (self.scheditemdragged.InternalID != course.InternalID)):
                        self.roomtimeslotlist.append(roomtime[1])

        self.DnDTimeslot = None

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

    def dragMoveEvent(self, e):
        """
        On a drag move find timeslot that the drag can be dropped and store in DnDTimeslot.
        This will then be used as a highlighted slot in the view to show where the course
        can be dropped.

        :param e: Drag move event.
        """
        self.mousePosition = self.mapFromGlobal(QCursor.pos())
        d, h, m = self.timeAtPosition(self.mousePosition.x(), self.mousePosition.y())

        # Create DnD timeslot
        # Add in all possible slots to tempDnDTimeslotList.  At the end we will
        # remove all those that conflict.
        self.DnDTimeslot = None
        tempDnDTimeslotList = []

        if self.DnDTimeslotMode == 0:
            for stdslot in self.Parent.standardtimeslots:
                if stdslot.timeInSlot(d, h, m):
                    tempDnDTimeslotList.append(stdslot)
        elif self.DnDTimeslotMode == 1:
            bh = h
            if m < 0:
                m = 0

            bm = int((m // 5) * 5)
            eh, em = self.createEndTime(bh, bm, 50)

            if eh <= 23:
                tempslot = TimeSlot()
                tempslot.setData(d, bh, bm, eh, em)
                tempDnDTimeslotList.append(tempslot)
        elif self.DnDTimeslotMode == 2:
            for stdslot in self.Parent.standardtimeslots:
                if stdslot.timeInSlot(d, h, m):
                    bh = stdslot.StartHour
                    bm = stdslot.StartMinute
                    eh, em = self.createEndTime(bh, bm, 50)

                    if eh <= 23:
                        tempslot = TimeSlot()
                        tempslot.setData(d, bh, bm, eh, em)
                        tempDnDTimeslotList.append(tempslot)
        elif self.DnDTimeslotMode == 3:
            minutes = self.coursedragged.Contact
            for stdslot in self.Parent.standardtimeslots:
                if stdslot.timeInSlot(d, h, m):
                    bh = stdslot.StartHour
                    bm = stdslot.StartMinute
                    eh, em = self.createEndTime(bh, bm, minutes)

                    if eh <= 23:
                        tempslot = TimeSlot()
                        tempslot.setData(d, bh, bm, eh, em)
                        tempDnDTimeslotList.append(tempslot)
        elif self.DnDTimeslotMode == 4:
            minutes = self.coursedragged.Contact
            bh = h
            if m < 0:
                m = 0

            bm = int((m // 5) * 5)
            eh, em = self.createEndTime(bh, bm, minutes)

            if eh <= 23:
                tempslot = TimeSlot()
                tempslot.setData(d, bh, bm, eh, em)
                tempDnDTimeslotList.append(tempslot)
        elif self.DnDTimeslotMode == 5:
            for stdslot in self.Parent.standardtimeslots:
                if stdslot.timeInSlot(d, h, m):
                    tempslot = TimeSlot()
                    tempslot.setData(d, stdslot.StartHour, stdslot.StartMinute,
                                     stdslot.EndHour, stdslot.EndMinute)
                    tempDnDTimeslotList.append(tempslot)
        elif self.DnDTimeslotMode == 6:
            minutesremain = self.mainapp.ScheduleItemTimeRemaining(self.scheditemdragged)
            for stdslot in self.Parent.standardtimeslots:
                if stdslot.timeInSlot(d, h, m):
                    tempslot = TimeSlot()
                    tempslot.setData(d, stdslot.StartHour, stdslot.StartMinute,
                                     stdslot.EndHour, stdslot.EndMinute)
                    if tempslot.getMinutes() > minutesremain:
                        eh, em = self.createEndTime(stdslot.StartHour, stdslot.StartMinute, minutesremain)
                        tempslot.setData(d, stdslot.StartHour, stdslot.StartMinute, eh, em)
                    tempDnDTimeslotList.append(tempslot)
        elif self.DnDTimeslotMode == 7:
            minutesremain = self.mainapp.ScheduleItemTimeRemaining(self.scheditemdragged)
            for stdslot in self.Parent.standardtimeslots:
                if stdslot.timeInSlot(d, h, m):
                    tempslot = TimeSlot()
                    eh, em = self.createEndTime(stdslot.StartHour, stdslot.StartMinute, minutesremain)
                    tempslot.setData(d, stdslot.StartHour, stdslot.StartMinute, eh, em)
                    tempDnDTimeslotList.append(tempslot)
        elif self.DnDTimeslotMode == 8:
            minutesremain = self.mainapp.ScheduleItemTimeRemaining(self.scheditemdragged)
            bh = h
            if m < 0:
                m = 0

            bm = int((m // 5) * 5)
            eh, em = self.createEndTime(bh, bm, minutesremain)

            if eh <= 23:
                tempslot = TimeSlot()
                tempslot.setData(d, bh, bm, eh, em)
                tempDnDTimeslotList.append(tempslot)
        elif self.DnDTimeslotMode == 9:
            for stdslot in self.Parent.standardtimeslots:
                if stdslot.timeInSlot(d, h, m):
                    bh = stdslot.StartHour
                    bm = stdslot.StartMinute
                    eh, em = self.createEndTime(bh, bm, 60)

                    self.DnDTimeslot = TimeSlot()
                    if eh <= 23:
                        tempslot = TimeSlot()
                        tempslot.setData(d, bh, bm, eh, em)
                        tempDnDTimeslotList.append(tempslot)
        elif self.DnDTimeslotMode == 10:
            bh = h
            if m < 0:
                m = 0

            bm = int((m // 5) * 5)
            eh, em = self.createEndTime(bh, bm, 60)

            if eh <= 23:
                tempslot = TimeSlot()
                tempslot.setData(d, bh, bm, eh, em)
                tempDnDTimeslotList.append(tempslot)
        elif self.DnDTimeslotMode == 11:
            for stdslot in self.Parent.standardtimeslots:
                if stdslot.timeInSlot(d, h, m):
                    bh = stdslot.StartHour
                    bm = stdslot.StartMinute
                    eh, em = self.createEndTime(bh, bm, 75)

                    self.DnDTimeslot = TimeSlot()
                    if eh <= 23:
                        tempslot = TimeSlot()
                        tempslot.setData(d, bh, bm, eh, em)
                        tempDnDTimeslotList.append(tempslot)
        elif self.DnDTimeslotMode == 12:
            bh = h
            if m < 0:
                m = 0

            bm = int((m // 5) * 5)
            eh, em = self.createEndTime(bh, bm, 75)

            if eh <= 23:
                tempslot = TimeSlot()
                tempslot.setData(d, bh, bm, eh, em)
                tempDnDTimeslotList.append(tempslot)

        # Remove overlaps with scheduled items.
        self.DnDTimeslotList = []
        tempDnDTimeslotList2 = []
        if len(tempDnDTimeslotList) == 0:
            self.DnDTimeslot = None
        else:
            for tempslot in tempDnDTimeslotList:
                if tempslot.getMinutes() <= 0:
                    tempslot = None

                if tempslot and len(self.roomtimeslotlist) > 0:
                    for slot in self.roomtimeslotlist:
                        if slot.overlap(tempslot):
                            tempslot = None

                if tempslot and (len(self.professortimeslotlist) > 0):
                    for slot in self.professortimeslotlist:
                        if slot.overlap(tempslot):
                            tempslot = None

                if tempslot and (len(self.linkedtimeslotlist) > 0):
                    for slot in self.linkedtimeslotlist:
                        if slot.overlap(tempslot):
                            tempslot = None

                if tempslot:
                    tempDnDTimeslotList2.append(tempslot)

        # Remove Duplicates.
        usedTimeslotStrings = []
        if len(tempDnDTimeslotList2) > 0:
            for tempslot in tempDnDTimeslotList2:
                if tempslot.getDescription() not in usedTimeslotStrings:
                    self.DnDTimeslotList.append(tempslot)
                    usedTimeslotStrings.append(tempslot.getDescription())

        # Set DnDTimeslot
        if len(self.DnDTimeslotList) == 0:
            self.DnDTimeslot = None
        elif len(self.DnDTimeslotList) >= 1:
            self.DnDTimeslot = self.DnDTimeslotList[0]

        self.repaint()

        # Create and show status bar string will all possible slots for drop.
        statusString = ""
        if len(self.DnDTimeslotList) > 0:
            for i in range(len(self.DnDTimeslotList)):
                statusString += self.DnDTimeslotList[i].getDescription()
                if i < len(self.DnDTimeslotList) - 1:
                    statusString += "  /  "
        self.Parent.updateStatusBar(statusString)

    def dragLeaveEvent(self, e):
        """
        On a drag leave, reset all drop restriction lists and variables.

        :param e: Drag leave event.
        """
        self.mousePosition = self.mapFromGlobal(QCursor.pos())
        self.DnDTimeslot = None
        self.scheditemdragged = None
        self.coursedragged = None
        self.professortimeslotlist = []
        self.linkedtimeslotlist = []
        self.roomtimeslotlist = []
        self.repaint()

    def multipleDropSelection(self, item, strlist):
        """
        Finds the index of the selection from the context menu for multiple drop slots.

        :param item: Timeslot string.
        :param strlist: List of timeslot strings.
        """
        self.multipleDropIndex = strlist.index(item)

    def multipleDropMenu(self, pos, list):
        """
        Creates a context menu of all the slots that can be dropped into for the drop.
        User selects the one they want and the drop is done to that slot.

        :param pos: Position of the mouse.
        :param list: List of timeslots for the drop.
        """
        menu = QMenu(self)

        self.multipleDropIndex = -1
        strlist = []
        for item in list:
            strlist.append(item.getDescription())

        for item in strlist:
            option_act = QAction(item, self)
            self.connect(option_act, SIGNAL('triggered()'),
                         lambda selection=item: self.multipleDropSelection(selection, strlist))
            menu.addAction(option_act)

        menu.exec(self.mapToGlobal(pos))

    def dropEvent(self, e):
        """
        Process a drop.

        :param e: Drop event.
        """

        # Determine if this is an add to the schedule or a move.
        addingTimeslot = True
        if isinstance(e.source(), FacultyTreeWidget):
            addingTimeslot = True
            e.accept()
        elif isinstance(e.source(), WeekViewer):
            addingTimeslot = False
            e.accept()
        else:
            e.ignore()
            return

        if not self.DnDTimeslot:
            return

        # If multiple slots available, invoke context menu.
        self.multipleDropIndex = -1
        if len(self.DnDTimeslotList) > 1:
            self.multipleDropMenu(e.pos(), self.DnDTimeslotList)
            if self.multipleDropIndex != -1:
                self.DnDTimeslot = self.DnDTimeslotList[self.multipleDropIndex]
            else:
                self.DnDTimeslot = None
                self.Parent.roomUpdated()
                self.repaint()
                return

        # Finish the drop and update the databases accordingly.
        roomstr = self.Parent.getSelectedRoom()
        if (not self.DnDTimeslot) or (roomstr == ""):
            return

        if addingTimeslot:
            self.mainapp.addRoomTimesToDatabase(e.mimeData().text(), roomstr, self.DnDTimeslot)
        else:
            self.mainapp.updateRoomTimesToDatabase(e.mimeData().text(), roomstr, self.DnDTimeslot)

        self.DnDTimeslot = None
        self.Parent.roomUpdated()
        self.mousePosition = self.mapFromGlobal(QCursor().pos())
        self.repaint()


class CourseListWidget(QListWidget):
    """
    Course list for the room at the bottom of the window.
    """

    def __init__(self, parent=None, ma=None):
        """
        Sets up mouse tracking and context menu.

        :param parent: Pointer to the parent object.
        :param ma: Pointer to the main app.
        """
        super(CourseListWidget, self).__init__(parent)
        self.Parent = parent
        self.mainapp = ma
        self.customContextMenuRequested.connect(self.contextMenuEvent)
        self.setMouseTracking(True)

    def mouseDoubleClickEvent(self, e):
        """
        On a double-click invoke the course properties dialog.

        :param e: Mouse event.
        """
        items = self.selectedItems()
        if len(items) > 0:
            item = items[0].text()
            coursestr = item.split(":")[0]
            self.mainapp.updateCourseProperties(coursestr)

    def keyPressEvent(self, event):
        """
        On return/enter invoke the course properties.

        :param event:
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
        If right-click on a course in the list create and show context menu.

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

            menu.exec(self.mapToGlobal(e.pos()))


class RoomListWidget(QListWidget):
    """
    Room list on the right of the window.
    """

    def __init__(self, parent=None):
        """
        Set parent.

        :param parent: Parent object.
        """
        super(RoomListWidget, self).__init__(parent)
        self.Parent = parent

    def selectionChanged(self, sel, des):
        """
        On selection change notify parent to make needed updates.

        :param sel: Selected objecte, dummy variable.
        :param des: Deselected objecte, dummy variable.
        """
        items = self.selectedItems()
        if len(items) > 0:
            item = items[0].text()
            self.Parent.roomUpdated()

    def keyPressEvent(self, event):
        """ On enter, invoke the room editor. """
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.Parent.editItem()
        QListWidget.keyPressEvent(self, event)

    def mouseDoubleClickEvent(self, event) -> None:
        """ On double-click, invoke the room editor. """
        self.Parent.editItem()


class RoomViewer(QMdiSubWindow):
    """
    Subwindow for room schedule viewing as well as drag and drop into and out of the weekly
    viewer.  Classes can be dragged in from the assignment window or another room viewer.
    """

    def __init__(self, parent):
        """
        Sets up the window UI.

        :param parent: Pointer to the parent object, must be the main app.
        """
        super(RoomViewer, self).__init__(parent)
        self.Parent = parent
        self.mainapp = parent
        self.setWindowIcon(QIcon(self.mainapp.resource_path('icons/ProgramIcon.png')))

        self.setWindowTitle("Room Viewer")
        self.roomlist = RoomListWidget(self)
        self.weekviewer = WeekViewer(self, self.mainapp)
        self.courselist = CourseListWidget(self, self.mainapp)

        weekviewlayout = QSplitter(Qt.Vertical)
        weekviewlayout.setHandleWidth(5)
        weekviewlayout.addWidget(self.weekviewer)
        weekviewlayout.addWidget(self.courselist)

        self.statusText = QLabel()
        sttextfont = self.statusText.font()
        fm = QFontMetrics(sttextfont)
        sttextheight = fm.height()
        self.statusText.setMaximumHeight(sttextheight)

        self.starttime = 24
        self.endtime = 0

        self.rooms = self.mainapp.rooms
        self.standardtimeslots = self.mainapp.standardtimeslots
        self.schedule = self.mainapp.schedule
        self.roomcourseslist = []
        self.RoomReal = False

        mainview = QSplitter(Qt.Horizontal)
        mainview.setHandleWidth(5)
        mainview.addWidget(weekviewlayout)

        roomswidget = QWidget()
        vbox = QVBoxLayout(roomswidget)
        listlabel = QLabel("Rooms")
        vbox.setContentsMargins(0,0,0,0)
        vbox.addWidget(listlabel)
        vbox.addWidget(self.roomlist)
        mainview.addWidget(roomswidget)
        mainview.setCollapsible(0, False)
        mainview.setCollapsible(1, False)

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
        self.updateStatusBar("")

    def createMenu(self):
        """ Set up the menu bar. """

        # Create the actions.
        new_rooms_act = QAction(QIcon(self.Parent.resource_path('icons/NewRooms.png')), "Add New Rooms...", self)
        new_rooms_act.setShortcut('Shift+Ctrl+N')
        new_rooms_act.triggered.connect(self.Parent.AddNewRooms)

        edit_room_act = QAction(QIcon(self.Parent.resource_path('icons/Preferences.png')), "Edit Room...", self)
        edit_room_act.setShortcut('Shift+Ctrl+E')
        edit_room_act.triggered.connect(self.editItem)

        delete_room_act = QAction(QIcon(self.Parent.resource_path('icons/Delete.png')), "Delete Room...", self)
        delete_room_act.triggered.connect(self.deleteItem)

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

        DnDtimeslotButton = QAction("Standard Timeslot", self)
        DnDtimeslotButton.setShortcut('Ctrl+1')
        DnDtimeslotButton.triggered.connect(self.setDnDTimeslot)

        DnDHourFreeButton = QAction("50 Minute Free Positioning", self)
        DnDHourFreeButton.setShortcut('Alt+2')
        DnDHourFreeButton.triggered.connect(self.setDnDOneHourFP)

        DnDHourTSSButton = QAction("50 Minute Standard Timeslot Starts", self)
        DnDHourTSSButton.setShortcut('Alt+1')
        DnDHourTSSButton.triggered.connect(self.setDnDOneHourTSS)

        DnD60FreeButton = QAction("60 Minute Free Positioning", self)
        DnD60FreeButton.setShortcut('Alt+4')
        DnD60FreeButton.triggered.connect(self.setDnD60FP)

        DnD60TSSButton = QAction("60 Minute Standard Timeslot Starts", self)
        DnD60TSSButton.setShortcut('Alt+3')
        DnD60TSSButton.triggered.connect(self.setDnD60TSS)

        DnD75FreeButton = QAction("75 Minute Free Positioning", self)
        DnD75FreeButton.setShortcut('Alt+6')
        DnD75FreeButton.triggered.connect(self.setDnD75FP)

        DnD75TSSButton = QAction("75 Minute Standard Timeslot Starts", self)
        DnD75TSSButton.setShortcut('Alt+5')
        DnD75TSSButton.triggered.connect(self.setDnD75TSS)

        DnDBlockTSSButton = QAction("Block with Standard Timeslot Starts", self)
        DnDBlockTSSButton.setShortcut('Ctrl+4')
        DnDBlockTSSButton.triggered.connect(self.setDnDBlockTSS)

        DnDBlockFPButton = QAction("Block with Free Positioning", self)
        DnDBlockFPButton.setShortcut('Ctrl+5')
        DnDBlockFPButton.triggered.connect(self.setDnDBlockFP)

        DnDBlockTSSCHTButton = QAction("Block with Standard Timeslot Starts and Contact Hour Truncation", self)
        DnDBlockTSSCHTButton.setShortcut('Ctrl+6')
        DnDBlockTSSCHTButton.triggered.connect(self.setDnDBlockTSSCHT)

        DnDBlockFPCHTButton = QAction("Block with Free Positioning and Contact Hour Truncation", self)
        DnDBlockFPCHTButton.setShortcut('Ctrl+7')
        DnDBlockFPCHTButton.triggered.connect(self.setDnDBlockFPCHT)

        DnDSingledayTSButton = QAction("Single Day Standard Timeslot", self)
        DnDSingledayTSButton.setShortcut('Ctrl+2')
        DnDSingledayTSButton.triggered.connect(self.setDnDSingledayTS)

        DnDSingledayTSCHTButton = QAction("Single Day Standard Timeslot with Contact Hour Truncation", self)
        DnDSingledayTSCHTButton.setShortcut('Ctrl+3')
        DnDSingledayTSCHTButton.triggered.connect(self.setDnDSingledayTSCHT)

        DnDtimeslotButton.setCheckable(True)
        DnDHourFreeButton.setCheckable(True)
        DnDHourTSSButton.setCheckable(True)
        DnDBlockTSSButton.setCheckable(True)
        DnDBlockFPButton.setCheckable(True)
        DnDSingledayTSButton.setCheckable(True)
        DnDSingledayTSCHTButton.setCheckable(True)
        DnDBlockTSSCHTButton.setCheckable(True)
        DnDBlockFPCHTButton.setCheckable(True)

        DnD60FreeButton.setCheckable(True)
        DnD60TSSButton.setCheckable(True)
        DnD75FreeButton.setCheckable(True)
        DnD75TSSButton.setCheckable(True)

        self.dropmodegroup = QActionGroup(self)
        self.dropmodegroup.addAction(DnDtimeslotButton)
        self.dropmodegroup.addAction(DnDHourTSSButton)
        self.dropmodegroup.addAction(DnDHourFreeButton)
        self.dropmodegroup.addAction(DnDBlockTSSButton)
        self.dropmodegroup.addAction(DnDBlockFPButton)
        self.dropmodegroup.addAction(DnDSingledayTSButton)
        self.dropmodegroup.addAction(DnDSingledayTSCHTButton)
        self.dropmodegroup.addAction(DnDBlockTSSCHTButton)
        self.dropmodegroup.addAction(DnDBlockFPCHTButton)
        self.dropmodegroup.addAction(DnD60FreeButton)
        self.dropmodegroup.addAction(DnD60TSSButton)
        self.dropmodegroup.addAction(DnD75FreeButton)
        self.dropmodegroup.addAction(DnD75TSSButton)

        DnDtimeslotButton.setChecked(True)

        self.dropmodegroup.triggered.connect(self.setDnDModeChange)

        # Create the menu bar
        menu_bar = QMenuBar(self)

        main_menu = menu_bar.addMenu("Options")
        main_menu.addAction(new_rooms_act)
        main_menu.addAction(edit_room_act)
        main_menu.addSeparator()
        main_menu.addAction(delete_room_act)
        main_menu.addSeparator()
        main_menu.addAction(saveImage_act)
        main_menu.addAction(copyImage_act)
        main_menu.addSeparator()
        main_menu.addAction(printImage_act)
        main_menu.addAction(printPreviewImage_act)
        main_menu.addSeparator()
        main_menu.addAction(self.showStatusBar_act)

        drop_menu = menu_bar.addMenu("Insert Mode")
        drop_menu.addAction(DnDtimeslotButton)
        drop_menu.addAction(DnDSingledayTSButton)
        drop_menu.addAction(DnDSingledayTSCHTButton)
        drop_menu.addSeparator()
        drop_menu.addAction(DnDBlockTSSButton)
        drop_menu.addAction(DnDBlockFPButton)
        drop_menu.addSeparator()
        drop_menu.addAction(DnDBlockTSSCHTButton)
        drop_menu.addAction(DnDBlockFPCHTButton)
        drop_menu.addSeparator()
        drop_menu.addAction(DnDHourTSSButton)
        drop_menu.addAction(DnDHourFreeButton)
        drop_menu.addSeparator()
        drop_menu.addAction(DnD60TSSButton)
        drop_menu.addAction(DnD60FreeButton)
        drop_menu.addSeparator()
        drop_menu.addAction(DnD75TSSButton)
        drop_menu.addAction(DnD75FreeButton)

        return menu_bar

    # Set of DnD mode selection functions.
    def setDnDModeChange(self):
        self.updateStatusBar("")

    def setDnDTimeslot(self):
        self.weekviewer.DnDTimeslotMode = 0

    def setDnDOneHourFP(self):
        self.weekviewer.DnDTimeslotMode = 1

    def setDnDOneHourTSS(self):
        self.weekviewer.DnDTimeslotMode = 2

    def setDnDBlockTSS(self):
        self.weekviewer.DnDTimeslotMode = 3

    def setDnDBlockFP(self):
        self.weekviewer.DnDTimeslotMode = 4

    def setDnDSingledayTS(self):
        self.weekviewer.DnDTimeslotMode = 5

    def setDnDSingledayTSCHT(self):
        self.weekviewer.DnDTimeslotMode = 6

    def setDnDBlockTSSCHT(self):
        self.weekviewer.DnDTimeslotMode = 7

    def setDnDBlockFPCHT(self):
        self.weekviewer.DnDTimeslotMode = 8

    def setDnD60TSS(self):
        self.weekviewer.DnDTimeslotMode = 9

    def setDnD60FP(self):
        self.weekviewer.DnDTimeslotMode = 10

    def setDnD75TSS(self):
        self.weekviewer.DnDTimeslotMode = 11

    def setDnD75FP(self):
        self.weekviewer.DnDTimeslotMode = 12

    def toggleStatusBar(self):
        """
        Toggle the status bar.
        """
        self.statusText.setVisible(self.showStatusBar_act.isChecked())

    def editItem(self):
        """"
        Edit the currently selected room
        """
        indexes = self.roomlist.selectedIndexes()
        if len(indexes) > 0:
            item = self.roomlist.model().itemData(indexes[0])[0]
            self.Parent.EditRoom(item)

    def deleteItem(self):
        """"
        Delete the currently selected room
        """
        indexes = self.roomlist.selectedIndexes()
        if len(indexes) > 0:
            item = self.roomlist.model().itemData(indexes[0])[0]
            self.Parent.DeleteRoom(item)

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

        for times in self.roomcourseslist:
            coursetime = times[2]
            if coursetime.StartHour < self.starttime:
                self.starttime = coursetime.StartHour
            if coursetime.EndHour >= self.endtime:
                self.endtime = coursetime.EndHour
                if coursetime.EndMinute > 0:
                    self.endtime += 1

    def updateRoomList(self):
        """
        Updates the room list viewer.
        """
        roomstr = self.getSelectedRoom()

        self.roomlist.clear()
        for room in self.rooms:
            self.roomlist.addItem(room.getName())

        if roomstr != "":
            for i in range(self.roomlist.count()):
                if self.roomlist.item(i).text() == roomstr:
                    self.roomlist.setCurrentRow(i)

        self.roomUpdated()

    def updateData(self):
        """
        Updates the data for the entire view.
        """
        self.rooms = self.mainapp.rooms
        self.standardtimeslots = self.mainapp.standardtimeslots
        self.schedule = self.mainapp.schedule
        self.updateRoomList()

    def updateStatusBar(self, text):
        """
        Updates the status bar with the input text or reverts to the insert mode display.

        :param text: Text to display in the status bar.
        """
        if text != "":
            self.statusText.setText(text)
        else:
            self.statusText.setText("Insert Mode: " + self.dropmodegroup.checkedAction().text())

    def getSelectedRoom(self) -> str:
        """
        Returns a string of the selected room from the list.

        :return: A string of the selected room from the list.
        """
        items = self.roomlist.selectedItems()
        if len(items) > 0:
            item = items[0].text()
            return item
        return ""

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

    def roomUpdated(self):
        """
        Updates the course list and weekly schedule image when the room selection is changed.
        """
        roomstr = self.getSelectedRoom()
        if roomstr != "":
            room = self.mainapp.findRoomFromString(roomstr)
            self.RoomReal = room.Real
            displaystr = roomstr
            if not room.Real:
                displaystr += "*"
            displaystr += "  (" + str(room.Capacity) + ")"
            if room.Special != "":
                displaystr += "  - " + room.Special
            self.setWindowTitle("Room Viewer  -  " + displaystr)

        # Get list of classes for display.
        self.roomcourseslist = []
        self.courselist.clear()

        schedule = self.mainapp.schedule
        for scheduleitem in schedule:
            coursename = self.mainapp.courseNameAndSection(scheduleitem)
            timeamountdes = self.mainapp.ScheduleItemTimeCheck(scheduleitem)
            isTentative = scheduleitem.Tentative
            profliststr = ""
            for profiid in scheduleitem.ProfessorIID:
                profliststr += self.mainapp.findProfessorFromIID(profiid).ShortDes + " "
            profliststr = profliststr.lstrip().rstrip()

            courseInfoString = ""
            classinroom = False
            for roomtimeslots in scheduleitem.RoomsAndTimes:
                roomiid = roomtimeslots[0]
                if self.mainapp.findRoomFromIID(roomiid).getName() == roomstr:
                    classinroom = True
                    self.roomcourseslist.append([coursename, profliststr, roomtimeslots[1],
                                                 timeamountdes, isTentative])

            if classinroom:
                courseInfoString = coursename + ": (" + profliststr + ") "
                courseInfoString += self.mainapp.createTimeslotStringFromScheduleItem(scheduleitem)

                self.courselist.addItem(courseInfoString)
                font = self.courselist.item(self.courselist.count() - 1).font()
                if isTentative:
                    font.setItalic(True)
                    self.courselist.item(self.courselist.count() - 1).foreground().setColor(QColor(Qt.darkGray))
                else:
                    font.setItalic(False)
                    self.courselist.item(self.courselist.count() - 1).foreground().setColor(QColor(Qt.black))
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
        printer.setDocName("RoomViewerImage")
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
        printer.setDocName("RoomViewerImage")
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
        roomstr = self.getSelectedRoom()
        if self.mainapp.options[0] != "":
            roomstr += "  /  " + self.mainapp.options[0]
        roomstr += "  /  " + str(datetime.datetime.now())

        font = QFont("Arial", 12)
        fm = QFontMetrics(font)
        h = fm.height()
        painter.setFont(font)
        painter.setPen(QColor(Qt.black))
        painter.drawText(QPoint(0, h), roomstr)
        painter.drawPixmap(QPoint(0, 2 * h), pixmap)
        painter.end()

    def print_completed(self, success):
        pass  # Nothing needs to be done.

    def printPreviewAll(self, roomstrs):
        """
        Invokes the print preview dialog on all schedule inages.

        :param roomstrs:  List of room names to create weekly images for.
        """

        printer = QPrinter()
        dialog = QPrintPreviewDialog(printer)
        printer.setDocName("RoomViewerImage")
        printer.setResolution(300)
        pl = QPageLayout(QPageSize(QPageSize.Letter), QPageLayout.Portrait,
                         QMarginsF(36, 36, 36, 36))
        printer.setPageLayout(pl)

        self.roomstringstoprint = roomstrs

        dialog.paintRequested.connect(self.printAllImages)
        dialog.exec()
        self.roomstringstoprint = None

    def printAllImages(self, printer):
        """
        This handles the printing of the image to the printer.  The function creates an internal,
        off-screen, weekly viewer and professor viewer sub-window, sets its size to the image width
        and height times the resolution of the printer, renders the image to the off-screen viewer
        and then to a pixmap, finally prints the pixmap to the printer object.

        :param printer: Pointer to a printer object.
        """

        # Create off-screen viewer.
        offscreenroomviewer = RoomViewer(self.mainapp)
        printviewer = offscreenroomviewer.weekviewer
        printres = printer.resolution()

        # Set width and height by resolution and scaling options.
        wid = self.mainapp.ImagePrintWidth * printres
        hei = self.mainapp.ImagePrintHeight * printres

        if self.mainapp.ImagePrintScaleMode == 0:
            hei = wid * self.weekviewer.height() / self.weekviewer.width()
        elif self.mainapp.ImagePrintScaleMode == 1:
            wid = hei * self.weekviewer.width() / self.weekviewer.height()

        painter = QPainter(printer)

        # Run through the rooms, paint the image and description to a page and
        # advance to the next page.
        count = 0
        for i in range(offscreenroomviewer.roomlist.count()):
            offscreenroomviewer.roomlist.setCurrentRow(i)
            roomstr = offscreenroomviewer.getSelectedRoom()
            if roomstr in self.roomstringstoprint:
                printviewer.setFixedSize(QSize(round(wid), round(hei)))
                pixmap = QPixmap(printviewer.size())
                printviewer.render(pixmap)

                if self.mainapp.options[0] != "":
                    roomstr += "  /  " + self.mainapp.options[0]
                roomstr += "  /  " + str(datetime.datetime.now())

                font = QFont("Arial", 12)
                fm = QFontMetrics(font)
                h = fm.height()
                painter.setFont(font)
                painter.setPen(QColor(Qt.black))
                painter.drawText(QPoint(0, h), roomstr)
                painter.drawPixmap(QPoint(0, 2 * h), pixmap)
                if count < len(self.roomstringstoprint) - 1:
                    printer.newPage()
                count += 1

        painter.end()
