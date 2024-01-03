import numpy as np


signal = np.array([np.nan, np.nan])
sig_min, sig_max = np.nanmin(signal), np.nanmax(signal)
print(sig_min)
# if sig_min == sig_max:
#     sig_min, sig_max = 0, 1
# normalized_signal = (signal - sig_min) / (sig_max - sig_min) * (100 - 1 * 2) + 1
# # Get values to draw (min/max values for every x value)
# min_array, max_array = split_min_max(normalized_signal, width - gap_x * 2)
# # For each pixel on the x-axis corresponding to a window of signal
# for x in range(width - gap_x * 2):
#     # Get the range of values here
#     min_sig, max_sig = min_array[x], max_array[x]
#     if min_sig != np.nan and max_sig != np.nan:
#         # Draw a verticle line on that x value
#         cv2.line(image, (x + gap_x, min_sig), (x + gap_x, max_sig), ION_SIG_COLOUR, 1)