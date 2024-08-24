import cv2
import numpy as np
import math
from simplekml import Kml, Color
import json
import os
from datetime import datetime
from tqdm import tqdm  

'''
This script processes each frame containing lines that are stored in 'filtered_lines_by_length_and_slope_and_yaw.json'.
It finds the timestamp for each frame and then finds the closest location and magnetic heading data for that timestamp.
Finally, it calculates the GPS coordinates of the start and end points of each line and writes them into a KML file.
'''

# Helper function to convert location timestamp to seconds from start of the day
def location_timestamp_to_seconds(timestamp_str):
    dt = datetime.strptime(timestamp_str, '%Y%m%d.%H%M%S.%f')
    seconds = (dt - dt.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    return seconds

# Helper function to convert frame timestamp to seconds
def frame_timestamp_to_seconds(timestamp_str):
    dt = datetime.strptime(timestamp_str, '%H%M%S.%f')
    seconds = dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6
    return seconds

# Helper function to find the closest timestamp in location data
def find_closest_timestamp(target_timestamp, data):
    target_seconds = frame_timestamp_to_seconds(target_timestamp)
    min_diff = float('inf')
    closest_entry = None
    for entry in data:
        entry_timestamp = entry['time']
        entry_seconds = location_timestamp_to_seconds(entry_timestamp)
        diff = abs(entry_seconds - target_seconds)
        if diff < min_diff:
            min_diff = diff
            closest_entry = entry
    return closest_entry


# Initialize KML
kml = Kml()

motion_data_file_path = "locations_and_magneticHeadings.json"
timestamp_file_path = 'timestamp_of_each_frame.json'
lines_data_path = 'too_closed_lines_filter.json'

with open(motion_data_file_path, 'r') as file:
    location_data = json.load(file)

with open(timestamp_file_path, 'r') as timestamp_file:
    timestamp_data = json.load(timestamp_file)

with open(lines_data_path, 'r') as lines_file:
    lines_data = json.load(lines_file)

ref_pixel = (115, 170)  # Reference pixel coordinates in the image. we have the GPS coordinates of this pixel
pixel_scale_cm = 10  # GPS coordinates scale (1 pixel = 10 cm)
lines_geo_data = []

# Process each frame in lines_data
for frame_data in tqdm(lines_data):
    frame_number = frame_data['framenumber']
    
    # Find the corresponding timestamp for the frame number
    frame_timestamp = next((item['timestamp'] for item in timestamp_data if item['frame'] == frame_number), None)
    if not frame_timestamp:
        continue
    
    # Find the closest timestamp entry in location data
    closest_entry = find_closest_timestamp(frame_timestamp, location_data)
    if not closest_entry:
        continue

    # Extract location and heading data from the closest entry
    latitude_ref = closest_entry['latitude']
    longitude_ref = closest_entry['longitude']
    mobile_magnetic_heading = closest_entry['magneticHeading']

    camera_heading = mobile_magnetic_heading - 270
    magnetic_deviation = 5.08
    # Direction angle from the reference pixel to the top of the image
    direction_angle_deg = camera_heading +  magnetic_deviation
    if direction_angle_deg < 0:
        direction_angle_deg += 360 

    # Convert direction angle to radians
    direction_angle_rad = math.radians(direction_angle_deg)

    # Calculate distance between pixels in GPS coordinates (assuming a flat Earth approximation)
    gps_distance_per_pixel = pixel_scale_cm / 11132000  ## 100000km = 1cm , each 111.32 km = 1 degree

    # Prepare a dictionary for the current frame's lines with geographic coordinates
    frame_lines_geo = {
        'framenumber': frame_number,
        'coords': [latitude_ref, longitude_ref],
        'lines_pixel_on_top_view': {}
    }  
    
    # Process each line in the current frame data
    lines_pixel_on_top_view = frame_data.get('lines_pixel_on_top_view', {})
    for line_id, line_coords in lines_pixel_on_top_view.items():
        start_pixel = line_coords['start']
        end_pixel = line_coords['end']

        # Calculate offsets from reference pixel for start point
        dx_start =  ref_pixel[0] - start_pixel[0] 
        dy_start =  ref_pixel[1] - start_pixel[1]
        distance_start_pixels = math.sqrt(dx_start**2 + dy_start**2)
        angle_start_rad = math.atan2(dx_start, dy_start)
        angle_start_true_north_rad = direction_angle_rad - angle_start_rad
        delta_start_latitude = gps_distance_per_pixel * distance_start_pixels * math.cos(angle_start_true_north_rad)
        delta_start_longitude = gps_distance_per_pixel * distance_start_pixels * math.sin(angle_start_true_north_rad)
        start_latitude = latitude_ref + delta_start_latitude
        start_longitude = longitude_ref + delta_start_longitude

        # Calculate offsets from reference pixel for end point
        dx_end = ref_pixel[0] - end_pixel[0]
        dy_end = ref_pixel[1] - end_pixel[1]
        distance_end_pixels = math.sqrt(dx_end**2 + dy_end**2)
        angle_end_rad = math.atan2(dx_end, dy_end)
        angle_end_true_north_rad = direction_angle_rad - angle_end_rad
        delta_end_latitude = gps_distance_per_pixel * distance_end_pixels * math.cos(angle_end_true_north_rad)
        delta_end_longitude = gps_distance_per_pixel * distance_end_pixels * math.sin(angle_end_true_north_rad)
        end_latitude = latitude_ref + delta_end_latitude
        end_longitude = longitude_ref + delta_end_longitude

        # Add line to KML with yellow dashed style
        line = kml.newlinestring(coords=[(start_longitude, start_latitude), (end_longitude, end_latitude)])
        line.style.linestyle.color = Color.yellow
        line.style.linestyle.width = 1 

        frame_lines_geo['lines_pixel_on_top_view'][line_id] = {
            'start': [start_latitude, start_longitude],
            'end': [end_latitude, end_longitude]
        }

    # Append the frame's line data to the list
    lines_geo_data.append(frame_lines_geo)

with open('lines_coords.json', 'w') as lines_coord_file:
    json.dump(lines_geo_data, lines_coord_file, indent=4)

# Save KML file
kml.save("final_filter.kml")
