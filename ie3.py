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

# Import modules for dealing with files
import cv2
import numpy as np

# Import local modules
from popup_elements import BackPopup
from jobs import ExperimentBox
from file_management import kivify_image, split_min_max, downsample_image

# Set colour constants
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
    # Will display the downsampled signal if True
    use_downsampled = BooleanProperty(True) 


    def __init__(self, **kwargs):
        """init method for IE3 screen"""
        # Call ScrollView init method
        super(IE3Window, self).__init__(**kwargs)
        # Save app as an attribute
        self.app = App.get_running_app()

    def on_proceed(self):
        """called by pressing the 'Proceed' button."""
        # self.use_downsampled = not self.use_downsampled
        # print(self.use_downsampled)
        # # Update everything visually
        # self.update_fields()
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
            # Update with current experiment's values
            self.location_label.text = str(current.vid_loc)
            self.update_video()
            # Update frame label
            self.frame_label.text = 'Frame: ' + str(current.current_frame) + '/' + str(current.num_frames)
            # Update ion current file select section
            if self.use_ion and current.ion_loc != '':
                self.ion_location_label.text = str(current.ion_loc)
                self.ion_view.update_view()
            else:
                self.ion_location_label.text = 'No file selected'
                self.ion_view.update_view()
            # Update the thumbnail cursor
            self.thumbnail_bar.update_cursor()
        else:
            # Update slider
            self.video_slider.value = 0
            # Reset with defaults
            self.location_label.text = "No experiment selected"
            self.video_widget.texture = None
            self.ion_location_label.text = 'No file selected'
            # Update frame label
            self.frame_label.text = ''
            self.ion_view.texture = None
            # Update the thumbnail cursor
            self.thumbnail_bar.cursor_x = -999

    def update_video(self):
        """Update the video view by displaying the current frame."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Get frame to use
            image, frame_num = current.get_frame(self.video_slider.value_normalized)
            # Convert the image to a format useable for Kivy
            self.video_widget.texture = kivify_image(image)

    def on_back_btn(self):
        """called by back btn
        - makes a BackPopup object
        - if there are no experiments, it immediately closes it"""
        print(self.exp_scroll.grid_layout.children)
        # If there are any experiment boxes
        if len(self.exp_scroll.grid_layout.children) > 0:
            # Make pop up - asks if you are sure you want to exit
            popup = BackPopup("IE1")
            # Open it
            popup.open()
        # If there are not experiments
        else:
            # Make pop up - asks if you are sure you want to exit
            popup = BackPopup("IE1")
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
        # update slider_on_event
        self.update_slider_on_event()
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
        # update slider_on_event
        self.update_slider_on_event()
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
        # update slider_on_event
        self.update_slider_on_event()
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
            

    def on_current_experiment(self, instance, current_experiment):
        """Called when current experiment changes. Updates slider"""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Update slider
            self.video_slider.value = (current.current_frame - 1) / (current.num_frames - 1)
        else:
            # Update slider
            self.video_slider.value = 0
        # Update bools
        self.ready_for_start = False if current is None else current.event_start_frame is None
        # Update visual stuff
        self.update_slider_on_event()
        self.thumbnail_bar.update_thumbnails(different_exp=True)

    def on_slider(self):
        """Called when slider value changes. Updates things."""
        # update slider_on_event
        self.update_slider_on_event()
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
        # update slider_on_event
        self.ie3_window.update_slider_on_event()

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
            # Get params
            ranges = current.event_ranges
            num_frames = current.num_frames
            current_frame = current.current_frame
            event_start_frame = current.event_start_frame
            # Draw grey rectangle at x position of slider (for frame)
            x1 = int((width - 1) * (current_frame - 1) / (num_frames))
            x2 = int((width - 1) * (current_frame) / (num_frames))
            cv2.rectangle(image, (x1, 0), (x2, height), ION_CURRENT_FRAME_COLOUR, -1)
            # Draw vertical blue box at frame of start of event
            if event_start_frame is not None:
                x1 = int((width - 1) * (event_start_frame - 1) / (num_frames))
                x2 = int((width - 1) * (event_start_frame) / (num_frames))
                # Draw vertical blue box at frame of start of event
                cv2.rectangle(image, (x1, 0), (x2, height), ION_EVENT_START_COLOUR, -1)
            # Draw event ranges
            for start_frame, stop_frame in ranges:
                start_x1 = int((width - 1) * (start_frame - 1) / (num_frames))
                stop_x2 = int((width - 1) * (stop_frame) / (num_frames))
                # Draw range
                cv2.rectangle(image, (start_x1, 0), (stop_x2 - 1, height), ION_EVENT_COLOUR, -1)
                # Draw edges
                cv2.line(image, (start_x1, 0), (start_x1, height), ION_EVENT_EDGE_COLOUR, 1)
                cv2.line(image, (stop_x2, 0), (stop_x2, height), ION_EVENT_EDGE_COLOUR, 1)
            # If using the ion current, draw it
            if self.ie3_window.use_ion:
                # Get the signal (either original or downsampled)
                signal = current.downsampled_ioncurr_sig if self.ie3_window.use_downsampled else current.ioncurr_sig
                # Normalize the signal values to fit within the height of the image
                gap_x, gap_y = 1, 3 # this gives some breathing room
                # (use downsampled data)
                sig_min, sig_max = signal.min(), signal.max()
                normalized_signal = (signal - sig_min) / (sig_max - sig_min) * (height - gap_y * 2) + gap_y
                # Get values to draw (min/max values for every x value)
                min_array, max_array = split_min_max(normalized_signal, width - gap_x * 2)
                # For each pixel on the x-axis corresponding to a window of signal
                for x in range(width - gap_x * 2):
                    # Get the range of values here
                    min_sig, max_sig = int(min_array[x]), int(max_array[x])
                    # Draw a verticle line on that x value
                    cv2.line(image, (x + gap_x, min_sig), (x + gap_x, max_sig), ION_SIG_COLOUR, 1)
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

    def update_thumbnails(self, different_exp=False):
        """Checks current experiment's frames and dimensions of thumbnail bar to update the thumbnail bar."""
        # If there is a current experiment
        current = self.app.current_experiment
        if current is not None:
            # Get dimensions of bar and frames
            frame_width, frame_height = current.first_frame.shape[:2]
            bar_width, bar_height = self.size
            # Use this ^ to determine number of frames to fit
            num_thumbnails = int(2 * bar_width / (frame_width * bar_height / frame_height))
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
                    image, frame_num = current.get_frame(prop)
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
            # Set cursor x according to slider position
            self.cursor_x = self.width * self.video_slider.value_normalized
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
            self.ie3_window.video_slider.value = (self.frame_num - 1) / (current.num_frames - 1)
            # update slider_on_event
            self.ie3_window.update_slider_on_event()
            