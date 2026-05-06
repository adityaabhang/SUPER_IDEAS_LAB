THE FIX (5 minutes)
Step 1: Install Missing ROS2 Packages
bash# SSH to Jetson (if you're not already there)
ssh aabhang@jetson_ip

# Install MAVROS and dependencies
sudo apt update
sudo apt install -y ros-humble-mavros ros-humble-mavros-msgs

# Install other SUPER dependencies
sudo apt install -y \
  ros-humble-pcl-conversions \
  ros-humble-pcl-ros \
  ros-humble-tf2-eigen \
  ros-humble-nav-msgs \
  ros-humble-sensor-msgs \
  ros-humble-std-msgs \
  ros-humble-rviz2

# Verify mavros_msgs installed
ros2 pkg list | grep mavros
Expected output: Should show mavros and mavros_msgs in the list
Step 2: Source ROS2 in Current Shell
bash# Make sure current shell has ROS2 environment
source /opt/ros/humble/setup.bash

# Verify you can find mavros_msgs
ros2 pkg prefix mavros_msgs
# Should output path like: /opt/ros/humble/share/mavros_msgs
Step 3: Clean and Rebuild SUPER
bashcd ~/super_ws

# Remove old build artifacts
rm -rf build install log

# Rebuild SUPER with clean state
colcon build --symlink-install


IF BUILD STILL FAILS: Use rosdep (Nuclear Option)
If the above doesn't work, use rosdep to automatically install all missing dependencies:
bashcd ~/super_ws

# Check what rosdep finds
rosdep check --from-paths src/SUPER --rosdistro humble --ignore-src

# Install everything rosdep finds as missing
rosdep install -y --from-paths src/SUPER --rosdistro humble --ignore-src

# Clean and rebuild
rm -rf build install log
colcon build --symlink-install

VERIFY BUILD SUCCESS
After build completes:
bash# Check all packages built
ls -la ~/super_ws/install/

# Should show:
# - mars_quadrotor_msgs/
# - rog_map/
# - mission_planner/
# - marsim_render/
# - fast_lio/
# etc.

# Source the new build
source ~/super_ws/install/setup.bash

# List all SUPER packages
ros2 pkg list | grep -E "mars_|mission_|rog_"

# Test SUPER in simulation (no sensors needed)
ros2 launch mission_planner benchmark_dense.launch.py

# You should see RViz open with:
# - Dense forest environment
# - Planning trajectories
# - Obstacle map


# This will take 10-15 minutes on Jetson Orin Nano
# Watch for: "Finished <<< mission_planner"
