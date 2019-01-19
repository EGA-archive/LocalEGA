package se.nbis.lega.cucumber;

import lombok.Data;
import net.schmizz.sshj.SSHClient;
import net.schmizz.sshj.sftp.SFTPClient;
import net.schmizz.sshj.userauth.keyprovider.KeyProvider;

import java.io.File;
import java.io.IOException;
import java.util.Map;

@Data
public class Context {

    private final Utils utils;

    private String user;
    private KeyProvider keyProvider;
    private String cegaMQUser;
    private String cegaMQPassword;
    private String cegaMQVHost;
    private String routingKey;
    private SSHClient ssh;
    private SFTPClient sftp;
    private File dataFolder;
    private File rawFile;
    private File encryptedFile;
    private File downloadedFile;
    private String sessionKey;
    private String iv;
    private Map<String, String> ingestionInformation;

    private boolean authenticationFailed;

    public Context() throws IOException {
        this.utils = new Utils();
    }

}
