# JETSON BUILD FIX - COPY AND PASTE THESE COMMANDS IN ORDER
 
## RUN THESE COMMANDS ONE BY ONE ON YOUR JETSON
 
### Step 1: Check if ROS2 is sourced
 
```bash
echo $ROS_DISTRO
```
 
**Expected output**: `humble`
 
**If empty or error**: Run this first:
```bash
source /opt/ros/humble/setup.bash
echo $ROS_DISTRO
```
 
---
 
### Step 2: Verify mavros_msgs exists
 
```bash
ros2 pkg list | grep mavros
```
 
**Expected output**:
```
mavros
mavros_msgs
```
 
**If empty**: Install it:
```bash
sudo apt update
sudo apt install -y ros-humble-mavros ros-humble-mavros-msgs
 
# Verify again
ros2 pkg list | grep mavros
```
 
---
 
### Step 3: Check SUPER files
 
```bash
ls -la ~/super_ws/src/SUPER/
```
 
**Expected output**: Should show directories like `FAST_LIO`, `mission_planner`, `ROG-Map`, etc.
 
**If SUPER directory doesn't exist**:
```bash
mkdir -p ~/super_ws/src
cd ~/super_ws/src
git clone --recursive https://github.com/hku-mars/SUPER.git
```
 
---
 
### Step 4: The Nuclear Rosdep Fix
 
This automatically installs ALL missing dependencies:
 
```bash
cd ~/super_ws
 
# Update rosdep
rosdep update
 
# Have rosdep install everything SUPER needs
rosdep install -y --from-paths src/SUPER --rosdistro humble --ignore-src
 
# This will take a few minutes - wait for completion
# You should see: "rosdep install completed successfully"
```
 
**This is the most important step** - rosdep reads every package.xml in SUPER and installs everything declared.
 
---
 
### Step 5: Clean Previous Build
 
```bash
cd ~/super_ws
 
# Remove all previous build artifacts
rm -rf build install log
 
# Verify they're gone
ls -la ~/super_ws/ | grep -E "build|install|log"
# Should show nothing
```
 
---
 
### Step 6: Build SUPER
 
```bash
cd ~/super_ws
 
# Build with reasonable parallelism for Jetson (8 cores)
colcon build --symlink-install
 
# This will take 10-15 minutes
# Watch the output - should show each package building
```
 
**Expected output at end**:
```
Finished <<< mission_planner [XXX.XXs]
Summary: 4 packages finished [YYYYs]
```
 
---
 
### Step 7: Verify Build Success
 
```bash
# Check all packages built
ls -la ~/super_ws/install/ | grep -E "mars_|mission_|rog_"
 
# Should show:
# mars_quadrotor_msgs/
# mission_planner/
# rog_map/
# marsim_render/
 
# Source new build
source ~/super_ws/install/setup.bash
 
# Verify packages are found
ros2 pkg list | grep mission_planner
# Should show: mission_planner
```
 
---
 
### Step 8: Test SUPER
 
```bash
# Make sure ROS2 is sourced
source ~/super_ws/install/setup.bash
 
# Launch SUPER in simulation
ros2 launch mission_planner benchmark_dense.launch.py
 
# You should see:
# 1. Terminal output showing RViz launching
# 2. RViz window opens
# 3. Dense forest environment visible
# 4. Red/green planning trajectories
# 5. Small red cube (MAV position)
 
# To exit: Press Ctrl+C in terminal
```
 
---
 
## FULL SEQUENCE (Copy All At Once)
 
If you want to run everything in one go:
 
```bash
# 1. Source ROS2
source /opt/ros/humble/setup.bash
 
# 2. Update system
sudo apt update
 
# 3. Install MAVROS (if not already)
sudo apt install -y ros-humble-mavros ros-humble-mavros-msgs
 
# 4. Navigate to SUPER workspace
cd ~/super_ws
 
# 5. Ensure SUPER is cloned
if [ ! -d "src/SUPER" ]; then
  mkdir -p src
  cd src
  git clone --recursive https://github.com/hku-mars/SUPER.git
  cd ..
fi
 
# 6. Install all dependencies with rosdep
rosdep update
rosdep install -y --from-paths src/SUPER --rosdistro humble --ignore-src
 
# 7. Clean and rebuild
rm -rf build install log
colcon build --symlink-install
 
# 8. Test SUPER
source install/setup.bash
echo "Build complete! Testing SUPER..."
ros2 launch mission_planner benchmark_dense.launch.py
```
 
---
 
## TROUBLESHOOTING DURING BUILD
 
### Build is slow or hanging
- Normal on Jetson Orin Nano (first build: 10-15 minutes)
- Check: `jtop` in another terminal
- If CPU/RAM maxed out, it's still working, just slow
### Build fails with different error
- Stop (Ctrl+C)
- Check error message
- Run: `colcon build --symlink-install --packages-select mission_planner --event-handlers console_direct+`
- This shows exact error details
### Out of memory
```bash
# Free memory
sudo sync && sudo sysctl -w vm.drop_caches=3
 
# Rebuild with fewer parallel jobs
colcon build --symlink-install -j2
```
 
---
 
## IF STILL FAILING
 
Follow ADVANCED_MAVROS_FIX.md for diagnostic steps.
 
Share the output of:
 
```bash
# Diagnostic check
echo "=== ROS2 Status ==="
ros2 --version
echo $ROS_DISTRO
ros2 pkg list | grep mavros
ros2 pkg prefix mavros_msgs
echo ""
echo "=== SUPER Files ==="
ls -la ~/super_ws/src/SUPER/
echo ""
echo "=== Build Error ==="
cd ~/super_ws && colcon build --symlink-install 2>&1 | tail -50
```
 
---
 
## NEXT PHASE (After SUPER Builds)
 
Once build succeeds and SUPER runs:
 
1. **Phase 2**: Livox LiDAR Setup
   ```bash
   cd ~
   git clone https://github.com/Livox-SDK/Livox-SDK2.git
   cd Livox-SDK2 && mkdir build && cd build
   cmake .. && make -j8 && sudo make install
   ```
 
2. **Phase 3**: Flight Controller Connection
   - Already setup with QGC on desktop
   - Then connect UART to Jetson TELEM1
3. **Phase 4**: FAST-LIO2 (already included in SUPER)
   - Configure for Livox Mid-360
   - Test LiDAR+IMU fusion
4. **Phase 5-10**: Integration and flight testing
---
 
**Run Step 1-3 now and report back with the result!**
 
The rosdep command (Step 4) is the key - it will automatically find and install everything.
