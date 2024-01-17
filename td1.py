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
from jobs import EventBox
from file_management import is_experiment_json, load_experiment_json, kivify_image, is_video_file


class TD1Window(Screen):
    """Tracking Deformation screen 1"""

    def __init__(self, **kwargs):
        """init method for TD1 screen"""
        # Call ScrollView init method
        super(TD1Window, self).__init__(**kwargs)
        # Save app as an attribute
        self.app = App.get_running_app()

    def on_predict(self):
        """called by pressing the 'Predict Start Point' button."""
        pass

    def check_events(self):
        return []

    def load_events(self, events=None):
        """Called by previous screen when migrating events over.
            Initialises evt boxes. Updates selection and visuals."""
        # If not explicitly defined, we will load all events 
        if events is None:
            events = self.app.events
        # For every event
        for event in events:
            # Create the accompanying list box
            new_evt_box = EventBox(event, self)
            self.evt_scroll.grid_layout.add_widget(new_evt_box)
        # Set the first event added as the current job (if any)
        self.app.deselect_all_events()
        first_event = events[0] if len(events) > 0 else None
        self.app.select_event(first_event)
        # Update everything visually
        self.update_fields()

    def select_experiment_jsons(self):
        """called when [select event file(s)] button is pressed
        - opens the file select window
        - selection is sent to self.selected()"""
        # Only allow selection of TDMS
        filters = []
        # Open folder selector window - send selection to self.selected
        filechooser.open_file(
            on_selection=self.experiment_json_selected, 
            title="Select file(s)", 
            filters=filters,
            multiple=True
        )

    def experiment_json_selected(self, selection):
        """receives selection from selector window
        - checks if the selections are valid
        - if they are it adds them as events
        - if any are not valid it will display an error string"""
        errors = ['no_events', 'no_valid_exps']
        # Set booleans to test if selection is valid
        no_valid, duplicate, invalid_json, invalid_video, invalid_ion, no_events = True, False, False, False,  False, True
        all_events = []
        for file_loc in selection:
            # If is is a genuine selection of valid type
            if is_experiment_json(file_loc):
                # Make an experiment object from the JSON file
                experiment, json_errors = load_experiment_json(file_loc)
                # If we loaded correctly
                if experiment is not None and len(json_errors) == 0:
                    # If it doesn't already exist
                    if not self.app.duplicate_experiment_obj(experiment):
                        # Add to the list
                        self.app.add_experiment(experiment)
                        # Make an event objects
                        use_ion = experiment.ion_loc != None
                        events = experiment.make_events(use_ion)
                        # For every event object
                        for event in events:
                            # Add event to app list
                            self.app.add_event(event)
                            # Add event to experiment
                            experiment.add_event(event)
                            # There was at least 1 event!
                            no_events = False
                            if 'no_events' in errors: errors.remove('no_events')
                        # add to list of events
                        all_events += events
                        # At least one valid exp
                        no_valid = False
                        if 'no_valid_exps' in errors: errors.remove('no_valid_exps')
                    # It is a duplicate!
                    else:
                        duplicate = True
                        errors.append('duplicate_exp')
                # Invalid JSON loading
                else:
                    # Grab errors
                    errors += json_errors
            # Invalid JSON file
            else:
                invalid_json = True
                errors.append('invalid_json')
        # No duplicate errors tolerated!
        errors = list(set(errors))
        # If none are valid
        if 'no_valid_exps' in errors:
            # Deselect any jobs, update location label
            self.app.deselect_all_events()
            # Disable layouts
            self.param_grid_layout.disabled = True
            self.name_grid_layout.disabled = True
            # Update everything visually
            self.update_fields()
            # Remove this error
            errors.remove('no_valid_exps')
        else:
            # Enable layouts
            self.param_grid_layout.disabled = False
            self.name_grid_layout.disabled = False
            # Load in the events to the screen
            self.load_events(events=all_events)
        # If there was any other errors
        if len(errors) > 0:
            # Make an error string describing the issue
            error_string = ""
            if 'duplicate_exp' in errors:
                # Update error string
                error_string += "Experiment duplicate(s). "
            if 'invalid_json' in errors:
                # Update error string
                error_string += "Invalid JSON file(s). "
            if 'vid_read_fail' in errors:
                # Update error string
                error_string += "Unable to read video file(s). "
            if 'ion_read_fail' in errors:
                # Update error string
                error_string += "Unable to read ion file(s). "
            # If no events loaded and that is the only problem
            if 'no_events' in errors and len(errors) == 1:
                # Update error string
                error_string += "No events found. "
            # Update location label
            self.location_label.text = error_string

    def on_current_event(self, instance, current_event):
        """Called when current event changes. Updates slider"""
        # Update everything visually
        self.update_fields()

    def update_fields(self):
        """updates the text inputs and the 'location label'
        - new values are determined by the current event"""
        # If there is a current event
        current = self.app.current_event
        if current is not None:
            # Update with current event's values
            self.location_label.text = str(current.experiment.vid_loc)
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
            