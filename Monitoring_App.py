# Importing needed components for application
from PySide6.QtWidgets import QApplication

# sys allows for processing command line arguments
import sys

# imports MainWindow class from separate file
from Monitoring_MainWindow import MonitorWindow

try:
    from ctypes import windll
    myappid = 'VNAMonitor.application'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)  # Used to trick windows into believing this is not a python application
except ImportError:
    pass

# Defines RVNA Application
Monitoring_App = QApplication(sys.argv)

# Defines Main Widow Interface for Application
Main_Window = MonitorWindow(Monitoring_App)
Main_Window.show()

# Starts event loop
Monitoring_App.exec()
