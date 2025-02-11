#pragma once
#include <string>
#include <vector>
#include <memory>
#include <map>
#include <functional>
#include <stdexcept>
#include <winsock2.h>
#include <windows.h>

class RemoteConnectionToolkit {
public:
    RemoteConnectionToolkit();
    ~RemoteConnectionToolkit();

    bool connectToHost(const std::string& host, int port);
    bool disconnectFromHost();
    bool isConnected() const;
    
    bool sendCommand(const std::string& command);
    std::string receiveResponse();
    
    void setTimeout(int seconds);
    std::string getLastError() const;

    std::string getLocalAddress() const;
    void passiveConnect(int timeout = 0);
    void initiativeConnect(int timeout = 0);
    void listen(const std::map<std::string, std::function<void(std::vector<std::string>)>>& funcList);

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

class RemoteToolkitError : public std::runtime_error {
public:
    explicit RemoteToolkitError(const std::string& message) : std::runtime_error(message) {}
};

void showError(RemoteConnectionToolkit& remote, const std::vector<std::string>& args);
void closeRemote(RemoteConnectionToolkit& remote, const std::vector<std::string>& args);
void sendPathList(RemoteConnectionToolkit& remote, const std::vector<std::string>& args);
void getPathList(RemoteConnectionToolkit& remote, const std::vector<std::string>& args);
void sendFile(RemoteConnectionToolkit& remote, const std::vector<std::string>& args);
void receiveFile(RemoteConnectionToolkit& remote, const std::vector<std::string>& args);
void getFile(RemoteConnectionToolkit& remote, const std::vector<std::string>& args);
void catchScreenshot(RemoteConnectionToolkit& remote, const std::vector<std::string>& args);
void sendScreenshot(RemoteConnectionToolkit& remote, const std::vector<std::string>& args);
void showScreenshot(RemoteConnectionToolkit& remote, const std::vector<std::string>& args);
void getScreenshot(RemoteConnectionToolkit& remote, const std::vector<std::string>& args);
void monitorRemoteScreen(RemoteConnectionToolkit& remote, const std::vector<std::string>& args);
