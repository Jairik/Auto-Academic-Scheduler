"""
Course Class

Description: Structure for holding the information for an academic course.

self.Code = ""    The department code, usually MATH, COSC, PHIL, BIOL, ...
self.Number = ""    The course/catalog number, e.g. 101, 300, 451, ...
self.Title = ""    The course title, e.g. Calculus I, Computer Science I, Algebra, ...
self.Contact = 150    The number of minutes per week that the course meets.
self.Workload = 3    The number of hours workload the course counts to the professor's annual workload.
self.InternalID = 0    This is an ID number that is not seen or used by the user, it is used for an
                       internal "linking" of a schedule item to a course.

@author: Don Spickler
Last Revision: 8/9/2022

"""


class Course:
    def __init__(self):
        """ Constructor of default values. """
        self.Code = ""
        self.Number = ""
        self.Title = ""
        self.Contact = 150
        self.Workload = 3
        self.InternalID = 0

    def getName(self) -> str:
        """ Returns the course code and catalog number, e.g. MATH 201 """
        return self.Code + " " + self.Number

    def __repr__(self) -> str:
        """ String representation of a course object. """
        return "{" + self.Code + ' ' + self.Number + ': ' + self.Title + " (" + str(self.Contact) + \
               " / " + str(self.Workload) + ")" + "  ID: " + str(self.InternalID) + "}"

    def __str__(self) -> str:
        """ String information of a course object. """
        return self.Code + ' ' + self.Number + ': ' + self.Title + "   (" + str(self.Contact) + \
               " / " + str(self.Workload) + ")"

    def getDisplayString(self) -> str:
        """ Display string of course information to be suitable for the end user. """
        return self.Code + ' ' + self.Number + ': ' + self.Title + "   (" + str(self.Contact) + \
               " / " + str(self.Workload) + ")"

    def getDisplayStringNoLoad(self) -> str:
        """ Display string of course information to be suitable for the end user.
            No load numbers are printed here.
        """
        return self.Code + ' ' + self.Number + ': ' + self.Title

    def getFieldList(self) -> []:
        """ Returns a list of fields of data for the object, excluding the internal ID. """
        return [self.Code, self.Number, self.Title, self.Contact, self.Workload]

    def getFieldListWithID(self) -> []:
        """ Returns a list of fields of data for the object, including the internal ID. """
        return [self.Code, self.Number, self.Title, self.Contact, self.Workload, self.InternalID]
