"""
Module: All functions related to file management
Program: Particle Deformation Analysis
Author: Haig Bishop (haig.bishop@pg.canterbury.ac.nz)
"""

# Kivy imports
from kivy.graphics.texture import Texture

# Import modules
from datetime import datetime
import cv2
import os
import numpy as np
import json
from nptdms import TdmsFile
from scipy.signal import savgol_filter, butter, filtfilt
from moviepy.editor import VideoFileClip
import math

def select_increment(value_range, num_labels):
    """num_labels must be > 1"""
    # Calculate the step size between labels
    step_size = value_range / (num_labels - 1)
    # Determine using math!
    increment = 10 ** (round(math.log10(step_size / 5)))
    return increment

def round_to_increment(value, increment):
    rounded_value = round(value / increment) * increment + 0
    # Round again to remove trailing decimal point values e.g. 0.02300000005
    return round(rounded_value, 12)

def generate_y_axis_labels(min_value, max_value, num_labels):
    # Calculate the step size between labels
    step_size = (max_value - min_value) / (num_labels - 1) if num_labels > 1 else 0
    # Choose a "nice" increment for rounding (e.g., 1, 5, 10, etc.)
    nice_increment = select_increment((max_value - min_value), num_labels)
    rounded_min = round_to_increment(min_value, nice_increment)
    # Generate the labels using a list comprehension
    labels = [round_to_increment(rounded_min + i * step_size, nice_increment) for i in range(num_labels)]
    # Ensure the first and last are not out of range
    if labels[0] < min_value:
        new_val = round_to_increment(min_value, nice_increment / 10)
        labels[0] = new_val if new_val > labels[0] else labels[0]
    if labels[-1] > max_value:
        new_val = round_to_increment(max_value, nice_increment / 10)
        labels[-1] = new_val if new_val < labels[-1] else labels[-1]
    # Convert to strings plus strip trailing zeroes if present (e.g. 17.0 -> 17)
    labels = [str(label).rstrip('0').rstrip('.') if '.' in str(label) else str(label) for label in labels]
    return labels

def count_frames(video_loc):
    """Accurately finds the number of frames in the video.
    - assumes the video can be read"""
    # Read file using cv2
    cap = cv2.VideoCapture(video_loc)
    # Get number of frames from meta data
    num_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    # Test if this number is reliable
    cap.set(cv2.CAP_PROP_POS_FRAMES, num_frames - 1)
    is_good_1, frame = cap.read()
    cap.set(cv2.CAP_PROP_POS_FRAMES, num_frames)
    is_good_2, frame = cap.read()
    metadata_reliable = is_good_1 and not is_good_2
    # If it is not reliable
    if not metadata_reliable:
        # Read file using moviepy
        clip = VideoFileClip(video_loc)
        # Get number of fps and duration to estimate number of frames
        frame_count = int(clip.fps * clip.duration)
        clip.close()
        # Using this estimate, find a counting start point
        start_frame = frame_count
        jump_amount = 100
        was_good = None
        # Jump around frames until you find roughly where the end of the video is
        while True:
            # Try read this frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            is_good, frame = cap.read()
            # If first loop
            if was_good is None:
                # Act like nothing has changed
                was_good = is_good
            # If this frame is good and the previous frame was not good
            if is_good is True and was_good is False:
                # Found the end point roughly - end here
                start_frame -= 1
                break
            # If this frame is good and the previous frame was also good
            elif is_good is True and was_good is True:
                # Not at end yet - jump forward
                start_frame += jump_amount
                was_good = True
            # If this frame is not good and the previous frame was good
            elif is_good is False and was_good is True:
                # Found the end point roughly - end here
                start_frame -= jump_amount + 1
                break
            # If this frame is not good and the previous frame was also not good
            elif is_good is False and was_good is False:
                # Not at end yet - jump backwards
                start_frame -= jump_amount
                was_good = False
            # What.. this isn't good.
            else:
                # Abort
                start_frame = 0
                break
        # Using this estimate, find a counting start point
        start_frame = start_frame
        jump_amount = 10
        was_good = None
        # Jump around frames until you find roughly where the end of the video is
        while True:
            # Try read this frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            is_good, frame = cap.read()
            # If first loop
            if was_good is None:
                # Act like nothing has changed
                was_good = is_good
            # If this frame is good and the previous frame was not good
            if is_good is True and was_good is False:
                # Found the end point roughly - end here
                start_frame -= 1
                break
            # If this frame is good and the previous frame was also good
            elif is_good is True and was_good is True:
                # Not at end yet - jump forward
                start_frame += jump_amount
                was_good = True
            # If this frame is not good and the previous frame was good
            elif is_good is False and was_good is True:
                # Found the end point roughly - end here
                start_frame -= jump_amount + 1
                break
            # If this frame is not good and the previous frame was also not good
            elif is_good is False and was_good is False:
                # Not at end yet - jump backwards
                start_frame -= jump_amount
                was_good = False
            # What.. this isn't good.
            else:
                # Abort
                start_frame = 0
                break
        # Use this as the start frame
        num_frames = max(start_frame, 0)
        # Step forward frame-by-frame until you find the end
        while True:
            # Try read this frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, num_frames)
            is_good, frame = cap.read()
            # If readable
            if is_good:
                # Not at end yet - next frame
                num_frames += 1
            else:
                # Found the end :)
                break
        cap.release()
    return int(num_frames)

def kivify_image(image, resampling_method="linear"):
    """uses image to make kivy_image
    - image is a np array
    - kivy_image is a kivy compatible texture"""
    # If there is an image
    if isinstance(image, np.ndarray):
        image = cv2.flip(image, 0)
        # Make kivy version
        kivy_image = Texture.create(
            size=(image.shape[1], image.shape[0]), colorfmt="bgr"
        )
        # Set magnification resampling method to either nearest or linear
        kivy_image.mag_filter = resampling_method
        kivy_image.blit_buffer(
            image.tobytes(), colorfmt="bgr", bufferfmt="ubyte"
        )
    return kivy_image

def file_date(file_loc):
    if os.path.exists(file_loc):
        date = datetime.fromtimestamp(os.path.getctime(file_loc)).strftime(
            "%d/%m/%Y"
        )
    elif file_loc == '':
        date = "No file selected."
    else:
        date = "File not found."
    return date

def is_video_file(file_loc):
    """Checks if the file has a correct extension and is readable."""
    # Extract the file extension
    file_extension = os.path.splitext(file_loc)[1].lower()
    # List of common video file extensions
    video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv']
    # If the file extension is in the list of video extensions
    if file_extension in video_extensions:
        # Try open and read file
        try:
            # Read file into TdmsFile object
            cap = read_vid(file_loc)
            cap_is_none = cap is None
            # Release the video capture object if not None
            if not cap_is_none:
                cap.release()
        except Exception as e:
            # Failed to read file
            print("Failed to read video file: ", e)
            return False
        else:
            if cap_is_none:
                # Failed to read first frame
                print("Failed to read the first frame.")
                return False
            else:
                # Is readable video file!
                return True
    else:
        # Incorrect extension
        return False

def is_ion_file(file_loc):
    """Checks if the file has the correct extension and is readable, etc."""
    # Extract the file extension
    file_extension = os.path.splitext(file_loc)[1].lower()
    # If TDMS extension
    if file_extension == '.tdms':
        # Try open and read file
        try:
            # Read file into TdmsFile object
            tdms_file = TdmsFile.read(file_loc)
            file_properties = tdms_file._properties
            name = file_properties['name']
            loop_factor = file_properties['Loop Factor']
            group =  tdms_file['Current (nA)']
            ioncurr_channel = group['Voltage']
            strobe_channel = group['Strobe']
            ioncurr_channel.properties['wf_increment']
        except Exception:
            # Failed to read file
            print("Failed to read TDMS file.")
            return False
        else:
            # Is ion current TDMS file!
            return True
    else:
        # Incorrect extension
        return False

def read_vid(video_loc):
    # Open the video file
    cap = cv2.VideoCapture(video_loc)
    # Check if the video file is opened successfully
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return None
    # Read the first frame
    ret, frame = cap.read()
    # Check if the frame is read successfully
    if not ret:
        print("Error: Could not read the first frame.")
        return None
    return cap

def get_frame(cap, target_frame):
    """Returns the specified frame in the video (cap)."""
    # Set the video capture object to the target frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    # Read the frame from the video
    ret, frame = cap.read()
    # Check if the frame is read successfully
    if not ret:
        print("Error: Could not read frame.")
        return None
    return frame

def read_tdms(file_loc):
    """Starter function to read a TDMS file.
    returns basic info and data."""
    # Read file into TdmsFile object
    tdms_file = TdmsFile.read(file_loc)
    # Get properties for this tdms file!
    file_properties = tdms_file._properties
    # name = file_properties['name']
    # author = file_properties['Author']
    # description = file_properties['Description']
    # time = file_properties['datetime']
    sample_rate = file_properties['Sampling Rate']
    # adj_sample_rate = file_properties['Adj. Sampling Rate']
    # fps = file_properties['FPS']
    # adj_fps = file_properties['Adj. FPS']
    # exposure_time = file_properties['Camera Exposure Time (ms)']
    loop_factor = file_properties['Loop Factor']
    # Extract each group and channel
    group =  tdms_file['Current (nA)']
    ioncurr_channel = group['Voltage']
    strobe_channel = group['Strobe']
    # Extract the data from each channel
    ioncurr_np = ioncurr_channel[:]
    strobe_np = strobe_channel[:]
    # Get number of datapoints in each channel
    ioncurr_len = len(ioncurr_channel)
    strobe_len = len(strobe_channel)
    # Get sampling frequency
    t_step = ioncurr_channel.properties['wf_increment']
    sample_freq = 1 / t_step
    time_scale = np.arange(t_step, t_step * (ioncurr_len + 1), t_step)
    # Convert each channel to dataframes
    # ioncurr_df = ioncurr_channel.as_dataframe()
    # strobe_df = strobe_channel.as_dataframe()
    # Return some of it
    return ioncurr_np, strobe_np, ioncurr_len, strobe_len, t_step, sample_rate, loop_factor, time_scale

def design_filter(frequency1, frequency2, sample_freq, filter_order=2):
    """Template for a bandstop filter."""
    nyquist = 0.5 * sample_freq
    low = frequency1 / nyquist
    high = frequency2 / nyquist
    b, a = butter(filter_order, [low, high], btype='bandstop')
    return b, a

def fft_and_filter(ioncurr_np, sample_freq):
    """This function does what FFTnFilter.m does...
     - FFT shows mains hum (DOESNT ACTUALLY APPEAR TO USE THIS SO DELETED IT)
     - filter uses several bandstop filters     
     """
    # Band stop filters
    # Actually design filters
    sos1_a, sos1_b = design_filter(49, 51, sample_freq)
    sos2_a, sos2_b = design_filter(99, 101, sample_freq)
    sos3_a, sos3_b = design_filter(149, 151, sample_freq)
    # Apply filters
    current_filt1 = filtfilt(sos1_a, sos1_b, ioncurr_np)
    current_filt2 = filtfilt(sos2_a, sos2_b, current_filt1)
    current_filtered = filtfilt(sos3_a, sos3_b, current_filt2)
    return current_filtered

def normalise_and_smooth_sig(current_filtered, sample_freq):
    """normalisation is performed after filtering"""
    # Normalise
    current_norm = current_filtered / np.max(current_filtered)
    # Smooth signal
    y = savgol_filter(current_norm, 1321, 1)
    return y

def split_min_max(signal, width):
    """Takes a signal (1D numpy array) splits it width times and gets min max for each split.
    e.g. split_min_max([1,2,3,4,5,6], 3) -> (array([1., 3., 5.]), array([2., 4., 6.]))
    Can also handle uneven splits and width > len(signal)"""
    # Define arrays to return
    min_array, max_array = np.zeros(width), np.zeros(width)
    # Get the size of each division (might be decimal)
    ideal_window_size = len(signal) / width
    # For each pixel across width
    j = 0
    for i in range(width):
        # Set start and end of split range
        a = int(j)
        b = int(j + ideal_window_size)
        # If they don't cover a whole value include the next one
        b = b + 1 if a == b else b
        # Get split range and their min and max value
        current_window = signal[a:b]
        min_array[i], max_array[i] = np.nanmin(current_window), np.nanmax(current_window)
        # Move to the next split
        j += ideal_window_size
    return min_array, max_array

def downsample_image(image, min_width, min_height):
    min_width = 150 if min_width < 150 else min_width
    min_height = 150 if min_height < 150 else min_height
    # Get the original image dimensions
    height, width = image.shape[:2]
    # Choose the maximum scale factor to maintain aspect ratio
    scale_x = max(1, width // min_width)
    scale_y = max(1, height // min_height)
    scale_factor = max(scale_x, scale_y)
    # Calculate the new dimensions
    new_width = width // scale_factor
    new_height = height // scale_factor
    # Resize the image using the calculated dimensions
    resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    return resized_image

def align_sig_to_frames(signal, num_frames, frame_range):
    # Extract the frame range for the signal
    start, stop = frame_range
    # Calculate the amount of chopping and buffering to perform
    zoom = (stop - start + 1) / num_frames
    frames_to_chop_start = max(0, 1 - start) / zoom
    frames_to_buffer_start = max(0, -1 * (1 - start)) / zoom
    frames_to_chop_stop = max(0, stop - num_frames) / zoom
    frames_to_buffer_stop = max(0, -1 * (stop - num_frames)) / zoom
    num_samples = len(signal)
    samples_to_chop_start = int(num_samples * frames_to_chop_start / num_frames)
    samples_to_buffer_start = int(num_samples * frames_to_buffer_start / num_frames)
    samples_to_chop_stop = int(num_samples * frames_to_chop_stop / num_frames)
    samples_to_buffer_stop = int(num_samples * frames_to_buffer_stop / num_frames)
    # Chop and add buffers to the signal
    start_buffer = np.full(samples_to_buffer_start, np.nan, dtype=np.float64)
    chopped_signal = signal[samples_to_chop_start : num_samples - samples_to_chop_stop]
    stop_buffer = np.full(samples_to_buffer_stop, np.nan, dtype=np.float64)
    # Add buffers to the signal
    new_signal = np.concatenate((start_buffer, chopped_signal, stop_buffer))
    return new_signal

def is_valid_json_path(file_path, overwrite_ok=False):
    """Check if the file path is valid for writing a JSON file."""
    # Get the directory
    directory = os.path.dirname(file_path)
    # Check if the directory exists
    if not os.path.exists(directory):
        print(f"Error: Directory {directory} does not exist.")
        return False
    # Check if the directory is writable
    elif not os.access(directory, os.W_OK):
        print(f"Error: No write permissions in directory {directory}.")
        return False
    # Check if the file exists already
    elif not overwrite_ok and os.path.exists(file_path):
        print(f"Error: File {file_path} already exists.")
        return False
    # We good
    else:
        return True

def write_experiment_json(experiment, use_ion=True, overwrite_ok=False):
    """Given an Experiment object, writes a json file to describe it.
    Includes only the paths of the files for the video and ion current data.
    But, it does include events and their ion current data."""
    # Make a list to hold all events
    event_dictionaries = []
    # If we have any events selected
    if len(experiment.event_ranges) > 0:
        # Align/zoom signal to the video frames
        aligned_signal = align_sig_to_frames(experiment.ioncurr_sig, experiment.num_frames, experiment.ion_frame_range)
        # For every event
        i = 1
        for first_frame, last_frame in experiment.event_ranges:
            # If using ion
            if use_ion:
                # Grab ion current data between first_frame and last_frame
                start_i = int(((first_frame - 1) / experiment.num_frames) * len(aligned_signal))
                end_i = int(((last_frame) / experiment.num_frames) * len(aligned_signal) + 1)
                ion_data = aligned_signal[start_i : end_i]
                # As a python list with Nones not NaNs
                ion_data = [None if np.isnan(x) else x for x in ion_data.tolist()]
            # If not using ion
            else:
                ion_data = None
            # Construct a dictionary
            event_dict = {
                'id' : i,
                'startFrame' : first_frame, 
                'endFrame' : last_frame, 
                'numFrames' : last_frame - first_frame + 1,
                'ionCurrentData' : ion_data
            }
            # Add to the list
            event_dictionaries.append(event_dict)
            # next ID
            i += 1
    # Construct dictionary
    data_dict = {
        'timestamp' : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'name' : experiment.name,
        'videoFileDirectory' : experiment.directory,
        'videoFileExtension': experiment.file_extension,
        'videoHeight' : experiment.shape[0], 
        'videoWidth' : experiment.shape[1],
        'numFrames' : experiment.num_frames,
        'videoDate' : experiment.vid_date,
        'ionCurrentFile' : experiment.ion_loc if use_ion else None,
        'ionDate' : experiment.ion_date if use_ion else None,
        'ionDataLength' : experiment.ioncurr_len if use_ion else None,
        'ionSampleFrequency' : experiment.sample_freq if use_ion else None,
        'ionTimeStep' : experiment.t_step if use_ion else None,
        'ionLoopFactor' : experiment.loop_factor if use_ion else None,
        'ionFrameRange' : experiment.ion_frame_range if use_ion else None,
        'numEvents' : len(event_dictionaries),
        'events' : event_dictionaries,
    }
    # Make a file path (where video file is)
    file_path = experiment.directory + '\\' + experiment.name + '.json'
    # If this path is okay
    if is_valid_json_path(file_path, overwrite_ok=overwrite_ok):
        # Write file
        with open(file_path, 'w') as json_file:
            json.dump(data_dict, json_file, indent=2)
        # Nice!
        success = True
    else:
        # Damn!
        success = False
    return success, file_path

def load_experiment_json(json_file_loc):
    """Load experiment data from a JSON file and return an Experiment object.
    - Reads all data contained, only uses some
    - Does not actually load the ion current data itself, but related info
    - Only loads frame ranges for events, not events themselves"""
    errors = []

    # Read the file as a dict
    with open(json_file_loc, 'r') as json_file:
        data_dict = json.load(json_file)

    # Get video file path
    name = data_dict['name']
    directory = data_dict['videoFileDirectory']
    file_extension = data_dict['videoFileExtension']
    vid_loc = os.path.join(directory, name + file_extension)

    # Is this video file legit?
    if is_video_file(vid_loc):
        # Create Experiment object
        from jobs import Experiment # This prevents a circular import
        experiment = Experiment(vid_loc)

        # Add ion file path to experiment object
        ion_loc = data_dict['ionCurrentFile']

        # If there is an ion file attached and it is legit
        if ion_loc is not None:
            # Is this ion file legit?
            if is_ion_file(ion_loc):
                # Load the ion current data
                experiment.add_ion_file(ion_loc)
                # Add the alignment of the current and the video file
                experiment.ion_frame_range = data_dict['ionFrameRange']
            else:
                # The ion file could not be read
                errors.append('ion_read_fail')
        # Extract all other data from the loaded dictionary
        timestamp = datetime.strptime(data_dict['timestamp'], "%Y-%m-%d %H:%M:%S")
        shape = (data_dict['videoHeight'], data_dict['videoWidth'])
        num_frames = data_dict['numFrames']
        vid_date = data_dict['videoDate']
        ion_date = data_dict['ionDate']
        ioncurr_len = data_dict['ionDataLength']
        sample_freq = data_dict['ionSampleFrequency']
        t_step = data_dict['ionTimeStep']
        loop_factor = data_dict['ionLoopFactor']
        
        # Load event ranges (if any)
        event_dicts = data_dict['events']
        for event_dict in event_dicts:
                # Add the frame range to the experiment object
                start_frame = event_dict['startFrame']
                end_frame = event_dict['endFrame']
                experiment.event_ranges.append((start_frame, end_frame))
                # Load all other data
                event_id = event_dict['id']
                num_frames_event = event_dict['numFrames']
                ion_current_data = event_dict['ionCurrentData']

        # Add the JSON file to the experiment
        experiment.json_file_loc = json_file_loc
    else:
        # The video file could not be read
        experiment = None
        errors.append('vid_read_fail')
    return experiment, errors

def is_experiment_json(file_loc):
    """Check if the given JSON file follows the expected structure for experiment data."""
    try:
        # Try open JSON file 
        with open(file_loc, 'r') as json_file:
            data_dict = json.load(json_file)
        # Check for required keys in the loaded dictionary
        required_keys = ['timestamp', 'name', 'videoFileDirectory', 'videoFileExtension',
                         'videoHeight', 'videoWidth', 'numFrames', 'videoDate',
                         'ionCurrentFile', 'ionDate', 'ionDataLength',
                         'ionSampleFrequency', 'ionTimeStep', 'ionLoopFactor',
                         'ionFrameRange', 'numEvents', 'events']
        for key in required_keys:
            if key not in data_dict:
                return False
        # Check if the 'events' key contains a list of dictionaries
        if not isinstance(data_dict['events'], list):
            return False
        for event_dict in data_dict['events']:
            # Check for required keys in each event dictionary
            required_event_keys = ['id', 'startFrame', 'endFrame', 'numFrames', 'ionCurrentData']
            for key in required_event_keys:
                if key not in event_dict:
                    return False
            # Check if 'ionCurrentData' is a list
            if not isinstance(event_dict['ionCurrentData'], list):
                return False
        return True
    # Error
    except (json.JSONDecodeError, FileNotFoundError):
        return False