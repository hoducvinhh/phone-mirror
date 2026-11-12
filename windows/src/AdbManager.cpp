#include "AdbManager.h"

#include <Windows.h>

#include <array>
#include <cstdio>
#include <filesystem>
#include <utility>
#include <vector>

namespace native_mirror {

AdbManager::AdbManager(std::string adbExecutable)
    : adb_(std::move(adbExecutable)) {}

bool AdbManager::run(const std::wstring& arguments, std::string& output) {
    SECURITY_ATTRIBUTES security{};
    security.nLength = sizeof(security);
    security.bInheritHandle = TRUE;

    HANDLE readPipe = nullptr;
    HANDLE writePipe = nullptr;
    if (!CreatePipe(&readPipe, &writePipe, &security, 0)) return false;

    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    startup.dwFlags = STARTF_USESTDHANDLES;
    startup.hStdOutput = writePipe;
    startup.hStdError = writePipe;
    startup.hStdInput = nullptr;

    PROCESS_INFORMATION process{};
    std::wstring command = L"\"" + std::wstring(adb_.begin(), adb_.end()) + L"\" " + arguments;
    std::vector<wchar_t> commandBuffer(command.begin(), command.end());
    commandBuffer.push_back(L'\0');

    BOOL created = CreateProcessW(nullptr, commandBuffer.data(), nullptr, nullptr, TRUE,
                                  CREATE_NO_WINDOW, nullptr, nullptr, &startup, &process);
    CloseHandle(writePipe);
    if (!created) {
        CloseHandle(readPipe);
        return false;
    }

    WaitForSingleObject(process.hProcess, 30000);
    std::array<char, 4096> buffer{};
    DWORD bytesRead = 0;
    while (ReadFile(readPipe, buffer.data(), static_cast<DWORD>(buffer.size()), &bytesRead, nullptr)
           && bytesRead > 0) {
        output.append(buffer.data(), bytesRead);
    }
    CloseHandle(readPipe);
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return true;
}

bool AdbManager::waitForDevice(int timeoutSeconds) {
    for (int i = 0; i < timeoutSeconds; ++i) {
        if (isDeviceConnected()) return true;
        Sleep(1000);
    }
    return false;
}

bool AdbManager::isDeviceConnected() {
    std::string output = devicesOutput();
    return output.find("\tdevice") != std::string::npos;
}

std::string AdbManager::devicesOutput() {
    std::string output;
    run(L"devices", output);
    return output;
}

bool AdbManager::forward(int localPort) {
    std::string output;
    return run(L"forward tcp:" + std::to_wstring(localPort) + L" localabstract:nativemirror",
               output);
}

bool AdbManager::pushServer() {
    std::string output;
    std::wstring jar = std::filesystem::current_path().wstring()
                     + L"\\android\\mirror-server\\build\\mirror-server.jar";
    return run(L"push \"" + jar + L"\" /data/local/tmp/mirror-server.jar", output);
}

bool AdbManager::startServer(int localPort) {
    std::string output;
    std::wstring arguments =
        L"shell CLASSPATH=/data/local/tmp/mirror-server.jar app_process "
        L"/system/bin com.nativemirror.Server --port "
        + std::to_wstring(localPort);
    return run(arguments, output);
}

bool AdbManager::installApk(const std::wstring& path) {
    std::string output;
    return run(L"install -r -d \"" + path + L"\"", output);
}

bool AdbManager::setTcpip(const std::string& host) {
    std::string output;
    std::wstring hostArg(host.begin(), host.end());
    if (!run(L"connect " + hostArg, output)) return false;
    output.clear();
    return run(L"-s " + hostArg + L" tcpip 5555", output);
}

}
