"""
Module:  All classes related to Tracking Deformation Screen 2
Program: Particle Deformation Analysis
Author: Haig Bishop (hbi34@uclive.ac.nz)
"""

# Kivy imports
from kivy.app import App
from kivy.uix.screenmanager import Screen

# Import modules
from plyer import filechooser
import cv2
from datetime import datetime
import os

# Import local modules
from popup_elements import BackPopup
from jobs import EventBox
from file_management import is_experiment_json, load_experiment_json, kivify_image, is_video_file


class TD2Window(Screen):
    """Tracking Deformation screen 1"""

    def __init__(self, **kwargs):
        """init method for TD2 screen"""
        # Call ScrollView init method
        super(TD2Window, self).__init__(**kwargs)
        # Save app as an attribute
        self.app = App.get_running_app()
        # Set attributes for zooming
        self.zoomed = False

    def on_confirm(self):
        """called by pressing the 'X' button."""
        pass

    def check_events(self):
        return []

    def load_events(self, predict_start=True, events=None):
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
        if predict_start:
            for event in events:
                event.predict_start()
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
        else:
            # Reset with defaults
            self.location_label.text = "No event selected"
            self.frame_range_label.text = ""
            self.event_id_label.text = ""
            self.image_widget.texture = None

    def update_image_preview(self):
        # If there is a current event
        current = self.app.current_event
        if current is not None:
            # Draw the start point and pipette position etc. on the image
            drawn_image = current.drawn_first_frame(zoomed=self.zoomed)
            # Resampling method is nearest neighbour if the image is enlargest a great deal
            resample_method = 'nearest' if current.first_frame.shape[0] * 3 < self.image_widget.height or self.zoomed else 'linear'
            # Convert the image to a format useable for Kivy
            self.image_widget.texture = kivify_image(drawn_image, resampling_method=resample_method)

    def on_back_btn(self):
        """called by back btn
        - makes a BackPopup object
        - if there are no events, it immediately closes it"""
        # If there are any events
        if len(self.app.events) > 0:
            # Make pop up - asks if you are sure you want to exit
            popup = BackPopup(from_screen="TD2", to_screen="TD1")
            # Open it
            popup.open()
        # If there are not events
        else:
            # Make pop up - asks if you are sure you want to exit
            popup = BackPopup(from_screen="TD2", to_screen="TD1")
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
            image = current.first_frame
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
            elif is_arrow_key:
                if key == 'up' or key == 'w':
                    # Up key
                    if self.app.shift_is_down:
                        # Shift + Up
                        current.zoom_in_pipette()
                    else:
                        # Up
                        current.move_up_circle()
                elif key == 'down' or key == 's':
                    # Down key
                    if self.app.shift_is_down:
                        # Shift + Down
                        current.zoom_out_pipette()
                    else:
                        # Down
                        current.move_down_circle()
                elif key == 'left' or key == 'a':
                    # Left key
                    if self.app.shift_is_down:
                        # Shift + Left
                        current.move_left_pipette()
                    else:
                        # Left
                        current.move_left_circle()
                elif key == 'right' or key == 'd':
                    # Right key
                    if self.app.shift_is_down:
                        # Shift + Right
                        current.move_right_pipette()
                    else:
                        # Right
                        current.move_right_circle()
                self.update_image_preview()

    def on_touch_move(self, touch):
        """called when there is a 'touch movement'
        - this includes things like click/drags and swipes"""
        # If there is a current event
        current = self.app.current_event
        if current is not None:
            # If the touch is within the image
            if self.pos_in_image(touch.pos) and not self.zoomed:
                # Update the circle position
                current.update_pos(self.convert_pos(touch.pos))
                # Update the image
                self.update_image_preview()
        # You have to return this because it is a Kivy method
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        """this is called by all mouse up things. (e.g. left, right, middle scroll)"""
        # If there is a current event
        current = self.app.current_event
        if current is not None:
            # If it is a button (Kivy thing) and the touch is within the image
            if "button" in touch.profile and self.pos_in_image(touch.pos):
                # If a left click
                if touch.button == "left":
                    # Update the circle position
                    current.update_pos(self.convert_pos(touch.pos))
                else:
                    # If a scroll up + not too big
                    if touch.button == "scrollup":
                        # Increase radius
                        current.zoom_in_circle()
                    # If a scroll down + not too small
                    if touch.button == "scrolldown":
                        # Decrease radius
                        current.zoom_out_circle()
                # Update the image
                self.update_image_preview()
        # You have to return this because it is a Kivy method
        return super().on_touch_down(touch)

    def pos_in_image(self, pos):
        """takes a position and returns True if it is within the image dimensions"""
        # Unzip pos
        x, y = pos
        # Get image dimensions etc
        norm_image_x = (self.image_widget.width - self.image_widget.norm_image_size[0]) / 2
        norm_image_y = (
            self.image_widget.height - self.image_widget.norm_image_size[1]) / 2
        norm_image_x2 = norm_image_x + self.image_widget.norm_image_size[0]
        norm_image_y2 = norm_image_y + self.image_widget.norm_image_size[1]
        # True if the pos in in the image
        is_in_image = (
            x >= norm_image_x
            and x <= norm_image_x2
            and y >= norm_image_y
            and y <= norm_image_y2
        )
        # If was within the image
        return is_in_image

    def convert_pos(self, pos):
        """Takes a touch.pos and converts it to be in terms of the original image dimensions."""
        current = self.app.current_event
        # Unzip pos
        x, y = pos
        # Get image dimensions etc
        norm_image_x = (self.image_widget.width - self.image_widget.norm_image_size[0]) / 2
        norm_image_y = (
            self.image_widget.height - self.image_widget.norm_image_size[1]) / 2
        norm_image_x2 = norm_image_x + self.image_widget.norm_image_size[0]
        norm_image_y2 = norm_image_y + self.image_widget.norm_image_size[1]
        # Calculate pixel positions
        img_prop_x = (x - norm_image_x) / (norm_image_x2 - norm_image_x)
        img_prop_y = abs((y - norm_image_y) / (norm_image_y2 - norm_image_y) - 1)
        pixel_x = int(img_prop_x * current.first_frame.shape[1])
        pixel_y = int(img_prop_y * current.first_frame.shape[0])
        # Return the pixel positions
        return pixel_x, pixel_y


    def on_size(self, instance, value):
        """Used to update image whenever the screen changes size"""
        self.update_image_preview()