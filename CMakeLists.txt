cmake_minimum_required(VERSION 3.20)
project(AppCuaTao VERSION 2.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(SDL2 CONFIG REQUIRED)
find_package(FFmpeg COMPONENTS avcodec avutil swscale REQUIRED)

add_executable(AppCuaTao
    windows/src/main.cpp
    windows/src/AdbManager.cpp
    windows/src/Protocol.cpp
    windows/src/H264Decoder.cpp
)

target_include_directories(AppCuaTao PRIVATE windows/src)
target_link_libraries(AppCuaTao PRIVATE SDL2::SDL2 FFmpeg::avcodec FFmpeg::avutil FFmpeg::swscale)

set_target_properties(AppCuaTao PROPERTIES
    OUTPUT_NAME "Appcuatao"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)
