#pragma once

#include <string>

namespace native_mirror {

class AdbManager {
public:
    explicit AdbManager(std::string adbExecutable = "adb");

    bool waitForDevice(int timeoutSeconds = 5);
    bool pushServer();
    bool startServer(int localPort);
    bool forward(int localPort);
    bool installApk(const std::wstring& path);
    bool setTcpip(const std::string& host);
    bool isDeviceConnected();
    std::string devicesOutput();

private:
    bool run(const std::wstring& arguments, std::string& output);
    std::string adb_;
};

}
