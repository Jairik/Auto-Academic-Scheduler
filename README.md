# Academic-Scheduler

The Academic Scheduler is an application that allows the user to create, save, and export a semester schedule for an academic department. It uses multiple subwindow viewers of information of the schedule and a drag-and-drop interface to make course scheduling quicker and easier. There is certainly no possible way that this or any other program will be able to encompass all the intricacies in scheduling for every department at every university, but it is hoped that it will be sufficient and ease a significantly difficult task for the departmental leadership.  There is an example schedule file `ExampleSchedule.ash` in the version directory to help you get started.

**Windows Users**

This is a Python application using the PySide6 GUI API, but you do not need to have either Python nor PySide6 installed on your machine to run this program.  The Windows distribution of this program is as a single stand-alone executable file, AcademicScheduler.exe.

- Download and extract the AcademicScheduler_WIN_EXE.zip file from the version directory.
- From Windows Explorer double-click the AcademicScheduler.exe file.

Note that there is a program icon included in the zip folder as well, for creating shortcuts to the program if you wish.  This has been tested on both Windows 10 and 11.

**Linux and MacOS Users**

This is a Python application using the PySide6 GUI API. To run this program from the source code you will need both Python3 and the python package PySide6 installed on your system.

To run this program from the source code:

- Download and extract the AcademicScheduler_src.zip file from the version directory.
- Make sure that Python3 and the python package PySide6 are installed on your system.
- Run the following command from your terminal,

`python AcademicScheduler.py` or possibly  `python3 AcademicScheduler.py`
