"""
Module: All functions related to file management
Program: Particle Deformation Analysis
Author: Haig Bishop (hbi34@uclive.ac.nz)
"""


# Import modules used for dealing with files
from datetime import datetime
import cv2
import os
import numpy as np
from kivy.graphics.texture import Texture
from nptdms import TdmsFile
from scipy.signal import savgol_filter, butter, filtfilt

def kivify_image(image):
    """uses image to make kivy_image
    - image is a np array
    - kivy_image is a kivy compatible texture"""
    # If there is an image
    if isinstance(image, np.ndarray):
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
    # Extract the file extension
    file_extension = os.path.splitext(file_loc)[1].lower()
    # List of common video file extensions
    video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv']
    # Check if the file extension is in the list of video extensions
    return file_extension in video_extensions

def is_event_file(file_loc):
    return False

def is_ion_file(file_loc):
    # Extract the file extension
    file_extension = os.path.splitext(file_loc)[1].lower()
    # List of common video file extensions
    ion_extensions = ['.tdms']
    # Check if the file extension is in the list of video extensions
    return file_extension in ion_extensions

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
    name = file_properties['name']
    author = file_properties['Author']
    description = file_properties['Description']
    time = file_properties['datetime']
    sample_rate = file_properties['Sampling Rate']
    adj_sample_rate = file_properties['Adj. Sampling Rate']
    fps = file_properties['FPS']
    adj_fps = file_properties['Adj. FPS']
    exposure_time = file_properties['Camera Exposure Time (ms)']
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
    ioncurr_df = ioncurr_channel.as_dataframe()
    strobe_df = strobe_channel.as_dataframe()
    # Return some of it
    return ioncurr_np, strobe_np, ioncurr_len, strobe_len, name, t_step, sample_freq, loop_factor, time_scale

def design_filter(frequency1, frequency2, sample_freq, filter_order=2):
    """Filter template function"""
    nyquist = 0.5 * sample_freq
    low = frequency1 / nyquist
    high = frequency2 / nyquist
    b, a = butter(filter_order, [low, high], btype='bandstop')
    return b, a

def fft_and_filter(ioncurr_np, ioncurr_len, sample_freq):
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
    current_norm = current_filtered / current_filtered[int(np.floor(sample_freq*2))]
    current_norm = current_filtered / np.max(current_filtered[int(np.floor(sample_freq*2)):])
    # Smooth signal
    y = savgol_filter(current_norm, 1321, 1)
    return y