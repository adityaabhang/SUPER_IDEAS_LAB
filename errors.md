ideas-ad@ideasad-desktop:~/super_ws$ colcon build --symlink-install
Starting >>> mars_quadrotor_msgs
Starting >>> marsim_render
Starting >>> rog_map
Starting >>> mission_planner
--- stderr: mission_planner                                             
CMake Error at CMakeLists.txt:33 (find_package):
  By not providing "Findmavros_msgs.cmake" in CMAKE_MODULE_PATH this project
  has asked CMake to find a package configuration file provided by
  "mavros_msgs", but CMake did not find one.

  Could not find a package configuration file provided by "mavros_msgs" with
  any of the following names:

    mavros_msgsConfig.cmake
    mavros_msgs-config.cmake

  Add the installation prefix of "mavros_msgs" to CMAKE_PREFIX_PATH or set
  "mavros_msgs_DIR" to a directory containing one of the above files.  If
  "mavros_msgs" provides a separate development package or SDK, be sure it
  has been installed.


---
Failed   <<< mission_planner [3.38s, exited with code 1]
Aborted  <<< mars_quadrotor_msgs [5.01s]        
Aborted  <<< rog_map [7.61s]                                                 
Aborted  <<< marsim_render [7.91s]                           
                                
Summary: 0 packages finished [8.58s]
  1 package failed: mission_planner
  3 packages aborted: mars_quadrotor_msgs marsim_render rog_map
  3 packages had stderr output: marsim_render mission_planner rog_map
  2 packages not processed
