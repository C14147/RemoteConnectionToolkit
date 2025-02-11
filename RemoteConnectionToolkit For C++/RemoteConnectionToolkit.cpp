#include "RemoteConnectionToolkit.hpp"
#include <iostream>
#include <sstream>
#include <fstream>
#include <thread>
#include <chrono>
#include <json/json.h>
#include <base64.h>
#include <mss.h>
#include <PIL.h>

#pragma comment(lib, "ws2_32.lib")

class RemoteConnectionToolkit::Impl {
public:
    SOCKET sock;
    SOCKET clientSock;
    bool connected;
    std::string lastError;
    int timeoutSeconds;
    std::string remoteIP;
    std::string host;
    int port;
    std::string connectMode;

    Impl() : sock(INVALID_SOCKET), clientSock(INVALID_SOCKET), connected(false), timeoutSeconds(30) {
        WSADATA wsaData;
        if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
            throw std::runtime_error("Failed to initialize Winsock");
        }
        char hostname[256];
        gethostname(hostname, sizeof(hostname));
        host = std::string(hostname);
    }

    ~Impl() {
        if (sock != INVALID_SOCKET) {
            closesocket(sock);
        }
        if (clientSock != INVALID_SOCKET) {
            closesocket(clientSock);
        }
        WSACleanup();
    }
};

RemoteConnectionToolkit::RemoteConnectionToolkit() : pImpl(new Impl()) {}
RemoteConnectionToolkit::~RemoteConnectionToolkit() = default;

bool RemoteConnectionToolkit::connectToHost(const std::string& host, int port) {
    pImpl->sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (pImpl->sock == INVALID_SOCKET) {
        pImpl->lastError = "Socket creation failed";
        return false;
    }

    struct sockaddr_in serverAddr = {0};
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(port);
    inet_pton(AF_INET, host.c_str(), &serverAddr.sin_addr);

    if (connect(pImpl->sock, (struct sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
        pImpl->lastError = "Connection failed";
        closesocket(pImpl->sock);
        pImpl->sock = INVALID_SOCKET;
        return false;
    }

    pImpl->connected = true;
    return true;
}

bool RemoteConnectionToolkit::disconnectFromHost() {
    if (!pImpl->connected) return false;
    
    closesocket(pImpl->sock);
    pImpl->sock = INVALID_SOCKET;
    pImpl->connected = false;
    return true;
}

bool RemoteConnectionToolkit::isConnected() const {
    return pImpl->connected;
}

bool RemoteConnectionToolkit::sendCommand(const std::string& command) {
    if (!pImpl->connected) {
        pImpl->lastError = "Not connected";
        return false;
    }

    if (send(pImpl->sock, command.c_str(), command.length(), 0) == SOCKET_ERROR) {
        pImpl->lastError = "Send failed";
        return false;
    }
    return true;
}

std::string RemoteConnectionToolkit::receiveResponse() {
    if (!pImpl->connected) {
        pImpl->lastError = "Not connected";
        return "";
    }

    char buffer[4096];
    int bytes = recv(pImpl->sock, buffer, sizeof(buffer) - 1, 0);
    if (bytes == SOCKET_ERROR) {
        pImpl->lastError = "Receive failed";
        return "";
    }

    buffer[bytes] = '\0';
    return std::string(buffer, bytes);
}

void RemoteConnectionToolkit::setTimeout(int seconds) {
    pImpl->timeoutSeconds = seconds;
    if (pImpl->connected) {
        DWORD timeout = seconds * 1000;
        setsockopt(pImpl->sock, SOL_SOCKET, SO_RCVTIMEO, (char*)&timeout, sizeof(timeout));
        setsockopt(pImpl->sock, SOL_SOCKET, SO_SNDTIMEO, (char*)&timeout, sizeof(timeout));
    }
}

std::string RemoteConnectionToolkit::getLastError() const {
    return pImpl->lastError;
}

std::string RemoteConnectionToolkit::getLocalAddress() const {
    return pImpl->host;
}

void RemoteConnectionToolkit::passiveConnect(int timeout) {
    pImpl->connectMode = "passiveConnect";
    pImpl->sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (pImpl->sock == INVALID_SOCKET) {
        pImpl->lastError = "Socket creation failed";
        throw RemoteToolkitError(pImpl->lastError);
    }

    struct sockaddr_in serverAddr = {0};
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(pImpl->port);
    serverAddr.sin_addr.s_addr = INADDR_ANY;

    if (bind(pImpl->sock, (struct sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
        pImpl->lastError = "Bind failed";
        closesocket(pImpl->sock);
        pImpl->sock = INVALID_SOCKET;
        throw RemoteToolkitError(pImpl->lastError);
    }

    if (listen(pImpl->sock, 3) == SOCKET_ERROR) {
        pImpl->lastError = "Listen failed";
        closesocket(pImpl->sock);
        pImpl->sock = INVALID_SOCKET;
        throw RemoteToolkitError(pImpl->lastError);
    }

    struct sockaddr_in clientAddr;
    int clientAddrSize = sizeof(clientAddr);
    pImpl->clientSock = accept(pImpl->sock, (struct sockaddr*)&clientAddr, &clientAddrSize);
    if (pImpl->clientSock == INVALID_SOCKET) {
        pImpl->lastError = "Accept failed";
        closesocket(pImpl->sock);
        pImpl->sock = INVALID_SOCKET;
        throw RemoteToolkitError(pImpl->lastError);
    }

    pImpl->connected = true;
    pImpl->remoteIP = inet_ntoa(clientAddr.sin_addr);
    pImpl->port = ntohs(clientAddr.sin_port);

    if (timeout > 0) {
        setTimeout(timeout);
    }

    sendCommand("Answer! Remote Connection Toolkit version 1.4.0,server ip: " + pImpl->host);
    std::string msg = receiveResponse();
    if (msg.find("Answer! Remote Connection Toolkit version") == std::string::npos) {
        pImpl->lastError = "Unsupported Client Interface";
        throw RemoteToolkitError(pImpl->lastError);
    }
}

void RemoteConnectionToolkit::initiativeConnect(int timeout) {
    pImpl->connectMode = "initiativeConnect";
    if (!connectToHost(pImpl->remoteIP, pImpl->port)) {
        throw RemoteToolkitError(pImpl->lastError);
    }

    if (timeout > 0) {
        setTimeout(timeout);
    }

    std::string msg = receiveResponse();
    sendCommand("Answer! Remote Connection Toolkit version 1.4.0,server ip: " + pImpl->host);
}

void RemoteConnectionToolkit::listen(const std::map<std::string, std::function<void(std::vector<std::string>)>>& funcList) {
    while (pImpl->connected) {
        std::string msg = receiveResponse();
        auto pos = msg.find('|');
        if (pos != std::string::npos) {
            std::string funcName = msg.substr(0, pos);
            std::string argsStr = msg.substr(pos + 1);
            std::vector<std::string> args;
            std::istringstream iss(argsStr);
            std::string arg;
            while (std::getline(iss, arg, ',')) {
                args.push_back(arg);
            }
            if (funcList.find(funcName) != funcList.end()) {
                funcList.at(funcName)(args);
            }
        }
    }
}

void showError(RemoteConnectionToolkit& remote, const std::vector<std::string>& args) {
    // args[0]: Error Message
    std::string errorMsg = base64_decode(args[0]);
    std::cerr << "Remote Computer Send An Error: " << errorMsg << " .Please Check The Error And Feedback To Us." << std::endl;
}

void closeRemote(RemoteConnectionToolkit& remote, const std::vector<std::string>& args) {
    // No arg used
    remote.sendCommand("Close|1,");
    remote.disconnectFromHost();
    std::cout << "Connection Closed." << std::endl;
}

void sendPathList(RemoteConnectionToolkit& remote, const std::vector<std::string>& args) {
    // args[0] : Folder Path
    std::string folderPath = args[0];
    std::vector<std::string> files;
    for (const auto& entry : std::filesystem::directory_iterator(folderPath)) {
        files.push_back(entry.path().string());
    }
    std::string fileList = json::serialize(files);
    remote.sendCommand(fileList);
}

void getPathList(RemoteConnectionToolkit& remote, const std::vector<std::string>& args) {
    // args[0] : Folder Path
    remote.sendCommand("sendPathList|" + args[0] + ",");
    std::string response = remote.receiveResponse();
    std::cout << response << std::endl;
}

void sendFile(RemoteConnectionToolkit& remote, const std::vector<std::string>& args) {
    // args[0] : File Path
    remote.sendCommand("receiveFile|" + args[0] + ",");
    std::string response = remote.receiveResponse();
    if (response == "Ready") {
        std::ifstream file(args[0], std::ios::binary);
        std::vector<char> buffer((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
        remote.sendCommand(std::string(buffer.begin(), buffer.end()));
    } else {
        throw RemoteToolkitError("The remote computer's response is incorrect when transferring files.");
    }
}

void receiveFile(RemoteConnectionToolkit& remote, const std::vector<std::string>& args) {
    // args[0] : File Path
    remote.sendCommand("Ready");
    std::ofstream file(args[0], std::ios::binary);
    std::string data = remote.receiveResponse();
    file.write(data.c_str(), data.size());
}

void getFile(RemoteConnectionToolkit& remote, const std::vector<std::string>& args) {
    // args[0] : File Path
    remote.sendCommand("sendFile|" + args[0] + ",");
}

void catchScreenshot(RemoteConnectionToolkit& remote, const std::vector<std::string>& args) {
    // args[0] : Monitor Number
    int monitor = std::stoi(args[0]);
    mss::screenshot monitorScreenshot = mss::grab(mss::monitors()[monitor]);
    mss::save(monitorScreenshot, "tmp_screenshot_" + std::to_string(monitor) + ".png");
}

void sendScreenshot(RemoteConnectionToolkit& remote, const std::vector<std::string>& args) {
    // args[0] : Monitor Number
    int monitor = std::stoi(args[0]);
    remote.sendCommand("sendFile|tmp_screenshot_" + std::to_string(monitor) + ".png");
}

void showScreenshot(RemoteConnectionToolkit& remote, const std::vector<std::string>& args) {
    // args[0] : Monitor Number
    int monitor = std::stoi(args[0]);
    PIL::Image img("tmp_screenshot_" + std::to_string(monitor) + ".png");
    img.show();
}

void getScreenshot(RemoteConnectionToolkit& remote, const std::vector<std::string>& args) {
    // args[0] : Monitor Number
    // args[1] : Is show image (default: false)
    int monitor = std::stoi(args[0]);
    bool showImage = args.size() > 1 && args[1] == "true";
    remote.sendCommand("catchScreenshot|" + std::to_string(monitor));
    remote.sendCommand("sendScreenshot|" + std::to_string(monitor));
    if (showImage) {
        showScreenshot(remote, {args[0]});
    }
}

void monitorRemoteScreen(RemoteConnectionToolkit& remote, const std::vector<std::string>& args) {
    // args[0] : Monitor Number
    // args[1] : Interval between screenshots in seconds
    int monitor = std::stoi(args[0]);
    int interval = std::stoi(args[1]);
    while (remote.isConnected()) {
        remote.sendCommand("catchScreenshot|" + std::to_string(monitor));
        remote.sendCommand("sendScreenshot|" + std::to_string(monitor));
        std::this_thread::sleep_for(std::chrono::seconds(interval));
    }
}
