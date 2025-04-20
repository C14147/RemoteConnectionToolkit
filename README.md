RemoteConnectionToolkit
===================
[![Language](https://img.shields.io/badge/Python-3.10.0-blue?logo=python)](https://python.org)
![Language](https://img.shields.io/badge/RemoteConnectionToolkit-1.4.0-green)
![Plantform](https://img.shields.io/badge/Windows-blue)
![Plantform](https://img.shields.io/badge/Linux-blue)


_A Development Kit for Remote Connection and Based on Python3._

## Introduction
Remote Connection Toolkit is a Python-based toolkit that simplifies the process of remote connection by encapsulating the Python network toolkit. It provides multiple operational tools for remote communication between computers.

## About This Project

I was influenced by various remote desktop software(especially PowerToys), and developed this project using socket interface. It establishes a connection between two computers and controls them through instructions. This connection is bidirectional, which means that this project is useful for remote login, remote collaboration, and file transfer.

## Features
- **Version Compatibility**: When communicating remotely, all digits except for the third digit of the version number must be the same to continue communication.
- **Debugging GUI**: A GUI debugger is available to assist in debugging the remote connection process.
- **Built-in Instruction Set**: It includes a set of built-in functions for common operations such as file transfer, screenshot capture, and remote screen monitoring.

## How did it work

I use Python 3 to call the socket interface of the system, establishing one as a server and the other as a client. When the client initiates a connection to the server, they will send their tool version and network IP information to the other party to ensure the security and stability of remote transmission. Afterwards, they will wait for the user's command to be issued. The instructions and execution results will be transmitted to the corresponding computer through the TCP protocol.

## Requirements
- Python 3.x
- PIL (Python Imaging Library)
- mss (Multiple ScreenShot)

## Installation
1. Clone the repository:
```bash
git clone https://github.com/your-repo/RemoteConnectionToolkit.git
```
**👉 The tool versions of two computers must have the same digits except for the third digit! The project has strong scalability and there are many areas that need improvement and optimization.**
2. Install the required dependencies:
```bash
pip install pillow mss
```

## Details of The RemoteConnection Class

The RemoteConnection class has the following member functions：

```python3
class RemoteConnection:
    def __init__(self, remoteIP: str, port: int, debugGUI=False): ...
	def getLocalAddress(self) -> str: ...
	def send(self, msg) -> int: ...
	def sendString(self, msg: str) -> int: ...
	def passiveConnect(self, timeout=10): ...
	def initiativeConnect(self, timeout=10): ...
	def listen(self, funcList: dict): ...
```

#### RemoteConnection(remoteIP: str, port: int, debugGUI=False):

This function takes three parameters.

_remoteIP: str_

The first parameter is the IP address of the computer you want to connect to. \
👉 When initiating a remote connection **in a passive manner**, a constant other than the IP address can be used: WRCD_ANY_IP_ADDRESS.It allows **any IP to connect the computer** and begin communication after compatibility and security checks.

_port: int_

The port used when establishing a connection on a computer.

_debugGUI=False_

If the parameter is True, the program will create a window for debugging.

#### getLocalAddress():

Obtain the IP host name or IP address of the local machine.

#### send(msg):

The usage is the same as _socket.send_.

#### sendString(msg: str):

Function for sending string messages to remote computers.

#### passiveConnect(timeout=0):

Start in passive mode and wait for other computers to connect. Equivalent to establishing a server on the computer executing the code.\
The ‘timeout’ parameter specifies the maximum duration of waiting for a connection, measured in seconds. When timeout=0, the computer executing the code will wait until the process ends or another computer connects.

#### initiativeConnect(timeout=0):

Start in initiative mode and wait for other computers to connect. Equivalent to establishing a client on the computer executing the code.\
The ‘timeout’ parameter specifies the maximum duration of waiting for a connection, measured in seconds. When timeout=0, the computer executing the code will wait until the process ends or another computer connects.

#### listen(funcList: dict):

Start listening for requests from connected computers.\
👉 This function will **block the process**. This means you need to **create a new thread** for this function.\
🚨 **Please execute this function after completing PassiveConnect or InitiativeConnect**. Otherwise, you will receive a gift called Traceback...

## Built-in Functions
The following is a list of built-in functions provided by the toolkit:

| Function Name | Description |
| --- | --- |
| `Close` | Close the connection with the remote computer. |
| `sendPathList` | Passively transfer the contents of a specified folder to the remote computer. |
| `getPathList` | Proactively request the contents of a specified folder from the remote computer. |
| `sendFile` | Proactively send a file to the remote computer. |
| `reciveFile` | Passively receive a file from the remote computer. |
| `getFile` | Proactively obtain a file from the remote computer. |
| `catchScreenshot` | Capture the screenshot of the local computer. |
| `sendScreenshot` | Send the screenshot of the local computer to the remote computer. |
| `showScreenshot` | Get and display the screenshot of the remote computer. |
| `getScreenshot` | Get the screenshot of the remote computer. |
| `monitorRemoteScreen` | Continuously monitor the remote screen. |

### 3.Examples

Here are some examples:

```python
from RemoteConnectionToolkit import *


if __name__ == "__main__":
    remote = RemoteConnection("192.168.0.102", 12345, True)
    remote.initiativeConnect(60)
    remote.listen(builtin_funcs)
```

```python3
from RemoteConnectionToolkit import *


if __name__ == "__main__":
    remote = RemoteConnection(WRCT_ANY_IP_ADDRESS, 12345, True)
    remote.initiativeConnect(30)
    remote.listen(builtin_funcs)
```

## Copyrights & Thanks

### Copyrights:

Copyright(C) 2023-2025 [C14147](https://github.com/C14147/).\
Follow the Apache 2.0 license agreement.\
https://github.com/C14147/RemoteConnectionToolkit

### Thanks:

[Honghaier-Game](https://github.com/honghaier-game/): GUI debugger design by his TKinterDesigner.\
TKinterDesigner is the predecessor of his software [PyMe](https://github.com/honghaier-game/PyMe). \
RemoteConnectionToolkit uses TKinterDesigner v1.5.1.
