import javax.swing.*;
import java.awt.*;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.logging.*;
import java.util.function.BiConsumer;
import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.util.Base64;
import org.json.JSONArray;

public class RemoteCT {
    private static final String VERSION = "1.4.0";
    public static final String WRCT_ANY_IP_ADDRESS = "WRCT_ANY_IP_ADDRESS";
    
    private Socket socket;
    private Socket clientSocket;
    private ServerSocket serverSocket;
    private boolean connected;
    private String connectMode;
    private String remoteIP;
    private String host;
    private int port;
    private PrintWriter out;
    private BufferedReader in;
    private Logger logger;
    private JTextArea debugTextArea;
    
    public RemoteCT(String remoteIP, int port, boolean debugGUI) throws Exception {
        this.remoteIP = remoteIP;
        this.port = port;
        this.connected = false;
        this.connectMode = "unconnect";
        
        setupLogging(debugGUI);
        
        try {
            this.host = InetAddress.getLocalHost().getHostName();
        } catch (UnknownHostException e) {
            throw new RemoteToolkitError("Failed to get local hostname");
        }
        
        if (debugGUI) {
            createDebugWindow();
        }
        
        logger.info("Complete initialization");
    }
    
    private void setupLogging(boolean debugGUI) {
        logger = Logger.getLogger("RemoteCT");
        logger.setLevel(Level.ALL);
        
        if (debugGUI) {
            // Debug GUI logging will be handled by the debug window
        } else {
            // File logging
            try {
                FileHandler fileHandler = new FileHandler("WRemoteConnection.logging.log");
                fileHandler.setFormatter(new SimpleFormatter());
                logger.addHandler(fileHandler);
            } catch (IOException e) {
                System.err.println("Failed to setup file logging: " + e.getMessage());
            }
        }
    }
    
    private void createDebugWindow() {
        JFrame frame = new JFrame("Remote Connection Toolkit - Debug Helper");
        frame.setSize(800, 600);
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        
        debugTextArea = new JTextArea();
        debugTextArea.setBackground(Color.BLACK);
        debugTextArea.setForeground(Color.WHITE);
        debugTextArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        debugTextArea.setEditable(false);
        
        JScrollPane scrollPane = new JScrollPane(debugTextArea);
        frame.add(scrollPane);
        
        JTextField commandField = new JTextField();
        commandField.addActionListener(e -> {
            String command = commandField.getText();
            debugTextArea.append(">>>" + command + "\n");
            try {
                // Execute command
                // This is simplified - you might want to add proper command handling
                commandField.setText("");
            } catch (Exception ex) {
                debugTextArea.append("Error: " + ex.getMessage() + "\n");
            }
        });
        frame.add(commandField, BorderLayout.SOUTH);
        
        frame.setVisible(true);
    }

    public String getLocalAddress() {
        return host;
    }

    public void passiveConnect(int timeout) throws RemoteToolkitError {
        connectMode = "passiveConnect";
        try {
            serverSocket = new ServerSocket(port);
            logger.info("Waiting for Client Connect...");
            
            clientSocket = serverSocket.accept();
            InetAddress clientAddress = clientSocket.getInetAddress();
            
            if (!remoteIP.equals(WRCT_ANY_IP_ADDRESS) && !clientAddress.getHostAddress().equals(remoteIP)) {
                clientSocket.close();
                throw new RemoteToolkitError("Connected IP " + clientAddress.getHostAddress() + 
                    " Does Not Match The Specified " + remoteIP);
            }
            
            setupStreams();
            
            if (timeout > 0) {
                clientSocket.setSoTimeout(timeout * 1000);
            }
            
            // Version check
            sendString("Answer! Remote Connection Toolkit version " + VERSION + ",server ip: " + host);
            String response = receiveString();
            if (!checkVersion(response)) {
                throw new RemoteToolkitError("Unsupported Client Interface");
            }
            
            connected = true;
            logger.info("Client Connected: " + clientAddress.getHostAddress());
            
        } catch (IOException e) {
            throw new RemoteToolkitError("Connection failed: " + e.getMessage());
        }
    }

    public void initiativeConnect(int timeout) throws RemoteToolkitError {
        connectMode = "initiativeConnect";
        try {
            socket = new Socket(remoteIP, port);
            if (timeout > 0) {
                socket.setSoTimeout(timeout * 1000);
            }
            
            setupStreams();
            
            String response = receiveString();
            sendString("Answer! Remote Connection Toolkit version " + VERSION + ",server ip: " + host);
            
            connected = true;
            logger.info("Connected to server: " + remoteIP);
            
        } catch (IOException e) {
            throw new RemoteToolkitError("Connection failed: " + e.getMessage());
        }
    }

    private void setupStreams() throws IOException {
        Socket activeSocket = (connectMode.equals("passiveConnect")) ? clientSocket : socket;
        out = new PrintWriter(activeSocket.getOutputStream(), true);
        in = new BufferedReader(new InputStreamReader(activeSocket.getInputStream()));
    }

    public void listen(Map<String, BiConsumer<RemoteCT, String[]>> funcList) {
        logger.info("Start ranging events...");
        while (connected) {
            try {
                String message = receiveString();
                String[] parts = message.split("\\|");
                if (parts.length == 2) {
                    String funcName = parts[0];
                    String[] args = parts[1].split(",");
                    
                    if (funcList.containsKey(funcName)) {
                        try {
                            funcList.get(funcName).accept(this, args);
                            logger.info("Event " + funcName + " executed successfully");
                        } catch (Exception e) {
                            logger.severe("Event " + funcName + " failed: " + e.getMessage());
                            sendError(e.getMessage());
                        }
                    }
                }
            } catch (Exception e) {
                logger.severe("Connection error: " + e.getMessage());
                break;
            }
        }
    }

    public void sendString(String message) {
        out.println(message);
    }

    public String receiveString() throws IOException {
        return in.readLine();
    }

    private void sendError(String error) {
        try {
            String encodedError = Base64.getEncoder().encodeToString(error.getBytes());
            sendString("showError|" + encodedError + ",");
        } catch (Exception e) {
            logger.severe("Failed to send error: " + e.getMessage());
        }
    }

    private boolean checkVersion(String message) {
        // Version check implementation
        return message.contains("Answer! Remote Connection Toolkit version") &&
               message.contains(VERSION.substring(0, VERSION.lastIndexOf(".")));
    }

    // Built-in command implementations follow...
    // Add the rest of the built-in commands here
}
