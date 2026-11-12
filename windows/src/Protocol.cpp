#include "Protocol.h"

#include <winsock2.h>

#include <cstdint>
#include <cstring>

namespace native_mirror {

std::vector<std::uint8_t> encodeTouch(Action action, std::uint32_t id,
                                      std::uint16_t x, std::uint16_t y) {
    std::vector<std::uint8_t> packet(sizeof(PacketHeader) + sizeof(TouchPacket));
    PacketHeader header;
    header.length = static_cast<std::uint32_t>(sizeof(TouchPacket));
    std::memcpy(packet.data(), &header, sizeof(header));
    TouchPacket touch{
        static_cast<std::uint8_t>(action), id, x, y
    };
    std::memcpy(packet.data() + sizeof(header), &touch, sizeof(touch));
    return packet;
}

static bool sendAll(void* socketHandle, const std::vector<std::uint8_t>& data) {
    SOCKET socket = static_cast<SOCKET>(reinterpret_cast<std::uintptr_t>(socketHandle));
    std::size_t sent = 0;
    while (sent < data.size()) {
        int result = ::send(socket, reinterpret_cast<const char*>(data.data() + sent),
                            static_cast<int>(data.size() - sent), 0);
        if (result <= 0) return false;
        sent += result;
    }
    return true;
}

bool sendTouchPacket(void* socketHandle, Action action, std::uint32_t id,
                     std::uint16_t x, std::uint16_t y) {
    return sendAll(socketHandle, encodeTouch(action, id, x, y));
}

bool sendTextPacket(void* socketHandle, const std::string& text) {
    std::vector<std::uint8_t> packet(sizeof(PacketHeader) + 1 + text.size());
    PacketHeader header;
    header.length = static_cast<std::uint32_t>(1 + text.size());
    std::memcpy(packet.data(), &header, sizeof(header));
    packet[sizeof(PacketHeader)] = static_cast<std::uint8_t>(Action::Text);
    std::memcpy(packet.data() + sizeof(header) + 1, text.data(), text.size());
    return sendAll(socketHandle, packet);
}

bool sendKeyPacket(void* socketHandle, Action action) {
    std::vector<std::uint8_t> packet(sizeof(PacketHeader) + sizeof(TouchPacket));
    PacketHeader header;
    header.length = static_cast<std::uint32_t>(sizeof(TouchPacket));
    std::memcpy(packet.data(), &header, sizeof(header));
    TouchPacket touch{static_cast<std::uint8_t>(action), 0, 0, 0};
    std::memcpy(packet.data() + sizeof(header), &touch, sizeof(touch));
    return sendAll(socketHandle, packet);
}

}
