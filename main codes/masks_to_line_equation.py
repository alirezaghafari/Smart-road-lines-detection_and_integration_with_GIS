import cv2
import numpy as np
import glob
import os
import json
from tqdm import tqdm 

'''
This script processes predicted masks from a deep learning model (LaneAF) to identify and map lane lines.
Each non-zero pixel in the predicted mask corresponds to a detected line, and each line is 
clustered with a unique color value (e.g., (1,1,1), (2,2,2), etc.).
The script fits a linear equation to the pixels of each line using linear regression. 
It then determines the start and end points of each line. These start and end points are 
transformed to a top-view (bird's eye view) perspective to obtain their real-world coordinates 
relative to the camera coordinates. Finally, the positions of the lines for each frame are saved to a JSON file.
'''


image_points = np.array([[550, 0], [173, 58], [8, 81],
                         [979, 0], [286, 110], [1026, 110],
                         [682, 0], [785, 0], [882, 0],
                         [664, 110], [1395, 110]], dtype=np.float32)

object_points = np.array([[40, 0],[40,110],[40,113],
                          [160, 0], [70, 125], [130, 125],
                          [70,0],[100,0],[130,0],
                          [100,125],[160,125]], dtype=np.float32)

input_folder = "selected_frames/every_60th_mask/"  # masks folder
output_folder_fitted = "selected_frames/every_60th_fitted_lines/" # visualized fitted lines
output_folder_birdseye = "every_60th_bird's_eye_view/"  # visualized top views
output_json_path = "output_jsons/lines_data.json"  # position of each line (by line's startpoint and endpoint)

# Compute the homography matrix
h, status = cv2.findHomography(image_points, object_points)

frame_data = []

image_paths = glob.glob(input_folder + "*.png")

for img_path in tqdm(image_paths, desc="Processing images"):
    image = cv2.imread(img_path)
    image = image[185:, :]
    black_image = np.zeros_like(image)

    base_name = os.path.splitext(os.path.basename(img_path))[0]
    frame_number = int(base_name.split('_')[1])  # assuming the frame number is the second part

    lines_pixel_on_top_view = {}

    # Get unique colors in the image, excluding black (no line predicted)
    unique_colors = np.unique(image.reshape(-1, image.shape[2]), axis=0)
    unique_colors = unique_colors[~np.all(unique_colors == [0, 0, 0], axis=1)]
    
    for i, color in enumerate(unique_colors):
        line_pixels = np.column_stack(np.where(np.all(image == color, axis=-1)))
        
        if line_pixels.size == 0: # black pixels (no line predicted)
            continue
        
        # Fit a line to the pixels using linear regression
        A = np.vstack([line_pixels[:, 1], np.ones(len(line_pixels))]).T
        m, c = np.linalg.lstsq(A, line_pixels[:, 0], rcond=None)[0]
        max_x = max(line_pixels[:, 1])
        min_x = min(line_pixels[:, 1])

        if int(m * max_x + c) < 0:
            max_x = int((0 - c) / m)

        if int(m * min_x + c) < 0:
            min_x = int((0 - c) / m)

        # Draw the fitted line on a black image
        for x in range(min_x, max_x):
            y = int(m * x + c)
            if 0 <= y < black_image.shape[0]:
                if (color == [1, 1, 1]).all():
                    black_image[y, x] = [0, 0, 255]  
                elif (color == [2, 2, 2]).all():
                    black_image[y, x] = [0, 255, 0]  
                elif (color == [3, 3, 3]).all():
                    black_image[y, x] = [255, 0, 0]  
                elif (color == [4, 4, 4]).all():
                    black_image[y, x] = [255, 255, 0]  
                elif (color == [5, 5, 5]).all():
                    black_image[y, x] = [255, 0, 255]  
                elif (color >= [6, 6, 6]).all():
                    black_image[y, x] = [255, 165, 0]  

 
            # Determine the start and end points of the line
            start_point = np.array([max_x, int(m * max_x + c)]) if int(m * max_x + c) > int(m * min_x + c) else np.array([min_x, int(m * min_x + c)])
            end_point = np.array([min_x, int(m * min_x + c)]) if int(m * max_x + c) > int(m * min_x + c) else np.array([max_x, int(m * max_x + c)])
            
            # Transform start and end points to top-view coordinates
            start_point_birdseye = cv2.perspectiveTransform(np.array([[start_point]], dtype=np.float32), h)
            end_point_birdseye = cv2.perspectiveTransform(np.array([[end_point]], dtype=np.float32), h)
            lines_pixel_on_top_view[i] = {
                "start": start_point_birdseye[0][0].tolist(),
                "end": end_point_birdseye[0][0].tolist()
            }

    frame_data.append({
        "framenumber": frame_number,
        "lines_pixel_on_top_view": lines_pixel_on_top_view
    })

    # Save the visualized fitted lines image 
    output_path_fitted = os.path.join(output_folder_fitted, os.path.basename(img_path))
    cv2.imwrite(output_path_fitted, black_image)

    birdseye_view = np.zeros((170, 200, 3), dtype=np.uint8)

    for line_number, line_data in lines_pixel_on_top_view.items():
        start_point_birdseye = tuple(map(int, line_data["start"]))
        end_point_birdseye = tuple(map(int, line_data["end"]))
        color = (0, 255, 255) 
        cv2.line(birdseye_view, start_point_birdseye, end_point_birdseye, color, thickness=1)

    # Save the visualized top-view image
    output_path_birdseye = os.path.join(output_folder_birdseye, os.path.basename(img_path))
    cv2.imwrite(output_path_birdseye, birdseye_view)

with open(output_json_path, 'w') as json_file:
    json.dump(frame_data, json_file, indent=4)

print("Done!")
