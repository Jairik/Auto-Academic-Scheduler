"""
Professor Class

Description: Structure for holding the information for a faculty member.

self.LastName = ""    Instructor's last name
self.FirstName = ""    Instructor's first name
self.MiddleName = ""    Instructor's middle name
self.Suffix = ""    Instructor's suffix
self.ShortDes = ""    Instructor's short designation, used in several views, usually initials are good.
self.ID = ""    Instructor's employee id number.
self.Real = True    If the instructor is real, meaning that it is a physical person.  When a
                    professor is real the program will not allow time conflicts of courses with
                    that instructor.  If an instructor is not real then the program will allow
                    time conflicts, such as for generic staff assigned classes.
self.InternalID = 0    This is an ID number that is not seen or used by the user, it is used for an
                       internal "linking" of a schedule item to a professor.

@author: Don Spickler
Last Revision: 8/9/2022

"""


class Professor:
    def __init__(self):
        """ Constructor of default values. """
        self.LastName = ""
        self.FirstName = ""
        self.MiddleName = ""
        self.Suffix = ""
        self.ShortDes = ""
        self.ID = ""
        self.Real = True
        self.InternalID = 0

    def getName(self) -> str:
        """ Returns the instructor's formal name. """
        retstr = self.LastName + ", " + self.FirstName
        if self.MiddleName != "":
            retstr += " " + self.MiddleName
        if self.Suffix != "":
            retstr += " " + self.Suffix
        return retstr

    def __repr__(self) -> str:
        """ String representation of a Professor object. """
        return "{" + self.getName() + " (" + self.ShortDes + ")  ID: " + self.ID + "   IID: " + str(self.InternalID) + \
               "  Real: " + str(self.Real) + "}"

    def __str__(self) -> str:
        """ String information of a Professor object, formal name followed by the designation and ID if given. """
        retstr = self.getName() + " (" + self.ShortDes + ")"
        if self.ID != "":
            retstr += " ID: " + self.ID
        return retstr

    def getFieldList(self) -> []:
        """ Returns a list of fields of data for the object, excluding the internal ID. """
        return [self.LastName, self.FirstName, self.MiddleName, self.Suffix, self.ShortDes, self.ID, self.Real]

    def getFieldListWithIID(self) -> []:
        """ Returns a list of fields of data for the object, including the internal ID. """
        return [self.LastName, self.FirstName, self.MiddleName, self.Suffix, self.ShortDes, self.ID, self.Real,
                self.InternalID]
