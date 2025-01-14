'''
Automatic Scheduler Class

Description: Helper class that holds algorithms and helper functions for automatically
assigning rooms and courses to professors. Copies over to a temporary database prior to 
algorithm.

@author: JJ McCauley
Last Revision: 12/27/2024
'''
import random
import itertools

class AutoScheduler():  # No extra windows necessary, simply updates database
    
    # Creating copies for each datatype for safe manipulation
    option: list[dict] = []
    rooms: list[dict] = []
    courses: list[dict] = []
    faculty: list[dict] = []
    faculty_count: dict = {}  # Number of classes for each professor
    standard_time_slots: list[dict] = []
    schedule: list[dict] = []
    timeslots: list[list][dict] = []  # Easier breakdown for algorithm
    temp_schedule: list[dict] = []
    
    # Copy over the current database into a temporary one
    def __init__(self, parent):
        '''
        Copies over data and breaks up the times into easily formattable slots
        '''
        self.options = parent.options.copy()
        self.rooms = parent.rooms.copy()
        self.courses = parent.courses.copy()
        self.faculty = parent.faculty.copy()
        self.standard_time_slots = parent.standardtimeslots.copy()
        self.schedule = parent.schedule.copy()
        
        # Split up the timeslots into a format easier for the algorithm
        for timeslot in self.standard_time_slots:
            days, time_range = timeslot.split()
            start, end = time_range.split('-')
            for day in days:
                self.timeslots.append({'day': day, 'start': start, 'end': end})
 
    
    def saveScheduleConfig(self, parent, asCopy=False):
        '''
        Saves the curruent schedule configuration to the database
        asCopy: Saves it to a new schedule file 
        '''
        pass
    
    # TESTING METHOD - Will go through and place classes on first available fit basis
    def place(self):
        '''
        Testing method that will place the classes in timeslots based on order.
        Ensuring the efficacy of data interaction and placements (compatibility
        with importing back into schedule object) 
        '''
        # Creating class count for each professor
        if self.faculty_count is {}:
            for prof in self.faculty:
                self.faculty_count[prof] = 0
                
        # Creating a list of rooms available at specific times. Will later optimize
        combined = [
            {**self.rooms, "timeslot": timeslot}
            for room, timeslot in zip(self.courses, itertools.cycle(self.timeslots))
        ]
        
        # Loop through each course, assigning a room, professor, and timeslot
        for course in self.courses:
            i = 0
            # Find the next compatible room
            if not self.roomIsCompatible(course, combined[i]):
                i += 1
            
    # Helper function that determines if a course and room+time is compatible
    def roomIsCompatible(course, roomtime):
        
        pass
        