#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

Description:  This is the main file in the Academic Scheduler program.  It has a dual purpose
and is the center of the program.  First, it functions as a specialized database for storing,
manipulating, and reporting the data for the schedule, and second, it coordinates the subwindow
functionality.  Keeping with a document/view methodology, the subwindows are primarily for
display and user interface purposes.  These use a make-shift callback structure to the main
program (this file) to do the actual database altering.  Although I am not fond of callback
systems in general it was the framework that made sense and was easier to implement as well
as read.  Hence, most of the child windows will contain "pointers" to the AcademicScheduler
class and call functions in this class directly.  Therefore, the child windows are
dependent on the AcademicScheduler class and not completely encapsulated.  Again, not a
design I am fond of in general but gets the job done with relative ease.

The program uses a desktop multiple document type interface with specialized subwindows
for specific functions.  Only one schedule may be loaded at a time.  Some child windows are
restricted to be single instance while others may have multiple instances.

Single instance child windows:

CourseList - List of courses, these are dragged to the FacultyList to assign courses to faculty.
FacultyList - List of faculty course assignments.  Courses are dragged to this window and courses
are dragged from this window to a RoomViewer to place the course in a room and time.
NoteEditor - Text notes to be stored with the schedule.
TimeslotList - List of standard timeslots.
CourseLinker - Course linker to link main courses to subsequenct classes.  Used to determine
time conflicts between classes that depend on each other.

Multiple instance child windows:

ProfessorViewer - Viewer for a professor's schedule.
RoomViewer - Viewer for a room's schedule, also allows courses to be dragged from the FacultyList
to the room for scheduling.
CoursePositionViewer - Viewer for course positioning and overlap.

The schedule consists of several databases.

options - A list of several options for the user.
faculty - List of Professor objects storing faculty information.
rooms - List of Room objects storing room information.
courses - List of courses offered by the department and associated information.
standardtimeslots - List of standard timeslots used by the institution or department.  These
are integrated into the drag-drop system for the room viewer to make scheduling class easier.
schedule - List of ScheduleItem objects that link the courses, faculty, and rooms together
into one scheduled class for the department.  Also contains other information such as
section number, subtitle, and designations.

@author: Don Spickler
Created on 6/3/2022
Last Revision: 8/21/2022

"""

import pickle
import sys
import os
import webbrowser
import copy
import collections
import datetime
import platform

from PySide6.QtCore import (Qt, QSize, QDir, QAbstractListModel)
from PySide6.QtGui import (QIcon, QColor, QBrush, QAction)
from PySide6.QtWidgets import (QApplication, QMainWindow, QStatusBar,
                               QToolBar, QDockWidget, QSpinBox, QHBoxLayout,
                               QVBoxLayout, QWidget, QLabel, QScrollArea, QMessageBox,
                               QInputDialog, QFileDialog, QDialog, QMdiArea,
                               QMdiSubWindow, QTreeWidgetItem, QLineEdit, QMenu, QStyleFactory,
                               QMenuBar)

from CSS_Class import appcss
from Course import Course
from Room import Room
from TimeSlot import TimeSlot
from Professor import Professor
from CourseList import CourseList
from CourseLinker import CourseLinker
from FacultyList import FacultyList
from TimeslotList import TimeslotList
from RoomViewer import RoomViewer
from ProfessorViewer import ProfessorViewer
from CoursePositionViewer import CoursePositionViewer
from NoteEditor import NoteEditor
from ScheduleItem import ScheduleItem
from Dialogs import *

# For the macOS
os.environ['QT_MAC_WANTS_LAYER'] = '1'


class AcademicScheduler(QMainWindow):

    def __init__(self, parent=None):
        """
        Initialize the program and set up the programList structure that
        allows the creation of child applications.
        """
        super().__init__()

        self.isMac = False
        if sys.platform == 'darwin':
            self.isMac = True

        self.authors = "Don Spickler"
        self.version = "2.3.1"
        self.program_title = "Academic Scheduler"
        self.copyright = "2022 - 2024"
        self.licence = "\nThis software is distributed under the GNU General Public License version 3.\n\n" + \
                       "This program is free software: you can redistribute it and/or modify it under the terms of the GNU " + \
                       "General Public License as published by the Free Software Foundation, either version 3 of the License, " + \
                       "or (at your option) any later version. This program is distributed in the hope that it will be useful, " + \
                       "but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A " + \
                       "PARTICULAR PURPOSE. See the GNU General Public License for more details http://www.gnu.org/licenses/."

        self.clipboard = QApplication.clipboard()
        self.loadedFilename = ""
        self.Parent = parent
        self.changemade = False

        # Initialize database lists.
        # Options 0: Description, 1: Annual Full Load
        self.options = ["", 24]
        self.faculty = []
        self.rooms = []
        self.courses = []
        self.standardtimeslots = []
        self.schedule = []

        # Set default style (theme) to Fusion
        self.Platform = platform.system()
        styles = QStyleFactory.keys()
        if "Fusion" in styles:
            app.setStyle('Fusion')

        # Set up preferences.
        # Mode 0: Scale height to width, 1: Sacle width to height, 2: No scaling.
        self.ImagePrintWidth = 7.5
        self.ImagePrintHeight = 4.75
        self.ImagePrintScaleMode = 2
        self.minimumGraphicFontSize = 8
        self.setMinimumSize(800, 600)
        self.updateProgramWindowTitle()
        icon = QIcon(self.resource_path("icons/ProgramIcon.png"))
        self.setWindowIcon(icon)

        # Setup UI, menu, toolbar, and desktop.
        menu_bar = self.createMenu()
        menu_bar.setNativeMenuBar(False)
        self.setMenuBar(menu_bar)

        self.createToolBar()
        self.desktop = QMdiArea()
        self.desktop.setBackground(QBrush(QColor(240, 240, 240)))
        self.setCentralWidget(self.desktop)

        # Set up subwindows.  These are single instance subwindows, others are multiple
        # instance.  These are created, added to the desktop, and closed.
        self.coureList = CourseList(self)
        self.facultyList = FacultyList(self)
        self.noteeditor = NoteEditor(self)
        self.timeslotlist = TimeslotList(self)
        self.courselinker = CourseLinker(self)

        self.desktop.addSubWindow(self.coureList)
        self.desktop.addSubWindow(self.facultyList)
        self.desktop.addSubWindow(self.noteeditor)
        self.desktop.addSubWindow(self.timeslotlist)
        self.desktop.addSubWindow(self.courselinker)

        self.coureList.close()
        self.noteeditor.close()
        self.timeslotlist.close()
        self.courselinker.close()
        self.internalhelp = None
        self.show()

    def resource_path(self, relative_path: str):
        """
        This adds the relative_path tp the path list.  Used for adding the icon and help
        system paths.

        :param relative_path: Path to add to the path list.
        :return: Joined path list.
        """
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def closeEvent(self, event):
        """
        Override for the close event.  If there has been a change made the system will
        prompt the user to quit or cancel.

        :param event: Close event.
        """
        if self.changemade:
            close = QMessageBox.warning(self, "Exit Program",
                                        "Changes have been made to the schedule and will be lost.  " +
                                        "Are you sure want to exit the program?",
                                        QMessageBox.Yes | QMessageBox.No)
            if close == QMessageBox.Yes:
                event.accept()
                if self.internalhelp:
                    self.internalhelp.close()
            else:
                event.ignore()
        else:
            event.accept()
            if self.internalhelp:
                self.internalhelp.close()

    def closeSubWindow(self, subwindow: QMdiSubWindow):
        """
        On a subwindow close this removes the window from the desktop.

        :param subwindow: Window to remove.
        """
        self.desktop.removeSubWindow(subwindow)

    def updateProgramWindowTitle(self):
        """
        Updates the titlebar of the main window to contain the loaded filepath, description,
        and an * if there is a change to the databases that is unsaved.
        """
        title = self.program_title
        if self.options[0] != "":
            title = title + " (" + self.options[0] + ")"
        if self.loadedFilename != "":
            title = title + " - " + self.loadedFilename
        if self.changemade:
            title += "*"
        self.setWindowTitle(title)

    def ChangeMade(self, b=True):
        """
        Sets the changemade variable to b for change tracking.  This is called by any function
        that alters any of the databases.

        :param b: Value for the changemade variable.
        """
        self.changemade = b
        self.updateProgramWindowTitle()

    def createMenu(self):
        """
        Set up the menu bar.
        """

        # File menu actions.
        self.file_new_act = QAction(QIcon(self.resource_path('icons/FileNew.png')), "&New...", self)
        self.file_new_act.setShortcut('Ctrl+N')
        self.file_new_act.triggered.connect(self.DeleteAllDatabases)

        self.file_open_act = QAction(QIcon(self.resource_path('icons/FileOpen.png')), "&Open...", self)
        self.file_open_act.setShortcut('Ctrl+O')
        self.file_open_act.triggered.connect(self.openFile)

        self.file_saveas_act = QAction("Save &As...", self)
        self.file_saveas_act.triggered.connect(self.saveFileAs)

        self.file_save_act = QAction(QIcon(self.resource_path('icons/FileSave.png')), "&Save", self)
        self.file_save_act.setShortcut('Ctrl+S')
        self.file_save_act.triggered.connect(self.saveFile)

        self.file_merge_act = QAction("&Merge...", self)
        self.file_merge_act.triggered.connect(self.mergeFile)

        self.file_mergeAnalysis_act = QAction("Merge &Report...", self)
        self.file_mergeAnalysis_act.triggered.connect(self.mergeFileAnalysis)

        quit_act = QAction("E&xit", self)
        quit_act.triggered.connect(self.close)

        # Create view menu actions
        self.view_courselist_act = QAction(QIcon(self.resource_path('icons/CourseList2.png')), "&Course List", self)
        self.view_courselist_act.triggered.connect(self.viewcourselist)

        self.view_facultylist_act = QAction(QIcon(self.resource_path('icons/CourseAssignments.png')),
                                            "Course/&Faculty Assignments", self)
        self.view_facultylist_act.triggered.connect(self.viewfacultylist)

        self.view_noteeditor_act = QAction(QIcon(self.resource_path('icons/TextEdit.png')), "&Note Editor", self)
        self.view_noteeditor_act.triggered.connect(self.viewNoteEditor)

        self.view_timeslotlist_act = QAction(QIcon(self.resource_path('icons/Timeslots.png')), "&Timeslot List", self)
        self.view_timeslotlist_act.triggered.connect(self.viewtimeslotlist)

        self.view_courselinker_act = QAction(QIcon(self.resource_path('icons/Link2.png')), "Course &Linker", self)
        self.view_courselinker_act.triggered.connect(self.viewcourselinker)

        self.view_addroomviewer_act = QAction(QIcon(self.resource_path('icons/Room.png')), "&Room Viewer", self)
        self.view_addroomviewer_act.triggered.connect(self.addroomviewer)

        self.view_addprofessorviewer_act = QAction(QIcon(self.resource_path('icons/Person.png')),
                                                   "&Professor Schedule Viewer", self)
        self.view_addprofessorviewer_act.triggered.connect(self.addprofessorviewer)

        self.view_addcoursepositionsviewer_act = QAction(QIcon(self.resource_path('icons/CoursePositionViewer.png')),
                                                         "C&ourse Position Viewer", self)
        self.view_addcoursepositionsviewer_act.triggered.connect(self.addcoursepositionsviewer)

        # Test action for help in development.  Not used in final app but remains for future use.
        view_test_act = QAction("Test", self)
        view_test_act.triggered.connect(self.testing)

        # Create edit menu actions.

        # Add to database actions.
        data_newcourses_act = QAction(QIcon(self.resource_path('icons/FileNew.png')), "Add New Courses...", self)
        data_newcourses_act.triggered.connect(self.AddNewCourse)

        data_newfaculty_act = QAction(QIcon(self.resource_path('icons/NewFaculty.png')), "Add New Faculty...", self)
        data_newfaculty_act.triggered.connect(self.AddNewFaculty)

        data_newtimeslots_act = QAction(QIcon(self.resource_path('icons/NewTimeslots.png')),
                                        "Add New Standard Timeslots...", self)
        data_newtimeslots_act.triggered.connect(self.AddNewTimeslots)

        data_newrooms_act = QAction(QIcon(self.resource_path('icons/NewRooms.png')), "Add New Rooms...", self)
        data_newrooms_act.triggered.connect(self.AddNewRooms)

        edit_sectionnumbers_act = QAction("&Section Numbers...", self)
        edit_sectionnumbers_act.triggered.connect(self.EditSectionNumbers)

        # Add to databases submenu setup.
        addDataMenu = QMenu("Add to Databases", self)
        addDataMenu.setIcon(QIcon(self.resource_path('icons/FileNew.png')))
        addDataMenu.addAction(data_newcourses_act)
        addDataMenu.addAction(data_newfaculty_act)
        addDataMenu.addAction(data_newtimeslots_act)
        addDataMenu.addAction(data_newrooms_act)

        # Delete database actions.
        data_RemoveRoomTime_act = QAction("Remove Rooms and Times...", self)
        data_RemoveRoomTime_act.triggered.connect(self.RemoveAlRoomsAndTimes)

        data_deletecourses_act = QAction("Delete Courses Database...", self)
        data_deletecourses_act.triggered.connect(self.DeleteCourses)

        data_deletefaculty_act = QAction("Delete Faculty Database...", self)
        data_deletefaculty_act.triggered.connect(self.DeleteFaculty)

        data_deletetimeslots_act = QAction("Delete Standard Timeslots Database...", self)
        data_deletetimeslots_act.triggered.connect(self.DeleteTimeslots)

        data_deleterooms_act = QAction("Delete Rooms Database...", self)
        data_deleterooms_act.triggered.connect(self.DeleteRooms)

        data_deleteschedule_act = QAction("Delete Schedule Database...", self)
        data_deleteschedule_act.triggered.connect(self.DeleteSchedule)

        data_deleteall_act = QAction("Delete All Databases...", self)
        data_deleteall_act.triggered.connect(self.DeleteAllDatabases)

        # Delete databases submenu setup.
        deleteDataMenu = QMenu("Delete Databases", self)
        deleteDataMenu.setIcon(QIcon(self.resource_path('icons/Delete.png')))
        deleteDataMenu.addAction(data_RemoveRoomTime_act)
        deleteDataMenu.addSeparator()
        deleteDataMenu.addAction(data_deleteschedule_act)
        deleteDataMenu.addSeparator()
        deleteDataMenu.addAction(data_deletecourses_act)
        deleteDataMenu.addAction(data_deletefaculty_act)
        deleteDataMenu.addAction(data_deletetimeslots_act)
        deleteDataMenu.addAction(data_deleterooms_act)
        deleteDataMenu.addSeparator()
        deleteDataMenu.addAction(data_deleteall_act)

        # Other edit menu actions.
        data_description_act = QAction("&Description...", self)
        data_description_act.triggered.connect(self.inputDescription)

        data_annualload_act = QAction("&Annual Hour Load...", self)
        data_annualload_act.triggered.connect(self.inputYearlyCourseHourLoad)

        ImagePrintProperties_act = QAction("&Image Printing Options...", self)
        ImagePrintProperties_act.triggered.connect(self.getImagePrintingOptions)

        ImageMinimumFontSize_act = QAction("&Minimum Font Size...", self)
        ImageMinimumFontSize_act.triggered.connect(self.getMinimumFontSize)

        selectTheme_act = QAction("&Theme...", self)
        selectTheme_act.triggered.connect(self.SelectTheme)

        # Subwindow layout options.
        self.window_cascade_act = QAction(QIcon(self.resource_path('icons/Cascade.png')), "&Cascade", self)
        self.window_cascade_act.triggered.connect(self.cascadesubwindows)

        self.window_tile_act = QAction(QIcon(self.resource_path('icons/Tile2.png')), "&Tile", self)
        self.window_tile_act.triggered.connect(self.tilesubwindows)

        # Create help menu actions
        self.help_about_act = QAction(QIcon(self.resource_path('icons/About.png')), "&About...", self)
        self.help_about_act.triggered.connect(self.aboutDialog)

        self.help_help_act = QAction(QIcon(self.resource_path('icons/Help2.png')), "Help - System &Browser...",
                                     self)
        self.help_help_act.triggered.connect(self.onHelp)

        # self.help_internalhelp_act = QAction(QIcon(self.resource_path('icons/HelpBrowser.png')),
        #                                      "&Help - Internal Browser...", self)
        # self.help_internalhelp_act.triggered.connect(self.onInternalHelp)

        # Create report actions and document/table submenus.
        report_facultylist_act = QAction("Document...", self)
        report_facultylist_act.triggered.connect(self.facultyListReport)

        report_facultylisttable_act = QAction("Table...", self)
        report_facultylisttable_act.triggered.connect(self.facultyListReportTable)

        FacultyListReportMenu = QMenu("Faculty List", self)
        FacultyListReportMenu.addAction(report_facultylist_act)
        FacultyListReportMenu.addAction(report_facultylisttable_act)

        report_courseassignmentscoursedoc_act = QAction("Document...", self)
        report_courseassignmentscoursedoc_act.triggered.connect(self.CourseAssignmentsCourseReport)

        report_courseassignmentscoursetable_act = QAction("Table...", self)
        report_courseassignmentscoursetable_act.triggered.connect(self.CourseAssignmentsCourseReportTable)

        CourseAssignemntsByCourseReportMenu = QMenu("Course Assignments by Course", self)
        CourseAssignemntsByCourseReportMenu.addAction(report_courseassignmentscoursedoc_act)
        CourseAssignemntsByCourseReportMenu.addAction(report_courseassignmentscoursetable_act)

        report_courseassignmentsprofdoc_act = QAction("Document...", self)
        report_courseassignmentsprofdoc_act.triggered.connect(self.CourseAssignmentsProfessorReport)

        report_courseassignmentsproftable_act = QAction("Table...", self)
        report_courseassignmentsproftable_act.triggered.connect(self.CourseAssignmentsProfessorReportTable)

        CourseAssignemntsByProfReportMenu = QMenu("Course Assignments by Professor", self)
        CourseAssignemntsByProfReportMenu.addAction(report_courseassignmentsprofdoc_act)
        CourseAssignemntsByProfReportMenu.addAction(report_courseassignmentsproftable_act)

        report_schedulebycoursedoc_act = QAction("Document...", self)
        report_schedulebycoursedoc_act.triggered.connect(self.ScheduleByCourseReport)

        report_schedulebycoursetable_act = QAction("Table...", self)
        report_schedulebycoursetable_act.triggered.connect(self.ScheduleByCourseReportTable)

        ScheduleByCourseReportMenu = QMenu("Schedule Sorted by Course", self)
        ScheduleByCourseReportMenu.addAction(report_schedulebycoursedoc_act)
        ScheduleByCourseReportMenu.addAction(report_schedulebycoursetable_act)

        report_schedulebyprofdoc_act = QAction("Document...", self)
        report_schedulebyprofdoc_act.triggered.connect(self.ScheduleByProfReport)

        report_schedulebyproftable_act = QAction("Table...", self)
        report_schedulebyproftable_act.triggered.connect(self.ScheduleByProfReportTable)

        ScheduleByProfReportMenu = QMenu("Schedule Sorted by Professor", self)
        ScheduleByProfReportMenu.addAction(report_schedulebyprofdoc_act)
        ScheduleByProfReportMenu.addAction(report_schedulebyproftable_act)

        report_schedulebyroomdoc_act = QAction("Document...", self)
        report_schedulebyroomdoc_act.triggered.connect(self.ScheduleByRoomReport)

        report_schedulebyroomtable_act = QAction("Table...", self)
        report_schedulebyroomtable_act.triggered.connect(self.ScheduleByRoomReportTable)

        ScheduleByRoomReportMenu = QMenu("Schedule Sorted by Room", self)
        ScheduleByRoomReportMenu.addAction(report_schedulebyroomdoc_act)
        ScheduleByRoomReportMenu.addAction(report_schedulebyroomtable_act)

        report_roomschedulesprint_act = QAction("Print &Room Schedule Images...", self)
        report_roomschedulesprint_act.triggered.connect(self.RoomSchedulesPrint)

        report_profschedulesprint_act = QAction("Print &Professor Schedule Images...", self)
        report_profschedulesprint_act.triggered.connect(self.ProfSchedulesPrint)

        report_schedulechanges_act = QAction("&Schedule Changes...", self)
        report_schedulechanges_act.triggered.connect(self.ScheduleChanges)

        # Create the menu bar
        menu_bar = QMenuBar(self)
        # menu_bar.setNativeMenuBar(False)

        # Create file menu and add actions
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(self.file_new_act)
        file_menu.addAction(self.file_open_act)
        file_menu.addSeparator()
        file_menu.addAction(self.file_save_act)
        file_menu.addAction(self.file_saveas_act)
        file_menu.addSeparator()
        file_menu.addAction(self.file_merge_act)
        file_menu.addSeparator()
        file_menu.addAction(quit_act)

        edit_menu = menu_bar.addMenu('&Edit')
        edit_menu.addAction(data_description_act)
        edit_menu.addAction(data_annualload_act)
        edit_menu.addSeparator()
        edit_menu.addAction(ImagePrintProperties_act)
        edit_menu.addAction(ImageMinimumFontSize_act)
        edit_menu.addSeparator()
        edit_menu.addAction(edit_sectionnumbers_act)
        edit_menu.addSeparator()
        edit_menu.addMenu(addDataMenu)
        edit_menu.addMenu(deleteDataMenu)
        edit_menu.addSeparator()
        edit_menu.addAction(selectTheme_act)

        view_menu = menu_bar.addMenu('&View')
        view_menu.addAction(self.view_courselist_act)
        view_menu.addAction(self.view_facultylist_act)
        view_menu.addSeparator()
        view_menu.addAction(self.view_addroomviewer_act)
        view_menu.addAction(self.view_addprofessorviewer_act)
        view_menu.addAction(self.view_addcoursepositionsviewer_act)
        view_menu.addSeparator()
        view_menu.addAction(self.view_courselinker_act)
        view_menu.addAction(self.view_timeslotlist_act)
        view_menu.addSeparator()
        view_menu.addAction(self.view_noteeditor_act)

        reports_menu = menu_bar.addMenu('&Reports')
        reports_menu.addMenu(FacultyListReportMenu)
        reports_menu.addSeparator()
        reports_menu.addMenu(CourseAssignemntsByCourseReportMenu)
        reports_menu.addMenu(CourseAssignemntsByProfReportMenu)
        reports_menu.addSeparator()
        reports_menu.addMenu(ScheduleByCourseReportMenu)
        reports_menu.addMenu(ScheduleByProfReportMenu)
        reports_menu.addMenu(ScheduleByRoomReportMenu)
        reports_menu.addSeparator()
        reports_menu.addAction(report_roomschedulesprint_act)
        reports_menu.addAction(report_profschedulesprint_act)
        reports_menu.addSeparator()
        reports_menu.addAction(report_schedulechanges_act)
        reports_menu.addAction(self.file_mergeAnalysis_act)

        window_menu = menu_bar.addMenu('&Window')
        window_menu.addAction(self.window_cascade_act)
        window_menu.addAction(self.window_tile_act)

        help_menu = menu_bar.addMenu('&Help')
        help_menu.addAction(self.help_help_act)
        # if not self.isMac:
        #     help_menu.addAction(self.help_internalhelp_act)
        # help_menu.addAction(self.help_internalhelp_act)
        help_menu.addSeparator()
        help_menu.addAction(self.help_about_act)

        return menu_bar

    def createToolBar(self):
        """
        Create toolbar for GUI
        """
        # Set up toolbar
        tool_bar = QToolBar("Main Toolbar")
        tool_bar.setIconSize(QSize(20, 20))
        self.addToolBar(tool_bar)

        # Add actions to toolbar
        tool_bar.addAction(self.file_open_act)
        tool_bar.addAction(self.file_save_act)
        tool_bar.addSeparator()
        tool_bar.addAction(self.view_courselist_act)
        tool_bar.addAction(self.view_facultylist_act)
        tool_bar.addSeparator()
        tool_bar.addAction(self.view_addroomviewer_act)
        tool_bar.addAction(self.view_addprofessorviewer_act)
        tool_bar.addAction(self.view_addcoursepositionsviewer_act)
        tool_bar.addSeparator()
        tool_bar.addAction(self.view_courselinker_act)
        tool_bar.addSeparator()
        tool_bar.addAction(self.view_noteeditor_act)
        tool_bar.addSeparator()
        tool_bar.addAction(self.window_cascade_act)
        tool_bar.addAction(self.window_tile_act)
        tool_bar.addSeparator()
        tool_bar.addAction(self.help_help_act)
        # if not self.isMac:
        #     tool_bar.addAction(self.help_internalhelp_act)
        # tool_bar.addAction(self.help_internalhelp_act)
        tool_bar.addAction(self.help_about_act)

    def cascadesubwindows(self):
        """
        Cascade the subwindows.
        """
        self.desktop.cascadeSubWindows()

    def tilesubwindows(self):
        """
        Tile the subwindows.
        """
        self.desktop.tileSubWindows()

    def SelectTheme(self):
        """
        Select the style/theme for the UI from the supported list of themes.
        """
        items = QStyleFactory.keys()
        if len(items) <= 1:
            return

        items.sort()
        item, ok = QInputDialog.getItem(self, "Select Theme", "Available Themes", items, 0, False)

        if ok:
            self.Parent.setStyle(item)

    #########################################################################
    ### Database Reports
    #########################################################################

    def HTML_FrontMatter(self):
        """
        Creates the HTML setup and CSS used for the HTML/document reports.

        :return: The front matter setup for the HTML/document reports.
        """

        htmltext = """<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            
        <style type="text/css">
        .regft1 { 
        margin-top: 10pt; margin-right: 20pt; margin-bottom: 10pt; margin-left: 20pt; 
        font-family: Trebuchet MS, verdana, arial, helvetica, Tahoma, sans-serif; 
        font-size: 12pt; }
        
        H4 {
        font-size: large;
        }
        
        .lightgray{
        color: gray;
        }

        .red{
        color: #FF0000;
        }

        p.headitem{
        margin: 10px 0px 0px 0px;
        }

        p.item{
        margin: 5px 0px 0px 0px;
        }
        
        table.report{
          border: 1px solid;
          border-collapse: collapse;
        }
         
        th.report, td.report {
          border: 1px solid;
          padding: 3px;
        }

        th.nowrap, td.nowrap{
          white-space: nowrap;
        }        
                
        th.left, td.left{
            text-align: left;
        }        

        th.center, td.center{
            text-align: center;
        }        

        th.right, td.right{
            text-align: right;
        }
        
        table.pad, th.pad, td.pad{
            width: 100%;
        }
        
        .smtopmar{
            margin-top: 5px;
        }

        .smbottommar{
            margin-bottom: 5px;
        }

        .notopmar{
            margin-top: 0px;
        }

        .nobottommar{
            margin-bottom: 0px;
        }
        
        .circlist{
        list-style-type: circle;
        }
         
        </style>
            
        </head>
        
        <body>
        <div class="regft1">
        
        """
        return htmltext

    def HTML_BackMatter(self):
        """
        Creates the ending to the HTML reports.

        :return: The backmatter ending to the HTML/document code.
        """
        htmltext = """
        
        </div>
        </body>
        </html>
        """
        return htmltext

    def HTML_Heading(self, title=""):
        """
        Creates a heading table for reports.

        :param title: Title to go into the heading.
        :return: The HTML table.
        """

        htmltext = "<P>"
        if self.options[0] != "":
            htmltext += self.options[0] + " - " + title + "\n"
        else:
            htmltext += title + "\n"
        htmltext += "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" + str(datetime.datetime.now()) + "</P>"
        return htmltext

    def facultyListReport(self):
        """
        Creates the faculty listing report in a document.
        """
        if len(self.faculty) == 0:
            return

        htmltext = self.HTML_FrontMatter()
        htmltext += self.HTML_Heading("Faculty List")
        htmltext += """
        <table class="report">
        <tr>
          <td class="report center">
            <b>Professor</b>
          </td>
          <td class="report center">
            <b>SD</b>
          </td>
        </tr>
        """

        for prof in self.faculty:
            htmltext += """
            <tr>
              <td class="report left nowrap">
              """
            htmltext += prof.getName() + "\n"
            htmltext += """
            </td>
              <td class="report center nowrap">
              """
            htmltext += prof.ShortDes + "\n"
            htmltext += """
              </td>
            </tr>
            """

        htmltext += """
            </table>
            """

        htmltext += self.HTML_BackMatter()
        reportview = HTMLViewer(self, "Faculty List", htmltext)
        reportview.exec()

    def facultyListReportTable(self):
        """
        Creates the faculty listing report in a table.
        """
        datalist = []
        for prof in self.faculty:
            datalist.append([prof.getName(), prof.ShortDes])

        if datalist == []:
            return

        reportview = GeneralTableDialog(self, "Faculty List", datalist, ["Professor", "SD"])
        reportview.exec()

    def CourseAssignmentsCourseInfoList(self) -> []:
        """
        Creates the course assignment list by course to be used by the course assignments
        document and table.

        :return: The course assignment list.
        """
        courselist = CourseList(self)

        datalist = []
        for course in self.courses:
            displaystring = courselist.courseString(course)
            displaylist = displaystring.split("\n")
            for i in range(len(displaylist)):
                displaylist[i] = displaylist[i].lstrip().rstrip()

            if len(displaylist) == 3:
                temp = displaylist[0].split(":")
                coursecodenumber = temp[0]

                temp = displaylist[1].split("Enrollment:")
                secnumbers = temp[0][9:].lstrip().rstrip()
                enrollnumbers = temp[1].lstrip().rstrip()

                sectrue = secnumbers.split("/")[0].lstrip().rstrip()
                sectent = secnumbers.split("/")[1].lstrip().rstrip()
                enrolltrue = enrollnumbers.split("/")[0].lstrip().rstrip()
                enrolltent = enrollnumbers.split("/")[1].lstrip().rstrip()

                staffing = displaylist[2][6:].lstrip().rstrip()
                datalist.append([coursecodenumber, sectrue, sectent, enrolltrue, enrolltent, staffing])

        return datalist

    def CourseAssignmentsCourseReport(self):
        """
        Creates the course assignments list by course document report.
        """
        courseinfo = self.CourseAssignmentsCourseInfoList()

        if courseinfo == []:
            return

        htmltext = self.HTML_FrontMatter()
        htmltext += self.HTML_Heading("Course Assignments by Course")
        htmltext += """
        <table class="report">
        <tr>
          <td class="report center">
            <b>Course</b>
          </td>
          <td class="report center nowrap">
            <b>Sec.</b>
          </td>
          <td class="report center nowrap">
            <b>T. Sec.</b>
          </td>
          <td class="report center nowrap">
            <b>Enroll.</b>
          </td>
          <td class="report center nowrap">
            <b>T. Enroll.</b>
          </td>
          <td class="report center pad">
            <b>Staffing</b>
          </td>

        </tr>
        """

        for ci in courseinfo:
            htmltext += "<tr> \n"
            htmltext += """<td class="report left nowrap">""" + ci[0] + "</td> \n"
            for i in range(1, 5):
                htmltext += """<td class="report center">""" + ci[i] + "</td> \n"
            htmltext += """<td class="report left">""" + ci[5] + "</td> \n"
            htmltext += "</tr> \n"

        htmltext += """
            </table>
            """

        htmltext += self.HTML_BackMatter()
        reportview = HTMLViewer(self, "Course Assignments by Course", htmltext)
        reportview.exec()

    def CourseAssignmentsCourseReportTable(self):
        """
        Creates the course assignments list by course table report.
        """
        courseinfo = self.CourseAssignmentsCourseInfoList()

        if courseinfo == []:
            return

        headers = ["Course", "Sec.", "T. Sec.", "Enroll.", "T. Enroll.", "Staffing"]
        reportview = GeneralTableDialog(self, "Course Assignments by Course", courseinfo, headers)
        reportview.exec()

    def CourseAssignmentsProfessorInfoList(self) -> []:
        """
        Creates the course assignment list by professor to be used by the course assignments
        document and table.

        :return: The course assignment list by professor.
        """
        data = []
        for prof in self.faculty:
            id = prof.InternalID
            workload = 0
            tentwork = 0
            classlist = []
            tentclasslist = []

            for schedit in self.schedule:
                if id in schedit.ProfessorIID:
                    course = self.findCourseFromIID(schedit.CourseIID)
                    if schedit.Tentative:
                        tentwork += course.Workload / len(schedit.ProfessorIID)
                        tentclasslist.append(course.getName())
                    else:
                        workload += course.Workload / len(schedit.ProfessorIID)
                        classlist.append(course.getName())

            freq = collections.Counter(classlist)
            tentfreq = collections.Counter(tentclasslist)

            teachinglist = []
            for item in freq:
                teachinglist.append(item)
            for item in tentfreq:
                teachinglist.append(item)

            teachinglist = list(set(teachinglist))
            classlist = []
            for item in teachinglist:
                numclasses = freq[item]
                numtentclasses = tentfreq[item]
                endstr = ""
                if numclasses + numtentclasses > 0:
                    if numtentclasses > 0:
                        endstr = "(" + str(numclasses) + "/" + str(numtentclasses) + ")"
                    elif numclasses > 1:
                        endstr = "(" + str(numclasses) + ")"

                    coursestr = item + " " + endstr
                    classlist.append(coursestr.lstrip().rstrip())

            classlist.sort()
            displaystr = ""
            for i in range(len(classlist)):
                displaystr += classlist[i]
                if i < len(classlist) - 1:
                    displaystr += ", "

            workloadstr = str(workload) + " (" + str(float("{:.4f}".format(workload / self.options[1]))) + ")"
            if tentwork > 0:
                workloadstr += " / " + str(tentwork) + " (" + str(
                    float("{:.4f}".format(tentwork / self.options[1]))) + ")"

            data.append([prof.getName(), displaystr, workloadstr])

        return data

    def CourseAssignmentsProfessorReport(self):
        """
        Creates the course assignments report by professor document.
        """
        profinfo = self.CourseAssignmentsProfessorInfoList()

        if profinfo == []:
            return

        htmltext = self.HTML_FrontMatter()
        htmltext += self.HTML_Heading("Course Assignments by Professor")
        htmltext += """
        <table class="report">
        <tr>
          <td class="report center nowrap">
            <b>Professor</b>
          </td>
          <td class="report center nowrap">
            <b>Course List</b>
          </td>
          <td class="report center nowrap">
            <b>Workload</b>
          </td>
        </tr>
        """

        for ci in profinfo:
            htmltext += "<tr> \n"
            htmltext += """<td class="report left nowrap">""" + ci[0] + "</td> \n"
            htmltext += """<td class="report left pad">""" + ci[1] + "</td> \n"
            htmltext += """<td class="report left nowrap">""" + ci[2] + "</td> \n"
            htmltext += "</tr> \n"

        htmltext += """
            </table>
            """

        htmltext += self.HTML_BackMatter()
        reportview = HTMLViewer(self, "Course Assignments by Course", htmltext)
        reportview.exec()

    def CourseAssignmentsProfessorReportTable(self):
        """
        Creates the course assignments report by professor table.
        """
        profinfo = self.CourseAssignmentsProfessorInfoList()

        if profinfo == []:
            return

        headers = ["Professor", "Course List", "Workload"]
        reportview = GeneralTableDialog(self, "Course Assignments by Professor", profinfo, headers)
        reportview.exec()

    def ScheduleByCourseInfoList(self) -> []:
        """
        Creates the schedule information list by course to be used by the schedule by course
        report document and table.

        :return: The schedule information list by course.
        """
        data = []

        for scheditem in self.schedule:
            dataitem = []

            course = self.findCourseFromIID(scheditem.CourseIID)
            dataitem.append(course.getName())
            dataitem.append(scheditem.Section)
            if scheditem.Tentative:
                dataitem.append("T")
            else:
                dataitem.append("")

            proflist = []
            for profiid in scheditem.ProfessorIID:
                prof = self.findProfessorFromIID(profiid)
                proflist.append(prof.getName())

            profstr = ""
            for i in range(len(proflist)):
                profstr += proflist[i]
                if i < len(proflist) - 1:
                    profstr += ", "

            dataitem.append(profstr)

            roomtimelist = []
            for slots in scheditem.RoomsAndTimes:
                room = self.findRoomFromIID(slots[0])
                times = slots[1]
                roomtimelist.append(times.getDescription() + " " + room.getName())

            roomtimelist.sort()
            slotstr = ""
            for i in range(len(roomtimelist)):
                slotstr += roomtimelist[i]
                if i < len(roomtimelist) - 1:
                    slotstr += ", "

            dataitem.append(slotstr)

            linkedclasslist = []
            for linkedclass in scheditem.LinkedCourses:
                linkedscheditem = self.findScheduleItemFromIID(linkedclass)
                course = self.findCourseFromIID(linkedscheditem.CourseIID)
                linkedclasslist.append(course.getName() + "-" + linkedscheditem.Section)

            linkedclasslist.sort()
            linkedstr = ""
            for i in range(len(linkedclasslist)):
                linkedstr += linkedclasslist[i]
                if i < len(linkedclasslist) - 1:
                    linkedstr += ", "

            dataitem.append(linkedstr)
            dataitem.append(scheditem.Subtitle)
            dataitem.append(scheditem.Designation)

            data.append(dataitem)

        data.sort()
        return data

    def ScheduleByCourseReport(self):
        """
        Creates the schedule sorted by course document report.
        """
        schedulebycoursedata = self.ScheduleByCourseInfoList()

        # Course section tentative profs times/rooms linked/linkedto subtitle designations
        if schedulebycoursedata == []:
            return

        htmltext = self.HTML_FrontMatter()
        htmltext += self.HTML_Heading("Schedule by Course")

        for course in self.courses:
            courseonschedule = False
            coursestr = course.getName()
            for item in schedulebycoursedata:
                if item[0] == coursestr:
                    courseonschedule = True

            if courseonschedule:
                htmltext += """<H4 class="smbottommar">""" + course.getName() + ": " + course.Title + "</H4>\n"
                htmltext += """<ul class="smtopmar"> \n"""
                for item in schedulebycoursedata:
                    if item[0] == coursestr:
                        if item[2] == "T":
                            htmltext += """<li class="smtopmar lightgray">"""
                        else:
                            htmltext += """<li class="smtopmar">"""

                        if item[2] == "T":
                            htmltext += """<I class="lightgray">"""

                        htmltext += item[0] + "-" + item[1] + ": " + item[3]

                        if item[2] == "T":
                            htmltext += "  (Tentative)</I>\n"

                        htmltext += "</li>\n"

                        if (item[4] != "") or (item[5] != "") or (item[6] != "") or (item[7] != ""):
                            htmltext += """<ul class="circlist"> \n"""
                            if item[4] != "":
                                if item[2] == "T":
                                    htmltext += """<li><I class="lightgray">""" + item[4] + "</I></li>\n"
                                else:
                                    htmltext += "<li>" + item[4] + "</li>\n"

                            if item[5] != "":
                                if item[2] == "T":
                                    htmltext += """<li><I class="lightgray">""" + "Linked Classes: " + item[
                                        5] + "</I></li>\n"
                                else:
                                    htmltext += "<li>" + "Linked Classes: " + item[5] + "</li>\n"

                            if item[6] != "":
                                if item[2] == "T":
                                    htmltext += """<li><I class="lightgray">""" + "Subtitle: " + item[6] + "</I></li>\n"
                                else:
                                    htmltext += "<li>" + "Subtitle: " + item[6] + "</li>\n"

                            if item[7] != "":
                                if item[2] == "T":
                                    htmltext += """<li><I class="lightgray">""" + "Designations: " + item[
                                        7] + "</I></li>\n"
                                else:
                                    htmltext += "<li>" + "Designations: " + item[7] + "</li>\n"

                            htmltext += """</ul> \n"""

                        if item[2] == "T":
                            htmltext += "</I>\n"

                htmltext += """</ul> \n"""

        htmltext += """<BR><BR> \n"""

        htmltext += self.HTML_BackMatter()
        reportview = HTMLViewer(self, "Schedule by Course", htmltext)
        reportview.exec()

    def ScheduleByCourseReportTable(self):
        """
        Creates the schedule sorted by course table report.
        """
        schedulebycoursedata = self.ScheduleByCourseInfoList()

        # Course section tentative profs times/rooms linked/linkedto subtitle designations
        if schedulebycoursedata == []:
            return

        headers = ["Course", "Section", "Tent.", "Professors", "Rooms & Times", "Linked Classes", "Subtitle",
                   "Designations"]
        reportview = GeneralTableDialog(self, "Schedule by Course", schedulebycoursedata, headers)
        reportview.exec()

    def ScheduleByProfInfoList(self) -> []:
        """
        Creates the schedule information list by professor to be used by the schedule by professor
        report document and table.

        :return: The schedule information list by professor.
        """
        schedulebycoursedata = self.ScheduleByCourseInfoList()

        if schedulebycoursedata == []:
            return []

        schedulebyprofdata = []
        for prof in self.faculty:
            profstr = prof.getName()
            for item in schedulebycoursedata:
                if profstr in item[3]:
                    profinfoline = [profstr, item[0], item[1], item[2], item[4], item[5], item[6], item[7]]
                    schedulebyprofdata.append(profinfoline)

        schedulebyprofdata.sort()
        return schedulebyprofdata

    def ScheduleByProfReport(self):
        """
        Creates the schedule sorted by professor document report.
        """
        schedulebyprofdata = self.ScheduleByProfInfoList()

        if schedulebyprofdata == []:
            return

        htmltext = self.HTML_FrontMatter()
        htmltext += self.HTML_Heading("Schedule by Professor")

        for prof in self.faculty:
            profonschedule = False
            profstr = prof.getName()
            for item in schedulebyprofdata:
                if item[0] == profstr:
                    profonschedule = True

            if profonschedule:
                htmltext += """<H4 class="smbottommar">""" + prof.getName() + "</H4>\n"
                htmltext += """<ul class="smtopmar"> \n"""
                for item in schedulebyprofdata:
                    if item[0] == profstr:
                        if item[3] == "T":
                            htmltext += """<li class="smtopmar lightgray">"""
                        else:
                            htmltext += """<li class="smtopmar">"""

                        if item[3] == "T":
                            htmltext += """<I class="lightgray">"""

                        coursename = self.findCourseFromString(item[1]).Title
                        htmltext += item[1] + "-" + item[2] + ": " + coursename

                        if item[3] == "T":
                            htmltext += "  (Tentative)</I>\n"

                        htmltext += "</li>\n"

                        if (item[4] != "") or (item[5] != "") or (item[6] != "") or (item[7] != ""):
                            htmltext += """<ul class="circlist"> \n"""
                            if item[4] != "":
                                if item[3] == "T":
                                    htmltext += """<li><I class="lightgray">""" + item[4] + "</I></li>\n"
                                else:
                                    htmltext += "<li>" + item[4] + "</li>\n"

                            if item[5] != "":
                                if item[3] == "T":
                                    htmltext += """<li><I class="lightgray">""" + "Linked Classes: " + item[
                                        5] + "</I></li>\n"
                                else:
                                    htmltext += "<li>" + "Linked Classes: " + item[5] + "</li>\n"

                            if item[6] != "":
                                if item[3] == "T":
                                    htmltext += """<li><I class="lightgray">""" + "Subtitle: " + item[6] + "</I></li>\n"
                                else:
                                    htmltext += "<li>" + "Subtitle: " + item[6] + "</li>\n"

                            if item[7] != "":
                                if item[3] == "T":
                                    htmltext += """<li><I class="lightgray">""" + "Designations: " + item[
                                        7] + "</I></li>\n"
                                else:
                                    htmltext += "<li>" + "Designations: " + item[7] + "</li>\n"

                            htmltext += """</ul> \n"""

                        if item[3] == "T":
                            htmltext += "</I>\n"

                htmltext += """</ul> \n"""

        htmltext += """<BR><BR> \n"""

        htmltext += self.HTML_BackMatter()
        reportview = HTMLViewer(self, "Schedule by Professor", htmltext)
        reportview.exec()

    def ScheduleByProfReportTable(self):
        """
        Creates the schedule sorted by professor table report.
        """
        schedulebyprofdata = self.ScheduleByProfInfoList()

        if schedulebyprofdata == []:
            return

        headers = ["Professor", "Course", "Section", "Tent.", "Rooms & Times", "Linked Classes", "Subtitle",
                   "Designations"]
        reportview = GeneralTableDialog(self, "Schedule by Professor", schedulebyprofdata, headers)
        reportview.exec()

    def ScheduleByRoomInfoList(self) -> []:
        """
        Creates the schedule information list by room to be used by the schedule by room
        report document and table.

        :return: The schedule information list by room.
        """

        # Room times course section tentative profs othertimes&rooms linked/linkedto subtitle designations
        data = []
        for scheditem in self.schedule:
            roomids = []
            for roomtime in scheditem.RoomsAndTimes:
                roomids.append(roomtime[0])
            roomids = list(set(roomids))

            for roomid in roomids:
                dataitem = []
                roomstr = self.findRoomFromIID(roomid).getName()
                dataitem.append(roomstr)
                timesinroom = []
                for roomtime in scheditem.RoomsAndTimes:
                    if roomtime[0] == roomid:
                        timesinroom.append(roomtime[1].getDescription())

                timesinroom.sort()
                timesinroomstr = ""
                for i in range(len(timesinroom)):
                    timesinroomstr += timesinroom[i]
                    if i < len(timesinroom) - 1:
                        timesinroomstr += ", "

                dataitem.append(timesinroomstr)

                course = self.findCourseFromIID(scheditem.CourseIID)
                dataitem.append(course.getName())
                dataitem.append(scheditem.Section)
                if scheditem.Tentative:
                    dataitem.append("T")
                else:
                    dataitem.append("")

                proflist = []
                for profiid in scheditem.ProfessorIID:
                    prof = self.findProfessorFromIID(profiid)
                    proflist.append(prof.getName())

                proflist.sort()
                profstr = ""
                for i in range(len(proflist)):
                    profstr += proflist[i]
                    if i < len(proflist) - 1:
                        profstr += ", "

                dataitem.append(profstr)

                timesnotinroom = []
                for roomtime in scheditem.RoomsAndTimes:
                    if roomtime[0] != roomid:
                        room = self.findRoomFromIID(roomtime[0])
                        timesnotinroom.append(roomtime[1].getDescription() + " " + room.getName())

                timesnotinroom.sort()
                timesnotinroomstr = ""
                for i in range(len(timesnotinroom)):
                    timesnotinroomstr += timesnotinroom[i]
                    if i < len(timesnotinroom) - 1:
                        timesnotinroomstr += ", "

                dataitem.append(timesnotinroomstr)

                linkedclasslist = []
                for linkedclass in scheditem.LinkedCourses:
                    linkedscheditem = self.findScheduleItemFromIID(linkedclass)
                    course = self.findCourseFromIID(linkedscheditem.CourseIID)
                    linkedclasslist.append(course.getName() + "-" + linkedscheditem.Section)

                linkedclasslist.sort()
                linkedstr = ""
                for i in range(len(linkedclasslist)):
                    linkedstr += linkedclasslist[i]
                    if i < len(linkedclasslist) - 1:
                        linkedstr += ", "

                dataitem.append(linkedstr)
                dataitem.append(scheditem.Subtitle)
                dataitem.append(scheditem.Designation)

                data.append(dataitem)

        data.sort()
        return data

    def ScheduleByRoomReportTable(self):
        """
        Creates the schedule sorted by room table report.
        """
        schedulebyroomdata = self.ScheduleByRoomInfoList()

        if schedulebyroomdata == []:
            return

        # Room times course section tentative profs othertimes&rooms linked/linkedto subtitle designations
        headers = ["Room", "Times", "Course", "Section", "Tent.", "Professors", "Other Rooms & Times", "Linked Classes",
                   "Subtitle", "Designations"]
        reportview = GeneralTableDialog(self, "Schedule by Room", schedulebyroomdata, headers)
        reportview.exec()

    def ScheduleByRoomReport(self):
        """
        Creates the schedule sorted by room document report.
        """
        schedulebyroomdata = self.ScheduleByRoomInfoList()

        if schedulebyroomdata == []:
            return

        # Room times course section tentative profs othertimes&rooms linked/linkedto subtitle designations
        roomlist = []
        for item in schedulebyroomdata:
            roomlist.append(item[0])

        roomlist = list(set(roomlist))
        roomlist.sort()

        htmltext = self.HTML_FrontMatter()
        htmltext += self.HTML_Heading("Schedule by Room")

        for roomstr in roomlist:
            htmltext += """<H4 class="smbottommar">""" + roomstr + "</H4>\n"
            htmltext += """<ul class="smtopmar"> \n"""
            for item in schedulebyroomdata:
                if item[0] == roomstr:
                    if item[4] == "T":
                        htmltext += """<li class="smtopmar lightgray">"""
                    else:
                        htmltext += """<li class="smtopmar">"""

                    if item[4] == "T":
                        htmltext += """<I class="lightgray">"""

                    coursename = self.findCourseFromString(item[2]).Title
                    htmltext += item[1] + " - " + item[2] + "-" + item[3] + ": " + coursename

                    if item[4] == "T":
                        htmltext += "  (Tentative)</I>\n"

                    htmltext += "</li>\n"

                    if (item[5] != "") or (item[6] != "") or (item[7] != "") or (item[8] != "") or (item[9] != ""):
                        htmltext += """<ul class="circlist"> \n"""
                        if item[5] != "":
                            if item[4] == "T":
                                htmltext += """<li><I class="lightgray">""" + "Professors: " + item[5] + "</I></li>\n"
                            else:
                                htmltext += "<li>" + "Professors: " + item[5] + "</li>\n"

                        if item[6] != "":
                            if item[4] == "T":
                                htmltext += """<li><I class="lightgray">""" + "Other Times: " + item[6] + "</I></li>\n"
                            else:
                                htmltext += "<li>" + "Other Times: " + item[6] + "</li>\n"

                        if item[7] != "":
                            if item[4] == "T":
                                htmltext += """<li><I class="lightgray">""" + "Linked Classes: " + item[
                                    7] + "</I></li>\n"
                            else:
                                htmltext += "<li>" + "Linked Classes: " + item[7] + "</li>\n"

                        if item[8] != "":
                            if item[4] == "T":
                                htmltext += """<li><I class="lightgray">""" + "Subtitle: " + item[8] + "</I></li>\n"
                            else:
                                htmltext += "<li>" + "Subtitle: " + item[8] + "</li>\n"

                        if item[9] != "":
                            if item[4] == "T":
                                htmltext += """<li><I class="lightgray">""" + "Designations: " + item[9] + "</I></li>\n"
                            else:
                                htmltext += "<li>" + "Designations: " + item[9] + "</li>\n"

                        htmltext += """</ul> \n"""

                    if item[4] == "T":
                        htmltext += "</I>"

            htmltext += """</ul> \n"""

        htmltext += """<BR><BR> \n"""

        htmltext += self.HTML_BackMatter()
        reportview = HTMLViewer(self, "Schedule by Room", htmltext)
        reportview.exec()

    def MergeReport(self, mergedata=[]):
        """
        Takes the report data produced by the mergeSchedules function and produces a document
        type report.

        :param mergedata: Merge report data produced by the mergeSchedules function.
        """
        if mergedata == []:
            return

        # mergereport = [reportNewFaculty, reportNewRooms, reportNewCourses, reportNewSlots,
        #                reportSectionChanges, reportTimeConflicts, reportNewClasses]

        rarrow = " &rarr; "

        reportNewFaculty = mergedata[0]
        reportNewRooms = mergedata[1]
        reportNewCourses = mergedata[2]
        reportNewSlots = mergedata[3]
        reportSectionChanges = mergedata[4]
        reportTimeConflicts = mergedata[5]
        reportNewClasses = mergedata[6]

        htmltext = self.HTML_FrontMatter()
        htmltext += self.HTML_Heading("Merge Report")

        if len(reportNewFaculty) > 0:
            htmltext += """<H4 class="smbottommar">""" + "Added Faculty" + "</H4>\n"
            htmltext += """<ul class="smtopmar"> \n"""
            for item in reportNewFaculty:
                htmltext += """<li class="smtopmar">""" + item + "</li>\n"
            htmltext += """</ul> \n"""

        if len(reportNewRooms) > 0:
            htmltext += """<H4 class="smbottommar">""" + "Added Rooms" + "</H4>\n"
            htmltext += """<ul class="smtopmar"> \n"""
            for item in reportNewRooms:
                htmltext += """<li class="smtopmar">""" + item + "</li>\n"
            htmltext += """</ul> \n"""

        if len(reportNewCourses) > 0:
            htmltext += """<H4 class="smbottommar">""" + "Added Courses" + "</H4>\n"
            htmltext += """<ul class="smtopmar"> \n"""
            for item in reportNewCourses:
                htmltext += """<li class="smtopmar">""" + item + "</li>\n"
            htmltext += """</ul> \n"""

        if len(reportNewSlots) > 0:
            htmltext += """<H4 class="smbottommar">""" + "Added Standard Timeslots" + "</H4>\n"
            htmltext += """<ul class="smtopmar"> \n"""
            for item in reportNewSlots:
                htmltext += """<li class="smtopmar">""" + item + "</li>\n"
            htmltext += """</ul> \n"""

        if len(reportSectionChanges) > 0:
            htmltext += """<H4 class="smbottommar">""" + "Section Number Changes" + "</H4>\n"
            htmltext += """<ul class="smtopmar"> \n"""
            for item in reportSectionChanges:
                htmltext += """<li class="smtopmar">""" + item[0] + rarrow + item[1] + "</li>\n"
            htmltext += """</ul> \n"""

        if len(reportTimeConflicts) > 0:
            htmltext += """<H4 class="smbottommar">""" + "Time Conflicts" + "</H4>\n"
            htmltext += """<ul class="smtopmar"> \n"""
            for item in reportTimeConflicts:
                htmltext += """<li class="smtopmar">""" + item[0] + "</li>\n"
                htmltext += """<ul class="smtopmar circlist"> \n"""
                for slot in item[1]:
                    htmltext += """<li class="smtopmar">""" + slot[1].getDescription() + "</li>\n"
                htmltext += """</ul> \n"""
            htmltext += """</ul> \n"""

        if len(reportNewClasses) > 0:
            htmltext += """<H4 class="smbottommar">""" + "Classes Added" + "</H4>\n"
            htmltext += """<ul class="smtopmar"> \n"""
            for item in reportNewClasses:
                htmltext += """<li class="smtopmar">""" + item + "</li>\n"
            htmltext += """</ul> \n"""

        htmltext += """<BR><BR> \n"""

        htmltext += self.HTML_BackMatter()
        reportview = HTMLViewer(self, "Merge Report", htmltext)
        reportview.exec()

    def RoomSchedulesPrint(self):
        """
        Function that coordinates the printing of all room schedules.  Uses an unseen
        RoomViewer subwindow to render the room schedules.
        """
        rooms = []
        for scheditem in self.schedule:
            for roomtime in scheditem.RoomsAndTimes:
                rooms.append(roomtime[0])

        if rooms == []:
            return

        rooms = list(set(rooms))
        roomstrs = [self.findRoomFromIID(roomid).getName() for roomid in rooms]
        roomstrs.sort()
        roomviewer = RoomViewer(self)
        roomviewer.printPreviewAll(roomstrs)

    def ProfSchedulesPrint(self):
        """
        Function that coordinates the printing of all professor schedules.  Uses an unseen
        ProfessorViewer subwindow to render the professor schedules.
        """
        profs = []
        for scheditem in self.schedule:
            for prof in scheditem.ProfessorIID:
                profs.append(prof)

        if profs == []:
            return

        profs = list(set(profs))
        profstrs = [self.findProfessorFromIID(profid).getName() for profid in profs]
        profstrs.sort()
        profviewer = ProfessorViewer(self)
        profviewer.printPreviewAll(profstrs)

    def courseNameSectionStr(self, scheditem, courselist) -> str:
        """
        Finds the schedule item in the given course list and produces the standardized class
        designation of course name followed by the section number, e.g. MATH 201-004.

        :param scheditem: Schedule item to be named.
        :param courselist: Course list to use for searching.
        :return: String of course name followed by the section number, e.g. MATH 201-004.
        """
        for course in courselist:
            if course.InternalID == scheditem.CourseIID:
                return course.getName() + "-" + scheditem.Section

        return ""

    def ScheduleChanges(self):
        """
        This function creates and displays a schedule change report.
        """

        # Load in previous schedule to be compared with the current schedule.
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File for Comparison",
                                                   "", "Schedule Files (*.ash);;All Files (*.*)")

        if file_name:
            with open(file_name, 'rb') as f:
                try:
                    filecontents = pickle.load(f)
                    oldoptions = filecontents[0]
                    oldfaculty = filecontents[1]
                    oldrooms = filecontents[2]
                    oldcourses = filecontents[3]
                    oldstandardtimeslots = filecontents[4]
                    oldschedule = filecontents[5]
                    oldnotes = filecontents[6]
                except:
                    QMessageBox.warning(self, "File Not Loaded", "The file " + file_name + " could not be loaded.",
                                        QMessageBox.Ok)
                    return
        else:
            return

        # Create header that displays the two files being compared.
        rarrow = " &rarr; "
        htmltext = self.HTML_FrontMatter()
        htmltext += self.HTML_Heading("Schedule Change Report")

        htmltext += "<H4 class=smbottommar>Compared Files</H4>\n"
        htmltext += "<ul class=smtopmar>\n"

        htmltext += "<LI>Previous Schedule File: " + file_name + "\n"
        if self.loadedFilename:
            htmltext += "<LI>Current Schedule File: " + self.loadedFilename + "</LI>\n"
        else:
            htmltext += "<LI>Current Schedule File: None Loaded." + "</LI>\n"

        htmltext += "</ul>\n"

        # Description or workload changes.
        if oldoptions[0] != self.options[0]:
            htmltext += "<B>Description Change:</B> " + oldoptions[0] + rarrow + self.options[0] + "<BR>\n"

        if oldoptions[1] != self.options[1]:
            htmltext += "<B>Annual Workload Change:</B> " + str(oldoptions[1]) + rarrow + str(
                self.options[1]) + "<BR>\n"

        # Find additions to the schedule.

        # Find new professors added to the schedule.
        newproflist = []
        for prof in self.faculty:
            name = prof.getName()
            found = False
            for prof2 in oldfaculty:
                if prof2.getName() == name:
                    found = True

            if not found:
                newproflist.append(prof)

        newproflist.sort(key=lambda x: x.getName())

        # Find new rooms added to the schedule.
        newroomlist = []
        for room in self.rooms:
            name = room.getName()
            found = False
            for room2 in oldrooms:
                if room2.getName() == name:
                    found = True

            if not found:
                newroomlist.append(room)

        newroomlist.sort(key=lambda x: x.getName())

        # Find new courses added to the schedule.
        newcourselist = []
        for course in self.courses:
            name = course.getName()
            found = False
            for course2 in oldcourses:
                if course2.getName() == name:
                    found = True

            if not found:
                newcourselist.append(course)

        newcourselist.sort(key=lambda x: x.getName())

        # Find new standard timsslots added to the schedule.
        newtimeslotlist = []
        for slot in self.standardtimeslots:
            found = False
            for slot2 in oldstandardtimeslots:
                if slot2.equals(slot):
                    found = True

            if not found:
                newtimeslotlist.append(slot)

        newtimeslotlist.sort(key=lambda x: x.getDescription())

        # Find new scheduled classes added to the schedule.
        newclasslist = []
        for course in self.schedule:
            found = False
            for course2 in oldschedule:
                if course2.getCourseNameData() == course.getCourseNameData():
                    found = True

            if not found:
                newclasslist.append(course)

        newclasslist.sort(key=lambda x: self.courseNameSectionStr(x, self.courses))

        # Create the added items display for the report.
        if len(newproflist) > 0:
            htmltext += "<H4 class=smbottommar>Added Professors</H4>\n"
            htmltext += "<ul class=smtopmar>\n"
            for prof in newproflist:
                htmltext += "<li>" + prof.getName() + "    (" + prof.ShortDes + ")"
                if prof.ID != "":
                    htmltext += "   (ID: " + prof.ID + ")"
                if not prof.Real:
                    htmltext += "   Fake"
                htmltext += "</li>\n"
            htmltext += "</ul>\n"

        if len(newroomlist) > 0:
            htmltext += "<H4 class=smbottommar>Added Rooms</H4>\n"
            htmltext += "<ul class=smtopmar>\n"
            for room in newroomlist:
                htmltext += "<li>" + room.getName() + "    (" + str(room.Capacity) + ")"
                if room.Special != "":
                    htmltext += "   " + room.Special
                if not room.Real:
                    htmltext += "   Fake"
                htmltext += "</li>\n"
            htmltext += "</ul>\n"

        if len(newcourselist) > 0:
            htmltext += "<H4 class=smbottommar>Added Courses</H4>\n"
            htmltext += "<ul class=smtopmar>\n"
            for course in newcourselist:
                htmltext += "<li>" + course.getName() + ": " + course.Title
                htmltext += "   (" + str(course.Contact) + " / " + str(course.Workload) + ")"
                htmltext += "</li>\n"
            htmltext += "</ul>\n"

        if len(newtimeslotlist) > 0:
            htmltext += "<H4 class=smbottommar>Added Standard Timeslots</H4>\n"
            htmltext += "<ul class=smtopmar>\n"
            for slot in newtimeslotlist:
                htmltext += "<li>" + slot.getDescription() + "</li>\n"
            htmltext += "</ul>\n"

        if len(newclasslist) > 0:
            htmltext += "<H4 class=smbottommar>Added Classes</H4>\n"
            htmltext += "<ul class=smtopmar>\n"
            for course in newclasslist:
                coursestr = self.findCourseFromIID(course.CourseIID).getName() + "-" + course.Section
                if course.Tentative:
                    htmltext += """<li class="lightgray smtopmar">"""
                    htmltext += """<I class="lightgray">"""
                    coursestr += "   (Tentative)</I>"
                else:
                    htmltext += """<li class="smtopmar">"""

                htmltext += coursestr + "</li>\n"

                profliststr = ""
                for profid in course.ProfessorIID:
                    profliststr += self.findProfessorFromIID(profid).getName() + ", "

                profliststr = profliststr.lstrip().rstrip()
                if profliststr.endswith(","):
                    profliststr = profliststr[:-1]

                roomtimelist = []
                for slots in course.RoomsAndTimes:
                    room = self.findRoomFromIID(slots[0])
                    times = slots[1]
                    roomtimelist.append(times.getDescription() + " " + room.getName())

                roomtimelist.sort()
                slotstr = ""
                for i in range(len(roomtimelist)):
                    slotstr += roomtimelist[i]
                    if i < len(roomtimelist) - 1:
                        slotstr += ", "

                linkedclasslist = []
                for linkedclass in course.LinkedCourses:
                    linkedscheditem = self.findScheduleItemFromIID(linkedclass)
                    linkedcourse = self.findCourseFromIID(linkedscheditem.CourseIID)
                    linkedclasslist.append(linkedcourse.getName() + "-" + linkedscheditem.Section)

                linkedclasslist.sort()
                linkedstr = ""
                for i in range(len(linkedclasslist)):
                    linkedstr += linkedclasslist[i]
                    if i < len(linkedclasslist) - 1:
                        linkedstr += ", "

                if (profliststr != "") or (slotstr != "") or (linkedstr != "") or (course.Subtitle != "") or (
                        course.Designation != ""):
                    htmltext += """<ul class="circlist">"""
                    if profliststr != "":
                        if course.Tentative:
                            htmltext += """<li><I class="lightgray">Professors: """ + profliststr + "</I></li>\n"
                        else:
                            htmltext += "<li>Professors: " + profliststr + "</li>\n"

                    if slotstr != "":
                        if course.Tentative:
                            htmltext += """<li><I class="lightgray">Rooms and Times: """ + slotstr + "</I></li>\n"
                        else:
                            htmltext += "<li>Rooms and Times: " + slotstr + "</li>\n"

                    if linkedstr != "":
                        if course.Tentative:
                            htmltext += """<li><I class="lightgray">Linked Courses: """ + linkedstr + "</I></li>\n"
                        else:
                            htmltext += "<li>Linked Courses: " + linkedstr + "</li>\n"

                    if course.Subtitle != "":
                        if course.Tentative:
                            htmltext += """<li><I class="lightgray">Subtitle: """ + course.Subtitle + "</I></li>\n"
                        else:
                            htmltext += "<li>Subtitle: " + course.Subtitle + "</li>\n"

                    if course.Designation != "":
                        if course.Tentative:
                            htmltext += """<li><I class="lightgray">Designations: """ + course.Designation + "</I></li>\n"
                        else:
                            htmltext += "<li>Designations: " + course.Designation + "</li>\n"

                    htmltext += "</ul>"

                if course.Tentative:
                    htmltext += "</I>\n"

            htmltext += "</ul>\n"

        # Find deletions to the schedule.

        # Create list of professors removed.
        deletedproflist = []
        for prof in oldfaculty:
            name = prof.getName()
            found = False
            for prof2 in self.faculty:
                if prof2.getName() == name:
                    found = True

            if not found:
                deletedproflist.append(prof)

        deletedproflist.sort(key=lambda x: x.getName())

        # Create list of rooms removed.
        deletedroomlist = []
        for room in oldrooms:
            name = room.getName()
            found = False
            for room2 in self.rooms:
                if room2.getName() == name:
                    found = True

            if not found:
                deletedroomlist.append(room)

        deletedroomlist.sort(key=lambda x: x.getName())

        # Create list of courses removed.
        deletedcourselist = []
        for course in oldcourses:
            name = course.getName()
            found = False
            for course2 in self.courses:
                if course2.getName() == name:
                    found = True

            if not found:
                deletedcourselist.append(course)

        deletedcourselist.sort(key=lambda x: x.getName())

        # Create list of standard timeslots removed.
        deletedtimeslotlist = []
        for slot in oldstandardtimeslots:
            found = False
            for slot2 in self.standardtimeslots:
                if slot2.equals(slot):
                    found = True

            if not found:
                deletedtimeslotlist.append(slot)

        deletedtimeslotlist.sort(key=lambda x: x.getDescription())

        # Create list of scheduled classes removed.
        deletedclasslist = []
        for course in oldschedule:
            found = False
            for course2 in self.schedule:
                if course2.getCourseNameData() == course.getCourseNameData():
                    found = True

            if not found:
                deletedclasslist.append(course)

        deletedclasslist.sort(key=lambda x: self.courseNameSectionStr(x, oldcourses))

        # Create the display of the items that were removed.
        if len(deletedproflist) > 0:
            htmltext += "<H4 class=smbottommar>Deleted Professors</H4>\n"
            htmltext += "<ul class=smtopmar>\n"
            for prof in deletedproflist:
                htmltext += "<li>" + prof.getName() + "    (" + prof.ShortDes + ")"
                if prof.ID != "":
                    htmltext += "   (ID: " + prof.ID + ")"
                if not prof.Real:
                    htmltext += "   Fake"
                htmltext += "</li>\n"
            htmltext += "</ul>\n"

        if len(deletedroomlist) > 0:
            htmltext += "<H4 class=smbottommar>Deleted Rooms</H4>\n"
            htmltext += "<ul class=smtopmar>\n"
            for room in deletedroomlist:
                htmltext += "<li>" + room.getName() + "    (" + str(room.Capacity) + ")"
                if room.Special != "":
                    htmltext += "   " + room.Special
                if not room.Real:
                    htmltext += "   Fake"
                htmltext += "</li>\n"
            htmltext += "</ul>\n"

        if len(deletedcourselist) > 0:
            htmltext += "<H4 class=smbottommar>Deleted Courses</H4>\n"
            htmltext += "<ul class=smtopmar>\n"
            for course in deletedcourselist:
                htmltext += "<li>" + course.getName() + ": " + course.Title
                htmltext += "   (" + str(course.Contact) + " / " + str(course.Workload) + ")"
                htmltext += "</li>\n"
            htmltext += "</ul>\n"

        if len(deletedtimeslotlist) > 0:
            htmltext += "<H4 class=smbottommar>Deleted Standard Timeslots</H4>\n"
            htmltext += "<ul class=smtopmar>\n"
            for slot in deletedtimeslotlist:
                htmltext += "<li>" + slot.getDescription() + "</li>\n"
            htmltext += "</ul>\n"

        if len(deletedclasslist) > 0:
            htmltext += "<H4 class=smbottommar>Deleted Classes</H4>\n"
            htmltext += "<ul class=smtopmar>\n"
            for course in deletedclasslist:
                for testcourse in oldcourses:
                    if course.CourseIID == testcourse.InternalID:
                        coursestr = testcourse.getName() + "-" + course.Section

                if course.Tentative:
                    htmltext += """<li class="lightgray smtopmar">"""
                    htmltext += """<I class="lightgray">"""
                    coursestr += "   (Tentative)</I>"
                else:
                    htmltext += """<li class="smtopmar">"""

                htmltext += coursestr + "</li>\n"

                profliststr = ""
                for profid in course.ProfessorIID:
                    for delprof in oldfaculty:
                        if delprof.InternalID == profid:
                            profliststr += delprof.getName() + ", "

                profliststr = profliststr.lstrip().rstrip()
                if profliststr.endswith(","):
                    profliststr = profliststr[:-1]

                roomtimelist = []
                for slots in course.RoomsAndTimes:
                    for room in oldrooms:
                        if room.InternalID == slots[0]:
                            times = slots[1]
                            roomtimelist.append(times.getDescription() + " " + room.getName())

                roomtimelist.sort()
                slotstr = ""
                for i in range(len(roomtimelist)):
                    slotstr += roomtimelist[i]
                    if i < len(roomtimelist) - 1:
                        slotstr += ", "

                linkedclasslist = []
                for linkedclass in course.LinkedCourses:
                    for linkedscheditem in oldschedule:
                        if linkedscheditem.InternalID == linkedclass:
                            for linkedcourse in oldcourses:
                                if linkedcourse.InternalID == linkedscheditem.CourseIID:
                                    linkedclasslist.append(linkedcourse.getName() + "-" + linkedscheditem.Section)

                linkedclasslist.sort()
                linkedstr = ""
                for i in range(len(linkedclasslist)):
                    linkedstr += linkedclasslist[i]
                    if i < len(linkedclasslist) - 1:
                        linkedstr += ", "

                if (profliststr != "") or (slotstr != "") or (linkedstr != "") or (course.Subtitle != "") or (
                        course.Designation != ""):
                    htmltext += """<ul class="circlist">"""
                    if profliststr != "":
                        if course.Tentative:
                            htmltext += """<li><I class="lightgray">Professors: """ + profliststr + "</I></li>\n"
                        else:
                            htmltext += "<li>Professors: " + profliststr + "</li>\n"

                    if slotstr != "":
                        if course.Tentative:
                            htmltext += """<li><I class="lightgray">Rooms and Times: """ + slotstr + "</I></li>\n"
                        else:
                            htmltext += "<li>Rooms and Times: " + slotstr + "</li>\n"

                    if linkedstr != "":
                        if course.Tentative:
                            htmltext += """<li><I class="lightgray">Linked Courses: """ + linkedstr + "</I></li>\n"
                        else:
                            htmltext += "<li>Linked Courses: " + linkedstr + "</li>\n"

                    if course.Subtitle != "":
                        if course.Tentative:
                            htmltext += """<li><I class="lightgray">Subtitle: """ + course.Subtitle + "</I></li>\n"
                        else:
                            htmltext += "<li>Subtitle: " + course.Subtitle + "</li>\n"

                    if course.Designation != "":
                        if course.Tentative:
                            htmltext += """<li><I class="lightgray">Designations: """ + course.Designation + "</I></li>\n"
                        else:
                            htmltext += "<li>Designations: " + course.Designation + "</li>\n"

                    htmltext += "</ul>"

                if course.Tentative:
                    htmltext += "</I>\n"

            htmltext += "</ul>\n"

        # Find changes to the schedule.

        # Find changes for the professors.  If the professor names are identical but
        # the ID, real type, or short designation have changed then this will be considered
        # a professor change.
        changeproflist = []
        for prof in self.faculty:
            name = prof.getName()
            change = False
            for prof2 in oldfaculty:
                if prof2.getName() == name:
                    shortdeschange = []
                    IDchange = []
                    Realchange = []
                    if prof.ShortDes != prof2.ShortDes:
                        shortdeschange = [prof2.ShortDes, prof.ShortDes]
                        change = True
                    if prof.ID != prof2.ID:
                        IDchange = [prof2.ID, prof.ID]
                        change = True
                    if prof.Real != prof2.Real:
                        Realchange = [prof2.Real, prof.Real]
                        change = True

                    if change:
                        changeproflist.append([prof, shortdeschange, IDchange, Realchange])

        changeproflist.sort(key=lambda x: x[0].getName())

        # Find changes for the rooms.  If the room names are identical but the capacity, real type,
        # or designation have changed then this will be considered a room change.
        changeroomlist = []
        for room in self.rooms:
            name = room.getName()
            change = False
            for room2 in oldrooms:
                if room2.getName() == name:
                    capchange = []
                    deschange = []
                    Realchange = []
                    if room.Capacity != room2.Capacity:
                        capchange = [room2.Capacity, room.Capacity]
                        change = True
                    if room.Special != room2.Special:
                        deschange = [room2.Special, room.Special]
                        change = True
                    if room.Real != room2.Real:
                        Realchange = [room2.Real, room.Real]
                        change = True

                    if change:
                        changeroomlist.append([room, capchange, deschange, Realchange])

        changeroomlist.sort(key=lambda x: x[0].getName())

        # Find changes for the courses.  If the course names are identical but the title, contact minutes,
        # or workload have changed then this will be considered a course change.
        changedcourselist = []
        for course in self.courses:
            name = course.getName()
            change = False
            for course2 in oldcourses:
                if course2.getName() == name:
                    titlechange = []
                    contactchange = []
                    workchange = []
                    if course.Title != course2.Title:
                        titlechange = [course2.Title, course.Title]
                        change = True
                    if course.Contact != course2.Contact:
                        contactchange = [course2.Contact, course.Contact]
                        change = True
                    if course.Workload != course2.Workload:
                        workchange = [course2.Workload, course.Workload]
                        change = True

                    if change:
                        changedcourselist.append([course, titlechange, contactchange, workchange])

        changedcourselist.sort(key=lambda x: x[0].getName())

        # Find changes for the scheduled classes.  If the class names are identical (course and section)
        # but any of the other fields are different from this will be considered a class change.
        changedclasslist = []
        for course in self.schedule:
            change = False
            for course2 in oldschedule:
                if course2.getCourseNameData() == course.getCourseNameData():
                    profchange = []
                    rtchange = []
                    subtitlechange = []
                    designationchange = []
                    linkedchange = []
                    tentchange = []
                    if set(course.ProfessorIID) != set(course2.ProfessorIID):
                        profchange = [course2.ProfessorIID, course.ProfessorIID]
                        change = True

                    rtequals = True
                    if len(course.RoomsAndTimes) != len(course2.RoomsAndTimes):
                        rtequals = False

                    for slot in course.RoomsAndTimes:
                        slotfound = False
                        for slot2 in course2.RoomsAndTimes:
                            if (slot[0] == slot2[0]) and slot[1].equals(slot2[1]):
                                slotfound = True
                        if not slotfound:
                            rtequals = False

                    if not rtequals:
                        rtchange = [course2.RoomsAndTimes, course.RoomsAndTimes]
                        change = True

                    if course.Subtitle != course2.Subtitle:
                        subtitlechange = [course2.Subtitle, course.Subtitle]
                        change = True

                    if course.Designation != course2.Designation:
                        designationchange = [course2.Designation, course.Designation]
                        change = True

                    if course.Tentative != course2.Tentative:
                        tentchange = [course2.Tentative, course.Tentative]
                        change = True

                    if set(course.LinkedCourses) != set(course2.LinkedCourses):
                        linkedchange = [course2.LinkedCourses, course.LinkedCourses]
                        change = True

                    if change:
                        changedclasslist.append(
                            [course, profchange, rtchange, subtitlechange, designationchange, linkedchange, tentchange])

        changedclasslist.sort(key=lambda x: self.courseNameSectionStr(x[0], self.courses))

        # Create the display for the changes that were found.
        if len(changeproflist) > 0:
            htmltext += "<H4 class=smbottommar>Professor Changes</H4>\n"
            htmltext += "<ul class=smtopmar>\n"
            for profchinfo in changeproflist:
                htmltext += "<li class=smtopmar>" + profchinfo[0].getName() + "</li>\n"
                htmltext += """<ul class="circlist"">\n"""
                if profchinfo[1] != []:
                    htmltext += "<LI>Short Description: " + profchinfo[1][0] + rarrow + profchinfo[1][1] + "</LI>\n"
                if profchinfo[2] != []:
                    htmltext += "<LI>ID: "
                    if profchinfo[2][0] != "":
                        htmltext += profchinfo[2][0]
                    else:
                        htmltext += "None"
                    htmltext += rarrow
                    if profchinfo[2][1] != "":
                        htmltext += profchinfo[2][1]
                    else:
                        htmltext += "None"
                    htmltext += "</LI>\n"
                if profchinfo[3] != []:
                    htmltext += "<LI>Real: "
                    if profchinfo[3][0]:
                        htmltext += "Real"
                    else:
                        htmltext += "Fake"
                    htmltext += rarrow
                    if profchinfo[3][1]:
                        htmltext += "Real"
                    else:
                        htmltext += "Fake"
                    htmltext += "</LI>\n"
                htmltext += "</ul>\n"
            htmltext += "</ul>\n"

        if len(changeroomlist) > 0:
            htmltext += "<H4 class=smbottommar>Room Changes</H4>\n"
            htmltext += "<ul class=smtopmar>\n"
            for roomchangeinfo in changeroomlist:
                htmltext += "<li class=smtopmar>" + roomchangeinfo[0].getName() + "</LI>\n"
                htmltext += """<ul class="circlist">\n"""
                if roomchangeinfo[1] != []:
                    htmltext += "<LI>Capacity: " + str(roomchangeinfo[1][0]) + rarrow + str(
                        roomchangeinfo[1][1]) + "</LI>\n"
                if roomchangeinfo[2] != []:
                    htmltext += "<LI>Designations: "
                    if roomchangeinfo[2][0] != "":
                        htmltext += roomchangeinfo[2][0]
                    else:
                        htmltext += "None"
                    htmltext += rarrow
                    if roomchangeinfo[2][1] != "":
                        htmltext += roomchangeinfo[2][1]
                    else:
                        htmltext += "None"
                    htmltext += "</LI>\n"
                if roomchangeinfo[3] != []:
                    htmltext += "<LI>Real: "
                    if roomchangeinfo[3][0]:
                        htmltext += "Real"
                    else:
                        htmltext += "Fake"
                    htmltext += rarrow
                    if roomchangeinfo[3][1]:
                        htmltext += "Real"
                    else:
                        htmltext += "Fake"
                    htmltext += "</LI>\n"
                htmltext += "</ul>\n"
            htmltext += "</ul>\n"

        if len(changedcourselist) > 0:
            htmltext += "<H4 class=smbottommar>Course Changes</H4>\n"
            htmltext += "<ul class=smtopmar>\n"
            for courseinfo in changedcourselist:
                htmltext += "<li class=smtopmar>" + courseinfo[0].getName() + "</LI>\n"
                htmltext += """<ul class=circlist>\n"""
                if courseinfo[1] != []:
                    htmltext += "<LI>Title: " + courseinfo[1][0] + rarrow + courseinfo[1][1] + "</LI>\n"
                if courseinfo[2] != []:
                    htmltext += "<LI>Contact: " + str(courseinfo[2][0]) + rarrow + str(courseinfo[2][1]) + "</LI>\n"
                if courseinfo[3] != []:
                    htmltext += "<LI>Workload: " + str(courseinfo[3][0]) + rarrow + str(courseinfo[3][1]) + "</LI>\n"
                htmltext += "</ul>\n"
            htmltext += "</ul>\n"

        if len(changedclasslist) > 0:
            htmltext += "<H4 class=smbottommar>Class Changes</H4>\n"
            htmltext += "<ul class=smtopmar>\n"
            for courseinfo in changedclasslist:
                coursestr = self.findCourseFromIID(courseinfo[0].CourseIID).getName() + "-" + courseinfo[0].Section
                if courseinfo[0].Tentative:
                    htmltext += """<li class="lightgray smtopmar">"""
                    htmltext += """<I class="lightgray">"""
                    coursestr += "   (Tentative)</I>"
                else:
                    htmltext += """<li class="smtopmar">"""

                htmltext += coursestr + "</li>\n"
                htmltext += """<ul class="circlist">\n"""

                if courseinfo[1] != []:
                    oldprofliststr = ""
                    for profid in courseinfo[1][0]:
                        for prof in oldfaculty:
                            if prof.InternalID == profid:
                                oldprofliststr += prof.getName() + ", "

                    oldprofliststr = oldprofliststr.lstrip().rstrip()
                    if oldprofliststr.endswith(","):
                        oldprofliststr = oldprofliststr[:-1]

                    newprofliststr = ""
                    for profid in courseinfo[1][1]:
                        newprofliststr += self.findProfessorFromIID(profid).getName() + ", "

                    newprofliststr = newprofliststr.lstrip().rstrip()
                    if newprofliststr.endswith(","):
                        newprofliststr = newprofliststr[:-1]

                    if courseinfo[0].Tentative:
                        htmltext += """<li><I class="lightgray">Professors: """ + oldprofliststr + rarrow + newprofliststr + "</I></li>\n"
                    else:
                        htmltext += "<li>Professors: " + oldprofliststr + rarrow + newprofliststr + "<li>\n"

                if courseinfo[2] != []:
                    oldroomtimelist = []
                    for slots in courseinfo[2][0]:
                        roomname = ""
                        for room in oldrooms:
                            if room.InternalID == slots[0]:
                                roomname = room.getName()
                        times = slots[1]
                        oldroomtimelist.append(times.getDescription() + " " + roomname)

                    oldroomtimelist.sort()
                    oldslotstr = ""
                    for i in range(len(oldroomtimelist)):
                        oldslotstr += oldroomtimelist[i]
                        if i < len(oldroomtimelist) - 1:
                            oldslotstr += ", "

                    if oldslotstr == "":
                        oldslotstr = "None"

                    roomtimelist = []
                    for slots in courseinfo[2][1]:
                        room = self.findRoomFromIID(slots[0])
                        times = slots[1]
                        roomtimelist.append(times.getDescription() + " " + room.getName())

                    roomtimelist.sort()
                    slotstr = ""
                    for i in range(len(roomtimelist)):
                        slotstr += roomtimelist[i]
                        if i < len(roomtimelist) - 1:
                            slotstr += ", "

                    if slotstr == "":
                        slotstr = "None"

                    if courseinfo[0].Tentative:
                        htmltext += """<li><I class="lightgray">Rooms and Times: """ + oldslotstr + "<BR>" + rarrow + slotstr + "</I></li>\n"
                    else:
                        htmltext += "<li>Rooms and Times: " + oldslotstr + "<BR>" + rarrow + slotstr + "</li>\n"

                if courseinfo[3] != []:
                    oldtitle = courseinfo[3][0]
                    if oldtitle == "":
                        oldtitle = "None"
                    newtitle = courseinfo[3][1]
                    if newtitle == "":
                        newtitle = "None"

                    if courseinfo[0].Tentative:
                        htmltext += """<li><I class="lightgray">Subtitle: """ + oldtitle + rarrow + newtitle + "</I></li>\n"
                    else:
                        htmltext += "<li>Subtitle: " + oldtitle + rarrow + newtitle + "</li>\n"

                if courseinfo[4] != []:
                    oldtitle = courseinfo[4][0]
                    if oldtitle == "":
                        oldtitle = "None"
                    newtitle = courseinfo[4][1]
                    if newtitle == "":
                        newtitle = "None"

                    if courseinfo[0].Tentative:
                        htmltext += """<li><I class="lightgray">Designations: """ + oldtitle + rarrow + newtitle + "</I></li>\n"
                    else:
                        htmltext += "<li>Designations: " + oldtitle + rarrow + newtitle + "</li>\n"

                if courseinfo[5] != []:
                    oldlinkedclasslist = []
                    for linkedclass in courseinfo[5][0]:
                        for item in oldschedule:
                            if linkedclass == item.InternalID:
                                sectionnum = item.Section
                                coursename = ""
                                for cl in oldcourses:
                                    if cl.InternalID == item.CourseIID:
                                        coursename = cl.getName()
                                oldlinkedclasslist.append(coursename + "-" + sectionnum)

                    oldlinkedclasslist.sort()
                    oldlinkedstr = ""
                    for i in range(len(oldlinkedclasslist)):
                        oldlinkedstr += oldlinkedclasslist[i]
                        if i < len(oldlinkedclasslist) - 1:
                            oldlinkedstr += ", "

                    if oldlinkedstr == "":
                        oldlinkedstr = "None"

                    linkedclasslist = []
                    for linkedclass in courseinfo[5][1]:
                        linkedscheditem = self.findScheduleItemFromIID(linkedclass)
                        linkedcourse = self.findCourseFromIID(linkedscheditem.CourseIID)
                        linkedclasslist.append(linkedcourse.getName() + "-" + linkedscheditem.Section)

                    linkedclasslist.sort()
                    linkedstr = ""
                    for i in range(len(linkedclasslist)):
                        linkedstr += linkedclasslist[i]
                        if i < len(linkedclasslist) - 1:
                            linkedstr += ", "

                    if linkedstr == "":
                        linkedstr = "None"

                    if courseinfo[0].Tentative:
                        htmltext += """<li><I class="lightgray">Linked Courses: """ + oldlinkedstr + rarrow + linkedstr + "</I></li>\n"
                    else:
                        htmltext += "<li>Linked Courses: " + oldlinkedstr + rarrow + linkedstr + "</li>\n"

                if courseinfo[6] != []:
                    if courseinfo[0].Tentative:
                        htmltext += """<li><I class="lightgray">Tentative: """
                    else:
                        htmltext += "<LI>Tentative: "

                    if courseinfo[6][0]:
                        htmltext += "Tentative"
                    else:
                        htmltext += "Not Tentative"
                    htmltext += rarrow
                    if courseinfo[6][1]:
                        htmltext += "Tentative"
                    else:
                        htmltext += "Not Tentative"

                    if courseinfo[0].Tentative:
                        htmltext += "</I></li>\n"
                    else:
                        htmltext += "</li>\n"
                htmltext += "</ul>"

                if courseinfo[0].Tentative:
                    htmltext += "</I>\n"

            htmltext += "</ul>\n"

        htmltext += "<BR><BR>\n"

        htmltext += self.HTML_BackMatter()
        reportview = HTMLViewer(self, "Schedule Changes", htmltext)
        reportview.exec()

    #########################################################################
    ### Database updating functions.
    #########################################################################

    def EditCourse(self, coursename: str):
        """
        Function that invokes the editing dialog for the given course.

        :param coursename: Course name to be edited.
        """
        index = -1
        for i in range(len(self.courses)):
            if self.courses[i].getName() == coursename:
                index = i

        if index >= 0:
            data = self.courses[index].getFieldList()
            id = self.courses[index].InternalID
            data[3] = str(data[3])
            data[4] = str(data[4])
            dlg = CourseDialog(self, "Edit Course", data, id)

            if dlg.exec():
                data = dlg.table_widget.getTableContents()
                item = data[0]

                item[0] = self.removeColon(self.removeWhitespace(item[0]).upper())
                item[1] = self.removeColon(self.removeWhitespace(item[1]))

                if item[0] != "":
                    newcourse = Course()
                    newcourse.Code = item[0]
                    newcourse.Number = item[1]
                    newcourse.Title = item[2]
                    newcourse.InternalID = id

                    try:
                        val = float(item[3])
                        newcourse.Contact = val
                    except Exception as e:
                        newcourse.Contact = 0

                    try:
                        val = float(item[4])
                        newcourse.Workload = val
                    except Exception as e:
                        newcourse.Workload = 0

                    self.courses[index] = newcourse
                    self.courses.sort(key=lambda x: x.getName())
                    self.ChangeMade()
                    self.UpdateAllLists()

    def AddNewCourse(self):
        """
        Invokes the Course input dialog to add in new courses to the course database.
        """
        dlg = CourseDialog(self)

        if dlg.exec():
            data = dlg.table_widget.getTableContents()

            for item in data:
                if item[0] != "":
                    item[0] = self.removeColon(self.removeWhitespace(item[0]).upper())
                    item[1] = self.removeColon(self.removeWhitespace(item[1]))

                    newcourse = Course()
                    newcourse.Code = item[0]
                    newcourse.Number = item[1]
                    newcourse.Title = item[2]

                    try:
                        val = float(item[3])
                        newcourse.Contact = val
                    except Exception as e:
                        newcourse.Contact = 0

                    try:
                        val = float(item[4])
                        newcourse.Workload = val
                    except Exception as e:
                        newcourse.Workload = 0

                    courseinternalids = []
                    for course in self.courses:
                        courseinternalids.append(course.InternalID)

                    IntID = 1
                    while IntID in courseinternalids:
                        IntID += 1

                    newcourse.InternalID = IntID
                    self.courses.append(newcourse)

            self.courses.sort(key=lambda x: x.getName())
            self.ChangeMade()
            self.UpdateAllLists()

    def AddNewFaculty(self):
        """
        Invokes the Professor input dialog to add in new instructors to the professor database.
        """
        dlg = FacultyDialog(self)

        if dlg.exec():
            data = dlg.table_widget.getTableContents()

            facultyinternalids = []
            for facmem in self.faculty:
                facultyinternalids.append(facmem.InternalID)

            for item in data:
                if item[0] != "":
                    newprof = Professor()
                    newprof.LastName = item[0]
                    newprof.FirstName = item[1]
                    newprof.MiddleName = item[2]
                    newprof.Suffix = item[3]
                    newprof.ShortDes = item[4]
                    newprof.ID = item[5]
                    if item[6].upper() == "N":
                        newprof.Real = False

                    IntID = 1
                    while IntID in facultyinternalids:
                        IntID += 1

                    newprof.InternalID = IntID
                    facultyinternalids.append(IntID)
                    self.faculty.append(newprof)

            self.faculty.sort(key=lambda x: x.getName())
            self.ChangeMade()
            self.UpdateAllLists()

    def EditFaculty(self, facultyname: str):
        """
        Function that invokes the editing dialog for the given professor.

        :param facultyname: Professor name to be edited.
        """
        index = -1
        for i in range(len(self.faculty)):
            if self.faculty[i].getName() == facultyname:
                index = i

        if index >= 0:
            data = self.faculty[index].getFieldList()
            id = self.faculty[index].InternalID
            if data[6]:
                data[6] = ""
            else:
                data[6] = "N"

            dlg = FacultyDialog(self, "Edit Professor", data, id)
            if dlg.exec():
                data = dlg.table_widget.getTableContents()
                item = data[0]
                for i in range(7):
                    item[i] = item[i].lstrip().rstrip()

                if item[0] != "":
                    newprof = Professor()
                    newprof.LastName = item[0]
                    newprof.FirstName = item[1]
                    newprof.MiddleName = item[2]
                    newprof.Suffix = item[3]
                    newprof.ShortDes = item[4]
                    newprof.ID = item[5]
                    if item[6].upper() == "N":
                        newprof.Real = False
                    newprof.InternalID = id

                    self.faculty[index] = newprof
                    self.faculty.sort(key=lambda x: x.getName())
                    self.ChangeMade()
                    self.UpdateAllLists()

    def AddNewTimeslots(self):
        """
        Invokes the Timeslot input dialog to add in new standard timeslots to the timeslot database.
        """
        dlg = TimeslotDialog(self)

        if dlg.exec():
            data = dlg.table_widget.getTableContents()

            for item in data:
                for i in range(5):
                    item[i] = item[i].lstrip().rstrip()

                if item[0] != "":
                    newslot = TimeSlot()
                    newslot.setData(item[0].upper(), int(item[1]), int(item[2]), int(item[3]), int(item[4]))
                    self.standardtimeslots.append(newslot)

            self.standardtimeslots.sort(key=lambda x: x.getDescription24Hr())
            self.ChangeMade()
            self.UpdateAllLists()

    def EditTimeslot(self, slot: TimeSlot):
        """
        Function that invokes the editing dialog for the given timeslot.

        :param slot: Timeslot to be edited.
        """
        index = -1
        for i in range(len(self.standardtimeslots)):
            if self.standardtimeslots[i].getDescription() == slot:
                index = i

        if index >= 0:
            data = self.standardtimeslots[index].getFieldList()
            for i in range(1, 5):
                data[i] = str(data[i])

            dlg = TimeslotDialog(self, "Edit Timeslot", data)

            if dlg.exec():
                data = dlg.table_widget.getTableContents()
                item = data[0]

                for i in range(5):
                    item[i] = item[i].lstrip().rstrip()

                if item[0] != "":
                    newslot = TimeSlot()
                    newslot.setData(item[0].upper(), int(item[1]), int(item[2]), int(item[3]), int(item[4]))
                    self.standardtimeslots[index] = newslot
                    self.standardtimeslots.sort(key=lambda x: x.getDescription24Hr())
                    self.ChangeMade()
                    self.UpdateAllLists()

    def AddNewRooms(self):
        """
        Invokes the Room input dialog to add in new rooms to the room database.
        """
        dlg = RoomsDialog(self)

        if dlg.exec():
            data = dlg.table_widget.getTableContents()

            roominternalids = []
            for room in self.rooms:
                roominternalids.append(room.InternalID)

            for item in data:
                for i in range(5):
                    item[i] = item[i].lstrip().rstrip()

                item[0] = self.removeColon(self.removeWhitespace(item[0]).upper())
                item[1] = self.removeColon(self.removeWhitespace(item[1]))

                if item[0] != "":
                    newroom = Room()
                    newroom.Building = item[0]
                    newroom.RoomNumber = item[1]
                    newroom.Capacity = int(item[2])
                    if newroom.Capacity < 0:
                        newroom.Capacity = 0
                    newroom.Special = item[3]
                    if item[4].upper() == "N":
                        newroom.Real = False

                    IntID = 1
                    while IntID in roominternalids:
                        IntID += 1

                    newroom.InternalID = IntID
                    roominternalids.append(IntID)
                    self.rooms.append(newroom)

            self.rooms.sort(key=lambda x: x.getName())
            self.ChangeMade()
            self.UpdateAllLists()

    def EditRoom(self, room: Room):
        """
        Function that invokes the editing dialog for the given room.

        :param room: Room to be edited.
        """
        index = -1
        for i in range(len(self.rooms)):
            if self.rooms[i].getName() == room:
                index = i

        if index >= 0:
            data = self.rooms[index].getFieldList()
            id = self.rooms[index].InternalID
            data[2] = str(data[2])
            if data[4]:
                data[4] = ""
            else:
                data[4] = "N"

            dlg = RoomsDialog(self, "Edit Room", data, id)

            if dlg.exec():
                data = dlg.table_widget.getTableContents()
                item = data[0]

                for i in range(5):
                    item[i] = item[i].lstrip().rstrip()

                if item[0] != "":
                    newroom = Room()
                    item[0] = self.removeColon(self.removeWhitespace(item[0]).upper())
                    item[1] = self.removeColon(self.removeWhitespace(item[1]))

                    newroom.Building = item[0]
                    newroom.RoomNumber = item[1]
                    newroom.Capacity = int(item[2])
                    if newroom.Capacity < 0:
                        newroom.Capacity = 0
                    newroom.Special = item[3]
                    if item[4].upper() == "N":
                        newroom.Real = False
                    newroom.InternalID = id

                    self.rooms[index] = newroom
                    self.rooms.sort(key=lambda x: x.getName())
                    self.ChangeMade()
                    self.UpdateAllLists()

    def inputDescription(self):
        """
        Invokes a simple input dialog to change the schedule description.
        """
        text, ok = QInputDialog.getText(self, 'Schedule Description', 'Description:',
                                        QLineEdit.Normal, self.options[0])
        if ok:
            self.options[0] = text
            self.ChangeMade()
            self.updateProgramWindowTitle()

    def inputYearlyCourseHourLoad(self):
        """
        Invokes a simple input dialog to change the annual hour course load for the faculty.
        """
        value, ok = QInputDialog.getInt(self, 'Annual Hour Course Load', 'Hours:',
                                        self.options[1], 1, 100)
        if ok:
            self.options[1] = value
            self.ChangeMade()
            self.UpdateOnScheduleChange()

    def DeleteCourses(self):
        """
        Function that will delete the course database and any associated classes, schedule items.
        A schedule item must be associated with a course, hence if the courses are removed then
        the schedule must be removed.
        """
        if self.courses != []:
            messagestr = "This will remove all courses from the course database.  "
            messagestr += "Since each scheduled class must be associated with a course, "
            messagestr += "the schedule database will be removed as well. "
            messagestr += "\n\n"
            messagestr += "Do you wish to delete the courses database?"
            result = QMessageBox.warning(self, "Delete Courses", messagestr, QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if result == QMessageBox.Yes:
                self.schedule = []
                self.courses = []
                self.UpdateAllLists()
                self.loadedFilename = ""
                self.ChangeMade()
                self.updateProgramWindowTitle()

    def DeleteCourse(self, coursename: str):
        """
        Function that deletes the course corresponding to the input coursename.

        :param coursename: Course to be deleted.
        """
        index = -1
        for i in range(len(self.courses)):
            if self.courses[i].getName() == coursename:
                index = i

        if index >= 0:
            messagestr = "This will remove the course "
            messagestr += coursename + ": " + self.courses[index].Title + " "
            messagestr += "from the course database and from the current schedule.\n\n"
            messagestr += "Do you wish to delete this course?"
            result = QMessageBox.warning(self, "Delete a Course", messagestr,
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if result == QMessageBox.Yes:
                newschedulelist = []
                for course in self.schedule:
                    if self.findCourseFromIID(course.CourseIID).getName() == coursename:
                        for linkedcourse in self.schedule:
                            if course.InternalID in linkedcourse.LinkedCourses:
                                linkedcourse.LinkedCourses.remove(course.InternalID)

                for course in self.schedule:
                    if self.findCourseFromIID(course.CourseIID).getName() != coursename:
                        newschedulelist.append(course)

                self.schedule = newschedulelist

                index = -1
                for i in range(len(self.courses)):
                    if self.courses[i].getName() == coursename:
                        index = i

                if index > -1:
                    del self.courses[index]
                self.ChangeMade()
                self.UpdateAllLists()

    def DeleteFaculty(self):
        """
        Function that will delete the professor database and any associated classes, schedule items.
        A schedule item must be associated with at least one instructor, hence if the faculty
        are removed then the schedule must be removed.
        """
        if self.faculty != []:
            messagestr = "This will remove all professors from the faculty database.  "
            messagestr += "Since each scheduled class must be associated with a faculty member, "
            messagestr += "the schedule database will be removed as well. "
            messagestr += "\n\n"
            messagestr += "Do you wish to delete the faculty database?"
            result = QMessageBox.warning(self, "Delete Faculty", messagestr, QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if result == QMessageBox.Yes:
                self.schedule = []
                self.faculty = []
                self.UpdateAllLists()
                self.loadedFilename = ""
                self.ChangeMade()
                self.updateProgramWindowTitle()

    def DeleteFacultyMember(self, facultyname: str):
        """
        Function that deletes the instructor corresponding to the input facultyname.

        :param facultyname: Instructor to be deleted.
        """
        index = -1
        for i in range(len(self.faculty)):
            if self.faculty[i].getName() == facultyname:
                index = i

        if index >= 0:
            messagestr = "This will remove the faculty member " + facultyname + " "
            messagestr += "from the professor database as well as all the courses "
            messagestr += "from the current schedule this faculty member is teaching.\n\n"
            messagestr += "Do you wish to delete this faculty member?"
            result = QMessageBox.warning(self, "Delete a Faculty Member", messagestr,
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if result == QMessageBox.Yes:
                prof = self.findProfessorFromString(facultyname)
                profid = prof.InternalID

                for course in self.schedule:
                    if profid in course.ProfessorIID:
                        course.ProfessorIID.remove(profid)

                for course in self.schedule:
                    if course.ProfessorIID == []:
                        for linkedcourse in self.schedule:
                            if course.InternalID in linkedcourse.LinkedCourses:
                                linkedcourse.LinkedCourses.remove(course.InternalID)

                newschedulelist = []
                for course in self.schedule:
                    if course.ProfessorIID != []:
                        newschedulelist.append(course)

                self.schedule = newschedulelist
                del self.faculty[index]
                self.ChangeMade()
                self.UpdateAllLists()

    def DeleteTimeslots(self):
        """
        Function that deletes the standard timeslots database.  Since the timeslots
        are not linked to schedule items and are just for drop convenience in scheduling no
        other data is deleted.
        """
        if self.standardtimeslots != []:
            messagestr = "This will remove all the standard timeslots.  "
            messagestr += "The standard timeslots are not linked to any scheduled classes, "
            messagestr += "so none of the scheduled courses will be removed. "
            messagestr += "\n\n"
            messagestr += "Do you wish to delete the standard timeslots database?"
            result = QMessageBox.warning(self, "Delete Standard Timeslots", messagestr,
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if result == QMessageBox.Yes:
                self.standardtimeslots = []
                self.UpdateAllLists()
                self.loadedFilename = ""
                self.ChangeMade()
                self.updateProgramWindowTitle()

    def DeleteTimeslot(self, slot: TimeSlot):
        """
        Function that deletes the timeslot corresponding to the input slot.

        :param slot: Timeslot to be deleted.
        """
        index = -1
        for i in range(len(self.standardtimeslots)):
            if self.standardtimeslots[i].getDescription() == slot:
                index = i

        if index >= 0:
            messagestr = "This will remove the standard timeslot\n"
            messagestr += self.standardtimeslots[index].getDescription()
            messagestr += "\n\n"
            messagestr += "Do you wish to delete this timeslot?"
            result = QMessageBox.warning(self, "Delete a Standard Timeslot", messagestr,
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if result == QMessageBox.Yes:
                del self.standardtimeslots[index]
                self.ChangeMade()
                self.UpdateAllLists()

    def DeleteRooms(self):
        """
        Function that deletes the rooms database.  Since each timeslot has a room associated
        with it, each schedule item that has scheduled rooms and times will lose the room and time
        data.  The courses and professors associated with the schedule item will remain.
        """
        if self.rooms != []:
            messagestr = "This will remove all the rooms from the room database.  "
            messagestr += "Since each timeslot for all scheduled classes must be associated with a room, "
            messagestr += "the rooms and times for all scheduled classes will be removed as well. "
            messagestr += "\n\n"
            messagestr += "Do you wish to delete the room database?"
            result = QMessageBox.warning(self, "Delete Rooms", messagestr, QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if result == QMessageBox.Yes:
                self.rooms = []
                for scheditem in self.schedule:
                    scheditem.RoomsAndTimes = []
                self.UpdateAllLists()
                self.loadedFilename = ""
                self.ChangeMade()
                self.updateProgramWindowTitle()

    def DeleteRoom(self, room: str):
        """
        Function that deletes the room corresponding to the input room.  Since timeslots
        need a room, any timeslot that is associated with the deleted room will be removed
        from the schedule.

        :param room: Room to be deleted.
        """
        index = -1
        for i in range(len(self.rooms)):
            if self.rooms[i].getName() == room:
                index = i

        if index >= 0:
            messagestr = "This will remove the room " + room + " "
            messagestr += "from the room database as well as remove all the scheduled times "
            messagestr += "that are using this room.\n\n"
            messagestr += "Do you wish to delete this room?"
            result = QMessageBox.warning(self, "Delete a Room", messagestr,
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if result == QMessageBox.Yes:
                roomid = self.rooms[index].InternalID

                for course in self.schedule:
                    for roomtime in course.RoomsAndTimes:
                        if roomtime[0] == roomid:
                            course.RoomsAndTimes.remove(roomtime)

                del self.rooms[index]
                self.ChangeMade()
                self.UpdateAllLists()

    def DeleteSchedule(self):
        """
        Function that deletes the schedule database.
        """
        if self.schedule != []:
            messagestr = "This will remove all scheduled courses from the schedule database.\n\n"
            messagestr += "Do you wish to delete the schedule database?"
            result = QMessageBox.warning(self, "Delete Schedule", messagestr, QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if result == QMessageBox.Yes:
                self.schedule = []
                self.UpdateAllLists()
                self.loadedFilename = ""
                self.ChangeMade()
                self.updateProgramWindowTitle()

    def RemoveAlRoomsAndTimes(self):
        """
        Function that removes the days and times from all schedule items but retains the
        professor course assignments.
        """
        somescheduled = False
        for item in self.schedule:
            if item.RoomsAndTimes != []:
                somescheduled = True

        if somescheduled:
            messagestr = "This will remove all rooms and times from the scheduled courses database.  "
            messagestr += "The faculty course assignments will not be removed.\n\n"
            messagestr += "Do you wish to delete the rooms and times from the scheduled courses database?"
            result = QMessageBox.warning(self, "Delete Rooms and Times", messagestr, QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if result == QMessageBox.Yes:
                for item in self.schedule:
                    item.RoomsAndTimes = []
                self.UpdateAllLists()
                self.loadedFilename = ""
                self.ChangeMade()
                self.updateProgramWindowTitle()

    def DeleteAllDatabases(self):
        """
        Function to delete all databases and reset the options.
        """
        messagestr = "This will remove all databases from memory.\n\n"
        messagestr += "Do you wish to delete all databases?"
        result = QMessageBox.warning(self, "Delete All Databases", messagestr, QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if result == QMessageBox.Yes:
            self.options = ["", 24]
            self.faculty = []
            self.rooms = []
            self.courses = []
            self.standardtimeslots = []
            self.schedule = []
            self.noteeditor.editor.setText("")
            self.UpdateAllLists()
            self.loadedFilename = ""
            self.ChangeMade()
            self.updateProgramWindowTitle()

    def EditSectionNumbers(self):
        """
        Invokes the section numbering editing dialog. For editing the section numbers, designations,
        and subtitles in mass.
        """
        if len(self.schedule) == 0:
            return

        sectiondata = []
        for scheditem in self.schedule:
            coursenamesection = self.courseNameAndSection(scheditem)
            sectionnumber = scheditem.Section
            subtitle = scheditem.Subtitle
            desig = scheditem.Designation
            sectiondata.append([coursenamesection, sectionnumber, subtitle, desig])

        sectiondata.sort()
        dlg = SectionNumberDialog(self, "Edit Section Numbers, Subtitles, and Designations", sectiondata)

        if dlg.exec():
            data = dlg.table_widget.getTableContents()
            courses = [self.findScheduleItemFromString(item[0]) for item in sectiondata]

            for i in range(len(courses)):
                courses[i].Section = data[i][0]
                if data[i][1]:
                    courses[i].Subtitle = data[i][1].lstrip().rstrip()
                else:
                    courses[i].Subtitle = ""

                if data[i][2]:
                    courses[i].Designation = data[i][2].lstrip().rstrip()
                else:
                    courses[i].Designation = ""
            self.ChangeMade()
            self.UpdateAllLists()

    #########################################################################
    ### Course linker updaters.
    #########################################################################

    def LinkCourses(self, maincoursestr: str, subs: []):
        """
        Sets the linking of a main course and a list of subsequent courses.

        :param maincoursestr: The main course (string name) to be linked.
        :param subs: A list of subsequent courses (string names) to link to the main course.
        """
        mainscheditem = self.findScheduleItemFromString(maincoursestr)
        subsscheditem = [self.findScheduleItemFromString(item).InternalID for item in subs]
        sublist = []
        for iid in subsscheditem:
            if iid != mainscheditem.InternalID:
                sublist.append(iid)
        mainscheditem.LinkedCourses = sublist
        self.ChangeMade()

    def UninkCourses(self, maincoursestr: str):
        """
        Unlinks the main course, i.e. sets its list of linked courses to the empty list.

        :param maincoursestr: Course to unlink.
        """
        mainscheditem = self.findScheduleItemFromString(maincoursestr)
        mainscheditem.LinkedCourses = []
        self.ChangeMade()

    #########################################################################
    ### Child window updaters.
    #########################################################################

    def UpdateAllLists(self):
        """
        Updates the views of all subwindows on the desktop.
        """
        self.coureList.UpdateCourseList()
        self.facultyList.UpdateFacultyList()
        self.timeslotlist.UpdateStandardTimeslotsList()
        self.courselinker.UpdateLinkerLists()
        for subwin in self.desktop.subWindowList():
            if isinstance(subwin, RoomViewer):
                subwin.updateData()

        for subwin in self.desktop.subWindowList():
            if isinstance(subwin, ProfessorViewer):
                subwin.updateData()

        for subwin in self.desktop.subWindowList():
            if isinstance(subwin, CoursePositionViewer):
                subwin.updateData()

    def UpdateOnScheduleAddition(self):
        """
        Updates the views of all subwindows on the desktop except for timeslots and course linker.
        Called when there is an addition to the schedule database.
        """
        self.coureList.UpdateCourseList()
        self.facultyList.UpdateFacultyList()
        self.courselinker.UpdateLinkerLists()
        for subwin in self.desktop.subWindowList():
            if isinstance(subwin, RoomViewer):
                subwin.updateData()

        for subwin in self.desktop.subWindowList():
            if isinstance(subwin, ProfessorViewer):
                subwin.updateData()

        for subwin in self.desktop.subWindowList():
            if isinstance(subwin, CoursePositionViewer):
                subwin.updateData()

    def UpdateOnScheduleChange(self):
        """
        Updates the views of all subwindows on the desktop except for timeslots and course linker.
        Called when there is a change to the schedule database.
        """
        self.coureList.UpdateCourseList()
        self.facultyList.UpdateFacultyList()
        self.courselinker.UpdateLinkerLists()
        for subwin in self.desktop.subWindowList():
            if isinstance(subwin, RoomViewer):
                subwin.updateData()

        for subwin in self.desktop.subWindowList():
            if isinstance(subwin, ProfessorViewer):
                subwin.updateData()

        for subwin in self.desktop.subWindowList():
            if isinstance(subwin, CoursePositionViewer):
                subwin.updateData()

    #########################################################################
    ### Course updaters.
    #########################################################################

    def AddScheduleItem(self, profIndex: int, courseString: str):
        """
        Adds a schedule item to the schedule database.

        :param profIndex: Internal ID for the professor associated with the class.  Initially
        there is only one professor associated with a course.  Others can be added later.
        :param courseString: String name of the course associated with the schedule item.
        """
        scheditem = ScheduleItem()
        scheditem.ProfessorIID.append(self.faculty[profIndex].InternalID)
        scheditem.CourseIID = self.findCourseIIDFromString(courseString)

        schedinternalids = []
        for schditem in self.schedule:
            schedinternalids.append(schditem.InternalID)

        IntID = 0
        while IntID in schedinternalids:
            IntID += 1

        scheditem.InternalID = IntID
        scheditem.Section = self.GenerateSectionNumber(scheditem.CourseIID)
        self.schedule.append(scheditem)
        self.ChangeMade()
        self.UpdateOnScheduleAddition()

    def addRoomTimesToDatabase(self, course: str, room: str, timeslot: TimeSlot):
        """
        This function adds a room and time timeslot to a course in the schedule database.

        :param course: String of the course name (e.g. MATH 201-003).
        :param room: String representation of the room (e.g. HS 115)
        :param timeslot: A timeslot object associated with the room and schedule item.
        """
        scheditem = self.findScheduleItemFromString(course)
        roomIID = self.findRoomFromString(room).InternalID
        scheditem.RoomsAndTimes.append([roomIID, timeslot])

        # Combine timeslots if possible.
        scheditem.RoomsAndTimes = self.combineScheduleItemTimeslots(scheditem.RoomsAndTimes)
        self.ChangeMade()
        self.UpdateOnScheduleChange()

    def combineScheduleItemTimeslots(self, RoomsAndTimes):
        """
        Combines rooms and times in a list of [room, slot] data.

        :param RoomsAndTimes: List of room timeslot pairs to be combined.
        :return: A list of room timeslot pairs after all combining is done.
        """
        tempslots = copy.deepcopy(RoomsAndTimes)
        if len(tempslots) > 1:
            combinedone = True
            while combinedone:
                combinedone = False
                for i in range(len(tempslots)):
                    for j in range(i + 1, len(tempslots)):
                        if not combinedone:
                            slot1 = tempslots[i]
                            slot2 = tempslots[j]
                            if slot1[0] == slot2[0]:
                                slot3time = slot1[1].combine(slot2[1])
                                if slot3time:
                                    tempslots.append([slot1[0], slot3time])
                                    tempslots.remove(slot1)
                                    tempslots.remove(slot2)
                                    combinedone = True

        return tempslots

    def updateRoomTimesToDatabase(self, course: str, room: str, timeslot: TimeSlot):
        """
        This is invoked when a class is dropped into a slot in one of the room viewer
        subwindows.  Since a drop of this type sets the scheduled item to this slot only
        the rest of the RoomsAndTimes are removed.

        :param course: String of the course name (e.g. MATH 201-003).
        :param room: String representation of the room (e.g. HS 115)
        :param timeslot: A timeslot object associated with the room and schedule item.
        """
        scheditem = self.findScheduleItemFromString(course)
        roomIID = self.findRoomFromString(room).InternalID
        scheditem.RoomsAndTimes = [[roomIID, timeslot]]
        self.ChangeMade()
        self.UpdateOnScheduleChange()

    def makeCourseTentative(self, scheditemIID: int, checked: bool):
        """
        Sets the tentative boolean to the value of checked.

        :param scheditemIID: Internal ID of the schedule item to be made tentative or not.
        :param checked: Boolean to set the tentative field.
        """
        for scheditem in self.schedule:
            if scheditem.InternalID == scheditemIID:
                scheditem.Tentative = checked
        self.ChangeMade()
        self.UpdateOnScheduleChange()

    def removeCourseRoomsAndTimes(self, course: str):
        """
        Removes the rooms and times the course is scheduled for.  In other words, it removes
        the class from the rooms but leaves the professor assignment unaltered.

        :param course: Course name string to be altered.
        """
        scheditem = self.findScheduleItemFromString(course)
        if not scheditem:
            return

        messagestr = "This will remove all scheduled days and times from "
        messagestr += self.courseNameAndSection(scheditem) + "."
        messagestr += "\n\n"
        messagestr += "Do you wish to proceed with room and time deletion?"
        returnValue = QMessageBox.warning(self, "Remove Rooms and Times", messagestr,
                                          QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)

        if returnValue == QMessageBox.Ok:
            scheditem.RoomsAndTimes = []
            self.ChangeMade()
            self.UpdateAllLists()

    def removeCourseFromSchedule(self, course: str):
        """
        Removes the course from the schedule.

        :param course: Course name string to be removed.
        """
        scheditem = self.findScheduleItemFromString(course)
        if not scheditem:
            return

        messagestr = "This will remove "
        messagestr += self.courseNameAndSection(scheditem) + " from the schedule."
        messagestr += "\n\n"
        messagestr += "Do you wish to proceed with deleting this course?"
        returnValue = QMessageBox.warning(self, "Course Deletion", messagestr,
                                          QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)

        if returnValue == QMessageBox.Ok:
            for schitem in self.schedule:
                if scheditem.InternalID in schitem.LinkedCourses:
                    schitem.LinkedCourses.remove(scheditem.InternalID)

            self.schedule.remove(scheditem)
            self.ChangeMade()
            self.UpdateAllLists()

    def updateCourseProperties(self, course: str):
        """
        Invokes the course properties dialog for the class.

        :param course: Course name string to be edited.
        """
        scheditem = self.findScheduleItemFromString(course)
        if not scheditem:
            return

        courseoptions = CourseOptions(self, "Course Information", scheditem)

        if courseoptions.exec():
            scheditem = copy.deepcopy(courseoptions.thisSI)
            scheditem.Tentative = courseoptions.TentativeYes.isChecked()
            scheditem.Subtitle = courseoptions.subtitleedit.text()
            scheditem.Designation = courseoptions.designationsedit.text()
            scheditem.Section = courseoptions.sectionnumberedit.text()
            scheditem.RoomsAndTimes = self.combineScheduleItemTimeslots(scheditem.RoomsAndTimes)

            delindex = -1
            for i in range(len(self.schedule)):
                if self.schedule[i].InternalID == scheditem.InternalID:
                    delindex = i

            if delindex > -1:
                del self.schedule[delindex]
                self.schedule.append(scheditem)
                self.ChangeMade()
                self.UpdateAllLists()

    #########################################################################
    ### Boolean functions to check conflicts.
    #########################################################################

    def professorTimeslotConflict(self, prof: Professor, times: [TimeSlot], skipiids=[-1]) -> bool:
        """
        Determines if the given timeslot list will create a time conflict with the given
        professor.  The skipiids is a list of internal IDs of schedule items not to check
        against the timeslot list.

        :param prof: Professor to check time against.
        :param times: List of timeslots to check.
        :param skipiids: List of schedule item internal IDs to skip in the check.
        :return: True if there is a time conflict and false if not.
        """
        if not prof.Real:
            return False

        conflict = False
        for course in self.schedule:
            if (course.InternalID not in skipiids) and (prof.InternalID in course.ProfessorIID):
                for slot in times:
                    for courseslot in course.RoomsAndTimes:
                        if slot.overlap(courseslot[1]):
                            conflict = True

        return conflict

    def RoomTimeslotConflict(self, roomtimes: [int, TimeSlot], skipiids=[-1]) -> bool:
        """
        Determines if the given room/timeslot list will create a time conflict.
        The skipiids is a list of internal IDs of schedule items not to check
        against the timeslot list.

        :param roomtimes: List of room timeslot pairs to check [roomIID, TimeSlot].
        :param skipiids: List of schedule item internal IDs to skip in the check.
        :return: True if there is a time conflict and false if not.
        """
        room = self.findRoomFromIID(roomtimes[0])
        if not room.Real:
            return False

        conflict = False
        for course in self.schedule:
            if course.InternalID not in skipiids:  # and (prof.InternalID in course.ProfessorIID):
                for rt in course.RoomsAndTimes:
                    if rt[0] == roomtimes[0]:
                        if rt[1].overlap(roomtimes[1]):
                            conflict = True

        return conflict

    def CheckAllRoomTimeslotConflictForRoom(self, room: Room) -> bool:
        """
        Checks the current schedule for any time overlaps in the given room.

        :param room: Room to check.
        :return: True if there is a conflict and false if not.
        """
        timeslist = []
        for course in self.schedule:
            for rt in course.RoomsAndTimes:
                if rt[0] == room.InternalID:
                    timeslist.append(rt[1])

        for i in range(len(timeslist) - 1):
            for j in range(i + 1, len(timeslist)):
                if (timeslist[i].overlap(timeslist[j])):
                    return True

        return False

    def CheckAllRoomTimeslotConflictForProf(self, prof: Professor) -> bool:
        """
        Checks the current schedule for any time overlaps for the given professor.

        :param prof: Professor to check.
        :return: True if there is a conflict and false if not.
        """
        timeslist = []
        for course in self.schedule:
            if prof.InternalID in course.ProfessorIID:
                for rt in course.RoomsAndTimes:
                    timeslist.append(rt[1])

        for i in range(len(timeslist) - 1):
            for j in range(i + 1, len(timeslist)):
                if (timeslist[i].overlap(timeslist[j])):
                    return True

        return False

    #########################################################################
    ### Database searching functions.
    #########################################################################

    def findCourseIIDFromString(self, courseString: str) -> int:
        """
        Finds and returns the internal ID of a course given its name string.

        :param courseString: String name of the course.
        :return: Internal ID of the course. If not found -1 is returned.
        """
        for course in self.courses:
            if course.getName() == courseString:
                return course.InternalID

        return -1

    def findCourseFromString(self, courseString: str) -> Course:
        """
        Finds and returns the Course object with the given course name.

        :param courseString: String name of course.
        :return: Course object found. None if not found.
        """
        for course in self.courses:
            if course.getName() == courseString:
                return course

        return None

    def findCourseFromIID(self, courseIID: int) -> Course:
        """
        Finds and returns the Course object with the given internal ID.

        :param courseIID: Internal ID of the course.
        :return: Course object found. None if not found.
        """
        for course in self.courses:
            if course.InternalID == courseIID:
                return course

        return None

    def findProfessorFromString(self, profstr: str) -> Professor:
        """
        Finds and returns the Professor object with the given name.

        :param profstr: String name of the professor.
        :return: The professor object with that name, None if not found.
        """
        for prof in self.faculty:
            if prof.getName() == profstr:
                return prof

        return None

    def findProfessorFromIID(self, profIID: int) -> Professor:
        """
        Finds and returns the Professor object with the given internal ID.

        :param profIID: Internal ID of the professor.
        :return: The professor object with that ID, None if not found.
        """
        for prof in self.faculty:
            if prof.InternalID == profIID:
                return prof

        return None

    def findScheduleItemFromString(self, coursestr: str) -> ScheduleItem:
        """
        Finds and returns the ScheduleItem object with the given course name (i.e. MATH 201-003).

        :param coursestr: String name of the ScheduleItem.
        :return: The ScheduleItem object with that name, None if not found.
        """
        for scheditem in self.schedule:
            scheditemstr = self.courseNameAndSection(scheditem)
            if scheditemstr == coursestr:
                return scheditem

        return None

    def findScheduleItemFromIID(self, schedIID: int) -> ScheduleItem:
        """
        Finds and returns the ScheduleItem object with the given internal ID.

        :param schedIID: Internal ID of the ScheduleItem.
        :return: The ScheduleItem object with that ID, None if not found.
        """
        for scheditem in self.schedule:
            if scheditem.InternalID == schedIID:
                return scheditem

        return None

    def findRoomFromString(self, roomstr: str) -> Room:
        """
        Finds and returns the Room object with the given name (i.e. HS 115).

        :param roomstr: String name of the Room.
        :return: The Room object with that name, None if not found.
        """
        for room in self.rooms:
            if roomstr == room.getName():
                return room

        return None

    def findRoomFromIID(self, roomIID: int) -> Room:
        """
        Finds and returns the Room object with the given internal ID.

        :param schedIID: Internal ID of the Room.
        :return: The Room object with that ID, None if not found.
        """
        for room in self.rooms:
            if roomIID == room.InternalID:
                return room

        return None

    #########################################################################
    ### Functions for consistant naming and calculations.
    #########################################################################

    def courseNameAndSection(self, courseSI: ScheduleItem) -> str:
        """
        Creates the standard name for the schedule item, the course name and section, i.e. MATH 201-003.

        :param courseSI: ScheduleItem to name.
        :return: String name for the class.
        """
        course = self.findCourseFromIID(courseSI.CourseIID)
        return course.getName() + "-" + courseSI.Section

    def courseName(self, courseSI: ScheduleItem) -> str:
        """
        Creates the course name for the schedule item, i.e. MATH 201.

        :param courseSI: ScheduleItem to name.
        :return: String name for the class.
        """
        course = self.findCourseFromIID(courseSI.CourseIID)
        return course.getName()

    def createTimeslotStringFromScheduleItem(self, scheditem: ScheduleItem) -> str:
        """
        Creates a timeslot string for display of the given schedule item.

        :param scheditem: ScheduleItem to create slot string from.
        :return: Display timeslot string.
        """
        timeslots = scheditem.RoomsAndTimes
        timeslotstring = ""
        firstentry = True
        for slot in timeslots:
            roomname = self.findRoomFromIID(slot[0]).getName()
            if not firstentry:
                timeslotstring += "/ "
            firstentry = False
            timeslotstring += slot[1].getDescription() + " " + roomname + " "

        timeslotstring = timeslotstring.rstrip().lstrip()
        return timeslotstring

    def ScheduleItemTimeCheck(self, scheditem: ScheduleItem) -> int:
        """
        Checks the amount of time the schedule item has been scheduled for and returns a code
        number for the overtime/undertime designation.

        Code:  -2 nothing scheduled, -1 undertime, 0 on time, 1 overtime

        :param scheditem: ScheduleItem to be checked.
        :return: Code number.
        """
        timeinminutes = 0
        for slot in scheditem.RoomsAndTimes:
            timeinminutes += slot[1].getMinutes()

        course = self.findCourseFromIID(scheditem.CourseIID)
        targettimeminutes = course.Contact

        if timeinminutes == 0:
            return -2
        if timeinminutes < targettimeminutes:
            return -1
        elif timeinminutes > targettimeminutes:
            return 1
        else:
            return 0

    def ScheduleItemTimeRemaining(self, scheditem: ScheduleItem) -> int:
        """
        Finds the number of minutes that the course needs to add.

        :param scheditem: ScheduleItem to be checked.
        :return: Amount of time the item needs to be scheduled to reach its minute/week count.
        """
        timeinminutes = 0
        for slot in scheditem.RoomsAndTimes:
            timeinminutes += slot[1].getMinutes()

        course = self.findCourseFromIID(scheditem.CourseIID)
        targettimeminutes = course.Contact
        return targettimeminutes - timeinminutes

    def getChartBackgroundColor(self, timedes: int) -> QColor:
        """
        Takes the time designation code number and returns the respective color.

        :param timedes: Time designation, value from ScheduleItemTimeCheck.
        Code:  -2 nothing scheduled, -1 undertime, 0 on time, 1 overtime
        :return: Color for the designation.
        """
        backcolor = QColor()
        if timedes == -2:
            backcolor.setRgb(255, 0, 0)
        elif timedes == -1:
            backcolor.setRgb(255, 255, 150)
        elif timedes == 1:
            backcolor.setRgb(200, 255, 200)
        else:
            backcolor.setRgb(140, 230, 140)
        return backcolor

    def getChartBackgroundHighlightColor(self, timedes: int) -> QColor:
        """
        Takes the time designation code number and returns the respective color for highlighting.

        :param timedes: Time designation, value from ScheduleItemTimeCheck.
        Code:  -2 nothing scheduled, -1 undertime, 0 on time, 1 overtime
        :return: Color for the designation.
        """
        backcolor = QColor()
        if timedes == -2:
            backcolor.setRgb(255, 0, 0)
        elif timedes == -1:
            backcolor.setRgb(255, 255, 230)
        elif timedes == 1:
            backcolor.setRgb(230, 255, 230)
        else:
            backcolor.setRgb(200, 255, 200)
        return backcolor

    def calculateProfessorWorkload(self, prof: Professor):
        """
        Calculates the professor workload for the semester.

        :param prof: Professor to calculate workload.
        :return: List of 4 values, workload, fractional load, workload for tentative classes,
        and fractional load for tentative classes.
        """
        workload = 0
        tentativeworkload = 0
        for schditem in self.schedule:
            if prof.InternalID in schditem.ProfessorIID:
                course = self.findCourseFromIID(schditem.CourseIID)
                if schditem.Tentative:
                    tentativeworkload += course.Workload / len(schditem.ProfessorIID)
                else:
                    workload += course.Workload / len(schditem.ProfessorIID)

        workloadfrac = workload / self.options[1]
        tentativeworkloadfrac = tentativeworkload / self.options[1]
        return workload, workloadfrac, tentativeworkload, tentativeworkloadfrac

    def GenerateSectionNumber(self, courseIID: int, skipids=[]) -> str:
        """
        Takes a course internal ID and finds the first section number of the form, 001, 002, 003, ...
        that has not yet been used.

        :param courseIID: Internal ID for the course.
        :param skipids: Schedule item internal IDs to skip.
        :return: Section number that has not been used, as a string.
        """
        schedsections = []
        for scheditem in self.schedule:
            if (courseIID == scheditem.CourseIID) and (scheditem.InternalID not in skipids):
                schedsections.append(scheditem.Section)

        secnum = 1
        secstring = str(secnum).zfill(3)
        while secstring in schedsections:
            secnum += 1
            secstring = str(secnum).zfill(3)

        return secstring

    def CheckSectionNumber(self, courseIID: int, sectionnumber: str, skipids=[]) -> [str, bool]:
        """
        Checks if the given section number is valid, i.e. not already been used.

        :param courseIID: Internal ID for the course.
        :param sectionnumber: Section number to check.
        :param skipids: Schedule item internal IDs to skip.
        :return: Pair of the reformatted section number string and boolean on if it is valid.
        """
        sectionnumber = sectionnumber.lstrip().rstrip()
        sectionnumber = self.removeWhitespace(sectionnumber)
        sectionnumber = self.removeColon(sectionnumber)

        sectionnumberfound = False
        for scheditem in self.schedule:
            if (courseIID == scheditem.CourseIID) and (scheditem.InternalID not in skipids):
                if sectionnumber == scheditem.Section:
                    sectionnumberfound = True

        return sectionnumber, sectionnumberfound

    #########################################################################
    ### Support Functions
    #########################################################################

    def itemsToTabString(self, items: []) -> str:
        """
        Converts a list of row lists of table elements to a tab delimited string.

        :param items: Items of strings to convert.
        :return: Tab delimited string of the items.
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

        :param tdstr:  Tab delimited string of the items.
        :return: List of lists, essentially a 2D array.
        """
        retitems = []
        strobj = str(tdstr)
        strlist = strobj.split('\n')
        for line in strlist:
            if len(line) > 0:
                splitline = line.split('\t')
                retitems.append(splitline)

        return retitems

    def removeWhitespace(self, s: str) -> str:
        """
        Removes all whitespace from the given string.

        :param s: String to process.
        :return: Final string with whitespace removed.
        """
        return "".join(s.split())

    def removeColon(self, s: str) -> str:
        """
        Removes all colons from the given string.

        :param s: String to process.
        :return: Final string without colons.
        """
        return "".join(s.split(':'))

    #########################################################################
    ### Subwindow creators and viewers.
    #########################################################################

    def addroomviewer(self):
        """
        Adds an instance of the room viewer subwindow to the desktop.
        """
        roomviewer = RoomViewer(self)
        self.desktop.addSubWindow(roomviewer)
        roomviewer.show()

    def addprofessorviewer(self):
        """
        Adds an instance of the professor viewer subwindow to the desktop.
        """
        profviewer = ProfessorViewer(self)
        self.desktop.addSubWindow(profviewer)
        profviewer.show()

    def addcoursepositionsviewer(self):
        """
        Adds an instance of the course position viewer subwindow to the desktop.
        """
        courseposviewer = CoursePositionViewer(self)
        self.desktop.addSubWindow(courseposviewer)
        courseposviewer.show()

    def viewcourselist(self):
        """
        Adds an instance of the course list viewer subwindow to the desktop if needed, otherwise
        sets the focus to that subwindow.
        """
        if not self.coureList.isVisible():
            self.desktop.addSubWindow(self.coureList)
            self.coureList.show()
        else:
            self.coureList.setFocus()

    def viewfacultylist(self):
        """
        Adds an instance of the faculty list viewer subwindow to the desktop
        (faculty course assignments) if needed, otherwise sets the focus to
        that subwindow.
        """
        if not self.facultyList.isVisible():
            self.desktop.addSubWindow(self.facultyList)
            self.facultyList.show()
        else:
            self.facultyList.setFocus()

    def viewNoteEditor(self):
        """
        Adds an instance of the note editor subwindow to the desktop if needed, otherwise
        sets the focus to that subwindow.
        """
        if not self.noteeditor.isVisible():
            self.desktop.addSubWindow(self.noteeditor)
            self.noteeditor.show()
        else:
            self.noteeditor.setFocus()

    # def onInternalHelp(self):
    #     """
    #     Opens the internal help system.
    #     """
    #     if not self.internalhelp:
    #         self.internalhelp = InternalHelp()
    #
    #     self.internalhelp.setVisible(True)
    #     self.internalhelp.activateWindow()

    def viewtimeslotlist(self):
        """
        Adds an instance of the timeslot subwindow to the desktop if needed, otherwise
        sets the focus to that subwindow.
        """
        if not self.timeslotlist.isVisible():
            self.desktop.addSubWindow(self.timeslotlist)
            self.timeslotlist.show()
        else:
            self.timeslotlist.setFocus()

    def viewcourselinker(self):
        """
        Adds an instance of the course linker subwindow to the desktop if needed, otherwise
        sets the focus to that subwindow.
        """
        if not self.courselinker.isVisible():
            self.desktop.addSubWindow(self.courselinker)
            self.courselinker.show()
        else:
            self.courselinker.setFocus()

    def testing(self):
        """
        Test function linked to the test menu option that can be used in development.
        Currently, this menu item is not visible in th menu.
        """
        pass

    #########################################################################
    ### Functions for preferences.
    #########################################################################

    def getImagePrintingOptions(self):
        options = [self.ImagePrintWidth, self.ImagePrintHeight, self.ImagePrintScaleMode]
        imgprintopts = ImagePrintOptions(self, "Image Printing Options", options)
        if imgprintopts.exec():
            self.ImagePrintWidth = imgprintopts.widthvalue.value()
            self.ImagePrintHeight = imgprintopts.heightvalue.value()

            if imgprintopts.HeightToWidthRB.isChecked():
                self.ImagePrintScaleMode = 0
            elif imgprintopts.WidthToHeightRB.isChecked():
                self.ImagePrintScaleMode = 1
            else:
                self.ImagePrintScaleMode = 2
            self.ChangeMade()

    def getMinimumFontSize(self):
        value, ok = QInputDialog.getInt(self, 'Minimum Font Size', 'Minimum Font Size for Graphics:',
                                        self.minimumGraphicFontSize, 5, 72)
        if ok:
            self.minimumGraphicFontSize = value
            self.ChangeMade()
            self.UpdateAllLists()

    #########################################################################
    ### Help and about functions
    #########################################################################

    def aboutDialog(self):
        """
        Display information about program dialog box
        """
        QMessageBox.about(self, self.program_title + "  Version " + self.version,
                          self.authors + "\nVersion " + self.version +
                          "\nCopyright " + self.copyright +
                          "\nDeveloped in Python using the PySide6 GUI toolset.\n" + self.licence)

    def onHelp(self):
        """
        Open the help system in the system browser.
        """
        self.url_home_string = "file://" + self.resource_path("Help/Help.html")
        webbrowser.open(self.url_home_string)

    #########################################################################
    ### Open and save functions.
    #########################################################################

    def ListFromDatabases(self):
        """
        Creates a single list containing the data in all the databases.

        :return: The list of databases.
        """
        filecontents = []
        filecontents.append(self.options)
        filecontents.append(self.faculty)
        filecontents.append(self.rooms)
        filecontents.append(self.courses)
        filecontents.append(self.standardtimeslots)
        filecontents.append(self.schedule)
        filecontents.append(self.noteeditor.editor.toPlainText())
        return filecontents

    def DatabasesFromList(self, filecontents: []):
        """
        Takes a list of all database data, as would be returned from the ListFromDatabases
        function, and loads the data into the scheduling databases.

        :param filecontents: A list of all database data, as would be returned from the
        ListFromDatabases function.
        :return: Boolean True if the loading succeeded and false if not.
        """
        try:
            self.options = filecontents[0]
            self.faculty = filecontents[1]
            self.rooms = filecontents[2]
            self.courses = filecontents[3]
            self.standardtimeslots = filecontents[4]
            self.schedule = filecontents[5]
            self.noteeditor.editor.setPlainText(filecontents[6])
            return True
        except:
            return False

    def openFile(self, file_name=None):
        """
        Open a binary file containing all the database data and load it into the scheduling
        databases.
        """
        if self.changemade:
            res = QMessageBox.warning(self, "Changes Made",
                                      "Changes have been made to the schedule and will be lost if you open a file.  " +
                                      "Are you sure want to open a file?",
                                      QMessageBox.Yes | QMessageBox.No)
            if res == QMessageBox.No:
                return

        if not file_name:
            file_name, _ = QFileDialog.getOpenFileName(self, "Open File",
                                                       "", "Schedule Files (*.ash);;All Files (*.*)")

        if file_name:
            tempDatabaseList = self.ListFromDatabases()
            with open(file_name, 'rb') as f:
                try:
                    filecontents = pickle.load(f)
                    if not self.DatabasesFromList(filecontents):
                        self.DatabasesFromList(tempDatabaseList)
                    else:
                        self.loadedFilename = file_name
                        self.ChangeMade(False)
                        self.updateProgramWindowTitle()
                except:
                    self.DatabasesFromList(tempDatabaseList)
                    QMessageBox.warning(self, "File Not Loaded", "The file " + file_name + " could not be loaded.",
                                        QMessageBox.Ok)

            self.UpdateAllLists()

    def saveDataToFile(self, filename: str = ""):
        """
        Loads all the database data to a single list and then saves the data to a single
        file, filename.

        :param filename: Name of the file to save.
        """
        if filename == "":
            return

        filecontents = self.ListFromDatabases()
        with open(filename, 'wb') as f:
            try:
                pickle.dump(filecontents, f)
                self.loadedFilename = filename
                self.ChangeMade(False)
                self.updateProgramWindowTitle()
            except:
                QMessageBox.warning(self, "File Not Saved", "The file " + filename + " could not be saved.",
                                    QMessageBox.Ok)

    def saveFileAs(self):
        """
        Opens a file dialog box to select a filename for saving the database data.
        """
        dialog = QFileDialog()
        dialog.setFilter(dialog.filter() | QDir.Hidden)
        dialog.setDefaultSuffix('ash')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters(['Schedule Files (*.ash)'])
        dialog.setWindowTitle('Save As')

        if dialog.exec() == QDialog.Accepted:
            filelist = dialog.selectedFiles()
            if len(filelist) > 0:
                file_name = filelist[0]
                self.saveDataToFile(file_name)

    def saveFile(self):
        """
        If there is already a file loaded it will call saveDataToFile to update the file contents.
        If there is no file loaded it will call saveFileAs to get a filename from the user and
        then save the contents from there.
        """
        if self.loadedFilename != "":
            self.saveDataToFile(self.loadedFilename)
        else:
            self.saveFileAs()

    def mergeSchedules(self, completemerge=False):
        """
        Merges the current scheduling data with the data from another file.  If completemerge
        is true the data will be merged and if false the information for a merge report will
        be generated and returned but no altering of the databases will be done.

        :param completemerge: Boolean on whether to load the merged data into the
        databases.  If true the files will be merged into the program databases and if
        false the report data will be generated but the original databases will be unaltered.
        :return: List of merge changes for a merge report.
        """
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File for Merging",
                                                   "", "Schedule Files (*.ash);;All Files (*.*)")

        # Load in the data from the file to merge.
        if file_name:
            with open(file_name, 'rb') as f:
                try:
                    filecontents = pickle.load(f)
                    mergeoptions = filecontents[0]  # use options from current schedule.
                    mergefaculty = filecontents[1]
                    mergerooms = filecontents[2]
                    mergecourses = filecontents[3]
                    mergestandardtimeslots = filecontents[4]
                    mergeschedule = filecontents[5]
                    mergenotes = filecontents[6]
                except:
                    QMessageBox.warning(self, "File Not Loaded", "The file " + file_name + " could not be loaded.",
                                        QMessageBox.Ok)
                    return None
        else:
            return None

        # Set all internal ids to -1 of what they were do avoid conflicts in merging.
        # These will be reset or altered to avoid conflicts with the schedule being merged
        # into.
        for i in range(len(mergefaculty)):
            mergefaculty[i].InternalID *= -1

        for i in range(len(mergerooms)):
            mergerooms[i].InternalID *= -1

        for i in range(len(mergecourses)):
            mergecourses[i].InternalID *= -1

        for i in range(len(mergeschedule)):
            mergeschedule[i].CourseIID *= -1
            mergeschedule[i].InternalID *= -1
            for j in range(len(mergeschedule[i].ProfessorIID)):
                mergeschedule[i].ProfessorIID[j] *= -1
            for j in range(len(mergeschedule[i].RoomsAndTimes)):
                mergeschedule[i].RoomsAndTimes[j][0] *= -1
            for j in range(len(mergeschedule[i].LinkedCourses)):
                mergeschedule[i].LinkedCourses[j] *= -1

        # Do a deep copy of all current database data so the merge process does
        # not alter the current data until mrege is complete and successful.
        combinedFaculty = copy.deepcopy(self.faculty)
        combinedRooms = copy.deepcopy(self.rooms)
        combinedCourses = copy.deepcopy(self.courses)
        combinedstandardtimeslots = copy.deepcopy(self.standardtimeslots)
        combinedSchedule = copy.deepcopy(self.schedule)
        combinedNotes = self.noteeditor.editor.toPlainText()

        # Set up reporting lists for the merge report.
        reportNewFaculty = []
        reportNewRooms = []
        reportNewCourses = []
        reportNewSlots = []
        reportSectionChanges = []
        reportTimeConflicts = []
        reportNewClasses = []

        # Merge in the faculty.  For each faculty member being merged determine if they
        # are already in the combined faculty list, if so adjust the merging schedule professor
        # ID to the combined (old) faculty ID.  If they are not in the combined schedule, set
        # a new internal ID for the professor that does not conflict with the combined list,
        # then adjust the merging schedule professor ID to the new faculty ID.
        # New professor's names are stored in the reportNewFaculty list to be added to the report.
        for i in range(len(mergefaculty)):
            profname = mergefaculty[i].getName()
            profid = mergefaculty[i].InternalID
            found = False
            foundid = -1
            for mprof in combinedFaculty:
                if mprof.getName() == profname:
                    found = True
                    foundid = mprof.InternalID
            if found:
                for j in range(len(mergeschedule)):
                    for k in range(len(mergeschedule[j].ProfessorIID)):
                        if mergeschedule[j].ProfessorIID[k] == profid:
                            mergeschedule[j].ProfessorIID[k] = foundid
            else:
                newidfound = False
                newid = 0
                while not newidfound:
                    newid += 1
                    newidfound = True
                    for mprof in combinedFaculty:
                        if newid == mprof.InternalID:
                            newidfound = False
                mergefaculty[i].InternalID = newid
                for j in range(len(mergeschedule)):
                    for k in range(len(mergeschedule[j].ProfessorIID)):
                        if mergeschedule[j].ProfessorIID[k] == profid:
                            mergeschedule[j].ProfessorIID[k] = newid
                combinedFaculty.append(mergefaculty[i])
                reportNewFaculty.append(mergefaculty[i].getName())

        # Sort the combined faculty by the formal faculty name.
        combinedFaculty.sort(key=lambda x: x.getName())

        # Merge in the rooms.  For each room being merged determine if it is
        # already in the combined room list, if so adjust the merging schedule room internal
        # ID to the combined (old) room ID.  If the room is not in the combined schedule, set
        # a new internal ID for the room that does not conflict with the combined list,
        # then adjust the merging schedule room ID to the new room ID.
        # New room's names are stored in the reportNewRooms list to be added to the report.
        for i in range(len(mergerooms)):
            roomname = mergerooms[i].getName()
            roomid = mergerooms[i].InternalID
            found = False
            foundid = -1
            for mroom in combinedRooms:
                if mroom.getName() == roomname:
                    found = True
                    foundid = mroom.InternalID
            if found:
                for j in range(len(mergeschedule)):
                    for k in range(len(mergeschedule[j].RoomsAndTimes)):
                        if mergeschedule[j].RoomsAndTimes[k][0] == roomid:
                            mergeschedule[j].RoomsAndTimes[k][0] = foundid
            else:
                newidfound = False
                newid = 0
                while not newidfound:
                    newid += 1
                    newidfound = True
                    for mroom in combinedRooms:
                        if newid == mroom.InternalID:
                            newidfound = False
                mergerooms[i].InternalID = newid
                for j in range(len(mergeschedule)):
                    for k in range(len(mergeschedule[j].RoomsAndTimes)):
                        if mergeschedule[j].RoomsAndTimes[k][0] == roomid:
                            mergeschedule[j].RoomsAndTimes[k][0] = newid
                combinedRooms.append(mergerooms[i])
                reportNewRooms.append(mergerooms[i].getName())

        # Sort the combined room list by the room name.
        combinedRooms.sort(key=lambda x: x.getName())

        # Merge in the curses.  For each course being merged determine if it is
        # already in the combined course list, if so adjust the merging schedule course internal
        # ID to the combined (old) course ID.  If the course is not in the combined schedule, set
        # a new internal ID for the course that does not conflict with the combined list,
        # then adjust the merging schedule course ID to the new course ID.
        # New course's names are stored in the reportNewCourses list to be added to the report.
        for i in range(len(mergecourses)):
            coursename = mergecourses[i].getName()
            courseid = mergecourses[i].InternalID
            found = False
            foundid = -1
            for mcourse in combinedCourses:
                if mcourse.getName() == coursename:
                    found = True
                    foundid = mcourse.InternalID
            if found:
                for j in range(len(mergeschedule)):
                    if mergeschedule[j].CourseIID == courseid:
                        mergeschedule[j].CourseIID = foundid
            else:
                newidfound = False
                newid = 0
                while not newidfound:
                    newid += 1
                    newidfound = True
                    for mcourse in combinedCourses:
                        if newid == mcourse.InternalID:
                            newidfound = False
                mergecourses[i].InternalID = newid
                for j in range(len(mergeschedule)):
                    if mergeschedule[j].CourseIID == courseid:
                        mergeschedule[j].CourseIID = newid
                combinedCourses.append(mergecourses[i])
                reportNewCourses.append(mergecourses[i].getName())

        # Sort the combined course list by the course name.
        combinedCourses.sort(key=lambda x: x.getName())

        # Merge in the schedule items, classes.
        for i in range(len(mergeschedule)):
            mergeclass = mergeschedule[i]

            # Determine if the merge course is a duplicate of one already in the combined
            # list, if so, adjust its section number to one not being used.  Store the
            # section number change for reporting.
            mergeclassNameAndSection = ""
            mergeclassName = ""
            for course in combinedCourses:
                if course.InternalID == mergeclass.CourseIID:
                    mergeclassName = course.getName()
                    mergeclassNameAndSection = course.getName() + "-" + mergeclass.Section

            found = False
            for mclass in combinedSchedule:
                mclassNameAndSection = ""
                for course in combinedCourses:
                    if course.InternalID == mclass.CourseIID:
                        mclassNameAndSection = course.getName() + "-" + mclass.Section

                if mergeclassNameAndSection == mclassNameAndSection:
                    found = True

            if found:
                schedsections = []
                for scheditem in combinedSchedule:
                    if (mergeclass.CourseIID == scheditem.CourseIID):
                        schedsections.append(scheditem.Section)

                secnum = 1
                secstring = str(secnum).zfill(3)
                while secstring in schedsections:
                    secnum += 1
                    secstring = str(secnum).zfill(3)
                mergeclass.Section = secstring
                reportSectionChanges.append([mergeclassNameAndSection, mergeclass.Section])

            # Sort section changes by course name.
            reportSectionChanges.sort(key=lambda x: x[0])
            oldid = mergeclass.InternalID

            # Give the schedule item a new internal id that does not conflict and
            # adjust the linked course IDs to this new ID.
            schediids = []
            for scheditem in combinedSchedule:
                schediids.append(scheditem.InternalID)

            iid = 1
            while iid in schediids:
                iid += 1
            mergeclass.InternalID = iid

            for linkedclass in mergeschedule:
                for k in range(len(linkedclass.LinkedCourses)):
                    if linkedclass.LinkedCourses[k] == oldid:
                        linkedclass.LinkedCourses[k] = mergeclass.InternalID

            # Check the merged classrooms and times for conflicts.  If there is a conflict
            # with a room in the schedule or with the professor's schedule remove that
            # time slot from the merged class.  Save the new class names and any time
            # conflicts for reporting.
            oldslots = mergeclass.RoomsAndTimes
            slots = []
            badslots = []
            for slot in oldslots:
                slotroom = None
                for room in combinedRooms:
                    if room.InternalID == slot[0]:
                        slotroom = room

                goodslot = True
                if slotroom:
                    for mclass in combinedSchedule:
                        for mslot in mclass.RoomsAndTimes:
                            if (slot[0] == mslot[0]) and slotroom.Real and slot[1].overlap(mslot[1]):
                                goodslot = False

                for mprofid in mergeclass.ProfessorIID:
                    mprof = None
                    for prof in combinedFaculty:
                        if prof.InternalID == mprofid:
                            mprof = prof

                    if mprof and mprof.Real:
                        for mclass in combinedSchedule:
                            if mprofid in mclass.ProfessorIID:
                                for mslot in mclass.RoomsAndTimes:
                                    if (slot[0] == mslot[0]) and slot[1].overlap(mslot[1]):
                                        goodslot = False

                if goodslot:
                    slots.append(slot)
                else:
                    badslots.append(slot)

            mergeclassNameAndSection = mergeclassName + "-" + mergeclass.Section
            mergeclass.RoomsAndTimes = slots
            if len(badslots) > 0:
                badslots.sort(key=lambda x: x[1].getDescription())
                reportTimeConflicts.append([mergeclassNameAndSection, badslots])
            reportNewClasses.append(mergeclassNameAndSection)
            combinedSchedule.append(mergeclass)

        # Sort the new class and time conflicts report data.
        reportTimeConflicts.sort(key=lambda x: x[0])
        reportNewClasses.sort()

        # Add in new standard timeslots.
        for i in range(len(mergestandardtimeslots)):
            newslot = True
            for j in range(len(combinedstandardtimeslots)):
                if combinedstandardtimeslots[j].equals(mergestandardtimeslots[i]):
                    newslot = False

            if newslot:
                combinedstandardtimeslots.append(mergestandardtimeslots[i])
                reportNewSlots.append(mergestandardtimeslots[i].getDescription())

        # Sort the combined standard timeslots.
        combinedstandardtimeslots.sort(key=lambda x: x.getDescription())

        # Merge the notes.
        if mergenotes != combinedNotes:
            if (mergenotes != "") and (combinedNotes != ""):
                combinedNotes = combinedNotes + "\n\n------------------------\n\n" + mergenotes
            elif mergenotes != "":
                combinedNotes = mergenotes

        # If the completemerge parameter is true load the combined data into the schedule
        # databases.
        if completemerge:
            self.faculty = combinedFaculty
            self.rooms = combinedRooms
            self.courses = combinedCourses
            self.standardtimeslots = combinedstandardtimeslots
            self.schedule = combinedSchedule
            self.noteeditor.editor.setText(combinedNotes)

        # Store the merge report data into a single list and return to be displayed.
        mergereport = [reportNewFaculty, reportNewRooms, reportNewCourses, reportNewSlots,
                       reportSectionChanges, reportTimeConflicts, reportNewClasses]
        return mergereport

    def mergeFile(self):
        """
        Merge the schedule with another schedule file and display a merge report.
        """
        mergereport = self.mergeSchedules(True)
        if mergereport:
            self.UpdateAllLists()
            self.loadedFilename = ""
            self.updateProgramWindowTitle()
            self.MergeReport(mergereport)

    def mergeFileAnalysis(self):
        """
        Display a merge report for merging another file with the current data, do not
        merge the data.
        """
        mergereport = self.mergeSchedules()
        if mergereport:
            self.MergeReport(mergereport)


# Main program that simply starts the application.
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AcademicScheduler(app)
    progcss = appcss()
    app.setStyleSheet(progcss.getCSS())

    # Load file parameter if one is given.
    if len(sys.argv) > 1:
        window.openFile(sys.argv[1])

    sys.exit(app.exec())
