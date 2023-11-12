"""
Program: Particle Distortion Analysis (Version 0.1)
Description:
- Software for the analysis of micro aspiration data
Author: Haig Bishop (hbi34@uclive.ac.nz)
Date: 13/11/2023
Version Description:
- Main Screen only
- Bare bones job object class
"""

# Import os and sys
import os

# Stops debug messages - alsoprevents an error after .exe packaging
# os.environ["KIVY_NO_CONSOLELOG"] = "1"

# Import kivy and make sure that the version is at least 2.2.0
import kivy

kivy.require("2.2.0")

# Import config to adjust settings
from kivy.config import Config

# Set window size
Config.set("graphics", "width", "900")
Config.set("graphics", "height", "600")
# Set min window size
Config.set("graphics", "minimum_width", "750")
Config.set("graphics", "minimum_height", "500")
# Disable red dots from right-clicking
Config.set("input", "mouse", "mouse,multitouch_on_demand")

# Other kivy related imports
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.core.window import Keyboard
from kivy.uix.screenmanager import SlideTransition

# Import local modules
from job import PDAjob

# Set background colour to grey
DARK_GREY = (32 / 255, 33 / 255, 35 / 255, 1)
Window.clearcolor = DARK_GREY


class WindowManager(ScreenManager):
    """Screen manager class"""

    def __init__(self, **kwargs):
        """The init method for the screen manager"""
        # Set a transition object so it can be referenced
        self.transition = SlideTransition()
        # Call ScreenManager init method
        super(ScreenManager, self).__init__(**kwargs)
        # Save a reference to the app object
        self.app = App.get_running_app()


class MainWindow(Screen):
    """The screen for the main menu of PDA"""

    def __init__(self, **kwargs):
        """init method for the main menu"""
        # Call Screen init method
        super(MainWindow, self).__init__(**kwargs)
        # Get app reference
        self.app = App.get_running_app()


class PDAApp(App):
    """base of the PDA kivy app"""

    def build(self):
        """initialises the app"""
        # Label window
        self.title = "Particle Distortion Analysis"
        # Get a reference to the app
        self.app = App.get_running_app()
        # Initialise list of jobs
        self.jobs = []
    
    def current_job(self):
        """Returns the job currently selected. If no job is selected return None."""
        current = None
        # For every job
        for job in self.jobs:
            # If this is the current job, break loop and return job
            if job.is_selected:
                current = job
                break
        return current


# If this is the main python file
if __name__ == "__main__":
    # Run the PDA app
    PDAApp().run()
