"""
ScheduleItem Class

Description: Structure for holding the information for a schedule item.  A schedule item is a single
class in the department schedule.

self.CourseIID = -1    This is the internal ID of the class.
self.ProfessorIID = []    This is a list of internal IDs of the professors teaching the course.
                            This is set up as a list to allow team teaching of the course.
self.RoomsAndTimes = []  # [[RoomIID, TimeSlot],...]    This is a list of lists, each internal list
                                                        is a room internal ID followed by a timeslot
                                                        object. The class can have multiple room/times
                                                        in its schedule.
self.Section = ""    This is the section number of the class, e.g. MATH 201-001  the section is 001.
self.Tentative = False    This is if the course is tentative or not.  Tentative classes are like any
                            other class except they are designated as tentative, i.e. not active on the
                            university schedule.
self.Subtitle = ""    The subtitle for the course, optional.
self.Designation = ""    Any designations for the course that are appropriate, e.g. LLC, SI, Honors, ...
self.LinkedCourses = []    List of linked classes internal ids.  A linked class is a subsequent course,
                            for example, a lab that accompanies a course.
self.InternalID = 0    This is an ID number that is not seen or used by the user, it is used for an
                       internal "linking" of subsequent classes in the schedule.

@author: Don Spickler
Last Revision: 8/9/2022

"""


class ScheduleItem:
    def __init__(self):
        """ Constructor of default values. """
        self.CourseIID = -1
        self.ProfessorIID = []
        self.RoomsAndTimes = []  # [[RoomIID, TimeSlot],...]
        self.Section = ""
        self.Tentative = False
        self.Subtitle = ""
        self.Designation = ""
        self.LinkedCourses = []
        self.InternalID = 0

    def getCourseNameData(self) -> str:
        """ Returns the course internal id and section number as a string. """
        return str(self.CourseIID) + " " + self.Section

    def createRepString(self) -> str:
        """ String representation of a ScheduleItem object. """
        retstr = str(self.CourseIID) + ' ' + self.Section + ': Professor(s): '
        for piid in self.ProfessorIID:
            retstr += str(piid) + ", "
        retstr += "   Rooms and Times: ["
        for rid in self.RoomsAndTimes:
            retstr += "[" + str(rid[0]) + ", " + str(rid[0]) + "] "
        retstr += "]   Tentative: "
        if self.Tentative:
            retstr += "True"
        else:
            retstr += "False"
        if self.Subtitle != "":
            retstr += "   Subtitle: " + self.Subtitle
        if self.Designation != "":
            retstr += "   Subtitle: " + self.Designation
        retstr += '  Linked: '
        for liid in self.LinkedCourses:
            retstr += str(liid) + ", "
        retstr += "   InternalID: " + str(self.InternalID)

        return retstr

    def __repr__(self) -> str:
        """ String representation of a ScheduleItem object. """
        return "{" + self.createRepString() + "}"

    def __str__(self) -> str:
        """ String representation of a ScheduleItem object. """
        return self.createRepString()

    def getFieldList(self) -> []:
        """ Returns a list of fields of data for the object, excluding the internal ID. """
        return [self.CourseIID, self.ProfessorIID, self.RoomsAndTimes, self.Section,
                self.Tentative, self.Subtitle, self.Designation, self.LinkedCourses]

    def getFieldListWithID(self) -> []:
        """ Returns a list of fields of data for the object, including the internal ID. """
        return [self.CourseIID, self.ProfessorIID, self.RoomsAndTimes, self.Section,
                self.Tentative, self.Subtitle, self.Designation, self.LinkedCourses,
                self.InternalID]
