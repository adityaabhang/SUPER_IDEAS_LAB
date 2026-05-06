# Complete Roadmap: Jetson Orin Nano Autonomous Drone with SUPER Planning Framework

## Overview
This document provides a structured learning path with curated links and resources to help you independently understand and implement:
1. **SUPER Planning Framework** (HKU-MARS Lab)
2. **Jackson Library** (JSON serialization for data handling)
3. **Jetson Orin Nano Setup** (ROS2 + Flight Controller Integration)
4. **Motion Planning Filters** (Sensor Fusion & EKF for flight)

**Goal for Tomorrow**: Have the drone flying with autonomous motion planning.

---

## PART 1: SUPER Planning Framework Deep Dive

### What is SUPER?
A 280-mm MAV with a thrust-to-weight ratio >5.0 for agile flight in cluttered environments, using lightweight 3D LiDAR for long-range obstacle detection and an efficient planning framework that generates two trajectories—one for safety, another for speed.

### Key Resources to Explore

#### Official Repository Structure
- **Main SUPER Repo**: https://github.com/hku-mars/SUPER
  - **Start here**: Explore the README, directory structure, and configuration files
  - **What to look for**: How the planning framework is organized, module dependencies

#### Hardware Reference
- **SUPER Hardware Components**: https://github.com/hku-mars/SUPER-Hardware
  - Learn what sensors/motors they use for real deployments
  - Study the baseboard integration with Jetson
  - Note: Use this as a reference, not a requirement (your drone may differ)

#### Learning Path
1. **Step 1**: Read the SUPER paper abstract on Science Robotics (linked in the GitHub README)
   - Understand: What problem does SUPER solve? Why two trajectories?
   
2. **Step 2**: Clone and explore the repository structure
   ```
   mkdir -p super_ws/src && cd super_ws/src
   git clone https://github.com/hku-mars/SUPER.git
   cd SUPER && ls -la
   ```
   - What are the main modules? (Planning, Control, Simulation, etc.)
   - What does `mars_uav_sim/` contain?
   
3. **Step 3**: Build process understanding
   - The standard build uses: `colcon build --symlink-install`
   - Study why `--symlink-install` matters for development
   - Check: What does `select_ros_version.sh` do?

4. **Step 4**: Investigate launch files
   - Look at benchmark examples: `ros2 launch mission_planner benchmark_high_speed.launch.py` and `benchmark_dense.launch.py`
   - Question: What parameters differ between high-speed and dense forest modes?

### Key Challenge: Hardware Deployment
⚠️ **Important Note**: A detailed guide for deploying SUPER on real-world hardware will be available soon. In the meantime, refer to issue #5 for some helpful hints.

**Where to look for real-world hints**:
- GitHub Issues: https://github.com/hku-mars/SUPER/issues (especially issue #5)
- Community discussion on Jetson compatibility: Check issue #55 on Jetson Orin Nano + PX4 setup

---

## PART 2: Jackson Library for Data Handling

### Why Jackson?
Your drone generates JSON data (sensor readings, flight logs, waypoints). Jackson handles serialization/deserialization efficiently.

### Learning Resources (Self-Directed)

#### Official Starting Points
- **Jackson Tutorial (TutorialsPoint)**: https://www.tutorialspoint.com/jackson/index.htm
  - Simple, progressive introduction
  - **Your task**: Work through the basic ObjectMapper examples
  
- **Jackson ObjectMapper Deep Dive (Baeldung)**: https://www.baeldung.com/jackson-object-mapper-tutorial
  - Advanced features (custom serializers, annotations)
  - **Key to explore**: @JsonProperty, @JsonIgnore, @JsonInclude
  - **Question to answer**: How would you serialize a sensor reading with a timestamp?

#### GitHub Documentation
- **FasterXML Jackson Docs**: https://github.com/FasterXML/jackson-docs
  - Official documentation hub
  - **Explore**: Different Jackson modules and their use cases

#### Practical Tutorials
1. **DigitalOcean Jackson Guide**: https://www.digitalocean.com/community/tutorials/jackson-json-java-parser-api-example-tutorial
   - Complete examples with complex objects
   
2. **Medium: Jackson Library Basics**: https://rameshfadatare.medium.com/jackson-library-in-java-eef28ab9fb40
   - Real-world examples with annotations
   
3. **DEV Community Comprehensive Guide**: https://dev.to/sadiul_hakim/jackson-tutorial-comprehensive-guide-with-examples-2gdj
   - Multiple JSON processing patterns

### Applied Learning Task
**For Your Drone Context**:
- Create a Java class representing a drone waypoint with Jackson annotations
- Question: How would you deserialize a JSON flight plan into a List<Waypoint>?
- Reference: Look at Baeldung's example for array/list deserialization

### Maven Dependency (If Needed)
```xml
<dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
    <version>2.14.1</version> <!-- Use latest version -->
</dependency>
```

---

## PART 3: Jetson Orin Nano Setup & Flight Controller Integration

### Hardware Architecture Overview
Your system needs:
1. **Jetson Orin Nano** (companion computer, runs ROS2 + SUPER planning)
2. **Flight Controller** (PX4 or ArduPilot, runs low-level control)
3. **Communication bridge** (UART/Serial or Ethernet)

### Key Learning Resources

#### Official Jetson Setup
- **NVIDIA JetPack Installation**: https://developer.nvidia.com/embedded/jetson-orin-nano
  - Start with JetPack 6.2 (latest stable for Orin Nano)
  - **What to do**: Install JetPack using NVIDIA's official guide

#### Companion Computer Integration

**Primary Reference (Real-World Proven)**:
- **Seeed Studio: Control PX4 with Jetson Orin**: https://wiki.seeedstudio.com/control_px4_with_recomputer_jetson/
  - **Most valuable section**: UART/Serial communication setup
  - Learn the three methods: PX4 DDS, MAVSDK, MAVROS
  - Question: Which is best for your use case? (Hint: MAVROS for complex ROS2 systems)

**Official PX4 Documentation**:
- **Holybro Pixhawk-Jetson Baseboard**: https://docs.px4.io/main/en/companion_computer/holybro_pixhawk_jetson_baseboard
  - IP networking setup (if using Ethernet)
  - Static IP configuration in Netplan
  - How to test: `ping` the Pixhawk from Jetson

#### MAVROS Setup (Recommended Path)
- **Purpose**: Bridge PX4 autopilot messages into ROS2
- **Your learning path**:
  1. Understand MAVLink protocol (30 min read)
  2. Install MAVROS package
  3. Configure serial port (typically /dev/ttyTHS1 on Jetson)
  4. Test with: `ros2 topic list | grep /fmu/`

#### GPS-Denied Navigation (Relevant to Your Forest Scenario)
- **Hackster.io: GPS-Denied Drone with Jetson Orin Nano**: https://www.hackster.io/bandofpv/gps-denied-drone-with-nvidia-jetson-orin-nano-9f3417
  - Uses Isaac ROS VSLAM on Jetson Orin Nano with PX4 flight controller and Intel D435i camera for real-time localization and map building
  - Key insight: You need vision + LiDAR fusion for dense forests
  - **Your task**: Compare VSLAM approach vs. your LiDAR + YOLO + BoT-SORT stack

#### ROS2 on Jetson
- **NVIDIA ROS2 Humble on Jetson**: Search "ros2 jetson orin nano humble"
  - Standard ROS2 installation and colcon workspace setup
  - Your drone's sensor drivers will publish to ROS2 topics

### Power Management
- Use NVIDIA Jetson recommended power supplies (7-21V typical)
- Monitor: Jetson power consumption vs. flight time trade-off
- Reference: SUPER-Hardware repo shows their power module choices

### Common Pitfall to Avoid
- **MAVROS geographic dataset missing** → drone crashes on startup
  - Solution: Install geographic dataset when setting up MAVROS

---

## PART 4: Motion Planning Filters (EKF + Sensor Fusion)

### The Problem
Raw sensor data is noisy. Your drone has:
- IMU (high-frequency, drifts)
- Camera (detects objects, has latency)
- LiDAR (accurate range, but slower update)
- Maybe GPS (if outdoor)

**You need a filter to fuse all of this into a clean state estimate.**

### Extended Kalman Filter (EKF) Fundamentals

#### Understanding EKF
- **Academic Resource**: Sensor Fusion Guide: https://arashdeepsinghmaan.github.io/robotics_software_tutorial/SensorFusion.html
  - **Start here**: Understand state vector, measurement model, update rate
  - Key concept: Complementary filters for gyro+accel, EKF for nonlinear systems
  - **Question for yourself**: What is your state vector? (position, velocity, orientation, ...)

#### Research Papers (For Deep Understanding)
1. **Sensor Fusion for Drone Estimation (EKF)**: https://www.researchsquare.com/article/rs-7087667/v1
   - Uses EKF to fuse GPS, IMU, and barometric altimeter for 9-state vector estimation in various motion scenarios
   - **Study**: How they handle IMU drift, GPS outages
   
2. **Kalman Filter with Intermittent Measurements**: https://arxiv.org/pdf/2212.01599
   - Proposes a hybrid multisensor fusion framework using Kalman filter to fuse IMU, UWB, and YOLO detections with intermittent sensor failures
   - **Relevant to you**: Handling when camera/LiDAR drop frames
   
3. **VIO Drift Correction for Drone Racing**: https://arxiv.org/pdf/2512.20475
   - Uses EKF to fuse Visual-Inertial Odometry with YOLO-detected gate positions to eliminate accumulated drift
   - **Your scenario**: Replace "gates" with "LiDAR landmarks"

### Practical Implementation Guidance

#### Multi-Sensor Fusion Architecture
- **Reference Paper**: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5298584/
  - Describes EKF that loosely fuses absolute measurements (GPS, barometer) and relative measurements (IMU, visual odometry)
  - **Key insight**: Two-stage fusion (visual + IMU first, then GPS corrects)

#### Your Drone's Filter Design Task
**Based on your sensors (LiDAR, Camera, IMU)**:
1. Define state vector: x = [position, velocity, attitude, bias]
2. Predict step: IMU propagates state
3. Update step: Camera (YOLO detections), LiDAR (range measurements), BoT-SORT (tracking)
4. **Question**: How do you weight camera vs. LiDAR updates? (Hint: trust the better sensor)

### Existing Implementations to Reference
- **PX4 EKF**: Already running on your Pixhawk
  - You don't need to rewrite it, but understand what it fuses
  - Your Jetson planning layer sits *above* PX4's EKF
  
- **SUPER Framework's Planning**: Assumes good state estimates from onboard sensors
  - Study: How does SUPER use localization outputs?

---

## PART 5: Complete Integration Plan (Tomorrow's Workflow)

### Morning Setup Checklist
- [ ] **Jetson Environment**: JetPack 6.2 installed, ROS2 Humble working
- [ ] **SUPER Build**: Cloned, built, understand module structure
- [ ] **Flight Controller**: PX4/ArduPilot flashed, MAVROS bridge running
- [ ] **Sensors**: IMU, LiDAR, Camera drivers publish to ROS2

### Sensor Pipeline
```
Hardware Sensors
    ↓
ROS2 Drivers (publish raw data)
    ↓
EKF / Sensor Fusion Node (state estimation)
    ↓
SUPER Planning Framework (trajectory generation)
    ↓
MAVROS / Flight Controller (motor commands)
    ↓
Quadrotor Motors (thrust)
```

### Step-by-Step for Tomorrow

#### 1. **Verify Sensor Data Flow** (1-2 hours)
- Launch your camera + LiDAR + IMU drivers
- Command: `ros2 topic list` (see all published topics)
- Command: `ros2 topic echo /camera/...` (verify data arriving)
- Question for yourself: Are timestamps synchronized across sensors?

#### 2. **Test Communication with Flight Controller** (1 hour)
- Start MAVROS: `ros2 launch mavros px4.launch`
- Check: `ros2 topic list | grep /fmu/`
- Can you echo `/fmu/out/vehicle_odometry`?
- Try a simple arming test (safety checks first!)

#### 3. **Run SUPER in Simulation** (1-2 hours)
- Launch: `ros2 launch mission_planner benchmark_dense.launch.py`
- Watch RVIZ: Does it plan trajectories in the simulated forest?
- Understand: What parameters control planning speed vs. safety?
- Modify: Try a custom .pcd map (your forest environment)

#### 4. **Implement Sensor Fusion Node** (2-3 hours)
- **Option A** (Easier): Use PX4's built-in EKF
  - Verify it's fusing your sensors correctly
  - Monitor: `rostopic echo /fmu/out/vehicle_status`
  
- **Option B** (Custom): Write your own lightweight EKF
  - Reference: https://arashdeepsinghmaan.github.io/robotics_software_tutorial/SensorFusion.html
  - Language: C++ (for performance on Jetson) or Python (for speed of development)
  - Test with recorded bag file first, then live data

#### 5. **Close the Loop: Planning → Flight** (1-2 hours)
- SUPER generates waypoints: `/motion_plan/path`
- MAVROS sends to PX4: `/mavros/setpoint_position/local`
- Questions:
  - Is trajectory smooth?
  - Does drone actually follow it?
  - Latency acceptable?

#### 6. **Flight Test** (Start cautious!)
- Indoors first (if possible)
- High fence, spotter, failsafe configured
- Start hovering only, then simple paths
- **Safety**: Always have manual control override ready

---

## PART 6: Key Questions to Answer as You Learn

### SUPER-Specific
- [ ] How does SUPER differ from other planners (RRT*, Rapidly-exploring Random Trees, etc.)?
- [ ] What's the difference between the "safety" and "speed" trajectories?
- [ ] Can SUPER run in real-time on Jetson Orin Nano? (Compute budget?)
- [ ] How does it handle dynamic obstacles?

### Jackson-Specific (For Logging/Config)
- [ ] How would you serialize sensor calibration parameters to JSON?
- [ ] Can you deserialize a mission plan (waypoints) from a JSON file?
- [ ] What annotations help with versioning if your data format changes?

### Jetson/Flight Controller
- [ ] What's the latency between SUPER planning and actual motor response?
- [ ] How do you handle PX4 firmware updates? (breaks compatibility?)
- [ ] What ROS2 quality-of-service (QoS) settings work best for flight critical messages?
- [ ] Power management: How long can your drone fly with Jetson Orin Nano onboard?

### Sensor Fusion
- [ ] What's the update rate of each sensor? (IMU: ~100 Hz, LiDAR: ~20 Hz, Camera: ~30 Hz?)
- [ ] How do you handle when one sensor fails?
- [ ] Is an EKF the right choice, or should you use a particle filter?
- [ ] How do you tune the process/measurement noise covariances?

---

## PART 7: Useful Tools & Commands

### Repository Exploration
```bash
# Clone SUPER and explore
git clone https://github.com/hku-mars/SUPER.git
cd SUPER
ls -la
tree -L 2  # visualize directory structure

# Check CI/CD examples (how they test)
cat .github/workflows/*.yml

# Look for example configs
find . -name "*.yaml" | head -10
```

### ROS2 Debugging
```bash
# List all topics
ros2 topic list

# Echo sensor data (check arrival rate)
ros2 topic echo /camera/image_raw
ros2 topic hz /camera/image_raw  # frequency

# Record for offline analysis
ros2 bag record -a  # all topics
ros2 bag record /sensor1 /sensor2  # specific topics

# Playback recorded data
ros2 bag play rosbag2_file
```

### Jetson-Specific
```bash
# Monitor power and thermal
jtop  # requires: pip install jetson-stats

# Check GPU usage (during planning)
tegrastats

# Verify MAVROS is bridging correctly
ros2 topic list | grep /fmu/
```

---

## PART 8: Where to Get Help

### Community Forums
- **NVIDIA Jetson Forums**: https://forums.developer.nvidia.com/
  - Search: "Jetson Orin Nano + ROS2 + drone"
  
- **HKU-MARS GitHub Issues**: https://github.com/hku-mars/SUPER/issues
  - Real deployment experience from researchers
  - Issue #5 (hardware deployment), Issue #55 (Jetson Orin Nano compatibility)

- **ROS Discourse**: https://discourse.ros.org/
  - Ask specific MAVROS/PX4 integration questions

### Resources for Debugging
- **PX4 Flight Stack Docs**: https://docs.px4.io/main/en/
- **ROS2 Official Docs**: https://docs.ros.org/en/rolling/
- **MAVROS GitHub**: https://github.com/mavlink/mavros/wiki

---

## Summary: Tomorrow's Goal

**By end of day, you should have**:
1. ✅ SUPER framework built and understood (high-level architecture)
2. ✅ Jetson + PX4 talking via MAVROS
3. ✅ Sensor drivers publishing to ROS2 topics
4. ✅ Sensor fusion running (state estimates flowing)
5. ✅ SUPER planning generating trajectories
6. ✅ First test flight with autonomous planning active

**Remember**: The goal is *learning-by-doing*, not following a recipe. Ask yourself why each component exists. Tinker. Break things safely (in simulation first!). Then fly.

---

## Quick Reference Links

| Topic | URL | Purpose |
|-------|-----|---------|
| SUPER Main | https://github.com/hku-mars/SUPER | Clone, explore, build |
| SUPER Hardware | https://github.com/hku-mars/SUPER-Hardware | Understand real deployments |
| Jackson Tutorial | https://www.tutorialspoint.com/jackson/index.htm | Learn JSON serialization |
| Jetson Setup | https://wiki.seeedstudio.com/control_px4_with_recomputer_jetson/ | PX4 + Jetson integration |
| EKF Basics | https://arashdeepsinghmaan.github.io/robotics_software_tutorial/SensorFusion.html | Sensor fusion fundamentals |
| Drone Racing EKF | https://arxiv.org/pdf/2512.20475 | Advanced fusion example |
| PX4 Docs | https://docs.px4.io/main/en/ | Official flight controller docs |
| GPS-Denied Setup | https://www.hackster.io/bandofpv/gps-denied-drone-with-nvidia-jetson-orin-nano-9f3417 | VSLAM on Jetson example |

---

**Good luck!** Go build something awesome. 🚁
