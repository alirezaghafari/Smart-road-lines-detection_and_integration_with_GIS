import json
import simplekml

# This script processes a JSON file containing geographic coordinates and timestamps.
# It identifies and collects all entries where the latitude or longitude has changed compared to the previous entry.
# The script then saves these updated coordinates into a KML file for visualization in mapping applications.

def find_updated_coordinates(json_data):
    updated_times = []
    updated_coordinates = []

    previous_lat = None
    previous_long = None

    for item in json_data:
        lat = item.get('latitude')
        long = item.get('longitude')

        # Check if the current coordinates are different from the previous ones
        if lat != previous_lat or long != previous_long:
            updated_times.append(item['time'])
            updated_coordinates.append(item)

        previous_lat = lat
        previous_long = long

    return updated_times, updated_coordinates

def save_to_kml(coordinates, output_file):
    kml = simplekml.Kml()

    for coord in coordinates:
        lat, lon = coord['latitude'], coord['longitude']
        kml.newpoint(name=f"({lat}, {lon})", coords=[(lon, lat)])

    kml.save(output_file)
    print(f"KML file with coordinates has been saved: {output_file}")

with open('locations_data/locations_and_magneticHeadings.json', 'r') as file:
    json_data = json.load(file)

# Find all times when coordinates were updated
updated_times, updated_coordinates = find_updated_coordinates(json_data)
if updated_times:
    print("All times when coordinates were updated:")
    print(updated_times)
    print("Number of updated coordinates:", len(updated_coordinates))
    print()

    output_file = 'output_kmls/captured_locations.kml'
    save_to_kml(updated_coordinates, output_file)
else:
    print("No time found when coordinates were updated.")
