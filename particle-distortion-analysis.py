"""
Program: Particle Deformation Analysis (Version 1.0.1)
Description:
- Software for the analysis of micro aspiration data
Author: Haig Bishop (haig.bishop@pg.canterbury.ac.nz)
Date: 29/01/2025
Version Description:
 - Main menu buttons
 - Path bug fix
"""

# Stops debug messages - may also prevent an error after .exe building
# os.environ["KIVY_NO_CONSOLELOG"] = "1"

# Import kivy 
import kivy

# Make sure that the version is at least 2.2.0
kivy.require("2.2.0")

# Import config to adjust settings
from kivy.config import Config

# Set window size
Config.set("graphics", "width", "1200")
Config.set("graphics", "height", "800")
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

# Import for opening URLs
import webbrowser

# Import local modules
from ie1 import *
from ie3 import *
from td1 import *
from td2 import *
from td3 import *
from file_management import resource_path, class_resource_path

# Set background colour to grey
DARK_GREY = (32 / 255, 33 / 255, 35 / 255, 1)
Window.clearcolor = DARK_GREY

# Info page text
INFO_FILE_POS = resource_path("resources/info_page_text.txt")


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
        # Get current screen
        current_screen = self.app.root.current
        # If current window is TD2, TD3
        if current_screen in ["TD2", "TD3"]:
            # Send key down command to that screen
            screen = self.app.root.get_screen(current_screen)
            screen.on_key_down(key, modifiers)
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
        # If current window is IE3, TD2, TD3
        if current_screen in ["IE3", "TD2", "TD3"]:
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

    def open_url(self, instance, value):
        """Opens URLs when clicked in the info page"""
        webbrowser.open(value)

class PDAApp(App):
    """base of the PDA kivy app"""

    # Initialise list of experiments
    experiments = ListProperty([])
    events = ListProperty([])
    # This holds the current event/experiment
    current_experiment = ObjectProperty(None, allownone=True)
    current_event = ObjectProperty(None, allownone=True)
    # True when the current experiment has ion data attached
    current_has_ion = BooleanProperty(False)
    # True when shift key is down
    shift_is_down = BooleanProperty(False)
    # This function/method allows files to be accessed in the .exe application
    resource_path = class_resource_path

    def build(self):
        """initialises the app"""
        # Label window
        self.title = "Particle Deformation Analysis"
        # Set app icon
        self.icon = resource_path("resources/icon.png")
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
        # Update current_has_ion
        self.current_has_ion = current_experiment is not None and current_experiment.ion_loc != ''
        # Get the current screen
        current_screen = self.root.current
        # If on a screen with an experiments list
        if current_screen in ["IE1", "IE3"]:
            # Call on_current_experiment for that exp list scrollview
            screen = self.root.get_screen(current_screen)
            screen.exp_scroll.on_current_experiment(instance, current_experiment)
            screen.on_current_experiment(instance, current_experiment)
    
    def on_current_event(self, instance, current_event):
        """Called when the current event changes.
        Calls on_current_event if the current screen has this method."""
        # Get the current screen
        current_screen = self.root.current
        # If on a screen with an events list
        if current_screen in ["TD1", "TD2", "TD3"]:
            # Call on_current_event for that evt list scrollview
            screen = self.root.get_screen(current_screen)
            screen.evt_scroll.on_current_event(instance, current_event)
            screen.on_current_event(instance, current_event)
    
    def remove_experiment(self, experiment):
        """Removes an experiment and deselects it if selected"""
        # If selected
        if self.current_experiment == experiment:
            # Deselect
            self.current_experiment = None
        # Remove from list
        self.experiments.remove(experiment)
    
    def remove_event(self, event):
        """Removes an event and deselects it if selected"""
        # If selected
        if self.current_event == event:
            # Deselect
            self.current_event = None
        # Remove from list
        self.events.remove(event)
    
    def add_experiment(self, experiment):
        """Adds an experiment"""
        self.experiments.append(experiment)

    def add_event(self, event):
        """Adds an event"""
        self.events.append(event)

    def select_experiment(self, experiment):
        """Selects an experiment"""
        # If it is in the list
        if experiment in self.experiments:
            # Set as current
            self.current_experiment = experiment

    def select_event(self, event):
        """Selects an event"""
        # If it is in the list
        if event in self.events:
            # Set as current
            self.current_event = event
    
    def deselect_all_experiments(self):
        """Deselects all experiments"""
        # Deselect
        self.current_experiment = None
    
    def deselect_all_events(self):
        """Deselects all events"""
        # Deselect
        self.current_event = None

    def duplicate_experiment_vid(self, vid_loc):
        """Returns True if the given video file is in the experiment list."""
        return vid_loc in [exp.vid_loc for exp in self.experiments]

    def duplicate_experiment_obj(self, experiment):
        """Returns True if the given video file is in the event list."""
        return experiment.vid_loc in [exp.vid_loc for exp in self.experiments]
    
    def clear_experiments(self, boxes_only=False, all_screens=False):
        """Clears all experiments and experiment boxes from the current screen."""
        current_screen = self.root.current
        if all_screens:
            # Get all screen's exp_scrolls
            ie1_exp_scroll = self.root.get_screen('IE1').exp_scroll
            ie3_exp_scroll = self.root.get_screen('IE3').exp_scroll
            # Clear the lists
            ie1_exp_scroll.clear_list(boxes_only=boxes_only)
            ie3_exp_scroll.clear_list(boxes_only=boxes_only)
        # If on a screen with an experiments list
        elif current_screen in ["IE1", "IE3"]:
            # Get that screen's exp_scroll
            exp_scroll = self.root.get_screen(current_screen).exp_scroll
            # Clear the list(s)
            exp_scroll.clear_list(boxes_only=boxes_only)
        # Deselect experiments
        self.deselect_all_experiments()
    
    def clear_events(self, boxes_only=False):
        """Clears all events and event boxes from the current screen."""
        # If on a screen with an events list
        current_screen = self.root.current
        if current_screen in ["TD1", "TD2", "TD3"]:
            # Get that screen's evt_scroll
            evt_scroll = self.root.get_screen(current_screen).evt_scroll
            # Clear both lists
            evt_scroll.clear_list(boxes_only=boxes_only)
        # Deselect events
        self.deselect_all_events()


# If this is the main python file
if __name__ == "__main__":
    # Run the PDA app
    PDAApp().run()
