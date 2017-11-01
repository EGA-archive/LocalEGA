package se.nbis.lega.cucumber;

import lombok.Data;
import net.schmizz.sshj.sftp.SFTPClient;
import org.apache.commons.io.FileUtils;

import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;

@Data
public class Context {

    private Utils utils = new Utils();

    private String user;
    private File privateKey;
    private String cegaMQUser;
    private String cegaMQPassword;
    private SFTPClient sftp;
    private File dataFolder;
    private File rawFile;
    private File encryptedFile;

    public Context() throws IOException {
        dataFolder = new File("data");
        dataFolder.mkdir();
        rawFile = File.createTempFile("data", ".raw", dataFolder);
        FileUtils.writeStringToFile(rawFile, "hello", Charset.defaultCharset());
    }

}
