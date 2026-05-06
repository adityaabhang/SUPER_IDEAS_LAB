# CORRECT SUPER SETUP FOR JETSON - FAST_LIO IS SEPARATE
 
## THE TRUTH ABOUT SUPER
 
**SUPER is ONLY the planning framework.** It does NOT include FAST_LIO.
 
FAST_LIO is a **completely separate repository** that you need to clone independently.
 
---
 
## WHAT SUPER ACTUALLY CONTAINS
 
When you clone SUPER, you get:
```
~/super_ws/src/SUPER/
├── mission_planner/       ← Main planning framework
├── mars_quadrotor_msgs/   ← ROS2 messages
├── mars_uav_sim/          ← Simulation environment
├── ROG-Map/               ← Occupancy mapping
├── marsim_render/         ← Simulation rendering
└── (no FAST_LIO!)
```
 
**FAST_LIO is NOT a submodule.** You must clone it separately.
 
---
 
## THE CORRECT SETUP FOR YOUR JETSON
 
### Step 1: Build SUPER (Planning Framework Only)
 
```bash
cd ~/super_ws
 
# Install dependencies SUPER needs
source /opt/ros/humble/setup.bash
sudo apt install -y ros-humble-mavros ros-humble-mavros-msgs
 
# Update rosdep
rosdep update
rosdep install -y --from-paths src/SUPER --rosdistro humble --ignore-src
 
# Clean and build SUPER
rm -rf build install log
colcon build --symlink-install
```
 
**Expected**: mission_planner, mars_quadrotor_msgs, ROG-Map, marsim_render build successfully.
 
---
 
### Step 2: Build FAST_LIO2 Separately
 
FAST_LIO is a separate ROS2 package for LiDAR-IMU odometry.
 
```bash
# Clone FAST_LIO2 into your workspace
cd ~/ros2_ws/src
git clone https://github.com/hku-mars/FAST_LIO.git
 
# Navigate to workspace root
cd ~/ros2_ws
 
# Install FAST_LIO dependencies
rosdep update
rosdep install -y --from-paths src/FAST_LIO --rosdistro humble --ignore-src
 
# Build FAST_LIO2
colcon build --symlink-install --packages-select fast_lio
```
 
**Expected**: fast_lio package builds successfully.
 
---
 
## YOUR COMPLETE SETUP COMMAND SEQUENCE
 
**Copy and paste this entire block:**
 
```bash
# 1. Source ROS2
source /opt/ros/humble/setup.bash
 
# 2. Update system
sudo apt update
 
# 3. Install MAVROS
sudo apt install -y ros-humble-mavros ros-humble-mavros-msgs
 
# 4. SUPER (planning framework)
cd ~/ros2_ws/src
# If SUPER already exists:
ls SUPER 2>/dev/null || git clone https://github.com/hku-mars/SUPER.git
 
# 5. FAST_LIO2 (LiDAR-IMU odometry) - SEPARATE CLONE
# If FAST_LIO doesn't exist:
ls FAST_LIO 2>/dev/null || git clone https://github.com/hku-mars/FAST_LIO.git
 
# 6. Go to workspace root
cd ~/ros2_ws
 
# 7. Install all dependencies
rosdep update
rosdep install -y --from-paths src --rosdistro humble --ignore-src
 
# 8. Clean previous build
rm -rf build install log
 
# 9. Build both SUPER and FAST_LIO
colcon build --symlink-install
 
# 10. Verify both built
echo "=== SUPER Packages ==="
ros2 pkg list | grep -E "mars_|mission_|rog_"
 
echo ""
echo "=== FAST_LIO Package ==="
ros2 pkg list | grep fast_lio
 
# 11. Test SUPER
source install/setup.bash
ros2 launch mission_planner benchmark_dense.launch.py
```
 
---
 
## WHAT YOU'LL HAVE AFTER THIS
 
```
Your Jetson ROS2 Workspace:
~/ros2_ws/src/
├── SUPER/                    ← Planning framework
│   ├── mission_planner/
│   ├── mars_quadrotor_msgs/
│   ├── ROG-Map/
│   └── marsim_render/
│
└── FAST_LIO/                 ← LiDAR-IMU odometry (SEPARATE)
    ├── fast_lio/
    └── (supporting packages)
```
 
Both will be built in the same workspace and can work together.
 
---
 
## HOW THEY WORK TOGETHER
 
1. **Livox LiDAR** publishes point cloud to `/livox/lidar`
2. **Livox IMU** publishes to `/livox/imu`
3. **FAST_LIO2** reads both → outputs odometry to `/fast_lio/odometry/body`
4. **SUPER Planning** reads odometry + LiDAR point cloud → outputs `/motion_plan/path`
5. **MAVROS** sends commands to flight controller
---
 
## VERIFY EVERYTHING BUILDS
 
After running the commands above:
 
```bash
# Check all packages
source ~/ros2_ws/install/setup.bash
 
# Should see both:
ros2 pkg list | grep -E "mars_|mission_|rog_|fast_lio"
 
# Expected output:
# fast_lio
# mars_quadrotor_msgs
# mission_planner
# rog_map
# etc.
```
 
---
 
## IF BUILD STILL FAILS
 
Check which package is failing:
 
```bash
cd ~/ros2_ws
 
# Try building one at a time
colcon build --packages-select fast_lio --event-handlers console_direct+
 
# If FAST_LIO fails, check its dependencies:
rosdep check --from-paths src/FAST_LIO --rosdistro humble --ignore-src
 
# Or SUPER:
rosdep check --from-paths src/SUPER --rosdistro humble --ignore-src
```
 
---
 
## SUMMARY
 
| Component | What | Where |
|-----------|------|-------|
| **SUPER** | Planning framework | github.com/hku-mars/SUPER |
| **FAST_LIO** | LiDAR-IMU odometry | github.com/hku-mars/FAST_LIO |
| **Livox Driver** | LiDAR point cloud | github.com/Livox-SDK/livox_ros_driver2 |
| **MAVROS** | Flight controller bridge | apt install ros-humble-mavros |
 
All 4 are built separately but work together in ROS2.
 
---
 
**Run the command sequence now and report which step succeeds/fails!**
 
