"""
Module:  All classes related to Import Experiments Screen 3
Program: Particle Deformation Analysis
Author: Haig Bishop (hbi34@uclive.ac.nz)
"""

# Kivy imports
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty, NumericProperty
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout

# Import modules
import cv2
import numpy as np
from math import exp

# Import local modules
from popup_elements import BackPopup
from jobs import ExperimentBox
from file_management import kivify_image, split_min_max, downsample_image, align_sig_to_frames

# Set constants
ION_BACKGROUND_SHADE = 245
ION_SIG_COLOUR = (68, 214, 24)
ION_CURRENT_FRAME_COLOUR = (212, 212, 212)
ION_EVENT_COLOUR = (238, 238, 238)
ION_EVENT_EDGE_COLOUR = (82, 82, 82)
ION_EVENT_START_COLOUR = (242, 144, 39)
ION_CURSOR_COLOUR = (0, 0, 255)


class IE3Window(Screen):
    """position -> force screen"""
    # True when using ion current data
    use_ion = BooleanProperty(False)
    # True when the slider is positioned on an event
    slider_on_event = BooleanProperty(False) 
    # True when ready for start - False when ready for stop
    ready_for_start = BooleanProperty(True)
    # Will always display the original signal if True
    always_use_OG_sig = BooleanProperty(False) 

    # Floats which define the zoom for the current experiment
    zoom_start = NumericProperty(0.0)
    zoom_end = NumericProperty(1.0)


    def __init__(self, **kwargs):
        """init method for IE3 screen"""
        # Call ScrollView init method
        super(IE3Window, self).__init__(**kwargs)
        # Save app as an attribute
        self.app = App.get_running_app()

    def on_proceed(self):
        """called by pressing the 'Proceed' button."""
        pass

    def load_experiments(self):
        """Called by previous screen when migrating experiments over.
            Initialises exp boxes. Updates selection and visuals."""
        for experiment in self.app.experiments:
            # Create the accompanying list box
            new_exp_box = ExperimentBox(experiment, self)
            self.exp_scroll.grid_layout.add_widget(new_exp_box)
        # Set the last experiment added as the current job
        self.app.deselect_all_experiments()
        self.app.select_experiment(experiment)
        # Update everything visually
        self.update_fields()

    def update_fields(self):
        """Updates visuals. Depends on current experiment, etc."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Update these
            self.update_current_frame()
            self.update_slider_on_event()
            self.update_video()
            # Update frame label
            self.frame_label.text = 'Frame: ' + str(current.current_frame) + '/' + str(current.num_frames)
            # Update with current experiment's values
            self.location_label.text = str(current.vid_loc)
            # Update ion current file select section
            if self.use_ion and current.ion_loc != '':
                self.ion_location_label.text = str(current.ion_loc)
                self.ion_view.update_view()
                self.ion_range_label.text = 'Ion range: ' + str(current.ion_frame_range[0]) + ' to ' + str(current.ion_frame_range[1])
            else:
                self.ion_location_label.text = 'No file selected'
                self.ion_view.update_view()
                self.ion_range_label.text = ''
                self.ion_adjust_btn.state = 'normal'
            # Update the thumbnail cursor
            self.thumbnail_bar.update_cursor()
        else:
            # Update slider
            self.video_slider.value = 0
            # Reset with defaults
            self.location_label.text = "No experiment selected"
            self.video_widget.texture = None
            self.ion_location_label.text = 'No file selected'
            # Update frame labels
            self.frame_label.text = ''
            self.ion_range_label.text = ''
            self.ion_view.texture = None
            # Update the thumbnail cursor
            self.thumbnail_bar.cursor_x = -9999
    
    def update_current_frame(self):
        """Updates the current experiments current_frame attribute."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Find the current range of frames in view
            start_frame = int((current.num_frames - 1) * self.zoom_start)
            end_frame = int((current.num_frames - 1) * self.zoom_end) + 1
            frame_range = end_frame - start_frame
            # Use this ^ and the slider position to calculate the frame number
            frame_num = start_frame + int((frame_range) * (self.video_slider.value_normalized - 10e-8)) + 1 # 1 -> num_frames
            current.current_frame = frame_num

    def update_video(self):
        """Update the video view by displaying the current frame."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            image = current.get_frame(current.current_frame)
            # Convert the image to a format useable for Kivy
            self.video_widget.texture = kivify_image(image)

    def zoom_in(self):
        """Try zoom in."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Calculate zoom amount
            old_range = self.zoom_end - self.zoom_start
            zoom_speed = old_range * 0.05
            # Divide between left and right according to cursor position
            # This is a signmoid function - makes values more extreme
            # This causes zoom to centre on the cursor if possible
            weight = 1 / (1 + exp(-24 * (self.video_slider.value_normalized - 0.5)))
            left_zoom_weighting = 2 * weight
            right_zoom_weighting = 2 * (1 - weight)
            # Preform the zoom
            new_zoom_start = self.zoom_start + zoom_speed * left_zoom_weighting
            new_zoom_end = self.zoom_end - zoom_speed * right_zoom_weighting
            # Ensure not too small
            new_range = new_zoom_end - new_zoom_start
            min_range = self.app.current_experiment.zoom_max
            if new_range < min_range:
                # Set to min range centred on current values
                centre = (self.zoom_start + self.zoom_end) / 2
                new_zoom_start = centre - min_range / 2
                new_zoom_end = centre + min_range / 2
            # Ensure not out of range (sometimes is values like -0.0003201 etc.)
            if new_zoom_start <= 0:
                new_zoom_start = 0
            if new_zoom_end >= 1:
                new_zoom_end = 1
            # Set actual values
            self.zoom_start = new_zoom_start
            self.zoom_end = new_zoom_end
            # Maintain cursor position on the same frame
            self.set_cursor_on_frame(self.app.current_experiment.current_frame)

    def zoom_out(self):
        """Try zoom out."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Calculate zoom amount
            old_range = self.zoom_end - self.zoom_start
            zoom_speed = old_range * 0.05
            # Divide between left and right according to cursor position
            # This is a signmoid function - makes values more extreme
            # This causes zoom to centre on the cursor if possible
            weight = 1 / (1 + exp(-24 * (self.video_slider.value_normalized - 0.5)))
            left_zoom_weighting = 2 * (1 - weight)
            right_zoom_weighting = 2 * weight
            # Preform the zoom
            new_zoom_start = self.zoom_start - zoom_speed * left_zoom_weighting
            new_zoom_end = self.zoom_end + zoom_speed * right_zoom_weighting
            new_range = min(1, new_zoom_end - new_zoom_start)
            # Ensure the new zoom is not out of range left
            if new_zoom_start < 0:
                # Set to far left with the same range
                new_zoom_start = 0
                new_zoom_end = new_range
            # Ensure the new zoom is not out of range right
            if new_zoom_end > 1:
                # Set to far right with the same range
                new_zoom_start = 1 - new_range
                new_zoom_end = 1
            # Set actual values
            self.zoom_start = new_zoom_start
            self.zoom_end = new_zoom_end
            # Maintain cursor position on the same frame
            self.set_cursor_on_frame(self.app.current_experiment.current_frame)

    def scroll_left(self):
        """Try scroll (zoom) left."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Calculate scroll amount
            old_range = self.zoom_end - self.zoom_start
            scroll_speed = old_range * 0.05
            # Preform the scroll
            new_zoom_start = self.zoom_start - scroll_speed
            new_zoom_end = self.zoom_end - scroll_speed
            # Ensure the new zoom is not out of range left
            if new_zoom_start < 0:
                # Set to far left with the same range
                new_zoom_start = 0
                new_zoom_end = old_range
            # Ensure not too small
            new_range = new_zoom_end - new_zoom_start
            min_range = self.app.current_experiment.zoom_max
            if new_range < min_range:
                # Set to min range centred on current values
                centre = (self.zoom_start + self.zoom_end) / 2
                new_zoom_start = centre - min_range / 2
                new_zoom_end = centre + min_range / 2
            # Ensure not out of range (sometimes is values like -0.0003201 etc.)
            if new_zoom_start <= 0:
                new_zoom_start = 0
            if new_zoom_end >= 1:
                new_zoom_end = 1
            # Set actual values
            self.zoom_start = new_zoom_start
            self.zoom_end = new_zoom_end
            # Maintain cursor position on the same frame
            self.set_cursor_on_frame(self.app.current_experiment.current_frame)

    def scroll_right(self):
        """Try scroll (zoom) right."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Calculate scroll amount
            old_range = self.zoom_end - self.zoom_start
            scroll_speed = old_range * 0.05
            # Preform the scroll
            new_zoom_start = self.zoom_start + scroll_speed
            new_zoom_end = self.zoom_end + scroll_speed
            # Ensure the new zoom is not out of range right
            if new_zoom_end > 1:
                # Set to far right with the same range
                new_zoom_start = 1 - old_range
                new_zoom_end = 1
            # Ensure not too small
            new_range = new_zoom_end - new_zoom_start
            min_range = self.app.current_experiment.zoom_max
            if new_range < min_range:
                # Set to min range centred on current values
                centre = (self.zoom_start + self.zoom_end) / 2
                new_zoom_start = centre - min_range / 2
                new_zoom_end = centre + min_range / 2
            # Ensure not out of range (sometimes is values like -0.0003201 etc.)
            if new_zoom_start <= 0:
                new_zoom_start = 0
            if new_zoom_end >= 1:
                new_zoom_end = 1
            # Set actual values
            self.zoom_start = new_zoom_start
            self.zoom_end = new_zoom_end
            # Maintain cursor position on the same frame
            self.set_cursor_on_frame(self.app.current_experiment.current_frame)

    def reset_zoom(self):
        """Reset the zoom to 100%."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Set actual values
            self.zoom_start = 0
            self.zoom_end = 1
            # Maintain cursor position on the same frame
            self.set_cursor_on_frame(self.app.current_experiment.current_frame)

    def set_cursor_on_frame(self, frame):
        """Will set the cursor on the given frame number."""
        # Find the current range of frames in view
        current = self.app.current_experiment
        start_frame = int((current.num_frames - 1) * self.zoom_start) + 1
        end_frame = int((current.num_frames - 1) * self.zoom_end) + 1
        # If the current frame is in the zoom range
        current_frame_in_range = start_frame <= frame <= end_frame
        if current_frame_in_range:
            # Calculate the proper position
            frame_range = end_frame - start_frame
            new_value = (frame - start_frame) / frame_range
        # If the current frame is out of view leftwards
        elif frame <= start_frame:
            # Just set to 0
            new_value = 0
        # If the current frame is out of view rightwards
        elif end_frame <= frame:
            new_value = 1
        # This shouldnt be possible, but still
        else:
            print('issue !')
            new_value = 0.5
        # Is it different to before?
        new_value_is_same = new_value == self.video_slider.value
        # Set actual value
        self.video_slider.value = new_value
        # Is it different to before?
        if new_value_is_same:
            # Update everything visually
            self.update_fields()

    def on_back_btn(self):
        """called by back btn
        - makes a BackPopup object
        - if there are no experiments, it immediately closes it"""
        # If there are any experiment boxes
        if len(self.exp_scroll.grid_layout.children) > 0:
            # Make pop up - asks if you are sure you want to exit
            popup = BackPopup(from_screen="IE3", to_screen="IE1")
            # Open it
            popup.open()
        # If there are not experiments
        else:
            # Make pop up - asks if you are sure you want to exit
            popup = BackPopup(from_screen="IE3", to_screen="IE1")
            # THEN IMMEDIATELY CLOSE IT
            popup.on_answer("yes")
    
    def add_start_here(self):
        """Called by 'Enter Start' button - Adds an event start if valid"""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Get params
            new_start = int(current.current_frame)
            ranges = current.event_ranges
            # Find if start is valid
            start_is_valid = True
            for start, end in ranges:
                # If new start overlaps with old ranges
                if start <= new_start <= end:
                    start_is_valid = False
                    break
            # If start is valid
            if start_is_valid:
                # Success! Add start.
                current.event_start_frame = new_start
                self.ready_for_start = False
        # Update everything visually
        self.update_fields()
    
    def add_stop_here(self):
        """Called by 'Enter Stop' button - Adds an event stop if valid"""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Get params
            ranges = current.event_ranges
            new_range = (current.event_start_frame, int(current.current_frame))
            # Find if range is valid
            range_is_valid = True
            # If stop smaller than start
            if new_range[0] >= new_range[1]:
                range_is_valid = False
            else:
                # Check for overlaps
                for old_range in ranges:
                    overlap_1 = (new_range[0] <= old_range[1] and new_range[1] >= old_range[0])
                    overlap_2 = (old_range[0] <= new_range[1] and old_range[1] >= new_range[0])
                    # If new range overlaps with old ranges
                    if overlap_1 or overlap_2:
                        range_is_valid = False
                        break
            # If range is valid
            if range_is_valid:
                # Success! Add range.
                current.event_start_frame = None
                current.event_ranges.append(new_range)
                self.ready_for_start = True
        # Update everything visually
        self.update_fields()
    
    def remove_here(self):
        """Called by 'Remove' button - Removes a start or an event if slider is on one."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Get params
            current_frame = int(current.current_frame)
            event_start_frame = current.event_start_frame
            event_ranges = current.event_ranges
            # If slider is on start
            if event_start_frame is not None and event_start_frame == current_frame:
                # Remove start
                current.event_start_frame = None
                self.ready_for_start = True
            else:
                # Find if on event range
                for start, end in event_ranges:
                    if start <= current_frame <= end:
                        # Remove range
                        current.event_ranges.remove((start, end))
                        break
        # Update everything visually
        self.update_fields()

    def on_key_up(self, key):
        """called when a key is released up
        - there are many results depending on the key"""
        # If there is a current experiment
        if self.app.current_experiment is not None:
            # If the 's' key is released
            if key == "s":
                # Add Stop or start depending which is next
                if self.ready_for_start:
                    self.add_start_here()
                else:
                    self.add_stop_here()
            # If the 'r' key is released
            elif key == "r" and self.slider_on_event:
                # Remove event 
                self.remove_here()
            # If the '<-' key is released
            elif key == "left":
                # If not adjusting the ion data
                if self.ion_adjust_btn.state != 'down':
                    self.scroll_left() 
                else:
                    self.ion_adjust_left()
            # If the 'r' key is released
            elif key == "right":
                # If not adjusting the ion data
                if self.ion_adjust_btn.state != 'down':
                    self.scroll_right() 
                else:
                    self.ion_adjust_right()
            # If the '+' key is released
            elif key == "=":
                # If not adjusting the ion data
                if self.ion_adjust_btn.state != 'down':
                    self.zoom_in() 
                else:
                    self.ion_adjust_in()
            # If the '-' key is released
            elif key == "-":
                # If not adjusting the ion data
                if self.ion_adjust_btn.state != 'down':
                    self.zoom_out() 
                else:
                    self.ion_adjust_out()
            # If the '0' key is released
            elif key == "0":
                # If not adjusting the ion data
                if self.ion_adjust_btn.state != 'down':
                    self.reset_zoom() 
                else:
                    self.ion_adjust_reset()
        return True

    def update_slider_on_event(self):
        """Updates the self.slider_on_event boolean."""
        on_event = False
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Get params
            current_frame = current.current_frame
            event_start_frame = current.event_start_frame
            event_ranges = current.event_ranges
            # If slider is on start
            if event_start_frame is not None and event_start_frame == current_frame:
                on_event = True
            # If still false
            else:
                # Find if frame is in ranges
                for start, end in event_ranges:
                    if start <= current_frame <= end:
                        on_event = True
                        break
        # Update with final value
        self.slider_on_event = on_event

    def ion_adjust_left(self, amount=1):
        """Try shift the ion data to the left."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            start, stop = current.ion_frame_range
            # Preform the scroll
            new_ion_start = start - amount
            new_ion_end = stop - amount
            # Set actual value
            current.ion_frame_range = (new_ion_start, new_ion_end)
            # Update everything visually
            self.update_fields()

    def ion_adjust_right(self, amount=1):
        """Try shift the ion data to the right."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            start, stop = current.ion_frame_range
            # Preform the scroll
            new_ion_start = start + amount
            new_ion_end = stop + amount
            # Set actual value
            current.ion_frame_range = (new_ion_start, new_ion_end)
            # Update everything visually
            self.update_fields()

    def ion_adjust_in(self, amount=1):
        """Try zoom into the ion data"""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            start, stop = current.ion_frame_range
            # Preform the zoom
            new_ion_start = start - amount
            new_ion_end = stop + amount
            # Set actual value
            current.ion_frame_range = (new_ion_start, new_ion_end)
            # Update everything visually
            self.update_fields()

    def ion_adjust_out(self, amount=1):
        """Try zoom into the ion data"""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            start, stop = current.ion_frame_range
            # Preform the zoom
            new_ion_start = start + amount
            new_ion_end = stop - amount
            # ensure not too small
            min_num_frames = min(100, current.num_frames)
            if new_ion_end - new_ion_start < min_num_frames:
                centre = (stop + start) / 2
                new_ion_start = int(centre - min_num_frames / 2)
                new_ion_end = int(centre + min_num_frames / 2)
            # Set actual value
            current.ion_frame_range = (new_ion_start, new_ion_end)
            # Update everything visually
            self.update_fields()

    def ion_adjust_reset(self):
        """Reset the ion data's alignment."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Set actual value
            current.ion_frame_range = (1, current.num_frames)
            # Update everything visually
            self.update_fields()

    def on_current_experiment(self, instance, current_experiment):
        """Called when current experiment changes. Updates slider"""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Update slider
            new_value = (current.current_frame - 1) / (current.num_frames - 1)
            new_value_is_same = new_value == self.video_slider.value
            self.video_slider.value = new_value
        else:
            # Update slider
            new_value = 0
            new_value_is_same = new_value == self.video_slider.value
            self.video_slider.value = new_value
        # Update bools
        self.ready_for_start = False if current is None else current.event_start_frame is None
        # Reset zoom
        self.zoom_start = 0
        self.zoom_end = 1
        # If cursor value didnt change
        if new_value_is_same:
            # Update everything visually
            self.update_fields()
        self.thumbnail_bar.update_thumbnails(different_exp=True)

    def on_slider(self):
        """Called when slider value changes. Updates things."""
        # Update everything visually
        self.update_fields()


class IonCurrentView(Image):
    """The widget which holds the image"""

    def __init__(self, **kwargs):
        """init method for the image widget in PS2"""
        # Call Image init method
        super(IonCurrentView, self).__init__(**kwargs)
        # Save app as an attribute
        self.app = App.get_running_app()

    def set_frame(self, pos):
        """Changes slider position based on click position on window."""
        # If user clicked on the ion current view
        if self.collide_point(*pos):
            # Take position as proportion of widget width
            self.video_slider.value = (pos[0] - self.x) / self.width

    def _on_touch_down(self, touch):
        """Called when touch down."""
        # If is on the ion current view
        if self.collide_point(*touch.pos):
            # Get the button and the shift key
            shift_is_down = self.app.shift_is_down
            button = touch.button
            # If the touch is a scrollleft or down with shift
            if button == "scrollleft" or (button == "scrolldown" and shift_is_down):
                # If not adjusting the ion data
                if self.ie3_window.ion_adjust_btn.state != 'down':
                    self.ie3_window.scroll_left() 
                else:
                    self.ie3_window.ion_adjust_left(amount=25)
            # If the touch is a scrollright or up with shift
            elif button == "scrollright" or (button == "scrollup" and shift_is_down):
                # If not adjusting the ion data
                if self.ie3_window.ion_adjust_btn.state != 'down':
                    self.ie3_window.scroll_right() 
                else:
                    self.ie3_window.ion_adjust_right(amount=25)
            # If the touch is a scrolldowm
            elif button == "scrolldown":
                # If not adjusting the ion data
                if self.ie3_window.ion_adjust_btn.state != 'down':
                    self.ie3_window.zoom_in() 
                else:
                    self.ie3_window.ion_adjust_in(amount=25)
            # If the touch is a scrollup
            elif button == "scrollup":
                # If not adjusting the ion data
                if self.ie3_window.ion_adjust_btn.state != 'down':
                    self.ie3_window.zoom_out() 
                else:
                    self.ie3_window.ion_adjust_out(amount=25)
            # If the touch is a left click
            elif button == "left":
                # Set frame
                self.set_frame(touch.pos)

    def _on_touch_move(self, touch):
        """Called when touch move."""
        # If is on the ion current view
        if self.collide_point(*touch.pos):
            # If the touch is a left click
            if touch.button == "left":
                # Set frame
                self.set_frame(touch.pos)

    def on_size(self, instance, current_size):
        """Called when size of widget changes."""
        # Update the widget's texture
        self.update_view()

    def update_view(self):
        """Updates the widget's texture."""
        # Get widget dimensions
        width, height = int(self.width), int(self.height)
        # Make white image
        image = ION_BACKGROUND_SHADE * np.ones((height, width, 3), dtype=np.uint8)
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Ensure zoom not out of range (sometimes is values like -0.0003201 etc.)
            if self.ie3_window.zoom_start <= 0:
                self.ie3_window.zoom_start = 0
            if self.ie3_window.zoom_end >= 1:
                self.ie3_window.zoom_end = 1
            # Get params
            start_frame = int((current.num_frames - 1) * self.ie3_window.zoom_start) + 1
            end_frame = int((current.num_frames - 1) * self.ie3_window.zoom_end) + 1
            frame_range = end_frame - start_frame
            frame_range = 1 if frame_range < 1 else frame_range
            current_frame = current.current_frame
            event_start_frame = current.event_start_frame
            current_frame_in_range = start_frame <= current_frame <= end_frame
            # If the current frame is in the zoom range
            if current_frame_in_range:
                # Draw grey rectangle at x position of slider (for frame) (frame - start_frame - 1) / (frame_range - 1)
                x1 = int(width * (current_frame - start_frame) / (frame_range + 1))
                x2 = int(width * (current_frame - start_frame + 1) / (frame_range + 1))
                cv2.rectangle(image, (x1, 0), (x2, height), ION_CURRENT_FRAME_COLOUR, -1)
            # Draw vertical blue box at frame of start of event
            if event_start_frame is not None:
                # If the start frame is in the zoom range
                start_frame_in_range = start_frame <= event_start_frame <= end_frame
                if start_frame_in_range:
                    # Draw vertical blue box at frame of start of event
                    x1 = int(width * (event_start_frame - start_frame) / (frame_range + 1))
                    x2 = int(width * (event_start_frame - start_frame + 1) / (frame_range + 1))
                    cv2.rectangle(image, (x1, 0), (x2, height), ION_EVENT_START_COLOUR, -1)
            # Draw event ranges
            for event_start_frame, event_stop_frame in current.event_ranges:
                # Is the start frame is in the zoom range?
                start_in_range = start_frame <= event_start_frame <= end_frame
                end_in_range = start_frame <= event_stop_frame <= end_frame
                # If event visible at all
                if start_in_range or end_in_range:
                    # Event in full view
                    if start_in_range and end_in_range:
                        start_x1 = int(width * (event_start_frame - start_frame) / (frame_range + 1))
                        stop_x2 = int(width * (event_stop_frame - start_frame + 1) / (frame_range + 1))
                    # Event over right edge
                    elif start_in_range:
                        start_x1 = int(width * (event_start_frame - start_frame) / (frame_range + 1))
                        stop_x2 = int(width * (frame_range + 1) / (frame_range + 1))
                    # Event over left edge
                    elif end_in_range:
                        start_x1 = int(width * (frame_range) / (frame_range + 1))
                        stop_x2 = int(width * (event_stop_frame - start_frame + 1) / (frame_range + 1))
                    # Draw range
                    cv2.rectangle(image, (start_x1, 0), (stop_x2 - 1, height), ION_EVENT_COLOUR, -1)
                    # Draw edges
                    cv2.line(image, (start_x1, 0), (start_x1, height), ION_EVENT_EDGE_COLOUR, 1)
                    cv2.line(image, (stop_x2, 0), (stop_x2, height), ION_EVENT_EDGE_COLOUR, 1)
            # If using the ion current, draw it
            if self.ie3_window.use_ion:
                # Decide to use down sampled signal or not
                downsample_too_small = len(current.downsampled_ioncurr_sig) * (self.ie3_window.zoom_end - self.ie3_window.zoom_start) < 25000
                use_OG = self.ie3_window.always_use_OG_sig or downsample_too_small
                # Get the signal (either original or downsampled)
                signal = current.ioncurr_sig if use_OG else current.downsampled_ioncurr_sig
                # Align/zoom signal to the video
                signal = align_sig_to_frames(signal, current.num_frames, current.ion_frame_range)
                # Trim signal for zoom
                start_sample_i = int((len(signal) - 1) * self.ie3_window.zoom_start)
                end_sample_i = int((len(signal) - 1) * self.ie3_window.zoom_end)
                # If they don't cover a whole value
                if start_sample_i == end_sample_i:
                    # If not at start
                    if start_sample_i > 0:
                        # Include previous one
                        start_sample_i -= 1
                    else:
                        # include the next one
                        end_sample_i += 1
                signal = signal[start_sample_i:end_sample_i]
                # Normalize the signal values to fit within the height of the image
                gap_x, gap_y = 1, 3 # this gives some breathing room
                # (use downsampled data)
                sig_min, sig_max = np.nanmin(signal), np.nanmax(signal)
                if sig_min == sig_max:
                    sig_min, sig_max = 0, 1
                normalized_signal = (signal - sig_min) / (sig_max - sig_min) * (height - gap_y * 2) + gap_y
                # Get values to draw (min/max values for every x value)
                min_array, max_array = split_min_max(normalized_signal, width - gap_x * 2)
                # For each pixel on the x-axis corresponding to a window of signal
                for x in range(width - gap_x * 2):
                    # Get the range of values here
                    min_sig, max_sig = min_array[x], max_array[x]
                    if not np.isnan(min_sig) and not np.isnan(max_sig):
                        # Draw a verticle line on that x value
                        cv2.line(image, (x + gap_x, int(min_sig)), (x + gap_x, int(max_sig)), ION_SIG_COLOUR, 1)
            # Draw vertical red line at x position of slider
            x = int((width - 1) * self.video_slider.value_normalized)
            cv2.line(image, (x, 0), (x, height), ION_CURSOR_COLOUR, 1)
        # Set as texture
        self.texture = kivify_image(image)

class ThumbnailBar(BoxLayout):
    """The layout which holds the row of thumbnails below the video."""

    # Integer for the number if thumbnails currently on the bar
    num_thumbnails = NumericProperty(1)
    # Float for the current x position of the cursor
    cursor_x = NumericProperty(-9999)

    def __init__(self, **kwargs):
        # Call the BoxLayout __init__ method
        super(ThumbnailBar, self).__init__(**kwargs)
        # Save app as an attribute
        self.app = App.get_running_app()

    def on_size(self, instance, current_size):
        """Called when size of widget changes."""
        # Update the thumbnail bar!
        self.update_thumbnails()

    def _on_touch_down(self, touch):
        """Called when touch down."""
        # If is on the thumbnail bar
        if self.collide_point(*touch.pos):
            # Get the button and the shift key
            shift_is_down = self.app.shift_is_down
            button = touch.button
            # If the touch is a scrollleft or down with shift
            if button == "scrollleft" or (button == "scrolldown" and shift_is_down):
                # Try scroll left
                self.ie3_window.scroll_left()
            # If the touch is a scrollright or up with shift
            elif button == "scrollright" or (button == "scrollup" and shift_is_down):
                # Try scroll right
                self.ie3_window.scroll_right()
            # If the touch is a scrolldowm
            elif button == "scrolldown":
                # Try zoom in
                self.ie3_window.zoom_in()
            # If the touch is a scrollup
            elif button == "scrollup":
                # Try zoom out
                self.ie3_window.zoom_out()

    def update_thumbnails(self, different_exp=False):
        """Checks current experiment's frames and dimensions of thumbnail bar to update the thumbnail bar."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Get dimensions of bar and frames
            frame_height, frame_width = current.first_frame.shape[:2]
            bar_width, bar_height = self.size
            # Use this ^ to determine number of frames to fit
            num_thumbnails = int(bar_width / (frame_width * bar_height / frame_height))
            # If not enough frames
            if num_thumbnails > current.num_frames:
                # Use all frames (do our best lol)
                num_thumbnails = current.num_frames
            # If either [the number of thumbnails] or [the current experiment] is changing
            if self.num_thumbnails != num_thumbnails or different_exp:
                # Update the thumbnail bar
                # Clear all thumbnails objects
                self.clear_widgets()
                # Makes all thumbnail objects
                for i in range(num_thumbnails):
                    # Get the proportion through the video
                    prop = i / (num_thumbnails - 1)
                    # Get frame to use
                    start_frame = int((current.num_frames - 1) * self.ie3_window.zoom_start)
                    end_frame = int((current.num_frames - 1) * self.ie3_window.zoom_end) + 1
                    frame_range = end_frame - start_frame
                    # Calculate the frame number based on the proportion
                    frame_num = start_frame + int((frame_range) * (prop - 10e-8)) + 1 # 1 -> num_frames
                    image = current.get_frame(frame_num)
                    # Downsize frame
                    min_width, min_height = int(bar_width / frame_width), int(bar_height)
                    image = downsample_image(image, min_width, min_height)
                    # Make and add thumbnail widget
                    thumbnail = Thumbnail(self, frame_num, texture=kivify_image(image))
                    self.add_widget(thumbnail)
                # Update num_thumbnails
                self.num_thumbnails = num_thumbnails
        else:
            # Clear all thumbnails objects
            self.clear_widgets()
        
    def update_cursor(self):
        """Updates the cursor x position (this will update the red line)."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Set cursor x according to slider position and zoom
            zoom_range = self.ie3_window.zoom_end - self.ie3_window.zoom_start
            self.cursor_x = self.width * ((self.video_slider.value_normalized * zoom_range) + self.ie3_window.zoom_start)
        else:
            self.cursor_x = -99999
        

class Thumbnail(Image):
    """The Image class for the thumbnails in the thumbnail bar."""

    def __init__(self, thumbnail_bar, frame_num, **kwargs):
        # Save bar as an attribute
        self.thumbnail_bar = thumbnail_bar
        # Call the Image __init__ method
        super(Thumbnail, self).__init__(**kwargs)
        # Save app as an attribute
        self.app = App.get_running_app()
        # Save the window as an attribute
        self.ie3_window = self.app.root.get_screen("IE3")
        # Set the frame number as current frame
        self.frame_num = frame_num

    def set_as_frame(self, pos):
        """Sets this frame as current if touch is a left click on this thumbnail."""
        # If there is a current experiment and the click is on this thumbnail
        current = self.app.current_experiment
        if current is not None and self.collide_point(*pos):
            # Set current frame as this frame
            self.ie3_window.set_cursor_on_frame(self.frame_num)
            