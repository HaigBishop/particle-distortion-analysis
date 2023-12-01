"""
Program: Particle Deformation Analysis (Version 0.1.5)
Description:
- Software for the analysis of micro aspiration data
Author: Haig Bishop (hbi34@uclive.ac.nz)
Date: 1/12/2023
Version Description:
- Added video scrolling in IE3
- Added ion view red line
- Frame counter
"""

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
from kivy.properties import ListProperty, ObjectProperty

# Import local modules
from ie1 import *
from ie3 import *

# Set background colour to grey
DARK_GREY = (32 / 255, 33 / 255, 35 / 255, 1)
Window.clearcolor = DARK_GREY

# Info page text
INFO_FILE_POS = "resources\\info_page_text.txt"


class WindowManager(ScreenManager):
    """Screen manager class"""

    def __init__(self, **kwargs):
        """The init method for the screen manager"""
        # Set a transition object so it can be referenced
        self.transition = SlideTransition()
        # Call ScreenManager init method
        super(ScreenManager, self).__init__(**kwargs)


class MainWindow(Screen):
    """The screen for the main menu of PDA"""

    def __init__(self, **kwargs):
        """init method for the main menu"""
        # Call Screen init method
        super(MainWindow, self).__init__(**kwargs)
        # Read the info page text file
        with open(INFO_FILE_POS, "r", encoding="utf8") as file:
            self.info_text = file.read()
        # Get app reference
        self.app = App.get_running_app()

    def toggle_info(self):
        """Toggles the info screen on/off"""
        # If off
        if self.info_layout.disabled:
            # Turn on
            self.info_layout.disabled = False
            self.info_layout.pos = (0, 0)
            self.main_grid.disabled = True
        # If on
        else:
            # Turn off
            self.info_layout.disabled = True
            self.info_layout.pos = (99999, 99999)  # Sends it far away
            self.main_grid.disabled = False
            self.help_scroll.scroll_y = 1  # Resets the scroll


class PDAApp(App):
    """base of the PDA kivy app"""

    # Initialise list of experiments
    experiments = ListProperty([])
    events = ListProperty([])
    # This holds the current experiment
    current_experiment = ObjectProperty(None, allownone=True)

    def build(self):
        """initialises the app"""
        # Label window
        self.title = "Particle Deformation Analysis"
        # Set app icon
        self.icon = "resources\\icon.png"
        # Bind the file drop call
        Window.bind(on_drop_file=self._on_file_drop)

    def _on_file_drop(self, window, file_path, x, y, *args):
        """called when a file is drag & dropped on the app window"""
        # Get the file path decoded
        file_path = file_path.decode("utf-8")
        current_screen = self.root.current
        # If on a screen that has file drop
        if current_screen == "IE1":
            # Send to that screen
            screen = self.root.get_screen(current_screen)
            screen._on_file_drop(file_path)

    def on_experiments(self, instance, experiments):
        """Called when the experiments list changes.
        Calls on_experiments if the current screen has that method."""
        # If on a screen with an on_experiments method
        current_screen = self.root.current
        if current_screen == "IE1":
            # Call on_experiments for that screen
            screen = self.root.get_screen(current_screen)
            screen.on_experiments(instance, experiments)
    
    def on_current_experiment(self, instance, current_experiment):
        """Called when the current experiment changes.
        Calls on_current_experiment if the current screen has this method."""
        current_screen = self.root.current
        # If on a screen with an experiments list
        if current_screen in ["IE1", "IE3"]:
            # Call on_current_experiment for that exp list scrollview
            screen = self.root.get_screen(current_screen)
            screen.exp_scroll.on_current_experiment(instance, current_experiment)
        # If on a IE3
        if current_screen in ["IE3"]:
            # Call on_current_experiment for that exp list scrollview
            screen = self.root.get_screen(current_screen)
            screen.on_current_experiment(instance, current_experiment)
    
    def remove_experiment(self, experiment):
        """Removes an experiment and deselects it if selected"""
        # If selected
        if self.current_experiment == experiment:
            # Deselect
            self.current_experiment = None
        # Remove from list
        self.experiments.remove(experiment)
    
    def add_experiment(self, experiment):
        """Adds an experiment"""
        self.experiments.append(experiment)

    def select_experiment(self, experiment):
        """Selects and experiment"""
        # If it is in the list
        if experiment in self.experiments:
            # Set as current
            self.current_experiment = experiment
    
    def deselect_all_experiments(self):
        """Deselects all experiments"""
        # Deselect
        self.current_experiment = None

    def duplicate_experiment(self, vid_loc):
        """Returns True if the given video file is in the experiment list."""
        return vid_loc in [exp.vid_loc for exp in self.experiments]
    
    def clear_experiments(self, boxes_only=False):
        """Clears all experiments and experiment boxes from the current screen."""
        # If on a screen with an experiments list
        current_screen = self.root.current
        if current_screen in ["IE1", "IE3"]:
            # Get that screen's exp_scroll
            exp_scroll = self.root.get_screen(current_screen).exp_scroll
            # Clear both lists
            exp_scroll.clear_list(boxes_only=boxes_only)
            # Deselect
            self.current_experiment = None


# If this is the main python file
if __name__ == "__main__":
    # Run the PDA app
    PDAApp().run()
