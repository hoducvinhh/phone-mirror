#pragma once

#include "Types.h"

#include <cstdint>
#include <vector>

namespace native_mirror {

#pragma pack(push, 1)
struct PacketHeader {
    char magic[4] = {'N', 'M', 'R', '2'};
    std::uint32_t length = 0;
};

struct TouchPacket {
    std::uint8_t action = 0;
    std::uint32_t id = 0;
    std::uint16_t x = 0;
    std::uint16_t y = 0;
};
#pragma pack(pop)

bool sendTouchPacket(void* socketHandle, Action action, std::uint32_t id,
                     std::uint16_t x, std::uint16_t y);
bool sendTextPacket(void* socketHandle, const std::string& text);
bool sendKeyPacket(void* socketHandle, Action action);

std::vector<std::uint8_t> encodeTouch(Action action, std::uint32_t id,
                                      std::uint16_t x, std::uint16_t y);

}
