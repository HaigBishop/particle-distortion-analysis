"""
Module:  All classes related to Tracking Deformation Screen 3
Program: Particle Deformation Analysis
Author: Haig Bishop (haig.bishop@pg.canterbury.ac.nz)
"""

# Kivy imports
import json
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock

# Import modules
from plyer import filechooser
import cv2
from datetime import datetime
import os

# Import local modules
from popup_elements import BackPopup, ErrorPopup, ConfirmPopup
from jobs import EventBox
from file_management import kivify_image

# Animation duration for play to end/start (seconds)
ANIMATION_DURATION = 1.5 


class TD3Window(Screen):
    """Tracking Deformation screen 1"""

    def __init__(self, **kwargs):
        """init method for TD2 screen"""
        # Call ScrollView init method
        super(TD3Window, self).__init__(**kwargs)
        # Save app as an attribute
        self.app = App.get_running_app()
        # Set attributes for zooming
        self.zoomed = False
        # When True, the red circle and line is hidden
        self.hidden = False

    def on_confirm_export(self, update_exp_json=False):
        """called by pressing the 'Confirm and Export' button."""
        # Check if the data is valid
        errors = self.check_events() ################
        # If there are issues with the data
        if errors != []:
            # Make pop up - alerts of invalid data
            popup = ErrorPopup()
            # Adjust the text on the popup
            popup.error_label.text = "Invalid Data:\n" + "".join(errors)
            popup.open()
        # If no issues with the data
        else:
            # List of names of events which did not export properly
            export_errors = []
            num_exported = 0
            # For event box in list
            for evt_box in self.evt_scroll.grid_layout.children:
                # Get the event object
                event = evt_box.event
                success = True
                try:
                    # Get the table of data
                    dataframe = event.get_distortion_data_for_export()
                    # Write the CSV file
                    csv_file_loc = event.experiment.directory + '\\' + event.name + '_distortion.csv'
                    dataframe.to_csv(csv_file_loc, index=False)
                    # If we are updating the experiments JSON by adding tracking data to the events
                    if update_exp_json:
                        # Get the events experiment
                        experiment = event.experiment
                        # Get the JSON path
                        json_path = experiment.json_file_loc
                        # Does the JSON file exist?
                        if os.path.exists(json_path):
                            # Load the JSON file
                            with open(json_path, 'r') as file:
                                json_data = json.load(file)
                            # Does json_data["events"] exist
                            if "events" in json_data:
                                # Add these values to the event:
                                # Find the matching event in the JSON data
                                for evt in json_data["events"]:
                                    if evt["id"] == event.id:
                                        # Add tracking data to the event - convert numpy types to native Python types
                                        evt["dL_pixels"] = [int(x) for x in dataframe["dL_pixels"].tolist()]
                                        evt["particle_tip_x"] = int(round(event.particle_tip_x))
                                        evt["particle_tip_y"] = [int(y) for y in event.distortion_y_positions]
                                        evt["particle_centre_x"] = int(round(event.particle_pos[0]))
                                        evt["particle_centre_y"] = int(round(event.particle_pos[1]))
                                        evt["particle_radius"] = int(round(event.particle_radius))
                                        evt["labelling_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        break
                                
                                # Write the updated JSON back to file
                                with open(json_path, 'w') as file:
                                    json.dump(json_data, file, indent=4)
                        else:
                            print('JSON file does not exist: ' + json_path)

                except Exception as e:
                    print("Event Export Error: " + str(e))
                    # Add this event to be displayed to user
                    export_errors.append(" • " + event.name + "\n")
                    success = False
                    continue
                
                # Export failed
                if not success:
                    # Add this event to be displayed to user
                    export_errors.append(" • " + event.name + "\n")
                    csv_file_loc = None
                else:
                    num_exported += 1

                # Add the CSV file (or None) to the event
                event.csv_file_loc = csv_file_loc


            # If there were issues exporting the data
            if export_errors != []:
                # Make pop up - alerts of issues data
                popup = ErrorPopup()
                # Adjust the text on the popup
                popup.error_label.text = "Failed to write the CSV files for the following events:\n" + "".join(export_errors)
                popup.title = "Issues exporting CSV file(s)"
                popup.open()
            else:
                # Make a pop up to confirm export
                popup = ConfirmPopup()
                # Adjust the text on the popup
                popup.confirm_label.text = f"CSV files have been exported successfully for {num_exported} events."
                popup.title = "CSV files exported successfully"
                popup.open()

    def check_events(self):
        return []

    def load_events(self, track_distortion=True, events=None):
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
        # Predict the start points
        if track_distortion:
            for event in events:
                event.track_distortion()
        # Update everything visually
        self.update_fields()

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
            self.frame_range_label.text = 'Frame range:  ' + str(current.first_frame_num) + ' - ' + str(current.last_frame_num)
            self.event_id_label.text = 'Event ID:  ' + str(current.id)
            self.update_image_preview()
            self.frame_label.text = str(current.current_frame_num - current.first_frame_num + 1) + '/' + str(current.num_frames)
        else:
            # Reset with defaults
            self.location_label.text = "No event selected"
            self.frame_range_label.text = ""
            self.event_id_label.text = ""
            self.image_widget.texture = None
            self.frame_label.text = ""

    def update_image_preview(self):
        # If there is a current event
        current = self.app.current_event
        if current is not None:
            # Draw the start point and pipette position etc. on the image
            drawn_image = current.drawn_specific_frame('current', zoomed=self.zoomed, hidden=self.hidden)
            # Sometimes when first showing, the height lies and is too small, so...
            # If height is <100, we use nearest neighbour
            height = self.image_widget.height
            bugger = height < 100
            # Resampling method is nearest neighbour if the image is enlargest a great deal
            resample_method = 'nearest' if current.first_frame.shape[0] * 1.5 < height or self.zoomed  or bugger else 'linear'
            # Convert the image to a format useable for Kivy
            self.image_widget.texture = kivify_image(drawn_image, resampling_method=resample_method)

    def on_back_btn(self):
        """called by back btn
        - makes a BackPopup object
        - if there are no events, it immediately closes it"""
        # If there are any events
        if len(self.app.events) > 0:
            # Make pop up - asks if you are sure you want to exit
            popup = BackPopup(from_screen="TD3", to_screen="TD2")
            # Open it
            popup.open()
        # If there are not events
        else:
            # Make pop up - asks if you are sure you want to exit
            popup = BackPopup(from_screen="TD3", to_screen="TD2")
            # THEN IMMEDIATELY CLOSE IT
            popup.on_answer("yes")

    def on_export(self):
        """Called when export button is pressed. 
        - Exports current frame if there is one"""
        # If there is a current event
        current = self.app.current_event
        if current is not None:
            # Get the directory and name
            directory = current.experiment.directory + '\\'
            name = current.name
            # Format the date and time as text
            now = datetime.now()
            date_extension = "_" + str(now.strftime("%d-%m-%y_%H-%M-%S"))
            # Check if the directory exists
            if not os.path.exists(directory):
                # If it doesn't exist, create it
                os.makedirs(directory)
            # Get the image itself
            image = current.get_frame('current')
            # Combine all and write
            path = directory + name + "_capture" + date_extension + ".png"
            cv2.imwrite(path, image)
            # Print export to console
            print('Exported: ' + path)
            

    def on_key_down(self, key, modifiers):
        """called when a key is pressed down
        - there are many results depending on the key"""
        # If there is a current event
        current = self.app.current_event
        if current is not None:
            # If the 'z' key is pressed down
            if key == "z" and self.zoomed == False:
                # Zoom in
                self.zoomed = True
                self.update_image_preview()
            # If the 'x' key is pressed down
            elif key == "x" and self.hidden == False:
                # Hide overlay
                self.hidden = True
                self.update_image_preview()

    def on_key_up(self, key):
        """called when a key is released up
        - there are many results depending on the key"""
        # Is True if an arrow key
        is_arrow_key = key in ["down", "up", "left", "right", "w", "a", "s", "d"]
        # If there is a current event
        current = self.app.current_event
        if current is not None:
            # If the 'z' key is released (and currently zoomed)
            if key == "z" and self.zoomed == True:
                # Stop zooming
                self.zoomed = False
                self.update_image_preview()
                self.crop_bbox = None
            # If the 'x' key is released (and currently hidden)
            elif key == "x" and self.hidden == True:
                # Show overlay
                self.hidden = False
                self.update_image_preview()
            elif is_arrow_key:
                if key == 'up' or key == 'w':
                    # Up key
                    current.move_distortion_up(maintain_nondecreasing=self.maintain_nondecreasing_checkbox.active)
                elif key == 'down' or key == 's':
                    # Down key
                    current.move_distortion_down(maintain_nondecreasing=self.maintain_nondecreasing_checkbox.active)
                elif key == 'left' or key == 'a':
                    # Left key
                    current.previous_frame()
                    self.update_fields()
                elif key == 'right' or key == 'd':
                    # Right key
                    current.next_frame()
                    self.update_fields()
                self.update_image_preview()

    def on_left_arrow_press(self, num_frames=1):
        """Called when the left arrow is pressed
        - if num_frames is between 0 and 1, it is interpreted as a fraction of the total number of frames
        """
        current = self.app.current_event
        if current is not None:
            # If num_frames is between 0 and 1
            if 0 < num_frames < 1:
                # Interpret as a fraction of the total number of frames
                num_frames = int(num_frames * current.num_frames)
            # Call previous frame num_frames times
            for _ in range(num_frames):
                current.previous_frame()
            self.update_image_preview()
            # Update everything visually
            self.update_fields()

    def on_right_arrow_press(self, num_frames=1):
        """Called when the right arrow is pressed
        - if num_frames is between 0 and 1, it is interpreted as a fraction of the total number of frames
        """
        current = self.app.current_event
        if current is not None:
            # If num_frames is between 0 and 1
            if 0 < num_frames < 1:
                # Interpret as a fraction of the total number of frames
                num_frames = int(num_frames * current.num_frames)
            # Call next frame num_frames times
            for _ in range(num_frames):
                current.next_frame()
            self.update_image_preview()
            # Update everything visually
            self.update_fields()

    def on_left_play_to_end_press(self):
        """Called when the left play to end button is pressed"""
        current = self.app.current_event
        if current is not None:
            animation_duration = ANIMATION_DURATION # seconds
            n_frames = current.num_frames + 2 # +2 as overkill just incase
            delay_per_frame = animation_duration / n_frames
            # Call previous frame n_frames times with a delay of delay_per_frame seconds
            def update_frame(dt):
                current.previous_frame()
                self.update_image_preview()
                self.update_fields()
            # Schedule the frame updates
            for i in range(n_frames):
                Clock.schedule_once(update_frame, i * delay_per_frame)
            self.update_image_preview()
            # Update everything visually
            self.update_fields()

    def on_right_play_to_end_press(self):
        """Called when the right play to end button is pressed"""
        current = self.app.current_event
        if current is not None:
            animation_duration = ANIMATION_DURATION # seconds
            n_frames = current.num_frames + 2 # +2 as overkill just incase
            delay_per_frame = animation_duration / n_frames
            # Call next frame n_frames times with a delay of delay_per_frame seconds
            def update_frame(dt):
                current.next_frame()
                self.update_image_preview()
                self.update_fields()
            # Schedule the frame updates
            for i in range(n_frames):
                Clock.schedule_once(update_frame, i * delay_per_frame)
            self.update_image_preview()
            # Update everything visually
            self.update_fields()

    def on_size(self, instance, value):
        """Used to update image whenever the screen changes size"""
        self.update_image_preview()