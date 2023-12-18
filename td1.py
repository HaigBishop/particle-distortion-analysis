"""
Module:  All classes related to Tracking Deformation Screen 1
Program: Particle Deformation Analysis
Author: Haig Bishop (hbi34@uclive.ac.nz)
"""

# Kivy imports
from kivy.app import App
from kivy.uix.screenmanager import Screen

# Import modules
from plyer import filechooser
from cv2 import flip

# Import local modules
from popup_elements import BackPopup
from jobs import Event, EventBox
from file_management import is_event_file, kivify_image


class TD1Window(Screen):
    """Tracking Deformation screen 1"""

    def __init__(self, **kwargs):
        """init method for TD1 screen"""
        # Call ScrollView init method
        super(TD1Window, self).__init__(**kwargs)
        # Save app as an attribute
        self.app = App.get_running_app()

    def on_track(self):
        """called by pressing the 'Proceed Without Current Data' button."""
        pass

    def check_events(self):
        return []

    def select_event_files(self):
        """called when [select event file(s)] button is pressed
        - opens the file select window
        - selection is sent to self.selected()"""
        # Only allow selection of TDMS
        filters = []
        # Open folder selector window - send selection to self.selected
        filechooser.open_file(
            on_selection=self.event_selected, 
            title="Select file(s)", 
            filters=filters,
            multiple=True
        )

    def event_selected(self, selection):
        """receives selection from selector window
        - checks if the selections are valid
        - if they are it adds them as events
        - if any are not valid it will display an error string"""
        # Set booleans to test if selection is valid
        no_valid, duplicate, invalid_type = True, False, False
        for file_loc in selection:
            # If is is a genuine selection of valid type
            if is_event_file(file_loc):
                # If it doesn't already exist
                if not self.app.duplicate_event(file_loc):
                    # Create a event object
                    new_event = Event(file_loc)
                    # Add to the list
                    self.app.add_event(new_event)
                    # Create the accompanying list box
                    new_evt_box = EventBox(new_event, self)
                    self.evt_scroll.grid_layout.add_widget(new_evt_box)
                    no_valid = False
                # It is a duplicate!
                else:
                    duplicate = True
            # It is invalid type!
            else:
                invalid_type = True
        # If none are valid
        if no_valid:
            # Deselect any jobs, update location label
            self.app.deselect_all_events()
            # Disable layouts
            self.param_grid_layout.disabled = True
            self.name_grid_layout.disabled = True
        else:
            # Set the last event added as the current job
            self.app.select_event(new_event)
            # Enable layouts
            self.param_grid_layout.disabled = False
            self.name_grid_layout.disabled = False
        # Update everything visually
        self.update_fields()
        # If there was a failed selection
        if duplicate or invalid_type:
            # Make an error string describing the issue
            error_string = ""
            if duplicate == True:
                # Update error string
                error_string += "File duplicate(s)  "
            if invalid_type == True:
                # Update error string
                error_string += "Incorrect file type(s)"
            # Update location label
            self.location_label.text = error_string

    def update_fields(self):
        """updates the text inputs and the 'location label'
        - new values are determined by the current event"""
        # If there is a current event
        current = self.app.current_event
        if current is not None:
            # Update with current event's values
            self.location_label.text = str(current.vid_loc)
            self.name_input.text = str(current.name)
            self.update_image_preview()
        else:
            # Reset with defaults
            self.location_label.text = "No event selected"
            self.name_input.text = ""
            self.image_widget.texture = None

    def on_name_text(self, text):
        """called when name text input is changed
        - takes the new text
        - updates the current event if there is one"""
        # If there is a current event
        current = self.app.current_event
        if current is not None:
            # Update the event's name
            current.name = text

    def update_image_preview(self):
        # If there is a current event
        current = self.app.current_event
        if current is not None:
            # Get the first frame and flip for Kivy
            image = flip(current.first_frame, 0)
            # Convert the image to a format useable for Kivy
            self.image_widget.texture = kivify_image(image)

    def on_back_btn(self):
        """called by back btn
        - makes a BackPopup object
        - if there are no events, it immediately closes it"""
        # If there are any events
        if len(self.app.events) > 0:
            # Make pop up - asks if you are sure you want to exit
            popup = BackPopup(from_screen="TD1", to_screen="main")
            # Open it
            popup.open()
        # If there are not events
        else:
            # Make pop up - asks if you are sure you want to exit
            popup = BackPopup(from_screen="TD1", to_screen="main")
            # THEN IMMEDIATELY CLOSE IT
            popup.on_answer("yes")

    def _on_file_drop(self, file_path):
        """called when a file is dropped on this screen
        - sends the file path to the selected method"""
        self.event_selected([file_path])
            