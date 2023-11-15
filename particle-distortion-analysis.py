"""
Program: Particle Deformation Analysis (Version 0.1.1)
Description:
- Software for the analysis of micro aspiration data
Author: Haig Bishop (hbi34@uclive.ac.nz)
Date: 15/11/2023
Version Description:
- Added Import experiment page (incomplete)
- Changes to experiments list
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
from kivy.properties import ListProperty

# Import local modules
from ie1 import *

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

    # Initialise list of experiments
    experiments = ListProperty([])
    events = ListProperty([])

    def build(self):
        """initialises the app"""
        # Label window
        self.title = "Particle Deformation Analysis"
        # Get a reference to the app
        self.app = App.get_running_app()
        self.experiments = []
        # Get references to the screens needed
        self.ie1_window = self.app.root.get_screen("IE1")
        # Bind the file drop call
        Window.bind(on_drop_file=self._on_file_drop)

    def _on_file_drop(self, window, file_path, x, y, *args):
        """called when a file is drag & dropped on the app window"""
        # Get the file path decoded
        file_path = file_path.decode("utf-8")
        # Send the path to one of these 4 windows if they are open
        if self.app.root.current == "IE1":
            self.ie1_window._on_file_drop(file_path, x, y)

    def on_experiments(self, _instance, _experiments):
        # ?
        pass
    
    def current_experiment(self):
        """Returns the experiment currently selected. If no experiment is selected return None."""
        current = None
        # For every experiment
        for experiment in self.experiments:
            # If this is the current experiment, break loop and return experiment
            if experiment.is_selected:
                current = experiment
                break
        return current
    
    def deselect_all_experiments(self):
        """Deselects all experiments - sets is_selected = False"""
        # For every experiment
        for experiment in self.experiments:
            # If this is the current experiment, break loop and return experiment
            experiment.is_selected = False

    def non_duplicate_experiment(self, vid_loc):
        duplicate = False
        # For every experiment
        for experiment in self.experiments:
            # If this is the current experiment, break loop and return experiment
            if experiment.vid_loc == vid_loc:
                duplicate = True
                break
        return duplicate
    
    def clear_experiments(self):
        self.experiments = []


# If this is the main python file
if __name__ == "__main__":
    # Run the PDA app
    PDAApp().run()
