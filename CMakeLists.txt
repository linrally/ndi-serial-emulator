cmake_minimum_required(VERSION 3.0 FATAL_ERROR)
set(CMAKE_CXX_STANDARD 17)
project(ndi-serial-emulator)

# Main executables
add_executable(main main.cpp)
set_property(TARGET main PROPERTY CXX_STANDARD 17)
set_property(TARGET main PROPERTY CXX_STANDARD_REQUIRED ON)

# NDI Combined API
add_subdirectory("./ndicapi")
target_link_libraries(main ndicapi)