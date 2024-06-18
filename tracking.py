"""
Module:  Support functions to predict/track the aspiration event
Program: Particle Deformation Analysis
Author: Haig Bishop (hbi34@uclive.ac.nz)
"""

import cv2
import numpy as np


def filter_circles_bbox(circles, bbox):
    """takes a list of circles (x, y, r) and a bounding box [x, y, x2, y2]'
    - returns a subset of the circles list
    - all circles must be positioned with centres inside of the bbox
    - the circle list is a weird shape (1, N, 3) because of Houghcircle"""
    # If there are any circles
    if circles is not None:
        # Get the x, y coordinates of the bounding box
        x1, y1, x2, y2 = bbox
        # Create a new array to store the circles that are within the bounding box
        new_circles = np.empty((0, 3), dtype=np.int32)
        # Iterate through all detected circles
        for circle in circles[0]:
            # Get the coordinates of the circle
            center_x, center_y, radius = circle[0], circle[1], circle[2]
            left_x, right_x = center_x - radius, center_x + radius
            bottom_y, top_y = center_y - radius, center_y + radius
            # Check if the center of the circle is within the bounding box
            if x1 < left_x and right_x < x2 and y1 < bottom_y and top_y < y2:
                # The center of the circle is inside the bounding box, keep it
                new_circles = np.vstack([new_circles, circle])
        # Reshape the array to shape (1, N, 3)
        circles = new_circles.reshape((1, new_circles.shape[0], new_circles.shape[1]))
        # If the circles are empty
        if circles.shape == (1, 0, 3):
            circles = None
    return circles


def get_best_circle(circles, expected_radius, expected_x):
    """takes a list of circles and an expected x pos and radius"""
    # This list will contain tuples like this:
    # (combined difference, circle, size difference, pos difference)
    master_list = []
    for x, y, r in circles:
        # Get their size difference
        size_difference = abs(r - expected_radius)
        # Get their position difference
        pos_difference = abs(x - expected_x)
        # Get combined score
        net_difference = size_difference + pos_difference
        # Add all to the list
        master_list.append((net_difference, (x, y, r), size_difference, pos_difference))
    # Get the circle with the lowest of both if possible
    circle = sorted(master_list)[0][1]
    return circle


def bounded_hough_circle(image, bbox, min_r, max_r, expected_radius, display=False):
    """takes an image, a bounding box, a min radius and a max radius
    - preforms hough transform iteratively until a circle is found
    - maximum # Iterations is 28
    - if no circles are found, an 'expected' circle is returned
    - each iteration the thresholds are decreased
    - the circles must be within the bbox
    - after Hough returns 1 or more circles, the 'best' one is picked"""
    # Define starting thresholds
    thres_1 = 150
    thres_2 = 75

    # The minimum distance between circles
    min_dist = 1
    # Define the expected circle in order to select the best one
    expected_x = int((bbox[0] + bbox[2]) / 2)
    expected_y = int((bbox[1] + bbox[3]) / 2)
        
    if display:
        disp_img = image.copy()
        expected_center = (expected_x, expected_y)
        cv2.circle(disp_img, expected_center, min_r, (0, 255, 0), 1)
        cv2.circle(disp_img, expected_center, expected_radius, (0, 255, 0), 1)
        cv2.circle(disp_img, expected_center, max_r, (0, 255, 0), 1)
        cv2.imshow('Expected & Min/Max Circles', disp_img)
        cv2.waitKey(0)

    # Loop until you find a circle or pass 28 iterations
    circles = None
    i = 0
    while circles is None and i < 28:
        i += 1
        # Attempt to detect circles in the grayscale image.
        circles = cv2.HoughCircles(
            image,
            cv2.HOUGH_GRADIENT,
            1,
            min_dist,
            param1=thres_1,
            param2=thres_2,
            minRadius=min_r,
            maxRadius=max_r,
        )
        
        if display and circles is not None:
            disp_img = image.copy()
            for circle in circles[0, :]:
                center = (int(circle[0]), int(circle[1]))
                radius = int(circle[2])
                cv2.circle(disp_img, center, radius, (0, 255, 0), 1)
            cv2.imshow('Circles 1', disp_img)
            cv2.waitKey(0)
        elif display:
            # print('no circles 1')
            pass

        # Filter circles outside of bbox
        circles = filter_circles_bbox(circles, bbox)
        
        if display and circles is not None:
            disp_img = image.copy()
            for circle in circles[0, :]:
                center = (int(circle[0]), int(circle[1]))
                radius = int(circle[2])
                cv2.circle(disp_img, center, radius, (0, 255, 0), 1)  # Draw the circle on the disp_img
            cv2.imshow('Circles 2', disp_img)
            cv2.waitKey(0)
        elif display:
            # print('no circles 2')
            pass

        # Increase thresholds
        thres_1 = int(thres_1 * 0.85)
        thres_2 = int(thres_2 * 0.85)
    # Format circles (all ints and remvove packet)
    if not circles is None:
        # Remove packet shell thing
        circles = circles[0]
        circles = [(int(x), int(y), int(r)) for x, y, r in circles]
        # Find the circle with the most likely size
        if len(circles) > 1:
            circle = get_best_circle(circles, expected_radius, expected_x)
        else:
            circle = circles[0]
    else:
        # Make up circle of expected size and pos
        print("NO CIRCLE FOUND")
        circle = (expected_x, expected_y, expected_radius)
        
    if display:
        disp_img = image.copy()
        center = (int(circle[0]), int(circle[1]))
        radius = int(circle[2])
        cv2.circle(disp_img, center, radius, (0, 255, 0), 1)  # Draw the circle on the disp_img
        cv2.imshow('The Circle', disp_img)
        cv2.waitKey(0)

    return circle

def calculate_alpha_beta(image):
    """Takes an image
    - returns alpha and beta values to optimally fix contrast/brightness"""
    # Automatic brightness and contrast optimisation with optional histogram clipping
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clip_hist_percent = 1
    # Calculate grayscale histogram
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist_size = len(hist)
    # Calculate cumulative distribution from the histogram
    accumulator = []
    accumulator.append(float(hist[0]))
    for index in range(1, hist_size):
        accumulator.append(accumulator[index - 1] + float(hist[index]))
    # Locate points to clip
    maximum = accumulator[-1]
    clip_hist_percent *= maximum / 100.0
    clip_hist_percent /= 2.0
    # Locate left cut
    minimum_gray = 0
    while accumulator[minimum_gray] < clip_hist_percent:
        minimum_gray += 1
    # Locate right cut
    maximum_gray = hist_size - 1
    while (
        accumulator[maximum_gray] >= (maximum - clip_hist_percent) and maximum_gray > 10
    ):
        maximum_gray -= 1
    # Calculate alpha and beta values
    alpha = 255 / (maximum_gray - minimum_gray)
    beta = -minimum_gray * alpha
    return alpha, beta

def detect_sides(image, display=False):
    """In the image it will predict the pipette position, angle and bottom"""
    
    # Copy and convert grayscale to RGB
    disp_img = cv2.cvtColor(image.copy(), cv2.COLOR_GRAY2RGB)

    # Get image dims
    height, width = image.shape

    # Blur to remove noise
    image = cv2.GaussianBlur(image, (17, 17), 0)

    if display:
        cv2.imshow("Blurred", image)
        cv2.waitKey(0)

    # Apply canny edge detection
    image = cv2.Canny(image, 40, 60, apertureSize=3)

    if display:
        cv2.imshow("Edges", image)
        cv2.waitKey(0)

    # Dialate binary image
    image = cv2.dilate(image, (3, 3), iterations=2)

    if display:
        cv2.imshow("Dialated", image)
        cv2.waitKey(0)

    # Find contours and draw with size of 2
    contours, hierarchy = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(image, contours, -1, (255, 255, 255), 2)

    if display:
        cv2.imshow("Contors", image)
        cv2.waitKey(0)

    # Apply Hough line transformation
    minLineLength = int(height / 5)
    maxLineGap = 3
    hough_lines = cv2.HoughLinesP(image, 1, np.pi/180, 115, minLineLength, maxLineGap)

    # Discard all lines too short
    # And return None if no lines
    if hough_lines is None:
        return 0, 0, 0, 0
    else:
        lines = []
        for line in hough_lines:
            x1, y1, x2, y2 = line[0]
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if length > minLineLength:
                lines.append((x1, y1, x2, y2))
    if lines is None:
        return 0, 0, 0, 0

    if display:
        for x1, y1, x2, y2 in lines:
            cv2.line(disp_img,(x1,y1),(x2,y2),(0,0,255),1)
        cv2.imshow("Hough lines", disp_img)
        cv2.waitKey(0)

    # Extract useful features from each line
    lines_features = []
    for x1, y1, x2, y2 in lines:
        # Get the 4 desired features from this line
        gradient = (x2 - x1) / (y2 - y1)
        x0 = int(x1 - gradient * y1)
        bottom_x = x1 if y1 > y2 else x2
        bottom_y = max(int(y1), int(y2))
        length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        # Add the line to the list of line features
        lines_features.append((gradient, x0, bottom_x, bottom_y, length))
        
    # Cluster based on x0 (ideal results in 4 vertical lines - all on pipette)
    new_list = []
    done = False
    # Sort by x0
    lines_features.sort(key=lambda x: x[1])
    # While we are still making changes
    while not done:
        done = True
        last_pair_was_diff = False
        # For each adjacent pair of lines
        for i in range(len(lines_features) - 1):
            # Get the two lines
            line_1_gradient, line_1_x0, line_1_bottom_x, line_1_bottom_y, line_1_length = lines_features[i]
            line_2_gradient, line_2_x0, line_2_bottom_x, line_2_bottom_y, line_2_length = lines_features[i + 1]
            # If they are the same line
            if abs(line_2_x0 - line_1_x0) <= 5:
                if last_pair_was_diff:
                    # Remove the last entry to new_list!
                    new_list.pop()
                # Group together by appending the best version of the line to the new list
                line_3_gradient = (line_1_gradient + line_2_gradient) / 2
                line_3_x0 = (line_1_x0 + line_2_x0) / 2
                line_3_bottom_x = (line_1_bottom_x + line_2_bottom_x) / 2
                line_3_bottom_y = max(line_1_bottom_y, line_2_bottom_y)
                line_3_length = max(line_1_length, line_2_length)
                new_list.append((line_3_gradient, line_3_x0, line_3_bottom_x, line_3_bottom_y, line_3_length))
                done = False
                last_pair_was_diff = False
            # If they are different lines
            else:
                # If this is iteration 1 add line 1
                if i == 0:
                    line_1 = (line_1_gradient, line_1_x0, line_1_bottom_x, line_1_bottom_y, line_1_length)
                    new_list.append(line_1)
                # Add line_2
                line_2 = (line_2_gradient, line_2_x0, line_2_bottom_x, line_2_bottom_y, line_2_length)
                new_list.append(line_2)
                last_pair_was_diff = True
        lines_features = new_list[:]
        new_list = []

    # Sort by x0
    lines_features.sort(key=lambda x: x[1])
    # Select the lines on the left and the right sides
    line_1, line_2 = lines_features[0], lines_features[-1]
    # Get the pipette angle (gradient) by averaging both lines
    pipette_angle = (line_1[0] + line_2[0]) / 2
    # Get the pipette bottom x positions
    left_bottom_x = int(min(line_1[2], line_2[2]))
    right_bottom_x = int(max(line_1[2], line_2[2]))
    # Get the pipette bottom y by averaging both lines
    bottom_y = int((line_1[3] + line_2[3]) / 2)
    return pipette_angle, left_bottom_x, right_bottom_x, bottom_y

def detect_particle(image, left_bottom_x, right_bottom_x, bottom_y, display=False):
    """In the image using the pipette position predict the particle position and size"""
    # Estimated size and pos
    expected_particle_radius = int((right_bottom_x - left_bottom_x) / 3)
    expected_particle_pos = (int((left_bottom_x + right_bottom_x) / 2), int(bottom_y + expected_particle_radius / 2))
    # Define the minimum and maximum radii to detect
    min_r = int(expected_particle_radius * 2/3)
    max_r = int(expected_particle_radius * 1.33333)
    # Define the bounding box to detect circles inside
    exp_x, exp_y = expected_particle_pos
    bbox = [exp_x - max_r, 
            exp_y - max_r, 
            exp_x + max_r, 
            exp_y + max_r]
    
    if display:
        disp_img = image.copy()
        x1, y1, x2, y2 = bbox
        # Draw the bounding box on the image
        cv2.rectangle(disp_img, (x1, y1), (x2, y2), (0, 255, 0), 1)
        cv2.imshow('bbox', disp_img)
        cv2.waitKey(0)

    # Perform iterative hough circle
    x, y, r = bounded_hough_circle(image, bbox, min_r, max_r, expected_particle_radius, display=display)
    return (x, y), r

def detect_start(image, display=False):
    """Detects the start state of the pipette and particle in the image"""
    # Auto adjust contrast and brightness
    alpha, beta = calculate_alpha_beta(image)
    image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if display:
        cv2.imshow("Start frame", image)
        cv2.waitKey(0)

    # Detect the pipette position, angle and bottom
    pipette_angle, left_bottom_x, right_bottom_x, bottom_y = detect_sides(image, display=display)
    # Detect the particle position and size
    particle_pos, particle_radius = detect_particle(image, left_bottom_x, right_bottom_x, bottom_y, display=display)
    # Return all that
    return particle_pos, particle_radius, pipette_angle, left_bottom_x, right_bottom_x
