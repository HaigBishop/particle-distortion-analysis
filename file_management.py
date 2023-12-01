"""
Module: All functions related to file management
Program: Particle Deformation Analysis
Author: Haig Bishop (hbi34@uclive.ac.nz)
"""


# Import modules used for dealing with files
from datetime import datetime
import cv2
import os
import re
import numpy as np
from kivy.graphics.texture import Texture

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
