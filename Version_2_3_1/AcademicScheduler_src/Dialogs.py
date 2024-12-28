"""
Dialog Classes

Description: This file contains a set of dialog box classes for user interaction at varius places in the
program.

CourseDialog: Used for input of new courses and editing existing ones.  Uses a table format for input and has
              functions for checking validity of the input data.
FacultyDialog: Used for input of new faculty and editing existing ones.  Uses a table format for input and has
               functions for checking validity of the input data.
TimeslotDialog: Used for input of new standard timeslots and editing existing ones.  Uses a table format for
                input and has functions for checking validity of the input data.
SectionNumberDialog: Used for mass altering of sectiuon numbers, subtitles, and designations for courses.  Table
                     input format with validity checking on the section numbers.
RoomsDialog: Used for input of new rooms and editing existing ones.  Uses a table format for input and has
             functions for checking validity of the input data.
HTMLViewer: Used for the document type reports.  Takes as parameters the dialog title and HTML content.  Displays the
            HTML content in the internal browser.  The dialog has the additional functionality of printing the
            document and exporting the document to a PDF file.
TextViewer: Was to be fsed for the plaintext document type reports but was not implemented into the system due to
            the creation of the HTML viewer.  The dialog remains in the system for possible future use.
            The dialog has the additional functionality of printing, saving, and copying the document.
GeneralTableDialog: Used for table type reports.  Takes as parameters the dialog title, list of lists (2D Array)
                    of table content, and a list of column headers. The dialog has the additional functionality of
                    copying the table contents as a tab delimited table that can be loaded directly into most
                    spreadsheet programs.
ImagePrintOptions: Simple dialog for the user to select options for printing images, image size and scaling
                   options.
GenSeparator: Simple class for the creation of a horizontal line on the dialog.
MinuteSpinBox: Simple derived class of an integer spin box that restricts the values between 0 and 59.
RoomTimeDialogInfo: Dialog for selecting a room, days, and times for class meeting times.  There is a dropdown for
                    the rooms, taken from the room database of the main program, check boxes for the days, and spin
                    boxes for the times.
CourseOptions: This is the course information dialog that is invoked from numerous places in the program.
               The course information dialog contains options for changing all aspects of the schedule item, instructor,
               meeting times, section number, course, tentative, subtitles, and designations. The course selection
               is done through a dropdown linked to the course database, the instructor and timeslots list have
               toolbars to the side to add, edit, and delete.  The section, subtitle, and designations are free-form
               text.  The tentative are yes/no radio buttons.  This dialog is linked to the main app so that it can
               check all changes as they are made.  It also has options for checking if a section number is valid and
               for generating an unused section number.

@author: Don Spickler
Last Revision: 8/12/2022

"""

import copy

from PySide6.QtPrintSupport import (QPrintDialog, QPrinter, QPrintPreviewDialog)
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QVBoxLayout, QApplication,
                               QFileDialog, QToolBar, QTableWidgetItem,
                               QRadioButton, QButtonGroup, QLabel, QHBoxLayout,
                               QSpinBox, QDoubleSpinBox, QListWidget, QComboBox,
                               QTextEdit, QPlainTextEdit, QLineEdit, QInputDialog,
                               QMessageBox, QCheckBox, QFrame, QPushButton, QAbstractItemView,
                               QTextBrowser)
from PySide6.QtGui import (QIcon, QPageSize, QPageLayout, QFontMetrics, QAction)
from PySide6.QtCore import (QDir, QSize, QUrl, QMarginsF, Qt)

from LC_Table import LC_Table
from TimeSlot import TimeSlot
from Professor import Professor
from Room import Room


class CourseDialog(QDialog):
    """
    Used for input of new courses and editing existing ones.  Uses a table format for input and has
    functions for checking validity of the input data.
    """

    def __init__(self, parent=None, title="Add New Courses", datatoload=[], courseeditID=-1):
        """
        Sets up the UI for the dialog.

        :param parent: Link to the calling control, which must be the main app.
        :param title: Title to put on the dialog.
        :param datatoload: Data of an existing course, used when editing a class.
        :param courseeditID: Course's internal id. This is to set an index the edited course for the main app
                             to change the correct class.
        """
        super().__init__(parent)
        self.Parent = parent
        self.mainapp = parent

        self.setWindowTitle(title)
        self.editmode = False
        self.editID = courseeditID

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.table_widget = LC_Table(self)
        if len(datatoload) == 0:
            self.table_widget.resizeTable(100, 5)
        else:
            self.table_widget.resizeTable(1, 5)
            self.editmode = True
            for j in range(5):
                self.table_widget.setItem(0, j, QTableWidgetItem(datatoload[j]))

        self.table_widget.setLables(["Code *", "Number *", "Title *", "Minutes/Week *", "Workload Hours *"])
        self.table_widget.resizeColumnsToContents()
        self.table_widget.resizeRowsToContents()
        self.table_widget.setColumnWidth(2, 250)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.table_widget)
        self.layout.addWidget(self.buttonBox)
        self.layout.setContentsMargins(5,5,5,5)
        self.setLayout(self.layout)
        self.setMinimumWidth(625)

    def accept(self):
        """
        Override on dialog acceptance to check the input data before accepting the new or edited courses.
        """
        if self.CheckCourses():
            super().accept()

    def CheckCourses(self) -> bool:
        """
        Checks all the input data for valid inputs and displays messages for anything that is invalid.  If
        all checks out the function returns true and if not the function returns false.

        :return: Boolean which is true if the data is valid and false if not.
        """
        data = self.table_widget.getTableContents()

        index = -1
        for item in data:
            index += 1
            item[0] = self.mainapp.removeColon(self.mainapp.removeWhitespace(item[0]).upper())
            item[1] = self.mainapp.removeColon(self.mainapp.removeWhitespace(item[1]))
            for i in range(2, 5):
                item[i] = item[i].lstrip().rstrip()

            # Determine if a row has been started, blank rows are ignored.  If started we do data validation.
            started = False
            for field in item:
                if field != "":
                    started = True

            if started:
                valid = True
                for field in item:
                    if field == "":
                        valid = False

                # Determine if all required fields are filled in.
                if not valid:
                    messagestr = "There are unfilled fields in position " + str(index + 1) + ".  "
                    messagestr += "All fields must be filled in."
                    QMessageBox.warning(self, "Unfilled Fields", messagestr, QMessageBox.Ok)
                    return False

                # Determine if the Minutes/Week entries are numeric.
                try:
                    val = float(item[3])
                except Exception as e:
                    messagestr = "The Minutes/Week in position " + str(index + 1) + " "
                    messagestr += "must be numeric."
                    QMessageBox.warning(self, "Invalid Field", messagestr, QMessageBox.Ok)
                    return False

                # Determine if the Workload Hours entries are numeric.
                try:
                    val = float(item[4])
                except Exception as e:
                    messagestr = "The Workload Hours in position " + str(index + 1) + " "
                    messagestr += "must be numeric."
                    QMessageBox.warning(self, "Invalid Field", messagestr, QMessageBox.Ok)
                    return False

                # Check for unique names of the classes, i.e. duplications.
                newcoursevalid = True
                if self.editmode:
                    for course in self.mainapp.courses:
                        if (course.getName() == item[0] + " " + item[1]) and (course.InternalID != self.editID):
                            newcoursevalid = False
                else:
                    for course in self.mainapp.courses:
                        if course.getName() == item[0] + " " + item[1]:
                            newcoursevalid = False

                if not newcoursevalid:
                    messagestr = "The course in position " + str(index + 1) + " "
                    messagestr += "is a duplicate of a class that is already in the database."
                    QMessageBox.warning(self, "Course Duplicate", messagestr, QMessageBox.Ok)
                    return False

        return True


class FacultyDialog(QDialog):
    """
    Used for input of new faculty and editing existing ones.  Uses a table format for input and has
    functions for checking validity of the input data.
    """

    def __init__(self, parent=None, title="Add New Faculty Members", datatoload=[], id=-1):
        """
        Sets up the UI for the dialog.

        :param parent: Link to the calling control, which must be the main app.
        :param title: Title to put on the dialog.
        :param datatoload: Data of an existing faculty member, used when editing a professor.
        :param id: Professor's internal id. This is to set an index the edited prof for the main app
                             to change the correct prof.
        """
        super().__init__(parent)
        self.Parent = parent
        self.mainapp = parent

        self.setWindowTitle(title)
        self.editmode = False
        self.editID = id

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.table_widget = LC_Table(self)
        if len(datatoload) == 0:
            self.table_widget.resizeTable(100, 7)
        else:
            self.table_widget.resizeTable(1, 7)
            self.editmode = True
            for j in range(7):
                self.table_widget.setItem(0, j, QTableWidgetItem(datatoload[j]))

        self.table_widget.setLables(
            ["Last Name *", "First Name *", "Middle Name", "Suffix", "Short Designation *", "ID", "Real (Y/n)"])
        self.table_widget.resizeColumnsToContents()
        self.table_widget.resizeRowsToContents()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.table_widget)
        self.layout.addWidget(self.buttonBox)
        self.layout.setContentsMargins(5,5,5,5)
        self.setLayout(self.layout)
        self.setMinimumWidth(625)

    def accept(self):
        """
        Override on dialog acceptance to check the input data before accepting the new or edited profs.
        """
        if self.CheckFaculty():
            super().accept()

    def CheckFaculty(self) -> bool:
        """
        Checks all the input data for valid inputs and displays messages for anything that is invalid.  If
        all checks out the function returns true and if not the function returns false.

        :return: Boolean which is true if the data is valid and false if not.
        """

        data = self.table_widget.getTableContents()

        index = -1
        for item in data:
            index += 1
            for i in range(7):
                item[i] = item[i].lstrip().rstrip()

            # Determine if a row has been started, blank rows are ignored.  If started we do data validation.
            started = False
            for i in range(7):
                if item[i] != "":
                    started = True

            # Determine if all required fields are filled in.
            if started:
                valid = True
                if (item[0] == "") or (item[1] == "") or (item[4] == ""):
                    valid = False

                if not valid:
                    messagestr = "Some of the required fields on line " + str(index + 1) + " are not filled in.  "
                    messagestr += "The first and last name must be filled in along with the shore designation."
                    QMessageBox.warning(self, "Unfilled Fields", messagestr, QMessageBox.Ok)
                    return False

                # Create new professor for data checking.
                newprof = Professor()
                newprof.LastName = item[0]
                newprof.FirstName = item[1]
                newprof.MiddleName = item[2]
                newprof.Suffix = item[3]
                newprof.ShortDes = item[4]
                newprof.ID = item[5]
                if item[6].upper() == "N":
                    newprof.Real = False
                else:
                    # If updating a professor and changing from virtual to real check for scheduling
                    # conflicts.  If any exist do not allow the change/
                    newprof.Real = True
                    if self.editmode:
                        for prof in self.mainapp.faculty:
                            if prof.getName() == newprof.getName():
                                if self.mainapp.CheckAllRoomTimeslotConflictForProf(prof):
                                    messagestr = "The professor in position " + str(index + 1) + " "
                                    messagestr += "cannot be set to a real faculty member.  "
                                    messagestr += "There are currently conflicting course times for this faculty member "
                                    messagestr += "which will need to be removed before converting this person "
                                    messagestr += "to a real professor."
                                    QMessageBox.warning(self, "Professor Time Conflicts", messagestr, QMessageBox.Ok)
                                    return False

                # Check for unique name, and flag duplicates.
                newfacultyvalid = True
                if self.editmode:
                    for facmem in self.mainapp.faculty:
                        if (facmem.getName() == newprof.getName() or facmem.ShortDes == newprof.ShortDes) and (
                                facmem.InternalID != self.editID):
                            newfacultyvalid = False
                else:
                    for facmem in self.mainapp.faculty:
                        if facmem.getName() == newprof.getName() or facmem.ShortDes == newprof.ShortDes:
                            newfacultyvalid = False

                if not newfacultyvalid:
                    messagestr = "The faculty member " + newprof.getName() + ", or their short designation, "
                    messagestr += "is a duplicate of a professor already in the database."
                    QMessageBox.warning(self, "Duplicate Professor", messagestr, QMessageBox.Ok)
                    return False

        return True


class TimeslotDialog(QDialog):
    """
    Used for input of new standard timeslots and editing existing ones.  Uses a table format for
    input and has functions for checking validity of the input data.
    """

    def __init__(self, parent=None, title="Add New Timeslots", datatoload=[]):
        """
        Sets up the UI for the dialog.

        :param parent: Link to the calling control, which must be the main app.
        :param title: Title to put on the dialog.
        :param datatoload: Data of an existing timeslot, used when editing.
        """
        super().__init__(parent)
        self.Parent = parent
        self.mainapp = parent

        self.setWindowTitle(title)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.table_widget = LC_Table(self)
        if len(datatoload) == 0:
            self.table_widget.resizeTable(100, 5)
        else:
            self.table_widget.resizeTable(1, 5)
            for j in range(5):
                self.table_widget.setItem(0, j, QTableWidgetItem(datatoload[j]))

        self.table_widget.setLables(["Days *", "Start Hour *", "Start Minute *", "End Hour *", "End Minute *"])
        self.table_widget.resizeColumnsToContents()
        self.table_widget.resizeRowsToContents()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.table_widget)
        self.layout.addWidget(self.buttonBox)
        self.layout.setContentsMargins(5,5,5,5)
        self.setLayout(self.layout)
        self.setMinimumWidth(625)

    def accept(self):
        """
        Override on dialog acceptance to check the input data before accepting the new or edited slots.
        """
        if self.CheckTimeslot():
            super().accept()

    def CheckTimeslot(self) -> bool:
        """
        Checks all the input data for valid inputs and displays messages for anything that is invalid.  If
        all checks out the function returns true and if not the function returns false.

        :return: Boolean which is true if the data is valid and false if not.
        """

        data = self.table_widget.getTableContents()

        index = -1
        for item in data:
            index += 1
            for i in range(5):
                item[i] = item[i].lstrip().rstrip()

            # Determine if a row has been started, blank rows are ignored.  If started we do data validation.
            started = False
            for field in item:
                if field != "":
                    started = True

            # Determine if all required fields are filled in.
            if started:
                valid = True
                for field in item:
                    if field == "":
                        valid = False

                if not valid:
                    messagestr = "There are unfilled fields in position " + str(index + 1) + ".  "
                    messagestr += "All fields must be filled in."
                    QMessageBox.warning(self, "Unfilled Fields", messagestr, QMessageBox.Ok)
                    return False

                item[0] = item[0].upper()

                # Check if the numeric fields are in fact numeric.
                try:
                    val = int(item[1])
                except Exception as e:
                    messagestr = "The Start Hour in position " + str(index + 1) + " "
                    messagestr += "must be numeric."
                    QMessageBox.warning(self, "Invalid Field", messagestr, QMessageBox.Ok)
                    return False

                try:
                    val = int(item[2])
                except Exception as e:
                    messagestr = "The Start Minute in position " + str(index + 1) + " "
                    messagestr += "must be numeric."
                    QMessageBox.warning(self, "Invalid Field", messagestr, QMessageBox.Ok)
                    return False

                try:
                    val = int(item[3])
                except Exception as e:
                    messagestr = "The End Hour in position " + str(index + 1) + " "
                    messagestr += "must be numeric."
                    QMessageBox.warning(self, "Invalid Field", messagestr, QMessageBox.Ok)
                    return False

                try:
                    val = int(item[4])
                except Exception as e:
                    messagestr = "The End Minute in position " + str(index + 1) + " "
                    messagestr += "must be numeric."
                    QMessageBox.warning(self, "Invalid Field", messagestr, QMessageBox.Ok)
                    return False

                if not (0 <= int(item[1]) <= 23):
                    messagestr = "The Start Hour in position " + str(index + 1) + " "
                    messagestr += "must be between 0 and 23."
                    QMessageBox.warning(self, "Invalid Field", messagestr, QMessageBox.Ok)
                    return False

                # Check if hour and minute values are in the correct ranges.
                if not (0 <= int(item[2]) <= 59):
                    messagestr = "The Start Minute in position " + str(index + 1) + " "
                    messagestr += "must be between 0 and 59."
                    QMessageBox.warning(self, "Invalid Field", messagestr, QMessageBox.Ok)
                    return False

                if not (0 <= int(item[3]) <= 23):
                    messagestr = "The End Hour in position " + str(index + 1) + " "
                    messagestr += "must be between 0 and 23."
                    QMessageBox.warning(self, "Invalid Field", messagestr, QMessageBox.Ok)
                    return False

                if not (0 <= int(item[4]) <= 59):
                    messagestr = "The End Minute in position " + str(index + 1) + " "
                    messagestr += "must be between 0 and 59."
                    QMessageBox.warning(self, "Invalid Field", messagestr, QMessageBox.Ok)
                    return False

                # Check days to verify they are in the correct set.
                for ch in item[0]:
                    if ch not in "MTWRFSU":
                        messagestr = "The Days in position " + str(index + 1) + " "
                        messagestr += "must be between in the set {M, T, W, R, F, S, U}."
                        QMessageBox.warning(self, "Invalid Field", messagestr, QMessageBox.Ok)
                        return False

                # Check for unique timeslot
                newslot = TimeSlot()
                newslot.setData(item[0].upper(), int(item[1]), int(item[2]), int(item[3]), int(item[4]))

                newslotvalid = True
                for slot in self.mainapp.standardtimeslots:
                    if newslot.equals(slot):
                        newslotvalid = False

                if not newslotvalid:
                    messagestr = "The timeslot in position " + str(index + 1) + " "
                    messagestr += "is a duplicate of a timeslot that is already in the database."
                    QMessageBox.warning(self, "Timeslot Duplicate", messagestr, QMessageBox.Ok)
                    return False

        return True


class SectionNumberDialog(QDialog):
    """
    Used for mass changing of section numbers, subtitles, and designations.
    """

    def __init__(self, parent=None, title="Edit Section Numbers, Subtitles, and Designations", datatoload=[]):
        """
        Sets up the window UI and loads in the data to the table.

        :param parent: Link to the calling control, which must be the main app.
        :param title: Title to put on the dialog.
        :param datatoload: Data of all existing class names, sections, subtitles, and designations.
        """
        super().__init__(parent)
        self.Parent = parent
        self.mainapp = parent

        if len(datatoload) == 0:
            return

        self.setWindowTitle(title)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        copybutton = QPushButton(QIcon(parent.resource_path('icons/copy.png')), "Copy &All", self)
        copybutton.clicked.connect(self.onCopy)

        buttonBox.addButton(copybutton, QDialogButtonBox.ActionRole)

        self.table_widget = LC_Table(self)
        self.table_widget.resizeTable(len(datatoload), 3)

        edititems = []
        for items in datatoload:
            edititems.append(items[1:])

        self.classLables = []
        for items in datatoload:
            self.classLables.append(items[0])

        self.table_widget.setLables(["Section *", "Subtitle", "Designations"], self.classLables)
        self.table_widget.loadItems(edititems)
        self.table_widget.resizeColumnsToContents()
        self.table_widget.resizeRowsToContents()
        self.table_widget.setColumnWidth(1, 250)
        self.table_widget.setColumnWidth(2, 250)

        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)
        layout.addWidget(buttonBox)
        layout.setContentsMargins(5,5,5,5)
        self.setLayout(layout)
        self.setMinimumWidth(625)

    def onCopy(self):
        """
        Copies the text to the clipboard.
        """
        copystr = ""
        data = self.table_widget.getTableContents()
        copystr += "Class\tNew Section\tSubtitle\tDesignations\n"
        try:
            for i in range(len(data)):
                copystr += self.classLables[i] + "\t"
                for j in range(len(data[0])):
                    copystr += data[i][j] + "\t"
                copystr += "\n"
        except Exception as e:
            copystr = ""

        clipboard = QApplication.clipboard()
        clipboard.setText(copystr)

    def accept(self):
        """
        Override on dialog acceptance to check the input data before accepting the new or edited slots.
        """
        if self.CheckSections():
            super().accept()

    def CheckSections(self) -> bool:
        """
        Checks all the input data for valid inputs and displays messages for anything that is invalid.  If
        all checks out the function returns true and if not the function returns false.

        :return: Boolean which is true if the data is valid and false if not.
        """

        # Create lists of the courses and new section numbers.
        data = self.table_widget.getTableContents()
        newsections = [data[i][0] for i in range(len(data))]
        newcourse = [self.classLables[i].split("-")[0] for i in range(len(self.classLables))]

        for i in range(len(newsections)):
            if not newsections[i]:
                newsections[i] = ""
            else:
                newsections[i] = self.mainapp.removeColon(self.mainapp.removeWhitespace(newsections[i]))

        # Length check of courses and sections, this should never be unequal, just a validity
        # check for the rest of the function.
        if len(newsections) != len(newcourse):
            messagestr = "There is an error in the section numbers column."
            QMessageBox.warning(self, "Section Numbers Error", messagestr, QMessageBox.Ok)
            return False

        # Check for any blank entries in the section numbers.
        badindex = -1
        for i in range(len(newsections)):
            if not newsections[i]:
                badindex = i
            elif newsections[i] == "":
                badindex = i

        if badindex >= 0:
            messagestr = "There is a blank section number in row " + str(badindex + 1) + "."
            QMessageBox.warning(self, "Section Numbers Error", messagestr, QMessageBox.Ok)
            return False

        # Create new list of courses and sections list.
        newcoursesectionlist = [newcourse[i] + "-" + newsections[i] for i in range(len(newcourse))]

        # Check for duplicates.
        dups = set()
        for item in newcoursesectionlist:
            if newcoursesectionlist.count(item) > 1:
                dups.add(item)

        duplist = []
        while len(dups) > 0:
            duplist.append(dups.pop())

        duplist.sort()
        if len(duplist) > 0:
            dupstr = ""
            for i in range(len(duplist)):
                dupstr += duplist[i]
                if i == len(duplist) - 1:
                    dupstr += "."
                else:
                    dupstr += ", "
            messagestr = "There are duplicate section numbers in the list: " + dupstr
            QMessageBox.warning(self, "Duplicate Section Numbers", messagestr, QMessageBox.Ok)
            return False

        return True


class RoomsDialog(QDialog):
    """
    Used for creating new rooms and editing existing ones.  Uses a table format for
    input and has functions for checking validity of the input data.
    """

    def __init__(self, parent=None, title="Add New Rooms", datatoload=[], id=-1):
        """
        Sets up the UI for the dialog.

        :param parent: Link to the calling control, which must be the main app.
        :param title: Title to put on the dialog.
        :param datatoload: Data of an existing room, used when editing a room.
        :param id: Rooms's internal id. This is to set an index the edited room for the main app
                             to change the correct room.
        """

        super().__init__(parent)
        self.Parent = parent
        self.mainapp = parent

        self.setWindowTitle(title)
        self.editmode = False
        self.editID = id

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.table_widget = LC_Table(self)
        if len(datatoload) == 0:
            self.table_widget.resizeTable(100, 5)
        else:
            self.table_widget.resizeTable(1, 5)
            self.editmode = True
            for j in range(5):
                self.table_widget.setItem(0, j, QTableWidgetItem(datatoload[j]))

        self.table_widget.setLables(["Building *", "Room Number *", "Capacity *", "Designation", "Real (Y/n)"])
        self.table_widget.resizeColumnsToContents()
        self.table_widget.resizeRowsToContents()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.table_widget)
        self.layout.addWidget(self.buttonBox)
        self.layout.setContentsMargins(5,5,5,5)
        self.setLayout(self.layout)
        self.setMinimumWidth(625)

    def accept(self):
        """
        Override on dialog acceptance to check the input data before accepting the new or edited slots.
        """
        if self.CheckRooms():
            super().accept()

    def CheckRooms(self) -> bool:
        """
        Checks all the input data for valid inputs and displays messages for anything that is invalid.  If
        all checks out the function returns true and if not the function returns false.

        :return: Boolean which is true if the data is valid and false if not.
        """

        data = self.table_widget.getTableContents()

        index = -1
        for item in data:
            index += 1
            for i in range(5):
                item[i] = item[i].lstrip().rstrip()

            # Determine if a row has been started, blank rows are ignored.  If started we do data validation.
            started = False
            for field in item:
                if field != "":
                    started = True

            if started:
                # Determine if all required fields are filled in.
                valid = True
                for i in range(3):
                    if item[i] == "":
                        valid = False

                if not valid:
                    messagestr = "There are unfilled fields in position " + str(index + 1) + ".  "
                    messagestr += "The Building, Room Number, and Capacity fields must be filled in."
                    QMessageBox.warning(self, "Unfilled Fields", messagestr, QMessageBox.Ok)
                    return False

                # Check if the Capacity is numeric.
                try:
                    val = int(item[2])
                except Exception as e:
                    messagestr = "The Capacity in position " + str(index + 1) + " "
                    messagestr += "must be numeric."
                    QMessageBox.warning(self, "Invalid Field", messagestr, QMessageBox.Ok)
                    return False

                # Create new room for data checking.
                newroom = Room()
                item[0] = self.mainapp.removeColon(self.mainapp.removeWhitespace(item[0]).upper())
                item[1] = self.mainapp.removeColon(self.mainapp.removeWhitespace(item[1]))

                newroom.Building = item[0]
                newroom.RoomNumber = item[1]
                newroom.Capacity = int(item[2])
                if newroom.Capacity < 0:
                    newroom.Capacity = 0
                newroom.Special = item[3]
                if item[4].upper() == "N":
                    newroom.Real = False
                else:
                    # If updating a room and changing from virtual to real check for scheduling
                    # conflicts.  If any exist do not allow the change.
                    newroom.Real = True
                    if self.editmode:
                        for room in self.mainapp.rooms:
                            if room.getName() == newroom.getName():
                                if self.mainapp.CheckAllRoomTimeslotConflictForRoom(room):
                                    messagestr = "The room in position " + str(index + 1) + " "
                                    messagestr += "cannot be set to a real room.  "
                                    messagestr += "There are currently conflicting course times in this room which will "
                                    messagestr += "need to be removed before converting this to a real room."
                                    QMessageBox.warning(self, "Course Time Conflicts", messagestr, QMessageBox.Ok)
                                    return False

                # Check for duplicates.
                newroomvalid = True
                if self.editmode:
                    for room in self.mainapp.rooms:
                        if (room.getName() == newroom.getName()) and (room.InternalID != self.editID):
                            newroomvalid = False
                else:
                    for room in self.mainapp.rooms:
                        if room.getName() == newroom.getName():
                            newroomvalid = False

                if not newroomvalid:
                    messagestr = "The room in position " + str(index + 1) + " "
                    messagestr += "is a duplicate of a room that is already in the database."
                    QMessageBox.warning(self, "Room Duplicate", messagestr, QMessageBox.Ok)
                    return False

        return True


class TextBrowserView(QTextBrowser):
    def __init__(self, parent=None):
        super(TextBrowserView, self).__init__(parent)

    def wheelEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if not (modifiers & Qt.ControlModifier):
            QTextBrowser.wheelEvent(self, event)


class HTMLViewer(QDialog):
    def __init__(self, parent=None, title="", htmltext=""):
        """
        Sets up the UI, additional buttons and loads the html into the viewer widget.

        :param parent: Link to the calling control, which must be the main app.
        :param title: Title to put on the dialog.
        :param htmltext: HTML text to be loaded into the viewer.
        """
        super(HTMLViewer, self).__init__(parent)

        if title == "":
            title = "Report"

        self.setWindowTitle(title)

        QBtn = QDialogButtonBox.Ok
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        self.view = TextBrowserView()
        self.view.setContextMenuPolicy(Qt.PreventContextMenu)
        self.view.setHtml(htmltext)

        exportbutton = QPushButton(QIcon(parent.resource_path('icons/FileSave.png')), "&Export to PDF...", self)
        exportbutton.clicked.connect(self.saveFile)

        printbutton = QPushButton(QIcon(parent.resource_path('icons/print.png')), "&Print...", self)
        printbutton.clicked.connect(self.printFile)

        self.buttonBox.addButton(printbutton, QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(exportbutton, QDialogButtonBox.ActionRole)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.view)
        self.layout.addWidget(self.buttonBox)
        self.layout.setContentsMargins(5,5,5,5)
        self.setLayout(self.layout)
        self.setMinimumSize(600, 600)

    def printFile(self):
        """
        Prints the document to the selected printer.
        """
        printer = QPrinter()
        dialog = QPrintDialog(printer)
        printer.setDocName("Report")
        printer.setResolution(300)
        if dialog.exec() == QDialog.Accepted:
            self.view.document().print_(printer)

    def saveFile(self):
        """
        Saves the document as a PDF file.
        """
        dialog = QFileDialog()
        dialog.setFilter(dialog.filter() | QDir.Hidden)
        dialog.setDefaultSuffix('pdf')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters(['PDF Files (*.pdf)'])
        dialog.setWindowTitle('Export to PDF')

        if dialog.exec() == QDialog.Accepted:
            filelist = dialog.selectedFiles()
            if len(filelist) > 0:
                file_name = filelist[0]
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(file_name)
                self.view.document().print_(printer)


class TextViewer(QDialog):
    """
    Was to be used for the plaintext document type reports but was not implemented into the system due to
    the creation of the HTML viewer.  The dialog remains in the system for possible future use.
    The dialog has the additional functionality of printing, saving, and copying the document.

    Note that this was not implemented mainly because on a Ctrl+Scroll which resizes the font the
    text widget got stuck wne the minimum size was reached.  The program then locked and crashed.
    """

    def __init__(self, parent=None, title="", text=""):
        """
        Sets up the UI, additional buttons and loads the text into the viewer widget.

        :param parent: Link to the calling control, which must be the main app.
        :param title: Title to put on the dialog.
        :param text: text to be loaded into the viewer.
        """
        super().__init__(parent)

        if title == "":
            title = "Report"

        self.setWindowTitle(title)

        QBtn = QDialogButtonBox.Ok
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        self.view = QTextBrowser()
        self.view.setContextMenuPolicy(Qt.PreventContextMenu)
        self.view.setText(text)

        copybutton = QPushButton(QIcon(parent.resource_path('icons/copy.png')), "&Copy All", self)
        copybutton.clicked.connect(self.onCopy)

        exportbutton = QPushButton(QIcon(parent.resource_path('icons/FileSave.png')), "&Save As...", self)
        exportbutton.clicked.connect(self.saveFile)

        printbutton = QPushButton(QIcon(parent.resource_path('icons/print.png')), "&Print...", self)
        printbutton.clicked.connect(self.printReport)

        printpreviewbutton = QPushButton(QIcon(parent.resource_path('icons/preview.png')), "Print Pre&view...", self)
        printpreviewbutton.clicked.connect(self.printPreview)

        self.buttonBox.addButton(printbutton, QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(printpreviewbutton, QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(copybutton, QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(exportbutton, QDialogButtonBox.ActionRole)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.view)
        self.layout.addWidget(self.buttonBox)
        self.layout.setContentsMargins(5,5,5,5)
        self.setLayout(self.layout)
        self.setMinimumSize(600, 600)

    def saveFile(self):
        """
        Saves the text to a text file.
        """
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
                file = open(file_name, 'w')
                file.write(self.view.toPlainText())

    def printReport(self):
        """
        Prints the text to the selected printer.
        """
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        printer.setDocName("Report")
        printer.setResolution(300)
        if dialog.exec() == QDialog.Accepted:
            self.view.print_(printer)

    def printPreview(self):
        """
        Invokes the print preview dialog.
        """
        printer = QPrinter()
        dialog = QPrintPreviewDialog(printer)
        printer.setDocName("Report")
        printer.setResolution(300)
        dialog.paintRequested.connect(self.printPreviewDoc)
        dialog.exec()

    def printPreviewDoc(self, printer):
        """
        Support function for print preview.

        :param printer: Printer device.
        """
        self.view.print_(printer)

    def onCopy(self):
        """
        Copies the text to the clipboard.
        """
        clipboard = QApplication.clipboard()
        clipboard.setText(self.view.toPlainText())


class GeneralTableDialog(QDialog):
    """
    Used for table type reports.  Takes as parameters the dialog title, list of lists (2D Array)
    of table content, and a list of column headers. The dialog has the additional functionality of
    copying the table contents as a tab delimited table that can be loaded directly into most
    spreadsheet programs.
    """

    def __init__(self, parent=None, title="Report", datatoload=[], colheaders=[]):
        """
        Sets up the UI, adds the additional buttons and loads in the headers and data for the
        table.

        :param parent: Link to the calling control, which must be the main app.
        :param title: Title to put on the dialog.
        :param datatoload: Data to be loaded into the grid.
        :param colheaders: List of column headers to display at the top of the grid.
        """
        super().__init__(parent)
        self.Parent = parent
        self.mainapp = parent
        self.setWindowTitle(title)

        self.data = datatoload
        self.headers = colheaders

        QBtn = QDialogButtonBox.Ok

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        self.table_widget = LC_Table(self)
        self.table_widget.resizeTable(len(datatoload), len(datatoload[0]))
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        if colheaders != []:
            self.table_widget.setLables(colheaders)

        for i in range(len(datatoload)):
            for j in range(len(datatoload[0])):
                self.table_widget.setItem(i, j, QTableWidgetItem(datatoload[i][j]))

        self.table_widget.resizeColumnsToContents()
        self.table_widget.resizeRowsToContents()

        copybutton = QPushButton(QIcon(parent.resource_path('icons/copy.png')), "&Copy All", self)
        copybutton.clicked.connect(self.onCopy)

        self.buttonBox.addButton(copybutton, QDialogButtonBox.ActionRole)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.table_widget)
        self.layout.addWidget(self.buttonBox)
        self.layout.setContentsMargins(5,5,5,5)
        self.setLayout(self.layout)
        self.setMinimumWidth(625)

    def onCopy(self):
        """
        Copies to the clipboard the entire grid, including column headers, as tab delimited
        text that can be loaded into any spreadsheet.
        """
        copystr = ""
        try:
            if self.headers != []:
                for item in self.headers:
                    copystr += item + "\t"

            copystr += "\n"

            for i in range(len(self.data)):
                for j in range(len(self.data[0])):
                    copystr += self.data[i][j] + "\t"
                copystr += "\n"
        except Exception as e:
            copystr = ""

        clipboard = QApplication.clipboard()
        clipboard.setText(copystr)


class ImagePrintOptions(QDialog):
    """
    Simple dialog for the user to select options for printing images, image size and scaling
    options.
    """

    def __init__(self, parent=None, title="Image Printing Options", datatoload=[]):
        """
        Sets up the UI for the dialog.

        :param parent: Link to the calling control, which must be the main app.
        :param title: Title to put on the dialog.
        :param datatoload: Imapge printing data to be loaded into the controls.
        """
        super().__init__(parent)

        if datatoload == []:
            datatoload = [7.5, 5, 0]

        self.setWindowTitle(title)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.HeightToWidthRB = QRadioButton("Scale Height to Width")
        self.WidthToHeightRB = QRadioButton("Scale Width to Height")
        self.NoScaleRB = QRadioButton("No Scaling")

        ScaleButtonGroup = QButtonGroup(self)
        ScaleButtonGroup.addButton(self.HeightToWidthRB)
        ScaleButtonGroup.addButton(self.WidthToHeightRB)
        ScaleButtonGroup.addButton(self.NoScaleRB)

        if datatoload[2] == 0:
            self.HeightToWidthRB.setChecked(True)
        elif datatoload[2] == 1:
            self.WidthToHeightRB.setChecked(True)
        else:
            self.NoScaleRB.setChecked(True)

        sizeslayout = QHBoxLayout()
        l1 = QLabel("Width (in.): ")
        sizeslayout.addWidget(l1)
        self.widthvalue = QDoubleSpinBox()
        self.widthvalue.setRange(1.0, 100.0)
        self.widthvalue.setSingleStep(0.01)
        self.widthvalue.setValue(datatoload[0])
        sizeslayout.addWidget(self.widthvalue)

        l2 = QLabel("Height (in.): ")
        sizeslayout.addWidget(l2)
        self.heightvalue = QDoubleSpinBox()
        self.heightvalue.setRange(1.0, 100.0)
        self.heightvalue.setSingleStep(0.01)
        self.heightvalue.setValue(datatoload[1])
        sizeslayout.addWidget(self.heightvalue)
        sizeslayout.addStretch(1)

        self.layout = QVBoxLayout()
        self.layout.addLayout(sizeslayout)
        self.layout.addWidget(self.HeightToWidthRB)
        self.layout.addWidget(self.WidthToHeightRB)
        self.layout.addWidget(self.NoScaleRB)

        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
        self.adjustSize()
        self.setFixedSize(self.size())


class GenSeparator(QFrame):
    """
    Simple class for the creation of a horizontal line on the dialog.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)


class MinuteSpinBox(QSpinBox):
    """
    Simple derived class of an integer spin box that restricts the values between 0 and 59.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 59)

    def textFromValue(self, value):
        return "%02d" % value


class RoomTimeDialogInfo(QDialog):
    """
    Dialog for selecting a room, days, and times for class meeting times.  There is a dropdown for
    the rooms, taken from the room database of the main program, check boxes for the days, and spin
    boxes for the times.
    """

    def __init__(self, parent=None, title="Room and Time Selection", roomlist=[], editroomtime=None):
        """
        Sets up the UI and loads in the data to the dialog.

        :param parent: Link to the calling control.
        :param title: Title to put on the dialog.
        :param roomlist: List of rooms to display in the dropdown selector in the dialog.
        :param editroomtime: Room and time data for editing.
        """
        super().__init__(parent)
        self.setWindowTitle(title)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        buttonBox.button(QDialogButtonBox.Cancel).setAutoDefault(True)
        buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)

        self.RoomListBox = QComboBox()
        for room in roomlist:
            self.RoomListBox.addItem(room)

        roomlistlayout = QHBoxLayout()
        roomlistlayout.addWidget(QLabel("Room: "))
        roomlistlayout.addWidget(self.RoomListBox)
        roomlistlayout.addStretch(0)

        self.MondayCB = QCheckBox("Monday")
        self.TuesdayCB = QCheckBox("Tuesday")
        self.WednesdayCB = QCheckBox("Wednesday")
        self.ThursdayCB = QCheckBox("Thursday")
        self.FridayCB = QCheckBox("Friday")
        self.SaturdayCB = QCheckBox("Saturday")
        self.SundayCB = QCheckBox("Sunday")

        dayslayout = QHBoxLayout()
        daysleftlayout = QVBoxLayout()
        daysleftlayout.addWidget(self.MondayCB)
        daysleftlayout.addWidget(self.WednesdayCB)
        daysleftlayout.addWidget(self.FridayCB)
        daysleftlayout.addWidget(self.SaturdayCB)

        daysrightlayout = QVBoxLayout()
        daysrightlayout.addWidget(self.TuesdayCB)
        daysrightlayout.addWidget(self.ThursdayCB)
        daysrightlayout.addStretch(0)
        daysrightlayout.addWidget(self.SundayCB)

        dayslayout.addLayout(daysleftlayout)
        dayslayout.addLayout(daysrightlayout)

        dayslabel = QLabel("Meeting Days")
        daysfont = dayslabel.font()
        daysfont.setUnderline(True)
        dayslabel.setFont(daysfont)

        alldaysleftlayout = QVBoxLayout()
        alldaysleftlayout.addWidget(GenSeparator())
        alldaysleftlayout.addWidget(dayslabel)
        alldaysleftlayout.addLayout(dayslayout)
        alldaysleftlayout.addWidget(GenSeparator())

        timeslabel = QLabel("Meeting Times")
        timesfont = timeslabel.font()
        timesfont.setUnderline(True)
        timeslabel.setFont(timesfont)

        starttimelayout = QHBoxLayout()
        starttimelayout.addWidget(QLabel("Start Time: "))
        self.starthourinput = QSpinBox()
        self.starthourinput.setMinimum(0)
        self.starthourinput.setMaximum(23)
        starttimelayout.addWidget(self.starthourinput)
        starttimelayout.addWidget(QLabel(":"))
        self.startminuteinput = MinuteSpinBox()
        starttimelayout.addWidget(self.startminuteinput)
        starttimelayout.addStretch(0)

        endtimelayout = QHBoxLayout()
        endtimelayout.addWidget(QLabel("End Time: "))
        self.endhourinput = QSpinBox()
        self.endhourinput.setMinimum(0)
        self.endhourinput.setMaximum(23)
        endtimelayout.addWidget(self.endhourinput)
        endtimelayout.addWidget(QLabel(":"))
        self.endminuteinput = MinuteSpinBox()
        endtimelayout.addWidget(self.endminuteinput)
        endtimelayout.addStretch(0)

        timeslayout = QVBoxLayout()
        timeslayout.addWidget(timeslabel)
        timeslayout.addLayout(starttimelayout)
        timeslayout.addLayout(endtimelayout)

        if editroomtime:
            self.RoomListBox.setCurrentText(editroomtime[0])
            timeslot = editroomtime[1]
            self.MondayCB.setChecked("M" in timeslot.Days)
            self.TuesdayCB.setChecked("T" in timeslot.Days)
            self.WednesdayCB.setChecked("W" in timeslot.Days)
            self.ThursdayCB.setChecked("R" in timeslot.Days)
            self.FridayCB.setChecked("F" in timeslot.Days)
            self.SaturdayCB.setChecked("S" in timeslot.Days)
            self.SundayCB.setChecked("U" in timeslot.Days)
            self.starthourinput.setValue(timeslot.StartHour)
            self.startminuteinput.setValue(timeslot.StartMinute)
            self.endhourinput.setValue(timeslot.EndHour)
            self.endminuteinput.setValue(timeslot.EndMinute)

        centerlayout = QVBoxLayout()
        centerlayout.addLayout(roomlistlayout)
        centerlayout.addLayout(alldaysleftlayout)
        centerlayout.addLayout(timeslayout)
        centerlayout.addWidget(buttonBox)
        self.setLayout(centerlayout)
        self.adjustSize()
        self.setFixedSize(self.size())

    def getDayString(self) -> str:
        """
        Returns a string representing the days for the timeslot.

        :return: String representing the days for the timeslot.
        """
        retstr = ""
        if self.MondayCB.isChecked():
            retstr += "M"
        if self.TuesdayCB.isChecked():
            retstr += "T"
        if self.WednesdayCB.isChecked():
            retstr += "W"
        if self.ThursdayCB.isChecked():
            retstr += "R"
        if self.FridayCB.isChecked():
            retstr += "F"
        if self.SaturdayCB.isChecked():
            retstr += "S"
        if self.SundayCB.isChecked():
            retstr += "U"
        return retstr

    def getRoomString(self) -> str:
        """
        Returns a string representing the room.

        :return: String representing the room.
        """
        return self.RoomListBox.currentText()

    def getTimes(self) -> [int]:
        """
        Returns a list of integers representing the hour and minute of the start and end times.

        :return: A list of integers representing the hour and minute of the start and end times.
        """
        return self.starthourinput.value(), self.startminuteinput.value(), self.endhourinput.value(), self.endminuteinput.value()


class CourseOptions(QDialog):
    """
    This is the course information dialog that is invoked from numerous places in the program.
    The course information dialog contains options for changing all aspects of the schedule item, instructor,
    meeting times, section number, course, tentative, subtitles, and designations. The course selection
    is done through a dropdown linked to the course database, the instructor and timeslots list have
    toolbars to the side to add, edit, and delete.  The section, subtitle, and designations are free-form
    text.  The tentative are yes/no radio buttons.  This dialog is linked to the main app so that it can
    check all changes as they are made.  It also has options for checking if a section number is valid and
    for generating an unused section number.
    """

    def __init__(self, parent=None, title="Course Information", paramSI=None):
        """
        Sets up the UI for the dialog and loads the schedule item data.

        :param parent: Link to calling object, must be the main app.
        :param title: Title for the dialog.
        :param paramSI: Schedule item to be loaded and edited.
        """

        super().__init__(parent)
        self.thisSI = copy.deepcopy(paramSI)
        self.setWindowTitle(title)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        buttonBox.button(QDialogButtonBox.Cancel).setAutoDefault(True)
        buttonBox.button(QDialogButtonBox.Cancel).setDefault(True)

        self.courseList = QComboBox()

        # Load course list from main app into course selection dropdown.  Find index
        # of schedule item's course and set.
        thiscoursestr = self.parent().findCourseFromIID(self.thisSI.CourseIID).getName()
        index = 0
        i = 0
        for tempcourse in self.parent().courses:
            self.courseList.addItem(tempcourse.getDisplayStringNoLoad())
            if tempcourse.getName() == thiscoursestr:
                index = i
            i += 1

        self.courseList.setCurrentIndex(index)
        courselayout = QHBoxLayout()
        courselayout.addWidget(QLabel("Course: "))
        courselayout.addWidget(self.courseList)
        courselayout.addStretch(1)

        # Create two buttons for the section number.  One to check validity and the other to
        # auto-generate a valid section number.
        self.CheckSectionNumberTool = QAction(QIcon(self.parent().resource_path('icons/Check.png')),
                                              "Check Section Number...", self)
        self.CheckSectionNumberTool.triggered.connect(self.CheckSection)

        self.GenerateSectionNumberTool = QAction(QIcon(self.parent().resource_path('icons/copylatex2.png')),
                                                 "Generate Section Number", self)
        self.GenerateSectionNumberTool.triggered.connect(self.GenSection)

        section_tool_bar = QToolBar("Section Number Toolbar")
        section_tool_bar.setIconSize(QSize(16, 16))
        section_tool_bar.addAction(self.CheckSectionNumberTool)
        section_tool_bar.addAction(self.GenerateSectionNumberTool)
        section_tool_bar.adjustSize()

        # Set up section number UI.
        self.sectionnumberedit = QLineEdit(self.thisSI.Section)
        self.sectionnumberedit.setMinimumWidth(100)
        sectionnumberlayout = QHBoxLayout()
        sectionnumberlayout.addWidget(QLabel("Section Number: "))
        sectionnumberlayout.addWidget(self.sectionnumberedit)
        sectionnumberlayout.addWidget(section_tool_bar)
        sectionnumberlayout.addStretch(1)

        # Set up subtitle UI.
        self.subtitleedit = QLineEdit(self.thisSI.Subtitle)
        self.subtitleedit.setMinimumWidth(400)
        subtitlelayout = QHBoxLayout()
        subtitlelayout.addWidget(QLabel("Subtitle: "))
        subtitlelayout.addWidget(self.subtitleedit)
        subtitlelayout.addStretch(1)

        # Set up designation UI.
        self.designationsedit = QLineEdit(self.thisSI.Designation)
        self.designationsedit.setMinimumWidth(400)
        designationslayout = QHBoxLayout()
        designationslayout.addWidget(QLabel("Designations: "))
        designationslayout.addWidget(self.designationsedit)
        designationslayout.addStretch(1)

        # Yes/No button group for tentative.
        self.TentativeYes = QRadioButton("Yes")
        self.TentativeNo = QRadioButton("No")

        TentativeButtonGroup = QButtonGroup(self)
        TentativeButtonGroup.addButton(self.TentativeYes)
        TentativeButtonGroup.addButton(self.TentativeNo)

        if self.thisSI.Tentative:
            self.TentativeYes.setChecked(True)
        else:
            self.TentativeNo.setChecked(True)

        # set up UI for tentative.
        tentativelayout = QHBoxLayout()
        tentativelayout.addWidget(QLabel("Tentative: "))
        tentativelayout.addWidget(self.TentativeYes)
        tentativelayout.addWidget(self.TentativeNo)
        tentativelayout.addStretch(1)

        # Setup UI for contact minutes and scheduled minutes.
        self.MinutesPerWeek = QLabel(str(int(self.parent().findCourseFromIID(self.thisSI.CourseIID).Contact)))
        self.ScheduledMinutesPerWeek = QLabel(str(self.calculateScheduledMinutes()))
        self.updateScheduledMinutesPerWeek()
        self.updateMinutesPerWeek()

        MinutesPerWeeklayout = QHBoxLayout()
        MinutesPerWeeklayout.addWidget(QLabel("Minutes/Week: "))
        MinutesPerWeeklayout.addWidget(self.MinutesPerWeek)
        MinutesPerWeeklayout.addStretch(1)

        ScheduledMinutesPerWeeklayout = QHBoxLayout()
        ScheduledMinutesPerWeeklayout.addWidget(QLabel("Scheduled Minutes/Week: "))
        ScheduledMinutesPerWeeklayout.addWidget(self.ScheduledMinutesPerWeek)
        ScheduledMinutesPerWeeklayout.addStretch(1)

        # Setup UI for instructor toolbar and list.
        self.AddProf = QAction(QIcon(self.parent().resource_path('icons/NewFaculty.png')), "Add Instructor...", self)
        self.AddProf.triggered.connect(self.AddInstructor)

        self.EditProf = QAction(QIcon(self.parent().resource_path('icons/Preferences.png')), "Edit Instructor...", self)
        self.EditProf.triggered.connect(self.EditInstructor)

        self.DeleteProf = QAction(QIcon(self.parent().resource_path('icons/Delete.png')), "Delete Instructor...", self)
        self.DeleteProf.triggered.connect(self.DeleteInstructor)

        prof_tool_bar = QToolBar("Professor Toolbar")
        prof_tool_bar.setIconSize(QSize(20, 20))
        prof_tool_bar.addAction(self.AddProf)
        prof_tool_bar.addAction(self.EditProf)
        prof_tool_bar.addAction(self.DeleteProf)
        prof_tool_bar.setOrientation(Qt.Vertical)
        prof_tool_bar.adjustSize()

        self.instructorList = QListWidget()
        self.instructorList.setMaximumHeight(prof_tool_bar.height() + 10)
        self.instructorList.itemDoubleClicked.connect(self.EditInstructor)

        for profiid in self.thisSI.ProfessorIID:
            prof = self.parent().findProfessorFromIID(profiid)
            self.instructorList.addItem(prof.getName())

        instructorListlayout = QVBoxLayout()
        instructorlabel = QLabel("Course Instructors")
        labfont = instructorlabel.font()
        labfont.setUnderline(True)
        instructorlabel.setFont(labfont)
        instructorListlayout.addWidget(instructorlabel)

        instructorListTools = QHBoxLayout()
        instructorListTools.addWidget(prof_tool_bar)
        instructorListTools.addWidget(self.instructorList)
        instructorListlayout.addLayout(instructorListTools)

        # Setup UI for timeslot toolbar and list.
        self.AddRT = QAction(QIcon(self.parent().resource_path('icons/NewTimeslots.png')), "Add Room and Time...", self)
        self.AddRT.triggered.connect(self.AddDayTime)

        self.EditRT = QAction(QIcon(self.parent().resource_path('icons/Preferences.png')), "Edit Room and Time...",
                              self)
        self.EditRT.triggered.connect(self.EditDayTime)

        self.DeleteRT = QAction(QIcon(self.parent().resource_path('icons/Delete.png')), "Delete Room and Time...", self)
        self.DeleteRT.triggered.connect(self.DeleteDayTime)

        rt_tool_bar = QToolBar("Room and Time Toolbar")
        rt_tool_bar.setIconSize(QSize(20, 20))
        rt_tool_bar.addAction(self.AddRT)
        rt_tool_bar.addAction(self.EditRT)
        rt_tool_bar.addAction(self.DeleteRT)
        rt_tool_bar.setOrientation(Qt.Vertical)
        rt_tool_bar.adjustSize()

        self.DaysandTimesList = QListWidget()
        self.updateRoomsAndTimesList()
        self.DaysandTimesList.setMaximumHeight(rt_tool_bar.height() + 10)
        self.DaysandTimesList.itemDoubleClicked.connect(self.EditDayTime)

        DaysandTimesListlayout = QVBoxLayout()
        RTlabel = QLabel("Rooms and Times")
        labfont = RTlabel.font()
        labfont.setUnderline(True)
        RTlabel.setFont(labfont)
        DaysandTimesListlayout.addWidget(RTlabel)

        # Set up main window layout.
        DaysandTimesListTools = QHBoxLayout()
        DaysandTimesListTools.addWidget(self.DaysandTimesList)
        DaysandTimesListTools.addWidget(rt_tool_bar)
        DaysandTimesListlayout.addLayout(DaysandTimesListTools)

        infolayout = QHBoxLayout()
        infolayout.addLayout(instructorListlayout)
        infolayout.addLayout(DaysandTimesListlayout)

        centerlayout = QVBoxLayout()
        centerlayout.addLayout(courselayout)
        centerlayout.addLayout(sectionnumberlayout)
        centerlayout.addLayout(subtitlelayout)
        centerlayout.addLayout(designationslayout)
        centerlayout.addLayout(tentativelayout)

        centerlayout.addLayout(infolayout)

        centerlayout.addLayout(MinutesPerWeeklayout)
        centerlayout.addLayout(ScheduledMinutesPerWeeklayout)

        centerlayout.addWidget(buttonBox)
        self.setLayout(centerlayout)
        self.adjustSize()
        self.setFixedSize(self.size())

        self.courseList.activated.connect(self.updateMinutesPerWeek)
        self.sectionnumberedit.setFocus()

    def accept(self):
        """
        Override on dialog acceptance to check the input data before accepting the new or edited slots.
        """
        if self.CheckCourseInfo():
            super().accept()

    def CheckCourseInfo(self) -> bool:
        """
        Checks all the input data for valid inputs and displays messages for anything that is invalid.  If
        all checks out the function returns true and if not the function returns false.

        :return: Boolean which is true if the data is valid and false if not.
        """

        # Check that at least one professor is selected for the course.  Each schedule must have
        # a course (guaranteed by the dropdown) and a professor.
        if self.instructorList.count() == 0:
            QMessageBox.warning(self, "No Course Instructor", "The course must have an instructor.", QMessageBox.Ok)
            return False

        # Check that the section number is valid.
        sectionnumber, sectionnumberfound = self.parent().CheckSectionNumber(self.thisSI.CourseIID,
                                                                             self.sectionnumberedit.text(),
                                                                             [self.thisSI.InternalID])
        self.sectionnumberedit.setText(sectionnumber)
        if sectionnumberfound:
            QMessageBox.warning(self, "Section Number Conflict", "The section number conflicts with a current "
                                + "course. Please select a different section number.",
                                QMessageBox.Ok)
            return False

        return True

    def calculateScheduledMinutes(self) -> int:
        """
        Calculates and returns the number of minutes that the class is scheduled for.

        :return: The number of minutes that the class is scheduled for.
        """
        minutesschuled = 0
        for slot in self.thisSI.RoomsAndTimes:
            minutesschuled += slot[1].getMinutes()
        return minutesschuled

    def updateScheduledMinutesPerWeek(self):
        """
        Updates the label of the scheduled minutes.
        """
        self.ScheduledMinutesPerWeek.setText(str(self.calculateScheduledMinutes()))

    def updateMinutesPerWeek(self):
        """
        Updates the minutes per week label.  This is needed if a different course is selected from the
        dropdown course selector.
        """
        courseitemstr = self.courseList.currentText()
        coursestr = courseitemstr.split(":")[0]
        course = self.parent().findCourseFromString(coursestr)
        self.MinutesPerWeek.setText(str(int(course.Contact)))
        self.thisSI.CourseIID = course.InternalID

    def AddInstructor(self):
        """
        Adds an instructor to the instructor list.  It also verifies that the new instructor does
        not have a time conflict with the currently scheduled times of the class.  If they do,
        an error will be displayed and the instructor will not be added.
        """
        instructorNames = []
        for inst in self.parent().faculty:
            instructorNames.append(inst.getName())

        item, ok = QInputDialog.getItem(self, "Select Additional Instructor",
                                        "Select an instructor to add to the class:", instructorNames, 0, False)

        if ok and item:
            newprof = True
            for index in range(self.instructorList.count()):
                if self.instructorList.item(index).text() == item:
                    newprof = False

            if newprof:
                prof = self.parent().findProfessorFromString(item)
                times = []
                for roomtime in self.thisSI.RoomsAndTimes:
                    times.append(roomtime[1])

                # Use conflict checker in the main app to check timeslots.
                conflict = self.parent().professorTimeslotConflict(prof, times, [self.thisSI.InternalID])

                if conflict:
                    QMessageBox.warning(self, "Time Conflict", "The instructor " + item +
                                        " has a time conflict with the current scheduled times and cannot be added to the instructor list.",
                                        QMessageBox.Ok)
                else:
                    self.instructorList.addItem(item)
                    self.instructorList.sortItems(Qt.AscendingOrder)
                    self.thisSI.ProfessorIID.append(prof.InternalID)

    def EditInstructor(self):
        """
        Edits an instructor to the instructor list.  It also verifies that the new instructor does
        not have a time conflict with the currently scheduled times of the class.  If they do,
        an error will be displayed and the instructor will not be added.
        """
        if self.instructorList.selectedItems() != []:
            institem = self.instructorList.selectedItems()[0]
            instname = institem.text()
        else:
            return

        instructorNames = []
        for inst in self.parent().faculty:
            instructorNames.append(inst.getName())

        instpos = instructorNames.index(instname)
        item, ok = QInputDialog.getItem(self, "Select New Instructor",
                                        "Select a new instructor for the course:", instructorNames, instpos, False)

        if ok and item:
            oldprof = self.parent().findProfessorFromString(instname)
            prof = self.parent().findProfessorFromString(item)
            times = []
            for roomtime in self.thisSI.RoomsAndTimes:
                times.append(roomtime[1])

            # Use conflict checker in the main app to check timeslots.
            conflict = self.parent().professorTimeslotConflict(prof, times, [self.thisSI.InternalID])

            if conflict:
                QMessageBox.warning(self, "Time Conflict", "The instructor " + item +
                                    " has a time conflict with the current scheduled times and cannot be added to the instructor list.",
                                    QMessageBox.Ok)
            else:
                self.instructorList.takeItem(self.instructorList.row(institem))
                self.instructorList.addItem(item)
                self.instructorList.sortItems(Qt.AscendingOrder)
                self.thisSI.ProfessorIID.append(prof.InternalID)
                self.thisSI.ProfessorIID.remove(oldprof.InternalID)

    def DeleteInstructor(self):
        """
        Removes an instructor from the list.
        """
        item = self.instructorList.currentItem()
        if item:
            self.instructorList.takeItem(self.instructorList.row(item))
            prof = self.parent().findProfessorFromString(item.text())
            self.thisSI.ProfessorIID.remove(prof.InternalID)

    def updateRoomsAndTimesList(self):
        """
        Updates the rooms and times list.
        """
        self.DaysandTimesList.clear()
        timeslots = self.thisSI.RoomsAndTimes
        timeslotstring = ""
        minutes = 0
        for slot in timeslots:
            roomname = self.parent().findRoomFromIID(slot[0]).getName()
            timeslotstring = slot[1].getDescription() + " " + roomname
            self.DaysandTimesList.addItem(timeslotstring)
            minutes += slot[1].getMinutes()

        self.ScheduledMinutesPerWeek.setText(str(minutes))

    def AddDayTime(self):
        """
        Adds a timeslot to the list of scheduled rooms and times.
        """
        roomNames = []
        for room in self.parent().rooms:
            roomNames.append(room.getName())

        roomtimeselect = RoomTimeDialogInfo(self, "Add Room and Time", roomNames)

        # Check for conflicts with all currently scheduled classes and display an error if there
        # are scheduling conflicts.
        conflict = True
        while conflict:
            conflict = False
            if roomtimeselect.exec_():
                roomtext = roomtimeselect.getRoomString()
                daystext = roomtimeselect.getDayString()
                times = roomtimeselect.getTimes()
                roomid = self.parent().findRoomFromString(roomtext).InternalID
                newtimeslot = TimeSlot()
                newtimeslot.setData(daystext, times[0], times[1], times[2], times[3])
                roomtimelist = [roomid, newtimeslot]
                conflict = self.parent().RoomTimeslotConflict(roomtimelist, [self.thisSI.InternalID])

                for slot in self.thisSI.RoomsAndTimes:
                    if slot[1].overlap(newtimeslot):
                        conflict = True

                if conflict:
                    QMessageBox.warning(self, "Time Conflict", "The selected timeslot conflicts with the current "
                                        + "scheduled times and cannot be added to the course. Please select a "
                                        + "different room, days, and times.",
                                        QMessageBox.Ok)
                    roomtimeselect = RoomTimeDialogInfo(self, "Add Room and Time", roomNames, [roomtext, newtimeslot])
                else:
                    self.thisSI.RoomsAndTimes.append(roomtimelist)
                    self.updateRoomsAndTimesList()

    def EditDayTime(self):
        """
        Edits a current timeslot to the list of scheduled rooms and times.
        """
        if self.DaysandTimesList.selectedItems() != []:
            institem = self.DaysandTimesList.selectedItems()[0]
            itemindex = self.DaysandTimesList.row(institem)
        else:
            return

        roomNames = []
        for room in self.parent().rooms:
            roomNames.append(room.getName())

        roomandtimetoedit = self.thisSI.RoomsAndTimes[itemindex]
        roomandtimeeditlist = []
        roomandtimeeditlist.append(self.parent().findRoomFromIID(roomandtimetoedit[0]).getName())
        roomandtimeeditlist.append(roomandtimetoedit[1])
        roomtimeselect = RoomTimeDialogInfo(self, "Edit Room and Time", roomNames, roomandtimeeditlist)

        # Check for conflicts with all currently scheduled classes and display an error if there
        # are scheduling conflicts.
        conflict = True
        while conflict:
            conflict = False
            if roomtimeselect.exec_():
                roomtext = roomtimeselect.getRoomString()
                daystext = roomtimeselect.getDayString()
                times = roomtimeselect.getTimes()
                roomid = self.parent().findRoomFromString(roomtext).InternalID
                newtimeslot = TimeSlot()
                newtimeslot.setData(daystext, times[0], times[1], times[2], times[3])
                roomtimelist = [roomid, newtimeslot]
                conflict = self.parent().RoomTimeslotConflict(roomtimelist, [self.thisSI.InternalID])

                for slot in self.thisSI.RoomsAndTimes:
                    if not roomandtimetoedit[1].equals(slot[1]):
                        if slot[1].overlap(newtimeslot):
                            conflict = True

                if conflict:
                    QMessageBox.warning(self, "Time Conflict", "The selected timeslot conflicts with the current "
                                        + "scheduled times and cannot be added to the course. Please select a "
                                        + "different room, days, and times.",
                                        QMessageBox.Ok)
                    roomtimeselect = RoomTimeDialogInfo(self, "Add Room and Time", roomNames, [roomtext, newtimeslot])
                else:
                    del self.thisSI.RoomsAndTimes[itemindex]
                    self.thisSI.RoomsAndTimes.append(roomtimelist)
                    self.updateRoomsAndTimesList()

    def DeleteDayTime(self):
        """
        Removes a scheduled room, day, and time from the classes schedule.
        """
        item = self.DaysandTimesList.currentItem()
        if item:
            index = self.DaysandTimesList.row(item)
            del self.thisSI.RoomsAndTimes[index]
            self.updateRoomsAndTimesList()

    def CheckSection(self):
        """
        Checks the section number of a valid section.  This is linked to the check button
        beside the section number.
        """
        sectionnumber, sectionnumberfound = self.parent().CheckSectionNumber(self.thisSI.CourseIID,
                                                                             self.sectionnumberedit.text(),
                                                                             [self.thisSI.InternalID])
        self.sectionnumberedit.setText(sectionnumber)

        if sectionnumberfound:
            QMessageBox.warning(self, "Section Number Conflict", "The section number conflicts with a current "
                                + "course. Please select a different section number.",
                                QMessageBox.Ok)
        else:
            QMessageBox.information(self, "Valid Section Number", "The section number can be used. ", QMessageBox.Ok)

    def GenSection(self):
        """
        Generates a valid section number for the currently selected course.  This is linked to the
        generate button beside the section number.
        """
        self.sectionnumberedit.setText(
            self.parent().GenerateSectionNumber(self.thisSI.CourseIID, [self.thisSI.InternalID]))
