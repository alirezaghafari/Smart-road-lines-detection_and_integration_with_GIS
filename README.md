# Table of Contents

- [About](#about)
- [Demo](#demo)

# About

&nbsp;&nbsp;&nbsp;&nbsp;This repository contains the code and resources for my bachelor's thesis project at Amirkabir University of Tehran. The project focuses on the automated detection of road lines and integration into Geographic Information System (GIS) using smartphone-based camera and motion data. The approach leverages a deep learning model to detect road lines from videos, processes and filters the detected lines, and visualizes them on a map, providing an efficient and cost-effective solution for urban infrastructure monitoring.

This approach has two significant applications:

1. **Urban Infrastructure Monitoring**: The generated maps can assist municipalities in monitoring and improving road line markings.
2. **Autonomous Vehicles**: Accurate road line information provides crucial data for autonomous vehicle systems, helping them better identify paths and make decisions in situations where the distance is beyond the range of the vehicle's cameras and sensors.

> **Line detection deep learning model:** <br>
> &nbsp;&nbsp;&nbsp;&nbsp;For the road line detection, we utilized the [LaneAF](https://paperswithcode.com/paper/laneaf-robust-multi-lane-detection-with) model with DLA-34 backbone, which has been pre-trained on the CULane dataset. This model provides high accuracy in detecting lane markings under various conditions. The LaneAF model was developed by Hala Abualsaud and her collaborators. For more details on the LaneAF model and its implementation, please refer to the [LaneAF GitHub repository](https://github.com/sel118/LaneAF?tab=readme-ov-file).

# Demo

To better understand what has been accomplished in this project, here is a demonstration of the results. <br>
For testing the project, we selected two streets with a total length of 4 kilometers in Tehran city. [Tap to see the area on the map.](https://www.google.com/maps?q=35.756888,51.372461)<br>
To view the visualized lane lines of these two streets (final output of my project), simply drag and drop the [`final_smoothed_lines.kml`](<https://github.com/alirezaghafari/Smart-road-lines-detection_and_integration_with_GIS/tree/master/output_kmls/smoothed_lines(final_output)/>) file into a GIS tool such as Google Earth. Some of the images are shown below:

### Detected Road Lines Using LaneAF:

<p align="center">
  <img src="assets/detected_lines.gif" alt="Detected Road Lines" width="700"/>
</p>

### Visualized Lines on Map (Final Result of My Project):

<p align="center">
  <img src="assets/smoothed_lines.png" alt="Final Visualization" width="700"/>
</p>
