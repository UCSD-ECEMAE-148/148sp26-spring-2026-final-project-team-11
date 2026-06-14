# Spring-2026-Final-Project-Team11
This repository contains all information regarding the DonkeyCar Taxi for team 11.

<h1 align="center">RoboCar Taxi using Lidar, ROS2, and OAK-D Lite</h1>

<br />
<div align="center">
    <img src="images\UCSDLogo_JSOE_BlueGold_Web.jpg" alt="Logo" width="400" height="100">
    <h3>ECE-MAE 148 Final Project</h3>
    <p>
    Team 11 Spring 2026
    </p>
</div>

<div align="center">
    <img src="images\20260610_163807.jpg" width="500" height="400">
</div>
<br>
<hr>


## Table of Contents
  <ol>
<li><a href="#team-members">Team Members</a></li>
    <li><a href="#abstract">Abstract</a></li>
    <li><a href="#Promises">Promises</a></li>
    <li><a href="#accomplishments">Accomplishments</a></li>
    <li><a href="#challenges">Challenges</a></li>
    <li><a href="#final-project-media">Final Project Media</a></li>
    <li><a href="#software">Software</a></li>
        <ul>
        <li><a href="#obstacle-avoidance">Obstacle Avoidance</a></li>
        <li><a href="#object-sign-detection">Object Sign Detection</a></li>
      </ul>
    <li><a href="#hardware">Hardware</a></li>
    <li><a href="#gantt-chart">Gantt Chart</a></li>
    <li><a href="#course-deliverables">Course Deliverables</a></li>
    <li><a href="#project-reproduction">Project Reproduction</a></li>
    <li><a href="#acknowledgements">Acknowledgements</a></li>
    <li><a href="#contacts">Contacts</a></li>
  </ol>

<hr>

## Team Members
Alan Ye - ECE [LinkedIn](https://www.linkedin.com/in/alan-ye-683ab6346/)

Wen Qiang - CS

Ryan Melson - MAE [LinkedIn](https://www.linkedin.com/in/ryan-melson-97ab44213/?skipRedirect=true)

<hr>

## Abstract
Our goal for the Final Project was to make a Taxi, that would bring a passenger, in our case a 3D printed duck, to a valid position to then stop for a short time and simulate a deboarding and boarding process. Using an enhance 2D LiDAR system coincided with an OAK-D Lite for visual confirmation and navigation. Valid parking being designated by a specific sign indicating temporary parking only. 
<hr>

## Promises
* Specific Object detection for allowed parking regions.
* Object / Pedestrian detection using the LiDAR module.
* Get the LiDAR unit operational into ROS2.
<hr>

## Accomplishments
* Navigated a complex network within a Linux environment and ROS2 packages. 
* Implemented a YOLO model to identify and track custom 3D-printed parking signs. 
* Successfully integrated and configured a LiDAR sensor.

## Future Work
If we were to redo this project in the future, it would have been necessary to spend more time learning and creating appropriate documentation on how to operate our LiDAR (see below for type). We would also need to learn how to implement it with an emergency stop feature and visually confirm passengers were on board. Visual confirmation being done with another OAK-D Lite camera with appropriate YOLO model. Being able to identify that it is at a stop and allowing the passenger to safely vacate the vehicle and the car understanding this as well. 
<hr>

## Challenges
* We ran into several component errors and issues leading us to have to delay our progress. As well as outside affairs we couldn't control. 
* LiDAR took a lot longer to learn and understand how it could be implemented into ROS2 than initially expected.
* Time was our biggest struggle especially when only having 3 team members, we all had to take on additional roles to get to the stage we eventually got to. 
<hr>

<h2 align="center">Final Project Demo Videos</h2>
<p align="center">Media below shows what we were able to complete for our Final project.</p>

<br />

<div align="center">
  <!-- VIDEO 1: SIGN DETECTION -->
  <h3>**Sign Detection Demo**</h3>
  <a href="https://www.youtube.com/watch?v=6DFxrUN5yMU" target="_blank">
    <img src="https://img.youtube.com/vi/6DFxrUN5yMU/0.jpg" alt="Sign Detection Demo" width="560" style="border-radius: 8px;" />
  </a>

  <br /><br /><br />

  <!-- VIDEO 2: WEB UI SIMULATION (SHORTS FORMAT) -->
  <h3>**Web UI simulation**</h3>
  <a href="https://www.youtube.com/shorts/nQIj7ubcuTM" target="_blank">
    <img src="https://img.youtube.com/vi/nQIj7ubcuTM/0.jpg" alt="Web UI simulation" width="320" style="border-radius: 8px; object-fit: cover;" />
  </a>

  <br /><br /><br />

  <!-- VIDEO 3: ROBOCAR DRIVING -->
  <h3>**Outside view of robocar driving around compound**</h3>
  <a href="https://www.youtube.com/watch?v=ZWnJwExIKY0" target="_blank">
    <img src="https://img.youtube.com/vi/ZWnJwExIKY0/0.jpg" alt="Outside view of robocar driving around compound" width="560" style="border-radius: 8px;" />
  </a>

  <br /><br /><br />

  <h3>**Slam Results**</h3>
  <a href="https://youtu.be/AAmaeHkyMxs" target="_blank">
    <img src="https://img.youtube.com/vi/AAmaeHkyMxs/0.jpg" alt="Outside view of robocar driving around compound" width="560" style="border-radius: 8px;" />
  </a>
  
</div>


<hr>

## Software --

### Overall Architecture
Our project bridges a high-level web dispatch system with low-level ROS2 navigation. The central logic is split between a Python Flask server (handling the state machine and UI), an OAK-D vision script (handling spatial AI and passenger telemetry), and the ROS2 `rclpy` packages controlling the physical actuators.

### Passenger UI & State Machine
The dispatch dashboard was built using HTML/CSS/JS and a Python Flask backend. 
- **The State Machine:** We utilized Python's `threading` library to run a continuous background physics/logic loop (`update_vehicle_physics`). This thread manages the active route, continuously calculating progress and transitioning between states (`Idle`, `Arrived at Pickup`, `In Transit`, `Waiting for Disembark`, and `Emergency Stop`).
- **Telemetry & Video Streaming:** The dashboard polls the Flask API for JSON state updates to move the digital car along a circular CSS map. Simultaneously, it embeds a live MJPEG byte stream (`multipart/x-mixed-replace`) generated by the camera script, providing the passenger with a real-time, low-latency cabin view.

### 📁 `web_dashboard/`
* **`app.py`**
    * **Description:** The main full-stack server application. It boots the Flask web framework, initializes the central vehicle state machine, spawns the non-blocking background simulation thread, and hosts the localized REST API endpoints.
    * **How to Run:**
        ```bash
        cd web_dashboard
        python app.py
        ```

### OAK-D Spatial Vision & YOLOv8
We utilized the DepthAI pipeline to implement real-time passenger verification and station detection.
- **Custom YOLOv8 Training:** We trained custom models to recognize our 3D-printed passenger duck and a custom parking sign, compiling them to run directly on the OAK-D's VPU.
- **Sensor Fusion:** By overlaying the 2D YOLO bounding boxes onto the OAK-D's stereo depth map (`YoloSpatialDetectionNetwork`), we could extract the Z-axis distance in millimeters. Once the sign's distance falls below a 0.5m threshold, the state machine registers a station arrival.
- **Safety Interlocks:** The camera script constantly verifies passenger presence. If the passenger is removed from the seat during transit, a hardware debouncing counter (preventing false-positives from blurs/shadows) trips, sending an API request to the central server that instantly forces the vehicle into an `Emergency Stop`.

### 📁 `vision/`
* **`passenger_cam.py`**
    * **Description:** The core Edge AI pipeline script. It configures the OAK-D Lite camera pipeline, loads the compiled custom YOLOv8 `.blob` models onto the camera's VPU, handles the spatial stereo depth fusion math, tracks passenger presence with frame-debounce safety logic, and streams the MJPEG live feed to the local network.
    * **How to Run:**
        ```bash
        cd vision
        python passenger_cam.py
        ```
* **`test_spatial_sign.py`**
    * **Description:** A dedicated hardware diagnostic and testing script used to validate the spatial coordinates and depth matching of the custom YOLOv8 traffic sign model prior to full integration.
    * **How to Run:**
        ```bash
        cd vision
        python test_spatial_sign.py
        ```

### Obstacle Avoidance & mapping --
We used the LD06 Lidar to implement obstacle avoidance within ROS2. The program logic is quite simple in that we are constantly scanning the 60 degrees in front of the robot. If an object is detected within our distance threshold, the robot will accordingly make a turn to avoid it. Our logic for selecting which direction to turn in is quite simple in that if the object is on the left side, we first turn right, and otherwise, we turn left. Both turning directions include a corrective turn to bring the robot back to the centerline of the track and continue lane following.

we utilize the slam toolbox for mapping and Foxglove Studio to visualize the SLAM process

To start the SLAM
First pull the docker image and download the Foxgolve Studio
```bash
      docker pull wuweowo/robocar:latest

```
launch the corresponding slam_launch file under 

home/donkey


## Hardware 

* __3D Printing:__ All board mounts, Raspberry Pi Mount, Camera Mount and containment.
* __Laser Cutting:__ Base plate to mount electronics and other components.

__Parts List__

* Traxxas Chassis with steering servo and sensored brushless DC motor
* Servo PDB
* Raspberry Pi
* WiFi adapter
* 64 GB Micro SD Card
* Adapter/reader for Micro SD Card
* Logitech F710 controller
* OAK-D Lite Camera
* SICK TiM 2D LiDAR
* VESC
* Anti-spark switch with power switch
* DC-DC Converter
* 4-cell LiPo battery
* Battery voltage checker/alarm
* DC Barrel Connector
* XT60, XT30, MR60 connectors
* USB-C to USB-A cable as well as USB-C to USB-C
* Micro USB to USB cable

__Baseplate__

<img src="images\chassis.png" height="300">

__Rasperry Pi Case/Shell__

<img src="images\rasp_pi.png" height="300">

__Camera Mount__

<img src="images\cam_mount.png" height="300">
<img src="images\camera.png" height="300">

__Circuit Diagram__

<img src="images\circuit.png" height="300">

__Board Mounts__

<img src="images\dcdc_conv.png" height="300">
<img src="images\gps_module.png" height="300">
<img src="images\servo_pdb.png" height="300">

__Parking Sign__

<img src="images\sign.png" height="300">

## Gantt Chart 

<img src="images\gantt.png" height="300">
<hr>

**References:** 
* [Spring 2023 Team 5](https://github.com/UCSD-ECEMAE-148/spring-2023-final-project-team-5) - GitHub Formatting
* [DepthAI](https://github.com/luxonis/depthai-python)
* [UCSD Robocar Framework](https://gitlab.com/ucsd_robocar2)

<hr>

## Contacts 

* Alan Ye (a8ye@ucsd.edu)- ECE [LinkedIn](https://www.linkedin.com/in/alan-ye-683ab6346/)

* Wen Qiang - CS

* Ryan Melson (rmelson@uscd.edu)- MAE [LinkedIn](https://www.linkedin.com/in/ryan-melson-97ab44213/?skipRedirect=true)

