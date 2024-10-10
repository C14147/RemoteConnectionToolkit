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
import time
import json
import socket
import logging
import tkinter
import threading

import Fun


__version__ = "1.2.1"
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
        Form_1.configure(bg="#000000")
        Form_1.configure(highlightthickness=0)
        Fun.Register(uiName, "root", root)
        Fun.Register(uiName, "Form_1", Form_1)
        # Create the elements of root
        self.Text_2 = tkinter.Text(root)
        Fun.Register(uiName, "Text_2", self.Text_2, "Text")
        self.Text_2.place(x=0, y=0, width=800, height=561)
        self.Text_2.configure(bg="#000000")
        self.Text_2.configure(fg="#ffffff")
        self.Text_2.configure(relief="flat")
        Entry_3_Variable = Fun.AddTKVariable(uiName, "Entry_3", "")
        self.Entry_3 = tkinter.Entry(root, textvariable=Entry_3_Variable)
        Fun.Register(uiName, "Entry_3", self.Entry_3)
        self.Entry_3.place(x=2, y=567, width=792, height=27)
        self.Entry_3.configure(bg="#151515")
        self.Entry_3.configure(fg="#ffffff")
        self.Entry_3.configure(relief="flat")
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
        self.clientAddress = addr[0]
        self.clientPort = addr[1]
        logging.info(
            "Client Connected: {}:{}".format(
                self.clientAddress, self.clientPort
            )
        )
        if self.clientAddress != self.remoteIP and self.remoteIP != WRCT_ANY_IP_ADDRESS:
            self.clientObject.close()
            logging.error(
                "Connected IP {} Does Not Match The Specified {}".format(
                    self.clientAddress, self.remoteIP
                )
            )
            raise RemoteToolkitError(
                "Connected IP {} Does Not Match The Specified {}".format(
                    self.clientAddress, self.remoteIP
                )
            )

        # Check the client
        self.sendString(
            "Answer! Remote Connection Toolkit version {},server ip: {}".format(
                __version__, self.host
            )
        )
        if timeout:
            self.clientObject.settimeout(timeout)
        try:
            msg = self.clientObject.recv(1024)
        except socket.timeout:
            logging.warning("Can't Connect Remote Computer: Time Out.")
        msg = msg.decode()
        ver = re.search("\d+\.\d+\.\d+", msg)[0]
        logging.debug(f"Recived Version: {ver}")
        if (
            msg
            and ("Answer! Remote Connection Toolkit version" in msg)
            and _check_version(ver)
        ):
            logging.info("Cilent Answered: " + msg)
        else:
            logging.error(
                "Unsupported Client Interface (Client Answer: {})".format(msg)
            )
            raise RemoteToolkitError(
                "Unsupported Client Interface (Client Answer: {})".format(msg)
            )

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
            msg = self.clientObject.recv(4096)
            msg = msg.decode()
            cvk = msg.split("|")
            for funcRE in funcList.keys():
                if funcRE == cvk[0]:
                    event_args = cvk[1].split(",")
                    logging.info(
                        "Event {} Started, Gived Args: {}".format(
                            funcRE, event_args
                        )
                    )
                    funcReturn = funcList[funcRE](self, event_args)
                    logging.log(
                        (
                            logging.INFO
                            if (funcReturn == 0 or funcReturn == None)
                            else logging.WARNING
                        ),
                        "Event {} Ended, Return Value: {}".format(
                            funcRE, funcReturn
                        )
                    )


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


def closeRemote(remote: RemoteConnection, args: list):
    """Close Connection of The Remote"""
    remote.sendString("Close|1,")
    remote.clientObject.close()
    logging.info("Connection Closed.")
    remote.connect = False
    remote.connectMode = "unconnect"


def sendPathList(remote: RemoteConnection, args: list):
    """Passive transfer function, generally do not call directly."""
    _tmp = json.dumps(list(os.listdir(os.path.abspath(args[0]))))
    remote.sendString(_tmp)


def getPathList(remote: RemoteConnection, args: list):
    """Proactively request the contents of a specified folder from a remote computer"""
    remote.sendString(f"sendPathList|{args[0]},")
    _tmp = remote.clientObject.recv(2048)
    print(_tmp.decode())


def sendFile(remote: RemoteConnection, args: list):
    """Proactively sending file to remote computer."""
    remote.sendString(f"reciveFile|{args[0]},")
    msg = remote.clientObject.recv(1024)
    msg = msg.decode()
    if msg == "Ready":
        with open(os.path.abspath(args[0]), "rb") as file:
            while True:
                f_data = file.read(1024)
                if f_data:
                    remote.send(f_data)
                else:
                    break
    else:
        raise RemoteToolkitError(
            "The remote computer's response is incorrect when transferring files."
        )


def reciveFile(remote: RemoteConnection, args: list):
    """Passive file-receiving function, generally do not call directly."""
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
    remote.sendString(f"sendFile|{args[0]},")


builtin_funcs = {
    "Close": closeRemote,
    "sendPathList": sendPathList,
    "getPathList": getPathList,
    "sendFile": sendFile,
    "reciveFile": reciveFile,
    "getFile": getFile,
}

if __name__ == "__main__":
    remote = RemoteConnection(WRCT_ANY_IP_ADDRESS, 12345, True)
    remote.initiativeConnect(30)
    remote.listen(builtin_funcs)
