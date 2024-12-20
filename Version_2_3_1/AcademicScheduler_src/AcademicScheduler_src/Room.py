"""
Room Class

Description: Structure for holding the information for a classroom.

self.Building = ""    Usually a short designation for the building, i.e. a building code such as HS, TETC, ...
self.RoomNumber = ""    Room number of the room, e.g. 205, 307H, ...
self.Capacity = 0    Room capacity for the largest class that can be put in the room.
self.Special = ""    Any special designation for the room, e.g. Lab, Seminar, Distance Learning, ...
self.Real = True    If the room is real, meaning that it is a physical room.  When a room is real
                    the program will not allow time conflicts of courses in that room.  If a room is
                    not real then the program will allow time conflicts, such as for remote or online
                    instruction.
self.InternalID = 0    This is an ID number that is not seen or used by the user, it is used for an
                       internal "linking" of a schedule item to a room.

@author: Don Spickler
Last Revision: 8/9/2022

"""


class Room:
    def __init__(self):
        """ Constructor of default values. """
        self.Building = ""
        self.RoomNumber = ""
        self.Capacity = 0
        self.Special = ""
        self.Real = True
        self.InternalID = 0

    def getName(self) -> str:
        """ Returns the building code and room number, e.g. HS 115 """
        return self.Building + " " + self.RoomNumber

    def getDescription(self) -> str:
        """ Returns the building code and room number along with any special designation, the capacity
            and if the room is real or not.
        """
        retstr = self.getName() + ": "
        if self.Special != "":
            retstr += self.Special

        retstr += " (" + str(self.Capacity) + ")"
        if not self.Real:
            retstr += " Virtual"

        return retstr

    def __repr__(self) -> str:
        """ String representation of a room object. """
        return "{" + self.Building + ' ' + self.RoomNumber + ': ' + str(self.Capacity) + " " + \
               self.Special + " " + str(self.Real) + " ID: " + str(self.InternalID) + "}"

    def __str__(self) -> str:
        """ String information of a room object. """
        return self.getName()

    def getFieldList(self) -> []:
        """ Returns a list of fields of data for the object, excluding the internal ID. """
        return [self.Building, self.RoomNumber, self.Capacity, self.Special, self.Real]

    def getFieldListWithIID(self) -> []:
        """ Returns a list of fields of data for the object, including the internal ID. """
        return [self.Building, self.RoomNumber, self.Capacity, self.Special, self.Real, self.InternalID]
