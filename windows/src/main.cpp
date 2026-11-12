#define SDL_MAIN_HANDLED

#include "AdbManager.h"
#include "H264Decoder.h"
#include "Protocol.h"

#include <SDL.h>
#include <winsock2.h>
#include <Windows.h>
#include <shellapi.h>

#include <atomic>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <iostream>
#include <thread>
#include <vector>

using namespace native_mirror;

static SOCKET connectToMirrorServer(int port) {
    WSADATA data{};
    WSAStartup(MAKEWORD(2, 2), &data);
    SOCKET socketHandle = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(static_cast<u_short>(port));
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (::connect(socketHandle, reinterpret_cast<sockaddr*>(&address), sizeof(address)) != 0) {
        closesocket(socketHandle);
        return INVALID_SOCKET;
    }
    return socketHandle;
}

int main(int argc, char** argv) {
    int port = 27183;
    std::string adbHost;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--port" && i + 1 < argc) port = std::stoi(argv[++i]);
        if (arg == "--adb-host" && i + 1 < argc) adbHost = argv[++i];
    }

    AdbManager adb;
    if (!adbHost.empty()) adb.setTcpip(adbHost);
    if (!adb.waitForDevice(10)) {
        MessageBoxW(nullptr, L"Không tìm thấy thiết bị Android (ADB) nào được kết nối.", L"Appcuatao", MB_OK | MB_ICONWARNING);
        return 1;
    }
    adb.pushServer();
    adb.forward(port);

    SOCKET socketHandle = connectToMirrorServer(port);
    if (socketHandle == INVALID_SOCKET) {
        adb.startServer(port);
        for (int i = 0; i < 20 && socketHandle == INVALID_SOCKET; ++i) {
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
            socketHandle = connectToMirrorServer(port);
        }
    }
    if (socketHandle == INVALID_SOCKET) return 2;
    u_long nonBlocking = 1;
    ioctlsocket(socketHandle, FIONBIO, &nonBlocking);

    if (SDL_Init(SDL_INIT_VIDEO) != 0) return 3;
    SDL_Window* window = SDL_CreateWindow("Appcuatao",
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, 405, 720,
        SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE | SDL_WINDOW_ALLOW_HIGHDPI);
    if (!window) return 4;
    SDL_Renderer* renderer = SDL_CreateRenderer(window, -1,
        SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    if (!renderer) return 5;
    SDL_EventState(SDL_DROPFILE, SDL_ENABLE);

    H264Decoder decoder;
    SDL_Texture* texture = nullptr;
    std::vector<std::uint8_t> framePixels;
    bool dragging = false;
    int pointerId = 1;
    bool running = true;
    PacketHeader header{};
    std::vector<std::uint8_t> headerBytes(sizeof(header));
    std::size_t headerOffset = 0;
    std::vector<std::uint8_t> encoded;
    std::size_t payloadOffset = 0;

    while (running) {
        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_QUIT) running = false;
            if (event.type == SDL_WINDOWEVENT &&
                event.window.event == SDL_WINDOWEVENT_RESIZED) {
                SDL_RenderSetLogicalSize(renderer, 405, 720);
            }
            if (event.type == SDL_DROPFILE) {
                std::filesystem::path path = event.drop.file;
                SDL_free(event.drop.file);
                if (path.extension() == ".apk") adb.installApk(path.wstring());
            }
            if (event.type == SDL_MOUSEBUTTONDOWN) {
                int width = 405, height = 720;
                SDL_GetWindowSize(window, &width, &height);
                if (event.button.button == SDL_BUTTON_RIGHT) {
                    sendKeyPacket(reinterpret_cast<void*>(socketHandle), Action::Back);
                } else if (event.button.button == SDL_BUTTON_MIDDLE) {
                    sendKeyPacket(reinterpret_cast<void*>(socketHandle), Action::Home);
                } else {
                    dragging = true;
                    sendTouchPacket(reinterpret_cast<void*>(socketHandle),
                                    Action::TouchDown, pointerId,
                                    static_cast<std::uint16_t>(event.button.x * 1080 / width),
                                    static_cast<std::uint16_t>(event.button.y * 1920 / height));
                }
            }
            if (event.type == SDL_MOUSEMOTION && dragging) {
                int width = 405, height = 720;
                SDL_GetWindowSize(window, &width, &height);
                sendTouchPacket(reinterpret_cast<void*>(socketHandle),
                                Action::TouchMove, pointerId,
                                static_cast<std::uint16_t>(event.motion.x * 1080 / width),
                                static_cast<std::uint16_t>(event.motion.y * 1920 / height));
            }
            if (event.type == SDL_MOUSEBUTTONUP && event.button.button == SDL_BUTTON_LEFT) {
                int width = 405, height = 720;
                SDL_GetWindowSize(window, &width, &height);
                dragging = false;
                sendTouchPacket(reinterpret_cast<void*>(socketHandle),
                                Action::TouchUp, pointerId,
                                static_cast<std::uint16_t>(event.button.x * 1080 / width),
                                static_cast<std::uint16_t>(event.button.y * 1920 / height));
            }
            if (event.type == SDL_MOUSEWHEEL) {
                sendTouchPacket(reinterpret_cast<void*>(socketHandle),
                                event.wheel.y > 0 ? Action::TouchMove : Action::TouchMove,
                                pointerId, 540, event.wheel.y > 0 ? 1400 : 500);
            }
            if (event.type == SDL_KEYDOWN) {
                const SDL_Keymod mods = SDL_GetModState();
                if ((mods & KMOD_CTRL) && event.key.keysym.sym == SDLK_t) {
#if SDL_VERSION_ATLEAST(2, 0, 16)
                    Uint32 flags = SDL_GetWindowFlags(window);
                    SDL_SetWindowAlwaysOnTop(window, !(flags & SDL_WINDOW_ALWAYS_ON_TOP));
#endif
                } else if ((mods & KMOD_CTRL) && event.key.keysym.sym == SDLK_s) {
                    sendKeyPacket(reinterpret_cast<void*>(socketHandle), Action::Recent);
                } else if ((mods & KMOD_CTRL) && event.key.keysym.sym == SDLK_p) {
                    sendKeyPacket(reinterpret_cast<void*>(socketHandle), Action::Power);
                } else if ((mods & KMOD_CTRL) && event.key.keysym.sym == SDLK_UP) {
                    sendKeyPacket(reinterpret_cast<void*>(socketHandle), Action::VolumeUp);
                } else if ((mods & KMOD_CTRL) && event.key.keysym.sym == SDLK_DOWN) {
                    sendKeyPacket(reinterpret_cast<void*>(socketHandle), Action::VolumeDown);
                } else if (event.key.keysym.sym == SDLK_v && (mods & KMOD_CTRL)) {
                    if (SDL_HasClipboardText()) {
                        char* text = SDL_GetClipboardText();
                        sendTextPacket(reinterpret_cast<void*>(socketHandle), text ? text : "");
                        SDL_free(text);
                    }
                }
            }
        }

        if (headerOffset < headerBytes.size()) {
            int received = recv(socketHandle,
                                reinterpret_cast<char*>(headerBytes.data()) + headerOffset,
                                static_cast<int>(headerBytes.size() - headerOffset), 0);
            if (received > 0) {
                headerOffset += received;
            } else if (received == 0) {
                running = false;
                continue;
            } else if (WSAGetLastError() != WSAEWOULDBLOCK) {
                running = false;
                continue;
            }
        }
        if (headerOffset == headerBytes.size() && encoded.empty()) {
            std::memcpy(&header, headerBytes.data(), sizeof(header));
            if (header.magic[0] == 'N' && header.magic[1] == 'M'
                && header.magic[2] == 'R' && header.magic[3] == '2'
                && header.length > 0) {
                encoded.resize(header.length);
            } else {
                headerOffset = 0;
                continue;
            }
        }
        if (!encoded.empty() && payloadOffset < encoded.size()) {
            int received = recv(socketHandle,
                                reinterpret_cast<char*>(encoded.data()) + payloadOffset,
                                static_cast<int>(encoded.size() - payloadOffset), 0);
            if (received > 0) {
                payloadOffset += received;
            } else if (received == 0) {
                running = false;
                continue;
            } else if (WSAGetLastError() != WSAEWOULDBLOCK) {
                running = false;
                continue;
            }
        }
        if (encoded.empty() || payloadOffset < encoded.size()) continue;

        int width = 0, height = 0;
        framePixels.resize(1080 * 1920 * 3);
        if (!decoder.decode(encoded.data(), encoded.size(), framePixels.data(), width, height))
            continue;
        if (!texture) {
            texture = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_RGB24,
                                        SDL_TEXTUREACCESS_STREAMING, width, height);
        }
        SDL_UpdateTexture(texture, nullptr, framePixels.data(), width * 3);
        SDL_SetWindowSize(window,
                          static_cast<int>(width * 720 / height), 720);
        SDL_RenderClear(renderer);
        SDL_Rect destination{0, 0, static_cast<int>(width * 720 / height), 720};
        SDL_RenderCopy(renderer, texture, nullptr, &destination);
        SDL_RenderPresent(renderer);
        headerOffset = 0;
        payloadOffset = 0;
        encoded.clear();
    }

    closesocket(socketHandle);
    SDL_DestroyTexture(texture);
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
    WSACleanup();
    return 0;
}
