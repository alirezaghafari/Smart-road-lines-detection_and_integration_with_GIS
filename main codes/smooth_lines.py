from tqdm import tqdm
import simplekml
import json
import numpy as np


'''
This code processes consecutive frames, combining the end point of a line from the prior frame with the start point of a line from the posterior frame. 
   This combination is done using probabilistic distribution (where points closer to the camera have higher probability and variance), 
   thereby smoothing out lines that are sequential but do not perfectly align, improving visual continuity.
   This probabilistic smoothing approach is similar to the Kalman filter, but in a much simpler form.

The results are saved into a KML file to visualize the smoothed lines.
'''



# This function combines points from consecutive frames that are close to each other and causes 
# lines in consecutive frames to be slightly apart, making the line not smooth.
# The function takes a list of points with their respective variances and combines them into a single point 
# with a new variance, effectively smoothing the line. 
def combine_points_with_variance(points_with_variance):
    if not points_with_variance:
        return None
    
    # Extract latitudes, longitudes, and variances
    latitudes = np.array([point[0] for point in points_with_variance])
    longitudes = np.array([point[1] for point in points_with_variance])
    variances = np.array([point[2] for point in points_with_variance])

    # Initialize with the first distribution
    mean_lat_new = latitudes[0]
    mean_lon_new = longitudes[0]
    var_new = variances[0]

    # Combine distributions incrementally
    for i in range(1, len(latitudes)):
        lat = latitudes[i]
        lon = longitudes[i]
        var = variances[i]

        # Calculate k and final variance for the new distribution
        k = var_new / (var_new + var)

        mean_lat_new = mean_lat_new + k * (lat - mean_lat_new)
        mean_lon_new = mean_lon_new + k * (lon - mean_lon_new)

        # Calculate final variance for the new distribution
        var_new = var_new * (1 - k) 

    return mean_lat_new, mean_lon_new, var_new


# Function to generate 50 points along a line and calculate variance
def generate_points_with_variance(start, end, frame_coord, num_points=50):
    start = np.array(start)
    end = np.array(end)
    frame_coord = np.array(frame_coord)
    t = np.linspace(0, 1, num_points)
    points = []
    for ti in t:
        point = start + (end - start) * ti
        distance = calculate_distance(point, frame_coord)
        var = 0.1 * distance  # Variance depends on distance
        points.append([point[0], point[1], var])
    return points

# Function to calculate variance for end_point and append it to end_point
def add_variance_to_end_point(end_point, frame_coord):
    end_point = np.array(end_point)  # Convert to np.array for computation
    distance = calculate_distance(end_point[:2], frame_coord)
    var = 0.1 * distance  # Variance depends on distance
    return np.append(end_point, var)  # Append variance to end_point

# Function to calculate distance in meters
def calculate_distance(point1, point2):
    lat1, lon1 = point1
    lat2, lon2 = point2
    lat_distance = (lat1 - lat2) * 111320  # Convert latitude distance to meters
    lon_distance = (lon1 - lon2) * (111320 * np.cos(np.radians(lat2)))  # Convert longitude distance to meters
    return np.sqrt(lat_distance**2 + lon_distance**2)

# Function to extract points and calculate variance for each line from frames
def extract_points_and_variance(sorted_data):
    all_points = {}
    for index, frame in enumerate(sorted_data):
        frame_number = index  # Use sorted index as frame number
        lines = frame['lines_pixel_on_top_view']
        frame_coords = frame['coords']
        # Create dictionary for current frame
        all_points[frame_number] = {
            'frame_coord': frame_coords,
            'lines': {}
        }
        
        for line_id, line in lines.items():
            start_point = line['start']
            end_point = line['end']
            
            # Generate 50 points along the line and calculate variance
            points = generate_points_with_variance(start_point, end_point, frame_coords, num_points=50)
            
            # Store points for each line
            all_points[frame_number]['lines'][line_id] = points
    
    return all_points

# Function to find frames within 50 meters of end_point
def find_nearby_frames(end_point, current_frame_index, sorted_data, distance_threshold=50):
    nearby_frames = []
    for index, frame in enumerate(sorted_data):
        if index <= current_frame_index:
            continue  # Skip current frame
        
        frame_coord = frame['coords']
        distance = calculate_distance(end_point[:2], frame_coord)
        
        if distance < distance_threshold:
            nearby_frames.append(index)
    
    return nearby_frames

# Function to find the closest point to end_point among the points in the identified frames
def find_closest_points(end_point, nearby_frames, all_points):
    closest_points = []
    for frame_number in nearby_frames:
        min_distance = float('inf')
        closest_point = None
        
        for line_id, line_points in all_points[frame_number]['lines'].items():
            for point in line_points:
                distance = calculate_distance(point[:2], end_point[:2])
                if distance < min_distance:
                    min_distance = distance
                    closest_point = point + [frame_number, line_id]  # Add frame number and line ID to closest_point
        
        if closest_point is not None and calculate_distance(end_point[:2],closest_point[:2]) < lines_merge_distance_threshold:
            closest_points.append(closest_point)
    
    return closest_points



def average_points(point1, point2):
    # Calculate the average of two points
    return [(point1[0] + point2[0]) / 2, (point1[1] + point2[1]) / 2]


lines_merge_distance_threshold = 1.1  # Distance threshold in meters; if the end of one line and the start of another line are within this distance, they will be merged.

with open('lines_coords.json', 'r') as f:
    data = json.load(f)

# Sort data based on frame number
sorted_data = sorted(data, key=lambda x: x['framenumber'])

np.set_printoptions(precision=15) 

# Extract points from each line in frames and calculate variance
all_points = extract_points_and_variance(sorted_data)

# Create a dictionary to store aggregated lines
aggregated_lines = {}

# Dictionary to keep track of unique line IDs
to_which_aggregated_line = {}
aggregated_line_counter = 0


for i, frame in tqdm(enumerate(sorted_data), total=len(sorted_data), desc="Processing frames"):
    lines = frame['lines_pixel_on_top_view']
    for line_id, line in lines.items():
        unique_line_id = (i, line_id)
        if unique_line_id not in to_which_aggregated_line:
            start_point = tuple(line['start'])
            aggregated_lines[aggregated_line_counter] = [start_point]
            to_which_aggregated_line[unique_line_id] = aggregated_line_counter
            aggregated_line_counter += 1
        
        end_point = tuple(line['end'])
        end_point_with_var = add_variance_to_end_point(np.array(end_point), frame['coords'])

        nearby_frames = find_nearby_frames(end_point_with_var, i, sorted_data, distance_threshold=50)
        closest_points = find_closest_points(end_point_with_var, nearby_frames, all_points)

        for cp in closest_points:
            cp_frame_index = cp[3]
            cp_line_id = cp[4]
            unique_cp_line_id = (cp_frame_index, cp_line_id)
            if to_which_aggregated_line.get(unique_cp_line_id) is None:
                to_which_aggregated_line[unique_cp_line_id] = to_which_aggregated_line[unique_line_id]
            else:
                current_path_index = to_which_aggregated_line[unique_cp_line_id]
                new_path_index = to_which_aggregated_line[unique_line_id]
                if calculate_distance(aggregated_lines[new_path_index][-1][:2],cp[:2])<calculate_distance(aggregated_lines[current_path_index][-1][:2],cp[:2]):
                    to_which_aggregated_line[unique_cp_line_id] = new_path_index
     
        all_points_to_combine = [end_point_with_var] + closest_points
        combined_point = combine_points_with_variance(all_points_to_combine)

        agg_line_index = to_which_aggregated_line[unique_line_id]
        if calculate_distance(aggregated_lines[agg_line_index][-1][:2],combined_point[:2]) >= 3.5:
            aggregated_lines[agg_line_index].append(combined_point)
        
    
kml = simplekml.Kml()

# calculate total length of aggregated lines. only lines with length of greater than 15m will write to kml file
for line_id, points in aggregated_lines.items():
    total_length = 0
    for j in range(len(points) - 1):
        total_length += calculate_distance(points[j][:2], points[j + 1][:2])

    if total_length >= 15: 
        coords = [(point[1], point[0]) for point in points] 
        linestring = kml.newlinestring(name=f"Line {line_id}")
        linestring.coords = coords
        linestring.style.linestyle.width = 2 
        linestring.style.linestyle.color = simplekml.Color.red  


kml.save("final_smoothed.kml")
print("KML file has been saved successfully.")
