'''
Automatic Scheduler Class

Description: Helper class that holds algorithms and helper functions for automatically
assigning rooms and courses to professors. Copies over to a temporary database prior to 
algorithm.

@author: JJ McCauley
Last Revision: 12/27/2024
'''

'''DEV PURPOSES - SAVED DATA LAYOUT (ONCE LOADED) 
Faculty: [{Jones, Martha (MJ)  ID:    IID: 5  Real: True}, {Noble, Donna (DN)  ID:    IID: 4  Real: True}, 
{Oswald, Clara Oswyn (COO)  ID:    IID: 6  Real: True}, {Pond, Amy (AP)  ID:    IID: 3  Real: True}, {Potts, Bill (BP)  ID:    IID: 7  Real: True}, 
{Smith, John (JS)  ID:    IID: 9  Real: True}, {Smith, Mickey (MS)  ID:    IID: 8  Real: True}, {Smith, Sarah Jane (SJS)  ID:    IID: 10  Real: True}, 
{Tyler, Rose (RT)  ID:    IID: 1  Real: True}, {Williams, Rory (RW)  ID:    IID: 2  Real: True}]


Rooms: [{HS 107: 24  True ID: 5}, {HS 109: 32  True ID: 4}, {HS 111: 32  True ID: 3}, {HS 113: 32  True ID: 2}, 
{HS 115: 32  True ID: 1}, {HS 123: 20  True ID: 6}, {HS 150: 32 Lab True ID: 7}, {ONLINE 1: 30  False ID: 10}]


Courses: [{COSC 120: Computer Science I (150.0 / 3.0)  ID: 6}, {COSC 120L: Computer Science I Lab (100.0 / 2.0)  ID: 9}, 
{COSC 220: Computer Science II (150.0 / 3.0)  ID: 10}, {COSC 220L: Computer Science II Lab (100.0 / 2.0)  ID: 11}, 
{MATH 155: Statistics (150.0 / 3.0)  ID: 8}, {MATH 160: Applied Calculus (150.0 / 3.0)  ID: 5}, {MATH 201: Calculus I (200.0 / 4.0)  ID: 1}, 
{MATH 202: Calculus II (200.0 / 4.0)  ID: 2}, {MATH 210: Discrete Mathematics (200.0 / 4.0)  ID: 4}, {MATH 310: Calculus III (200.0 / 4.0)  ID: 3}]


StandardTimeSlots: [{MW 15:00 - 16:15}, {MW 16:00 - 17:15}, {MW 17:30 - 18:45}, {MWF 10:00 - 10:50}, {MWF 11:00 - 11:50}, 
{MWF 12:00 - 12:50}, {MWF 13:00 - 13:50}, {MWF 14:00 - 14:50}, {MWF 15:00 - 15:50}, {MWF 16:00 - 16:50}, {MWF 8:00 - 8:50}, 
{MWF 9:00 - 9:50}, {TR 11:00 - 12:15}, {TR 12:30 - 13:45}, {TR 14:00 - 15:15}, {TR 15:00 - 16:15}, {TR 16:00 - 17:15}, {TR 17:30 - 18:45}, 
{TR 8:00 - 9:15}, {TR 9:30 - 10:45}]


Schedule: [{6 001: Professor(s): 5,    Rooms and Times: [[3, 3] ]   Tentative: False  Linked: 1,    InternalID: 0}, 
{9 001: Professor(s): 5,    Rooms and Times: [[7, 7] ]   Tentative: False  Linked:    InternalID: 1}, 
    {6 002: Professor(s): 5,    Rooms and Times: [[3, 3] ]   Tentative: False  Linked: 3,    InternalID: 2}, 
    {9 002: Professor(s): 5,    Rooms and Times: [[7, 7] ]   Tentative: False  Linked:    InternalID: 3}, 
    {10 001: Professor(s): 4,    Rooms and Times: [[3, 3] ]   Tentative: False  Linked: 5,    InternalID: 4}, 
    {11 001: Professor(s): 6,    Rooms and Times: [[7, 7] ]   Tentative: False  Linked:    InternalID: 5}, 
    {8 001: Professor(s): 4,    Rooms and Times: [[4, 4] ]   Tentative: False  Linked:    InternalID: 6}, 
    {5 001: Professor(s): 4,    Rooms and Times: [[4, 4] ]   Tentative: False  Linked:    InternalID: 7},
    {5 002: Professor(s): 4,    Rooms and Times: [[4, 4] ]   Tentative: False  Linked:    InternalID: 8}, 
    {5 003: Professor(s): 6,    Rooms and Times: [[4, 4] ]   Tentative: False  Linked:    InternalID: 14}, 
    {6 003: Professor(s): 8,    Rooms and Times: [[3, 3] ]   Tentative: False  Linked: 22,    InternalID: 21}, 
    {9 003: Professor(s): 8,    Rooms and Times: [[7, 7] ]   Tentative: False  Linked:    InternalID: 22}, 
    {8 002: Professor(s): 10,    Rooms and Times: [[1, 1] ]   Tentative: False  Linked:    InternalID: 23}, 
    {8 003: Professor(s): 10,    Rooms and Times: [[6, 6] ]   Tentative: False  Linked:    InternalID: 24}, 
    {8 004: Professor(s): 10,    Rooms and Times: [[1, 1] ]   Tentative: False  Linked:    InternalID: 25}, 
    {5 004: Professor(s): 10,    Rooms and Times: [[1, 1] ]   Tentative: False  Linked:    InternalID: 26}, 
    {10 002: Professor(s): 1,    Rooms and Times: [[3, 3] ]   Tentative: False  Linked: 28,    InternalID: 27}, 
    {11 002: Professor(s): 1,    Rooms and Times: [[7, 7] ]   Tentative: False  Linked:    InternalID: 28}, 
    {8 005: Professor(s): 2,    Rooms and Times: [[3, 3] ]   Tentative: False  Linked:    InternalID: 33}, 
    {8 006: Professor(s): 2,    Rooms and Times: [[3, 3] ]   Tentative: False  Linked:    InternalID: 34}, 
    {5 005: Professor(s): 2,    Rooms and Times: [[3, 3] ]   Tentative: False  Linked:    InternalID: 35}, 
    {5 006: Professor(s): 2,    Rooms and Times: [[3, 3] ]   Tentative: False  Linked:    InternalID: 36}, 
    {1 001: Professor(s): 6,    Rooms and Times: [[4, 4] ]   Tentative: False  Linked:    InternalID: 12}, 
    {1 002: Professor(s): 6,    Rooms and Times: [[4, 4] ]   Tentative: False  Linked:    InternalID: 13}, 
    {4 001: Professor(s): 3,    Rooms and Times: [[2, 2] ]   Tentative: False  Linked:    InternalID: 11}, 
    {3 001: Professor(s): 3,    Rooms and Times: [[2, 2] ]   Tentative: False  Linked:    InternalID: 9}, 
    {3 002: Professor(s): 3,    Rooms and Times: [[2, 2] ]   Tentative: False  Linked:    InternalID: 10}, 
    {3 003: Professor(s): 7,    Rooms and Times: [[2, 2] ]   Tentative: False  Linked:    InternalID: 16}, 
    {1 003: Professor(s): 7,    Rooms and Times: [[2, 2] ]   Tentative: False  Linked:    InternalID: 17}, 
    {2 001: Professor(s): 7,    Rooms and Times: [[2, 2] ]   Tentative: False  Linked:    InternalID: 15}, 
    {2 002: Professor(s): 9,    Rooms and Times: [[1, 1] ]   Tentative: False  Linked:    InternalID: 20}, 
    {4 002: Professor(s): 9,    Rooms and Times: [[1, 1] ]   Tentative: False  Linked:    InternalID: 18}, 
    {4 003: Professor(s): 9,    Rooms and Times: [[1, 1] ]   Tentative: False  Linked:    InternalID: 19}, 
    {2 003: Professor(s): 8,    Rooms and Times: [[1, 1] ]   Tentative: False  Linked:    InternalID: 29}, 
    {4 004: Professor(s): 8,    Rooms and Times: [[1, 1] ]   Tentative: False  Linked:    InternalID: 30}, 
    {1 004: Professor(s): 1,    Rooms and Times: [[2, 2] ]   Tentative: False  Linked:    InternalID: 31}, 
    {1 005: Professor(s): 1,    Rooms and Times: [[2, 2] [2, 2] ]   Tentative: False  Linked:    InternalID: 32}]'''

class AutoScheduler():  # No extra windows necessary, simply updates database
    
    # Creating copies for each datatype for safe manipulation
    option = {}
    rooms = {}
    courses = {}
    standard_time_slots = {}
    schedule = {}
    
    # Copy over the current database into a temporary one
    def __init__(self, parent):
        self.options = parent.options.copy()
        self.rooms = parent.options.copy()
        self.courses = parent.options.copy()
        self.standard_time_slots = parent.options.copy()
        self.schedule = parent.options.copy()
    
    
    # Saves the curruent schedule configuration to the database
    # asCopy: Saves it to a new schedule file 
    def saveScheduleConfig(self, parent, asCopy=False):
        pass