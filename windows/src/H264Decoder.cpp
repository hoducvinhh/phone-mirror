#include "H264Decoder.h"

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavutil/imgutils.h>
#include <libavutil/pixfmt.h>
#include <libswscale/swscale.h>
}

#include <cstring>

namespace native_mirror {

H264Decoder::H264Decoder() {
    const AVCodec* codec = avcodec_find_decoder_by_name("h264");
    if (!codec) return;
    codec_ = avcodec_alloc_context3(codec);
    if (!codec_) return;
    codec_->thread_count = 2;
    codec_->thread_type = FF_THREAD_SLICE;
    codec_->flags |= AV_CODEC_FLAG_LOW_DELAY;
    avcodec_open2(codec_, codec, nullptr);
    frame_ = av_frame_alloc();
    packet_ = av_packet_alloc();
}

H264Decoder::~H264Decoder() {
    av_packet_free(&packet_);
    av_frame_free(&frame_);
    avcodec_free_context(&codec_);
}

bool H264Decoder::decode(const std::uint8_t* data, std::size_t size,
                         std::uint8_t* rgbOutput, int& width, int& height) {
    if (!codec_ || !frame_ || !packet_) return false;
    packet_->data = const_cast<std::uint8_t*>(data);
    packet_->size = static_cast<int>(size);
    int result = avcodec_send_packet(codec_, packet_);
    if (result < 0 && result != AVERROR(EAGAIN)) return false;
    result = avcodec_receive_frame(codec_, frame_);
    if (result < 0) return false;

    width = frame_->width;
    height = frame_->height;
    if (!rgbOutput) return true;

    SwsContext* scaler = sws_getContext(width, height, codec_->pix_fmt,
                                        width, height, AV_PIX_FMT_RGB24,
                                        SWS_BILINEAR, nullptr, nullptr, nullptr);
    if (!scaler) return false;
    std::uint8_t* destination[1] = {rgbOutput};
    int destinationLines[1] = {width * 3};
    sws_scale(scaler, frame_->data, frame_->linesize, 0, height,
              destination, destinationLines);
    sws_freeContext(scaler);
    return true;
}

}
