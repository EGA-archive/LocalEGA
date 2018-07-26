package se.nbis.lega.deployment.test;

import net.schmizz.sshj.SSHClient;
import net.schmizz.sshj.sftp.SFTPClient;
import net.schmizz.sshj.transport.verification.PromiscuousVerifier;
import org.gradle.api.tasks.TaskAction;
import se.nbis.lega.deployment.Groups;
import se.nbis.lega.deployment.LocalEGATask;

import java.io.IOException;

public class UploadFileTask extends LocalEGATask {

    public UploadFileTask() {
        super();
        this.setGroup(Groups.TEST.name());
        this.dependsOn("encrypt");
    }

    @TaskAction
    public void run() throws IOException {
        SSHClient ssh = new SSHClient();
        ssh.addHostKeyVerifier(new PromiscuousVerifier());
        ssh.connect("localhost", 2222);
        ssh.authPublickey("john", getProject().file("cega/.tmp/users/john.sec").getAbsolutePath());
        SFTPClient client = ssh.newSFTPClient();
        client.put(getProject().file(".tmp/data.raw.enc").getAbsolutePath(), "data.raw.enc");
        ssh.close();
    }

}
