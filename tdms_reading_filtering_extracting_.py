"""Example of using TdmsFile module to read a bunch of files

Tip! use tdmsinfo from command line. 
e.g.
tdmsinfo -p [10.58.41]_mAsp_Q3.7_unmod_test.tdms

Also, the channels have the following properties which have not been accessed here:
    Voltage properties (data type: DaqMxRawData):
        NI_Scaling_Status: unscaled
        NI_Number_Of_Scales: 2
        NI_Scale[1]_Scale_Type: Polynomial
        NI_Scale[1]_Polynomial_Coefficients_Size: 4
        NI_Scale[1]_Polynomial_Coefficients[0]: 0.18922055823495115
        NI_Scale[1]_Polynomial_Coefficients[1]: 0.0008024242571535913
        NI_Scale[1]_Polynomial_Coefficients[2]: -2.2303461939076347e-14
        NI_Scale[1]_Polynomial_Coefficients[3]: 5.700822596099925e-19
        NI_Scale[1]_Polynomial_Input_Source: 0
        NI_ChannelName: Voltage
        wf_start_time: 2021-04-13T22:58:43.380022
        wf_increment: 1.5149999999999962e-05
        wf_start_offset: 0.0
        wf_samples: 1
    Strobe properties (data type: DaqMxRawData):
        NI_Scaling_Status: unscaled
        NI_Number_Of_Scales: 2
        NI_Scale[1]_Scale_Type: Polynomial
        NI_Scale[1]_Polynomial_Coefficients_Size: 4
        NI_Scale[1]_Polynomial_Coefficients[0]: 0.010836821753979362
        NI_Scale[1]_Polynomial_Coefficients[1]: 4.006979300618177e-05
        NI_Scale[1]_Polynomial_Coefficients[2]: -1.1137438770734735e-15
        NI_Scale[1]_Polynomial_Coefficients[3]: 2.8467581750455985e-20
        NI_Scale[1]_Polynomial_Input_Source: 0
        NI_ChannelName: Strobe
        unit_string: Volts
        NI_UnitDescription: Volts
        wf_start_time: 2021-04-13T22:58:43.380029
        wf_increment: 1.5149999999999962e-05
        wf_start_offset: 0.0
        wf_samples: 1

Documentation:
https://github.com/adamreeve/npTDMS/tree/74a312334d9f81120d6f3e4a7e8eb5552f17aec3
https://nptdms.readthedocs.io/en/stable/quickstart.html
"""

# Import modules
import os
from nptdms import TdmsFile
import numpy as np
from scipy.signal import savgol_filter, butter, filtfilt
import matplotlib.pyplot as plt
from scipy.fft import fft

# Get all tdms files in the directory
directory_path = 'C:/Users/haggi/Documents/School/mAsp/example_data'
file_paths = [os.path.join(directory_path, file) for file in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, file)) and str(file[-5:]).lower() == '.tdms']

# # For every tdms file
# for file_full_path in file_paths:

# Read one TDMS file
file_full_path = file_paths[3]
# Read file
tdms_file = TdmsFile.read(file_full_path)
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
voltage_channel = group['Voltage']
strobe_channel = group['Strobe']
# Extract the data from each channel
voltage_np = voltage_channel[:]
strobe_np = strobe_channel[:]
# Get dictionaries of properties
voltage_properties = voltage_channel.properties
strobe_properties = strobe_channel.properties
# Get number of datapoints in each channel
voltage_len = len(voltage_channel)
strobe_len = len(strobe_channel)
# Convert each channel to dataframes
voltage_df = voltage_channel.as_dataframe()
strobe_df = strobe_channel.as_dataframe()





# =================================================================
# Extraction and Filtering
### copying data_slider_GUI_V2.m

# A
# Get sampling frequency (two ways to do this)
# 1 - fs
t_step = voltage_properties['wf_increment']
fs = 1 / t_step
print(t_step)
print(fs)
# 2 - sample_rate
print(sample_rate)

# B
# Get current and strove signal
print(voltage_np)
print(strobe_np)

# B2
print(voltage_len)
time_scale = np.arange(t_step, t_step * (voltage_len + 1), t_step)
print(len(time_scale))
print(time_scale)
print(loop_factor)
time_cam = time_scale[::int(loop_factor)]
F = len(time_cam)
print(time_cam)
print(F)


# C (this does what FFTnFilter does... "filtering. reccomended. FFT shows mains hum")
# Filter (" uses several bandstop filters")
# Fast fourier transform
Y = fft(voltage_np)
# No clue why/what this is:
P2 = abs(Y/voltage_len)
P1 = P2[:voltage_len // 2 + 1]
f = fs * np.arange(0, (voltage_len / 2) + 1) / voltage_len
# Band stop filters
# Filter template function
def design_filter(frequency1, frequency2, fs, filter_order=2):
    nyquist = 0.5 * fs
    low = frequency1 / nyquist
    high = frequency2 / nyquist
    b, a = butter(filter_order, [low, high], btype='bandstop')
    return b, a
# Actually design filters
sos1_a, sos1_b = design_filter(49, 51, fs)
sos2_a, sos2_b = design_filter(99, 101, fs)
sos3_a, sos3_b = design_filter(149, 151, fs)
# Apply filters
current_filt1 = filtfilt(sos1_a, sos1_b, voltage_np)
current_filt2 = filtfilt(sos2_a, sos2_b, current_filt1)
current_filtered = filtfilt(sos3_a, sos3_b, current_filt2)


# D plot!
# "normalisation is performed after filtering"
current_norm = current_filtered / current_filtered[int(np.floor(fs*2))]
current_norm = current_filtered / np.max(current_filtered[int(np.floor(fs*2)):])
# Smooth signal
y = savgol_filter(current_norm, 1321, 1)

# Plot data
plt.figure()
plt.plot(time_scale, y)
plt.xlabel('time (s)')
plt.ylabel('I_n')
plt.show()

print(file_full_path)