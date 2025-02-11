"""
Remote Connection Toolkit
Copyright(C) 2023-2024 C14147.

A remote connection toolkit that provides multiple operational tools by encapsulating
the Python network toolkit, simplifying the process of remote connection.

Declaration: 
Due to the strong scalability and fast version iteration of this project, when 
communicating remotely with a computer, all digits except for the third digit of the 
version number must be the same in order to continue communication.
"""

import os
import re
import sys
import PIL.Image
import mss
import time
import json
import base64
import socket
import logging
import tkinter
import threading

import Fun


__version__ = "1.4.0"
WRCT_ANY_IP_ADDRESS = "WRCT_ANY_IP_ADDRESS"


class Redirector:
    """
    Imitate the FileObject class, which redirects the message originally output
    to the terminal to the debug window when performing a write operation.
    """

    def __init__(self, text_widget: tkinter.Text):
        self.text_widget = text_widget

    def write(self, message: str):
        self.text_widget.insert(tkinter.END, message)

    def flush(self):
        pass


class DebugHelper:
    """GUI debugger for remote connection"""

    def __init__(self, root: tkinter.Tk, isTKroot=True):
        uiName = "DebugHelper"
        Fun.Register(uiName, "UIClass", self)
        self.root = root
        if isTKroot == True:
            root.title("Remote Connection Toolkit - Debug Helper")
            Fun.CenterDlg(uiName, root, 797, 600)
            root["background"] = "#000000"
        Form_1 = tkinter.Canvas(root, width=10, height=4)
        Form_1.place(x=0, y=0, width=797, height=600)
        Form_1.configure(bg="#000000", highlightthickness=0)
        Fun.Register(uiName, "root", root)
        Fun.Register(uiName, "Form_1", Form_1)
        # Create the elements of root
        self.Text_2 = tkinter.Text(root, bg="#000000", fg="#ffffff", relief="flat")
        Fun.Register(uiName, "Text_2", self.Text_2, "Text")
        self.Text_2.place(x=0, y=0, width=800, height=561)
        Entry_3_Variable = Fun.AddTKVariable(uiName, "Entry_3", "")
        self.Entry_3 = tkinter.Entry(root, textvariable=Entry_3_Variable, bg="#151515", fg="#ffffff", relief="flat")
        Fun.Register(uiName, "Entry_3", self.Entry_3)
        self.Entry_3.place(x=2, y=567, width=792, height=27)
        self.Entry_3.bind("<Return>", self.runEvent)
        # Inital all element's Data
        Fun.InitElementData(uiName)

        self.Text_2.config(font=("Microsoft YaHei UI", 12))
        self.Entry_3.config(font=("Microsoft YaHei UI", 11))
        self.Text_2.insert(tkinter.END, "========================================\n")
        self.Text_2.insert(tkinter.END, "Remote Connection Toolkit - Debug Window\n")
        self.Text_2.insert(tkinter.END, "========================================\n")
        self.Text_2.insert(
            tkinter.END, "We'll not save STDOUT and STDERR in debig mode.\n"
        )
        sys.stdout = Redirector(self.Text_2)
        sys.stderr = Redirector(self.Text_2)

    def runEvent(self, evt):
        self.Text_2.insert(tkinter.END, f">>>{self.Entry_3.get()}\n")
        exec(str(self.Entry_3.get()))
        self.Entry_3.delete(0, tkinter.END)


class TextboxHandler(logging.Handler):
    """Inheriting logging.Handler to output logs to the window"""

    def __init__(self, textbox):
        logging.Handler.__init__(self)
        self.textbox = textbox

    def emit(self, record):
        msg = self.format(record)
        self.textbox.insert(tkinter.END, msg + "\n")


class RemoteToolkitError(Exception):
    """An Error Exception Class For Project"""

    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return self.message


def _debugWindow(remote):
    global text2
    debugHelperWindow = tkinter.Tk()
    debugHelper = DebugHelper(debugHelperWindow)
    text2 = debugHelper.Text_2
    debugHelperWindow.mainloop()
    remote.socketObject.close()
    exit()


def _split_version(version: str) -> list:
    vl = []
    _tmp = version.split(".")
    logging.debug(f"Splited list: {_tmp}")
    for ver_iter in _tmp:
        vl.append(int(ver_iter))
    return vl


def _check_version(version: str):
    vi = _split_version(version)
    vc = _split_version(__version__)
    return (vi[0] == vc[0]) and (vi[1] == vc[1])


class RemoteConnection:
    def __init__(self, remoteIP: str, port=4469, debugGUI=False):
        if debugGUI:
            threading.Thread(target=_debugWindow, args=[self]).start()
            time.sleep(1)
            logging.basicConfig(
                handlers=[TextboxHandler(text2)],
                level=logging.DEBUG,
                format="(Remote Connection Toolkit: %(asctime)s) [%(levelname)s]: %(message)s",
            )
        else:
            self.logger = logging.getLogger()
            format_str = logging.Formatter(
                "(Remote Connection: %(asctime)s) [%(levelname)s]: %(message)s"
            )
            self.logger.setLevel(logging.DEBUG)
            sh = logging.StreamHandler()
            sh.setFormatter(format_str)
            th = logging.FileHandler(
                filename="WRemoteConnection.logging.log", encoding="utf-8"
            )
            th.setFormatter(format_str)
            logging.basicConfig(
                level=logging.DEBUG,
                handlers=[sh, th],
            )
            sys.stderr = open("WRemoteConnection.stderr.log", "a", encoding="utf-8")

        logging.info("Starting Remote Connection...")

        self.connect = True
        self.connectMode = "unconnect"
        self.socketObject = socket.socket()
        self.remoteIP = remoteIP
        self.host = socket.gethostname()
        self.port = port

        logging.info("Complete initialization")

    def getLocalAddress(self) -> str:
        return self.host

    def send(self, msg) -> int:
        if self.connectMode == "passiveConnect":
            return self.clientObject.send(msg)
        else:
            return self.socketObject.send(msg)

    def sendString(self, msg: str) -> int:
        return self.send(msg.encode())

    def passiveConnect(self, timeout=0):
        self.connectMode = "passiveConnect"
        self.socketObject.bind((self.host, self.port))
        self.socketObject.listen(3)
        logging.info("Waiting for Client Connect...")
        self.clientObject, addr = self.socketObject.accept()
        self.clientAddress, self.clientPort = addr
        logging.info(f"Client Connected: {self.clientAddress}:{self.clientPort}")
        if self.clientAddress != self.remoteIP and self.remoteIP != WRCT_ANY_IP_ADDRESS:
            self.clientObject.close()
            logging.error(f"Connected IP {self.clientAddress} Does Not Match The Specified {self.remoteIP}")
            raise RemoteToolkitError(f"Connected IP {self.clientAddress} Does Not Match The Specified {self.remoteIP}")

        # Check the client
        self.sendString(f"Answer! Remote Connection Toolkit version {__version__},server ip: {self.host}")
        if timeout:
            self.clientObject.settimeout(timeout)
        try:
            msg = self.clientObject.recv(1024).decode()
        except socket.timeout:
            logging.warning("Can't Connect Remote Computer: Time Out.")
            return
        ver = re.search(r"\d+\.\d+\.\d+", msg)[0]
        logging.debug(f"Received Version: {ver}")
        if msg and "Answer! Remote Connection Toolkit version" in msg and _check_version(ver):
            logging.info(f"Client Answered: {msg}")
        else:
            logging.error(f"Unsupported Client Interface (Client Answer: {msg})")
            raise RemoteToolkitError(f"Unsupported Client Interface (Client Answer: {msg})")

    def initiativeConnect(self, timeout=0):
        self.connectMode = "initiativeConnect"
        logging.info("Connecting Client...")
        self.socketObject.connect((self.remoteIP, self.port))
        self.clientObject = self.socketObject
        self.clientAddress = self.remoteIP
        self.clientPort = self.port
        logging.info("Client Connected: {}".format(self.clientAddress))

        # Check the client
        if timeout:
            self.clientObject.settimeout(timeout)
        try:
            msg = self.clientObject.recv(1024)
        except socket.timeout:
            logging.warning("Can't Connect Remote Computer: Time Out.")
        msg = msg.decode()

        self.sendString(
            "Answer! Remote Connection Toolkit version {},server ip: {}".format(
                __version__, self.host
            )
        )

    def listen(self, funcList: dict):
        logging.info("Start ranging events...")
        while self.connect:
            # Call event message must like this: "EventKeyWord|arg1,arg2,..."
            msg = self.clientObject.recv(4096).decode()
            cvk = msg.split("|")
            funcRE = cvk[0]
            if funcRE in funcList:
                event_args = cvk[1].split(",")
                logging.info(f"Event {funcRE} Started, Given Args: {event_args}")
                try:
                    funcReturn = funcList[funcRE](self, event_args)
                    logging.log(
                        logging.INFO if funcReturn in (0, None) else logging.WARNING,
                        f"Event {funcRE} Ended, Return Value: {funcReturn}",
                    )
                except Exception as e:
                    logging.error(f"Event {funcRE} Crashed: {e}")
                    self.sendString(f"showError|{base64.b64encode(str(e).encode('utf-8')).decode('utf-8')},")


# Here is the implementation of the built-in instruction set:
"""
The following code is to implement the functions required for the funcList 
variable in remote computer communication. You can use them directly or refer 
to these functions to write your own functions to achieve the desired effect.

Your custom function must like this:
--> def func_name(remote: RemoteConnection, args: list) -> Any: 
        ...
The formal parameters of the function must have and only have the formal 
parameters of the above function. You can encapsulate other variables into 
the "args" parameter.
"""


def ArgsFormater(**kwargs):
    return {k: str(v) for k, v in kwargs.items()}


def showError(remote: RemoteConnection, args: list):
    """Show the error message of remote computer"""
    # args[0]: Error Message
    logging.error(
        "Remote Computer Send An Error: {} .Please Check The Error And Feedback To Us.".format(
            base64.b64decode(args[0]).decode("utf-8")
        )
    )


def closeRemote(remote: RemoteConnection, args: list):
    """Close Connection of The Remote"""
    # No arg used
    remote.sendString("Close|1,")
    remote.clientObject.close()
    logging.info("Connection Closed.")
    remote.connect = False
    remote.connectMode = "unconnect"


def sendPathList(remote: RemoteConnection, args: list):
    """Passive transfer function, generally do not call directly."""
    # args[0] : Folder Path(str)
    _tmp = json.dumps(list(os.listdir(os.path.abspath(args[0]))))
    remote.sendString(_tmp)


def getPathList(remote: RemoteConnection, args: list):
    """Proactively request the contents of a specified folder from a remote computer."""
    # args[0] : Folder Path(str)
    remote.sendString(f"sendPathList|{args[0]},")
    _tmp = remote.clientObject.recv(2048)
    print(_tmp.decode())


def sendFile(remote: RemoteConnection, args: list):
    """Proactively sending file to remote computer."""
    # args[0] : File Path(str)
    remote.sendString(f"receiveFile|{args[0]},")
    msg = remote.clientObject.recv(1024).decode()
    if msg == "Ready":
        with open(os.path.abspath(args[0]), "rb") as file:
            while (f_data := file.read(1024)):
                remote.send(f_data)
    else:
        raise RemoteToolkitError(
            "The remote computer's response is incorrect when transferring files."
        )


def reciveFile(remote: RemoteConnection, args: list):
    """Passive file-receiving function, generally do not call directly."""
    # args[0] : File Path(str)
    remote.sendString("Ready")
    filename = args[0]
    with open(filename, "wb") as file:
        while True:
            f_data = remote.clientObject.recv(1024)
            if f_data:
                file.write(f_data)
            else:
                break


def getFile(remote: RemoteConnection, args: list):
    """Proactively obtain file from remote computer."""
    # args[0] : File Path(str)
    remote.sendString(f"sendFile|{args[0]},")


def catchScreenshot(remote: RemoteConnection, args: list):
    """Catch The Screenshot of This Computer"""
    # args[0] : Monitor Number(int)
    with mss.mss() as sct:
        monitors = sct.monitors[1:]
    monitor = int(args[0])
    with mss.mss() as sct:
        screenshot = sct.grab(monitors[monitor])
        mss.tools.to_png(
            screenshot.rgb, screenshot.size, output=f"tmp_screenshot_{monitor}.png"
        )


def sendScreenshot(remote: RemoteConnection, args: list):
    """Send The Screenshot of This Computer"""
    # args[0] : Monitor Number(int)
    monitor = int(args[0])
    remote.sendString(f"sendFile|tmp_screenshot_{monitor}.png")


def showScreenshot(remote: RemoteConnection, args: list):
    """Get Screenshot of Remote Computer"""
    # args[0] : Monitor Number(int)
    monitor = int(args[0])
    img = PIL.Image.open(f"tmp_screenshot_{monitor}.png")
    img.show()


def getScreenshot(remote: RemoteConnection, args: list):
    """Get Screenshot of Remote Computer"""
    # args[0] : Monitor Number(int)
    # args[1] : Is show image(bool) , default: false
    monitor = int(args[0])
    if len(args) == 1:
        args[1] = "false"
    remote.sendString(f"catchScreenshot|{monitor}")
    remote.sendString(f"sendScreenshot|{monitor}")
    if args[1].lower() == "true":
        showScreenshot(remote, ArgsFormater(args[0]))


def monitorRemoteScreen(remote: RemoteConnection, args: list):
    """Monitor the remote screen continuously."""
    # args[0] : Monitor Number(int)
    # args[1] : Interval between screenshots in seconds (int)
    monitor = int(args[0])
    interval = int(args[1])
    while remote.connect:
        remote.sendString(f"catchScreenshot|{monitor}")
        remote.sendString(f"sendScreenshot|{monitor}")
        time.sleep(interval)


builtin_funcs = {
    "Close": closeRemote,
    "sendPathList": sendPathList,
    "getPathList": getPathList,
    "sendFile": sendFile,
    "reciveFile": reciveFile,
    "getFile": getFile,
    "catchScreenshot": catchScreenshot,
    "sendScreenshot": sendScreenshot,
    "showScreenshot": showScreenshot,
    "getScreenshot": getScreenshot,
    "monitorRemoteScreen": monitorRemoteScreen,
}

if __name__ == "__main__":
    remote = RemoteConnection(WRCT_ANY_IP_ADDRESS, 12345, True)
    remote.initiativeConnect(30)
    remote.listen(builtin_funcs)
