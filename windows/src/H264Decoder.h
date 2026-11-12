#pragma once

#include <cstdint>
#include <vector>

struct AVCodecContext;
struct AVFrame;
struct AVPacket;

namespace native_mirror {

class H264Decoder {
public:
    H264Decoder();
    ~H264Decoder();

    bool decode(const std::uint8_t* data, std::size_t size,
                std::uint8_t* rgbOutput, int& width, int& height);

private:
    AVCodecContext* codec_ = nullptr;
    AVFrame* frame_ = nullptr;
    AVPacket* packet_ = nullptr;
};

}
