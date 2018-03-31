package se.nbis.lega.cucumber;

import lombok.Data;
import net.schmizz.sshj.SSHClient;
import net.schmizz.sshj.sftp.SFTPClient;
import net.schmizz.sshj.userauth.keyprovider.KeyProvider;
import net.schmizz.sshj.userauth.keyprovider.KeyProviderUtil;

import java.io.File;
import java.io.IOException;
import java.security.KeyPair;
import java.util.List;

@Data
public class Context {

    private final Utils utils;

    private String user;
    private List<String> instances;
    private String targetInstance;
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

    private boolean authenticationFailed;

    public Context() throws IOException {
        this.utils = new Utils();
    }

}