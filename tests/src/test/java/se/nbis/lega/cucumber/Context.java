package se.nbis.lega.cucumber;

import lombok.Data;
import net.schmizz.sshj.SSHClient;
import net.schmizz.sshj.sftp.SFTPClient;

import java.io.File;

@Data
public class Context {

    private Utils utils = new Utils();

    private String user;
    private File privateKey;
    private String cegaMQUser;
    private String cegaMQPassword;
    private SSHClient ssh;
    private SFTPClient sftp;
    private File dataFolder;
    private File rawFile;
    private File encryptedFile;

    private boolean authenticationFailed;

}
