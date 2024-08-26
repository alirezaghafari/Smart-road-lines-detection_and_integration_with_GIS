import json
import numpy as np
import matplotlib.pyplot as plt
import csv
from datetime import datetime

'''
This script processes line data from a JSON file, filtering out lines based on their length and slope.
We first plot the distribution of line lengths to help decide which lines may be considered noise 
based on their length. Lines with lengths deemed non-standard or outliers can be filtered out.
After that, we filter lines based on their slope. The aim is to remove lines with small slopes that might
be considered unusual or noise. However, we take into account that if the vehicle is turning or in a curve,
lines with small slopes should not be removed as these lines are expected in such scenarios.
Finally, we apply a distance-based filter to ensure lines are not too close to each other in a single frame.
The distance filter works by sorting lines from left to right and keeping lines that are farther apart
than a specified threshold distance.
'''


def euclidean_distance(point1, point2):
    return np.sqrt(np.sum((np.array(point1) - np.array(point2)) ** 2))

def plot_line_length_distribution(line_lengths):
    plt.figure(figsize=(10, 6))
    plt.hist(line_lengths, bins=50, color='purple', edgecolor='white')
    plt.xlabel('Line Length (meters)')
    plt.ylabel('Number of Lines')
    plt.title('Distribution of Line Lengths')
    plt.grid(True)
    plt.show()

def filter_lines_by_length(data, length_threshold):
    """
    Filter out lines shorter than the given threshold.
    
    Parameters:
    - data: List of frames with lines information.
    - length_threshold: Minimum length of lines to keep (in meters).
    
    Returns:
    - List of frames with filtered lines.
    """
    filtered_data = []
    
    for frame in data:
        lines = frame["lines_pixel_on_top_view"]
        filtered_lines = {}
        
        for line_id, line_coords in lines.items():
            start_point = line_coords["start"]
            end_point = line_coords["end"]
            length = euclidean_distance(start_point, end_point) / 10  # Convert length to meters
            
            if length >= length_threshold:
                filtered_lines[line_id] = line_coords
        
        if filtered_lines:  # Only add frame if it has lines remaining
            filtered_data.append({
                "framenumber": frame["framenumber"],
                "lines_pixel_on_top_view": filtered_lines
            })
    
    return filtered_data

def length_filter(data, output_file_path, length_threshold=3.5, plot_histogram_before_filter=False):
    """
    Process lines data: optionally plot distribution and filter lines based on length.
    
    Parameters:
    - data: List of frames with lines information.
    - output_file_path: Path to the output JSON file.
    - length_threshold: Minimum length of lines to keep (in meters).
    - plot_histogram_before_filter: Whether to plot the histogram of line lengths before filtering.
    """
    line_lengths = []
    count = 0
    
    for frame in data:
        lines = frame["lines_pixel_on_top_view"]
        for line_id, line_coords in lines.items():
            count += 1
            start_point = line_coords["start"]
            end_point = line_coords["end"]
            length = euclidean_distance(start_point, end_point) / 10  # Convert length to meters
            line_lengths.append(length)
    
    if plot_histogram_before_filter:
        plot_line_length_distribution(line_lengths)
    
    filtered_data = filter_lines_by_length(data, length_threshold)
    
    with open(output_file_path, 'w') as file:
        json.dump(filtered_data, file, indent=4)
    
    print(f"Filtered data by length saved to {output_file_path}")

    return filtered_data

def calculate_slope(start_point, end_point):
    x1, y1 = start_point
    x2, y2 = end_point
    if x2 == x1:  # Handle vertical lines
        return np.inf
    return (y2 - y1) / (x2 - x1)

def read_yaw_derivative_csv(file_path):
    yaw_derivative_data = {}
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            yaw_derivative_data[row['exact_time']] = float(row['yaw_derivative'])
    return yaw_derivative_data

def convert_json_timestamp_to_csv_time(json_timestamp):
    """
    Convert JSON timestamp to CSV time format (HH:MM:SS).
    
    Parameters:
    - json_timestamp: Timestamp string in JSON format (HHMMSS).
    
    Returns:
    - Time string in CSV format (HH:MM:SS).
    """
    json_time = datetime.strptime(json_timestamp[:6], '%H%M%S').time()
    return json_time.strftime('%H:%M:%S')

def filter_lines_based_on_slope_and_yaw(data, slope_threshold, yaw_derivative_data, yaw_derivative_threshold, timestamp_data):
    """
    Filter lines based on absolute slope and yaw_derivative.
    
    Parameters:
    - data: List of frames with lines information.
    - slope_threshold: Minimum absolute slope of lines to keep.
    - yaw_derivative_data: Dictionary of yaw derivatives with time as key.
    - yaw_derivative_threshold: Minimum yaw derivative value to keep lines.
    - timestamp_data: List of timestamp data.
    
    Returns:
    - List of frames with filtered lines.
    """
    filtered_data_by_length = []
    
    for frame in data:
        framenumber = frame["framenumber"]
        lines = frame["lines_pixel_on_top_view"]
        filtered_lines = {}
        
        json_timestamp = next(item for item in timestamp_data if item["frame"] == framenumber)["timestamp"]
        exact_time = convert_json_timestamp_to_csv_time(json_timestamp)
        
        yaw_derivative = yaw_derivative_data.get(exact_time, 0)
        
        for line_id, line_coords in lines.items():
            start_point = line_coords["start"]
            end_point = line_coords["end"]
            slope = calculate_slope(start_point, end_point)
            abs_slope = abs(slope)
            
            if abs_slope >= slope_threshold or abs(yaw_derivative) > yaw_derivative_threshold:
                filtered_lines[line_id] = {
                    "start": start_point,
                    "end": end_point
                }

        if filtered_lines:
            filtered_data_by_length.append({
                "framenumber": framenumber,
                "lines_pixel_on_top_view": filtered_lines
            })
    return filtered_data_by_length

def slope_filter(data, timestamp_data, yaw_derivative_data, output_file_path, slope_threshold, yaw_derivative_threshold):
    """
    Filter lines based on slope and yaw derivative, and save the results.
    
    Parameters:
    - data: List of frames with lines information.
    - timestamp_data: List of timestamp data.
    - yaw_derivative_data: Dictionary of yaw derivatives with time as key.
    - output_file_path: Path to the output JSON file.
    - slope_threshold: Minimum absolute slope of lines to keep.
    - yaw_derivative_threshold: Minimum yaw derivative value to keep lines.
    """
    filtered_data = filter_lines_based_on_slope_and_yaw(data, slope_threshold, yaw_derivative_data, yaw_derivative_threshold, timestamp_data)

    with open(output_file_path, 'w') as file:
        json.dump(filtered_data, file, indent=4)

    print(f"Filtered data by length and slope saved to {output_file_path}")

    return filtered_data


def filter_too_close_lines_in_a_frame(data,output_file_path, distance_threshold=2):
    """
    Filter lines in each frame based on the distance to the previous line.
    Starting from the left-most line, if the distance between the current line
    and the previous line is greater than the threshold, add it to the new dictionary.

    Parameters:
    - data: List of frames with lines information.
    - distance_threshold: Minimum distance between lines to keep (in meters).

    Returns:
    - List of frames with filtered lines based on the distance to the previous line.
    """
    filtered_data = []

    for frame in data:
        lines = frame["lines_pixel_on_top_view"]
        frame_lines = list(lines.items())
        
        # Sort lines from left-most to right-most based on the x-coordinate of the start point
        frame_lines.sort(key=lambda line: line[1]["start"][0])

        filtered_lines = {}
        previous_line = None
        
        for line_id, line_coords in frame_lines:
            if previous_line is None or (
                abs(line_coords["start"][0]- previous_line["start"][0])/10 > distance_threshold and
                abs(line_coords["end"][0]- previous_line["end"][0])/10 > distance_threshold
            ):
                filtered_lines[line_id] = line_coords
                previous_line = line_coords

        if filtered_lines:  
            filtered_data.append({
                "framenumber": frame["framenumber"],
                "lines_pixel_on_top_view": filtered_lines
            })
    with open(output_file_path, 'w') as file:
        json.dump(filtered_data, file, indent=4)

    print(f"Final filtered data saved to {output_file_path}")

    return filtered_data

# File paths
input_file_path = "output_jsons/lines_data.json"
timestamp_file_path = "output_jsons/timestamp_of_each_frame.json"
yaw_derivative_file_path = "IMU_data/Angular_Velocity.csv"

# Load the original data
with open(input_file_path, 'r') as file:
    original_data = json.load(file)

# Read the timestamp JSON file
with open(timestamp_file_path, 'r') as file:
    timestamp_data = json.load(file)

# Read the Angular_Velocity.csv file
# The `Angular_Velocity` used for filtering is obtained from the `vehicle_angular_velocity.py` script and includes 
# fields for time, yaw, and yaw_derivative. The `yaw_derivative` represents the angular velocity of the vehicle,
# which gives us an indication of how fast the vehicle is turning.
yaw_derivative_data = read_yaw_derivative_csv(yaw_derivative_file_path)

# Filter noises by length
filtered_lines_by_length = length_filter(
    original_data, 
    output_file_path="output_jsons/1_filtered_lines_by_length.json", 
    length_threshold=3.5, 
    plot_histogram_before_filter=True
)

# Filter noises by slope
filtered_lines_by_slope = slope_filter(
    filtered_lines_by_length,
    timestamp_data,
    yaw_derivative_data,
    output_file_path="output_jsons/2_filtered_lines_by_length_and_slope_and_yaw.json",
    slope_threshold=7,
    yaw_derivative_threshold=0.045
)

# Filter noises by too close lines
final_filtered_data= filter_too_close_lines_in_a_frame(
    filtered_lines_by_slope,
    output_file_path = "output_jsons/3_filtered_lines_by_length_and_slope_and_yaw_and_closeLines.json",
    distance_threshold=2)
