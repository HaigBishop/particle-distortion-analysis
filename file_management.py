"""
Module: All functions related to file management
Program: Particle Deformation Analysis
Author: Haig Bishop (hbi34@uclive.ac.nz)
"""

# Kivy imports
from kivy.graphics.texture import Texture

# Import modules
from datetime import datetime
import cv2
import os
import numpy as np
from nptdms import TdmsFile
from scipy.signal import savgol_filter, butter, filtfilt


def kivify_image(image):
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
            read_vid(file_loc)
        except Exception as e:
            # Failed to read file
            print("Failed to read video file: ", e)
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

def is_event_file(file_loc):
    return False

def read_vid(video_loc):
    # Open the video file
    cap = cv2.VideoCapture(video_loc)
    # Check if the video file is opened successfully
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return None
    return cap

def first_frame(video_loc):
    """Returns the first frame of the video at video_loc"""
    # Open the video file
    cap = cv2.VideoCapture(video_loc)
    # Check if the video file is opened successfully
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return None
    # Read the first frame
    ret, frame = cap.read()
    # Release the video capture object
    cap.release()
    # Check if the frame is read successfully
    if not ret:
        print("Error: Could not read the first frame.")
        return None
    return frame

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
        min_array[i], max_array[i] = current_window.min(), current_window.max()
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
