#pragma once

#include <cstdint>
#include <string>

namespace native_mirror {

struct Frame {
    std::uint32_t width = 0;
    std::uint32_t height = 0;
    std::uint32_t timestamp = 0;
    std::uint32_t flags = 0;
};

struct Point {
    int x = 0;
    int y = 0;
};

enum class Action : std::uint8_t {
    TouchDown = 1,
    TouchMove = 2,
    TouchUp = 3,
    KeyDown = 4,
    KeyUp = 5,
    Text = 6,
    Back = 7,
    Home = 8,
    Recent = 9,
    Power = 10,
    VolumeUp = 11,
    VolumeDown = 12,
};

}
