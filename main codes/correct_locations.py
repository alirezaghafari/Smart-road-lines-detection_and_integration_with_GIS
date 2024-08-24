# This script corrects the error in mobile location data, specifically the error that occurs across the width of the street.
# The KML line file contains the true path driven. The erroneous locations are mapped onto the KML line to correct the error across the street width.
# The script reads a KML file containing points and a line, maps the points to the nearest point on the line using Shapely geometry operations,
# and saves the mapped points to a new KML file and updates the JSON data with the new coordinates, saving the updated data to a new JSON file.

import xml.etree.ElementTree as ET
from shapely.geometry import Point, LineString
import simplekml
import json

def parse_kml_line(kml_file):
    tree = ET.parse(kml_file)
    root = tree.getroot()
    namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
    coordinates = root.find('.//kml:LineString/kml:coordinates', namespace).text.strip()
    line_coords = []
    for coord in coordinates.split():
        lon, lat, _ = map(float, coord.split(','))
        line_coords.append((lon, lat))  # Use (longitude, latitude) format
    return LineString(line_coords)

def parse_kml_points(kml_file):
    tree = ET.parse(kml_file)
    root = tree.getroot()
    namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
    placemarks = root.findall('.//kml:Placemark', namespace)
    points = []
    for placemark in placemarks:
        coordinates = placemark.find('.//kml:coordinates', namespace).text.strip()
        lon, lat, _ = map(float, coordinates.split(','))
        points.append((lat, lon))  # Use (latitude, longitude) format
    return points

def nearest_point_on_line(line, point):
    """
    Find the nearest point on a Shapely LineString to a given point.

    Parameters:
    - line (LineString): Shapely LineString object representing the line.
    - point (Point): Shapely Point object representing the point.

    Returns:
    - Point: Shapely Point object representing the nearest point on the line.
    """
    return line.interpolate(line.project(point))

def map_points_to_line(points, kml_file):
    """
    Map a list of points to the nearest points on a line extracted from a KML file.

    Parameters:
    - points (list): List of tuples, each containing (latitude, longitude) of each point.
    - kml_file (str): Path to the KML file containing the line.

    Returns:
    - list: List of tuples, each containing (latitude, longitude) of each mapped point.
    """
    line = parse_kml_line(kml_file)
    mapped_points = []
    for point in points:
        point_geom = Point(point[1], point[0])  # (longitude, latitude)
        nearest_point = nearest_point_on_line(line, point_geom)
        mapped_points.append((nearest_point.y, nearest_point.x))  # (latitude, longitude)
    return mapped_points

def save_points_to_kml(points, output_file):
    kml = simplekml.Kml()
    for lat, lon in points:
        kml.newpoint(coords=[(lon, lat)])
    kml.save(output_file)

def load_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def save_json(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def map_json_points_to_line(json_data, kml_file):
    """
    Map a list of points from JSON data to the nearest points on a line extracted from a KML file.

    Parameters:
    - json_data (list): List of dicts with 'latitude' and 'longitude' keys.
    - kml_file (str): Path to the KML file containing the line.

    Returns:
    - list: List of dicts with 'latitude' and 'longitude' of the mapped points.
    """
    line = parse_kml_line(kml_file)
    mapped_points = []
    for point in json_data:
        point_geom = Point(point['longitude'], point['latitude'])  # (longitude, latitude)
        nearest_point = nearest_point_on_line(line, point_geom)
        mapped_point = {
            'latitude': nearest_point.y,
            'longitude': nearest_point.x
        }
        mapped_points.append(mapped_point)
    return mapped_points

# Paths to input KML and JSON files
points_kml_file = 'path_to_points_kml_file.kml'
line_kml_file = 'path_to_line_kml_file.kml'
json_file = 'path_to_input_json_file.json'

# Load and parse the KML points
points = parse_kml_points(points_kml_file)

# Map the points to the nearest points on the line in the KML file
mapped_points = map_points_to_line(points, line_kml_file)

# Save the mapped points to a new KML file
output_kml_file = 'path_to_output_kml_file.kml'
save_points_to_kml(mapped_points, output_kml_file)

# Print the original and mapped points
for original, mapped in zip(points, mapped_points):
    print(f"Original: {original} -> Mapped: {mapped}")

print(f"Mapped points have been saved to {output_kml_file}")

# Load the JSON data
data = load_json(json_file)

# Map the JSON points to the nearest points on the line in the KML file
mapped_json_points = map_json_points_to_line(data, line_kml_file)

# Update the original JSON data with the mapped points
for i, item in enumerate(data):
    item['latitude'] = mapped_json_points[i]['latitude']
    item['longitude'] = mapped_json_points[i]['longitude']

# Save the updated JSON data to a new JSON file
output_json_file = 'correctedLocation.json'
save_json(data, output_json_file)

print(f"Updated JSON data has been saved to {output_json_file}")
