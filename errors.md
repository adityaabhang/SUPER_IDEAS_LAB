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









/super_ws$ # 1. Source ROS2
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
ros2 launch mission_planner benchmark_dense.launch.py
Get:1 file:/var/cudnn-local-tegra-repo-ubuntu2204-9.3.0  InRelease [1,572 B]
Get:2 file:/var/l4t-cuda-tegra-repo-ubuntu2204-12-6-local  InRelease [1,572 B]
Get:1 file:/var/cudnn-local-tegra-repo-ubuntu2204-9.3.0  InRelease [1,572 B]
Get:3 file:/var/nv-tensorrt-local-tegra-repo-ubuntu2204-10.3.0-cuda-12.5  InRelease [1,572 B]
Get:2 file:/var/l4t-cuda-tegra-repo-ubuntu2204-12-6-local  InRelease [1,572 B]
Get:3 file:/var/nv-tensorrt-local-tegra-repo-ubuntu2204-10.3.0-cuda-12.5  InRelease [1,572 B]
Hit:4 https://brave-browser-apt-release.s3.brave.com stable InRelease          
Hit:5 http://packages.ros.org/ros2/ubuntu jammy InRelease                      
Hit:6 https://repo.download.nvidia.com/jetson/common r36.5 InRelease           
Get:7 https://download.docker.com/linux/ubuntu jammy InRelease [48.5 kB]
Hit:8 https://repo.download.nvidia.com/jetson/t234 r36.5 InRelease             
Hit:9 https://repo.download.nvidia.com/jetson/ffmpeg r36.5 InRelease
Hit:10 http://ports.ubuntu.com/ubuntu-ports jammy InRelease                    
Hit:11 http://ports.ubuntu.com/ubuntu-ports jammy-updates InRelease            
Hit:12 http://ports.ubuntu.com/ubuntu-ports jammy-backports InRelease          
Hit:13 http://ports.ubuntu.com/ubuntu-ports jammy-security InRelease           
Fetched 48.5 kB in 11s (4,233 B/s)                                             
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
All packages are up to date.
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
ros-humble-mavros is already the newest version (2.14.0-1jammy.20260326.111819).
ros-humble-mavros-msgs is already the newest version (2.14.0-1jammy.20260307.204842).
0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.
bash: cd: /home/ideas-ad/ros2_ws/src: No such file or directory
Cloning into 'SUPER'...
remote: Enumerating objects: 970, done.
remote: Counting objects: 100% (199/199), done.
remote: Compressing objects: 100% (113/113), done.
remote: Total 970 (delta 124), reused 86 (delta 86), pack-reused 771 (from 1)
Receiving objects: 100% (970/970), 108.61 MiB | 6.90 MiB/s, done.
Resolving deltas: 100% (341/341), done.
Updating files: 100% (756/756), done.
CMakeLists.txt  doc      launch   Log  package.xml  README.md  src
config          include  LICENSE  msg  PCD          rviz_cfg
bash: cd: /home/ideas-ad/ros2_ws: No such file or directory
reading in sources list data from /etc/ros/rosdep/sources.list.d
Hit https://raw.githubusercontent.com/ros/rosdistro/master/rosdep/osx-homebrew.yaml
Hit https://raw.githubusercontent.com/ros/rosdistro/master/rosdep/base.yaml
Hit https://raw.githubusercontent.com/ros/rosdistro/master/rosdep/python.yaml
Hit https://raw.githubusercontent.com/ros/rosdistro/master/rosdep/ruby.yaml
Hit https://raw.githubusercontent.com/ros/rosdistro/master/releases/fuerte.yaml
Query rosdistro index https://raw.githubusercontent.com/ros/rosdistro/master/index-v4.yaml
Skip end-of-life distro "ardent"
Skip end-of-life distro "bouncy"
Skip end-of-life distro "crystal"
Skip end-of-life distro "dashing"
Skip end-of-life distro "eloquent"
Skip end-of-life distro "foxy"
Skip end-of-life distro "galactic"
Skip end-of-life distro "groovy"
Add distro "humble"
Skip end-of-life distro "hydro"
Skip end-of-life distro "indigo"
Skip end-of-life distro "iron"
Skip end-of-life distro "jade"
Add distro "jazzy"
Add distro "kilted"
Skip end-of-life distro "kinetic"
Skip end-of-life distro "lunar"
Add distro "lyrical"
Skip end-of-life distro "melodic"
Skip end-of-life distro "noetic"
Add distro "rolling"
updated cache in /home/ideas-ad/.ros/rosdep/sources.cache
#All required rosdeps installed successfully
[0.689s] ERROR:colcon:colcon build: Duplicate package names not supported:
- marsim_render:
  - SUPER/mars_uav_sim/marsim_render
  - src/SUPER/mars_uav_sim/marsim_render
- mission_planner:
  - SUPER/mission_planner
  - src/SUPER/mission_planner
- perfect_drone_sim:
  - SUPER/mars_uav_sim/perfect_drone_sim
  - src/SUPER/mars_uav_sim/perfect_drone_sim
- rog_map:
  - SUPER/rog_map
  - src/SUPER/rog_map
- super_planner:
  - SUPER/super_planner
  - src/SUPER/super_planner
=== SUPER Packages ===

=== FAST_LIO Package ===
bash: install/setup.bash: No such file or directory
Package 'mission_planner' not found: "package 'mission_planner' not found, searching: ['/opt/ros/humble']"

 
**Run the command sequence now and report which step succeeds/fails!**
 
