import cv2
from datetime import datetime, timedelta
import json
import os


# We have the exact time of the first frame (obtained using a video recording application that records the exact start time 
# of the video in milliseconds). Now, we need to determine the exact time for all frames in the video so that we can match 
# the predictions made for each frame with the mobile sensor data and location information.

def get_frame_timestamps(video_path, start_time):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    start_datetime = datetime.strptime(start_time, '%H:%M:%S.%f')

    timestamps = []

    frame_no = 0
    while True:
        ret, _ = cap.read()
        if not ret:
            break

        current_frame_time = frame_no / fps
        frame_datetime = start_datetime + timedelta(seconds=current_frame_time)
        timestamps.append({
            "frame": frame_no,
            "timestamp": frame_datetime.strftime('%H:%M:%S.%f')
        })

        frame_no += 1

        # Clear the terminal screen after printing each frame number
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Frame:", frame_no, "of", frame_count)

    cap.release()
    return timestamps

video_file = ""
start_time = "09:23:56.224"
timestamps = get_frame_timestamps(video_file, start_time)

# Open a json file to write timestamps
with open('timestamp_of_each_frame.json', 'w') as file:
    json.dump(timestamps, file, indent=4)
