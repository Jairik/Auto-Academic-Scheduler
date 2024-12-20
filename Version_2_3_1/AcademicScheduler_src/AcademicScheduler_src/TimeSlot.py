"""
Timeslot Class

Description: Structure for holding the information for a timeslot.

self.Days = ""   String holding the days of the week code, MTWRFSU
self.StartHour = 0    Starting hour of the timeslot on a 24-hour clock.
self.StartMinute = 0   Starting minute of the timeslot.
self.EndHour = 0    Ending hour of the timeslot on a 24-hour clock.
self.EndMinute = 0    Ending minute of the timeslot.

@author: Don Spickler
Last Revision: 8/9/2022

"""


class TimeSlot:
    def __init__(self):
        """ Constructor of default values. """
        self.Days = ""
        self.StartHour = 0
        self.StartMinute = 0
        self.EndHour = 0
        self.EndMinute = 0

    def getDescription(self) -> str:
        """ Returns a string description of the timeslot on a 12-hour clock. """
        sh = self.StartHour
        sm = self.StartMinute
        sampm = "AM"
        eh = self.EndHour
        em = self.EndMinute
        eampm = "AM"
        if sh >= 12:
            sampm = "PM"
        if sh > 12:
            sh -= 12
        if eh >= 12:
            eampm = "PM"
        if eh > 12:
            eh -= 12
        smstr = str(sm)
        emstr = str(em)
        if len(smstr) < 2:
            smstr = "0" + smstr
        if len(emstr) < 2:
            emstr = "0" + emstr

        shstr = str(sh)
        ehstr = str(eh)
        if sh == 0:
            shstr = '12'
        if eh == 0:
            ehstr = '12'

        return self.Days + ' ' + shstr + ':' + smstr + " " + sampm + " - " + \
               ehstr + ':' + emstr + " " + eampm

    def getDescription24Hr(self) -> str:
        """ Returns a string description of the timeslot on a 24-hour clock. """
        sh = self.StartHour
        sm = self.StartMinute
        eh = self.EndHour
        em = self.EndMinute
        smstr = str(sm)
        emstr = str(em)
        if len(smstr) < 2:
            smstr = "0" + smstr
        if len(emstr) < 2:
            emstr = "0" + emstr
        shstr = str(sh)
        ehstr = str(eh)
        if sh == 0:
            shstr = '12'
        if eh == 0:
            ehstr = '12'

        return self.Days + ' ' + shstr + ':' + smstr + " - " + ehstr + ':' + emstr

    def clean(self):
        """ Revises the timeslot data into a "standard" format with the days
            of the week in standard order and uppercase.  The minutes, if over
            59, are converted to additional hours and remainder minutes.
        """
        cleandays = ""
        self.Days = self.Days.upper().rstrip().lstrip()
        if self.Days.find("M") != -1:
            cleandays += "M"
        if self.Days.find("T") != -1:
            cleandays += "T"
        if self.Days.find("W") != -1:
            cleandays += "W"
        if self.Days.find("R") != -1:
            cleandays += "R"
        if self.Days.find("F") != -1:
            cleandays += "F"
        if self.Days.find("S") != -1:
            cleandays += "S"
        if self.Days.find("U") != -1:
            cleandays += "U"

        self.Days = cleandays
        self.StartHour += self.StartMinute // 60
        self.StartMinute = self.StartMinute % 60
        self.EndHour += self.EndMinute // 60
        self.EndMinute = self.EndMinute % 60

    def isValid(self) -> bool:
        """ Returns True if the hours are between 0 and 23 for the start and end. """
        self.clean()
        if self.StartHour < 0 or self.StartHour > 23:
            return False
        if self.EndHour < 0 or self.EndHour > 23:
            return False

        return True

    def combine(self, time2):
        """ Combines two timeslots if it can into one returned timeslot.
            If two timeslots have the same start and end times the days will be combined.
            If two timeslots have the same days, and they overlap or are adjacent the slots are
            combined to the smaller start and larger end times.
        """
        self.clean()
        time2.clean()

        # Take care of combining days on slots with the same time range.
        if self.timeequals(time2):
            newslot = TimeSlot()
            newslot.setData(self.Days + time2.Days, self.StartHour, self.StartMinute, self.EndHour, self.EndMinute)
            newslot.clean()
            return newslot

        # Take care of combining the times if the days match and the times overlap.
        if self.Days == time2.Days:
            # Determines if the times overlap.
            okcomb = False
            okcomb = okcomb or self.timeInSlotNoDays(time2.StartHour, time2.StartMinute)
            okcomb = okcomb or self.timeInSlotNoDays(time2.EndHour, time2.EndMinute)
            okcomb = okcomb or time2.timeInSlotNoDays(self.StartHour, self.StartMinute)
            okcomb = okcomb or time2.timeInSlotNoDays(self.EndHour, self.EndMinute)

            # Find the new start and end times.
            if okcomb:
                selfst = self.StartHour * 60 + self.StartMinute
                selfet = self.EndHour * 60 + self.EndMinute
                t2st = time2.StartHour * 60 + time2.StartMinute
                t2et = time2.EndHour * 60 + time2.EndMinute
                if selfst < t2st:
                    newsth = self.StartHour
                    newstm = self.StartMinute
                else:
                    newsth = time2.StartHour
                    newstm = time2.StartMinute

                if selfet > t2et:
                    newseh = self.EndHour
                    newsem = self.EndMinute
                else:
                    newseh = time2.EndHour
                    newsem = time2.EndMinute

                # Create the new combined slot.
                newslot = TimeSlot()
                newslot.setData(self.Days, newsth, newstm, newseh, newsem)
                newslot.clean()
                return newslot

        return None

    def equals(self, time2) -> bool:
        """ Determines if the two slots are equal.  Both times and days must match """
        self.clean()
        time2.clean()
        timesequal = True
        if self.Days != time2.Days:
            timesequal = False
        if self.StartHour != time2.StartHour:
            timesequal = False
        if self.StartMinute != time2.StartMinute:
            timesequal = False
        if self.EndHour != time2.EndHour:
            timesequal = False
        if self.EndMinute != time2.EndMinute:
            timesequal = False

        return timesequal

    def timeequals(self, time2) -> bool:
        """ Determines if the two slots are equal in times only, no days considered. """
        self.clean()
        time2.clean()
        timesequal = True
        if self.StartHour != time2.StartHour:
            timesequal = False
        if self.StartMinute != time2.StartMinute:
            timesequal = False
        if self.EndHour != time2.EndHour:
            timesequal = False
        if self.EndMinute != time2.EndMinute:
            timesequal = False

        return timesequal

    def __repr__(self) -> str:
        """ String representation of the object, simply 24-hour clock description. """
        return "{" + self.getDescription24Hr() + "}"

    def __str__(self) -> str:
        """ String information of the object, simply 12-hour clock description. """
        return self.getDescription()

    def getFieldList(self) -> []:
        """ Returns a list of fields of data for the object. """
        return [self.Days, self.StartHour, self.StartMinute, self.EndHour, self.EndMinute]

    def setData(self, days: str, bh: int, bm: int, eh: int, em: int):
        """ Sets all the data fields for the object. """
        self.Days = days.upper()
        self.StartHour = bh
        self.StartMinute = bm
        self.EndHour = eh
        self.EndMinute = em

    def getMinutes(self) -> int:
        """ Returns the number of minutes in the timeslot, slot time times the number of days.
            This function assumes that the slot id in standard form, i.e. cleaned.
        """
        hourdif = self.EndHour - self.StartHour
        minutedif = self.EndMinute - self.StartMinute
        dayminutes = hourdif * 60 + minutedif
        total = dayminutes * len(self.Days)
        return total

    def timeInSlot(self, d: str, h: int, m: int) -> bool:
        """ Returns True if the day, hour, minute (d, h, m) parameters represent a time inside the slot.
            Times at the slot endpoints are considered inside the slot.
        """
        if d not in self.Days:
            return False

        starttime = self.StartHour * 60 + self.StartMinute
        endtime = self.EndHour * 60 + self.EndMinute
        thistime = h * 60 + m
        return starttime <= thistime <= endtime

    def timeInSlotNoDays(self, h: int, m: int) -> bool:
        """ Returns True if the hour and minute (h, m) parameters represent a time inside the slot.
            Times at the slot endpoints are considered inside the slot, and days are not considered here.
        """
        starttime = self.StartHour * 60 + self.StartMinute
        endtime = self.EndHour * 60 + self.EndMinute
        thistime = h * 60 + m
        return starttime <= thistime <= endtime

    def timeStrictlyInSlot(self, d: str, h: int, m: int) -> bool:
        """ Returns True if the day, hour, minute (d, h, m) parameters represent a time inside the slot.
            Times at the slot endpoints are not considered strictly inside the slot.
        """
        if d not in self.Days:
            return False

        starttime = self.StartHour * 60 + self.StartMinute
        endtime = self.EndHour * 60 + self.EndMinute
        thistime = h * 60 + m
        return starttime < thistime < endtime

    def overlap(self, timeslot) -> bool:
        """ Returns True if the two timeslots overlap.  Slots that are adjacent to each other are not
            considered to overlap.
        """
        if timeslot is None:
            return False

        retval = False
        for day in timeslot.Days:
            retval = retval or self.timeStrictlyInSlot(day, timeslot.StartHour, timeslot.StartMinute)
            retval = retval or self.timeStrictlyInSlot(day, timeslot.EndHour, timeslot.EndMinute)
            retval = retval or ((day in self.Days) and self.timeequals(timeslot))

        for day in self.Days:
            retval = retval or timeslot.timeStrictlyInSlot(day, self.StartHour, self.StartMinute)
            retval = retval or timeslot.timeStrictlyInSlot(day, self.EndHour, self.EndMinute)
            retval = retval or ((day in timeslot.Days) and self.timeequals(timeslot))

        return retval
