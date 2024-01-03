"""
Program: Particle Deformation Analysis (Version 0.1.16)
Description:
- Software for the analysis of micro aspiration data
Author: Haig Bishop (hbi34@uclive.ac.nz)
Date: 04/01/2024
Version Description:
- added text boxes for current frame and ion frame range
"""

# Stops debug messages - alsoprevents an error after .exe packaging
# os.environ["KIVY_NO_CONSOLELOG"] = "1"

# Import kivy 
import kivy

# Make sure that the version is at least 2.2.0
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
from td1 import *

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
        # Bind key strokes to methods
        Window.bind(on_key_down=self.on_key_down, on_key_up=self.on_key_up)
        # Save a reference to the app object
        self.app = App.get_running_app()

    def on_key_down(self, _1, keycode, _2, _3, modifiers):
        """called when the user presses a key
        - decodes the key e.g. '241' -> 'e'
        - send it to the current screen if needed"""
        # Decodes the key e.g. '241' -> 'e'
        key = Keyboard.keycode_to_string(Keyboard, keycode)
        # If current window is x
        if self.app.root.current == "":
            # Call x
            pass
        # Check if the 'shift' key is pressed down
        if key == "shift":
            # Shift key down
            self.app.shift_is_down = True

    def on_key_up(self, _1, keycode, _2):
        """called when the user stops pressing a key
        - decodes the key e.g. '241' -> 'e'
        - send it to the current screen if needed"""
        # Decodes the key e.g. '241' -> 'e'
        key = Keyboard.keycode_to_string(Keyboard, keycode)
        # Get current screen
        current_screen = self.app.root.current
        # If current window is IE3
        if current_screen == "IE3":
            # Send key up command to that screen
            screen = self.app.root.get_screen(current_screen)
            screen.on_key_up(key)
        # Check if the 'shift' key is pressed up
        if key == "shift":
            # Shift key up
            self.app.shift_is_down = False


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
            self.info_layout.x = 0
            self.main_grid.disabled = True
        # If on
        else:
            # Turn off
            self.info_layout.disabled = True
            self.info_layout.x = 69420  # Sends it far away
            self.main_grid.disabled = False
            self.help_scroll.scroll_y = 1  # Resets the scroll

class PDAApp(App):
    """base of the PDA kivy app"""

    # Initialise list of experiments
    experiments = ListProperty([])
    events = ListProperty([])
    # This holds the current event/experiment
    current_experiment = ObjectProperty(None, allownone=True)
    current_event = ObjectProperty(None, allownone=True)
    # True when shift key is down
    shift_is_down = BooleanProperty(False)

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
        if current_screen in ["IE1", "IE3"]:
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
    
    def deselect_all_events(self):
        """Deselects all events"""
        # Deselect
        self.current_event = None

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
        # Deselect experiments
        self.deselect_all_experiments()


# If this is the main python file
if __name__ == "__main__":
    # Run the PDA app
    PDAApp().run()
