package se.nbis.lega.deployment.test;

import net.schmizz.sshj.SSHClient;
import net.schmizz.sshj.sftp.SFTPClient;
import net.schmizz.sshj.transport.verification.PromiscuousVerifier;
import org.gradle.api.internal.tasks.options.Option;
import org.gradle.api.tasks.Input;
import org.gradle.api.tasks.InputFile;
import org.gradle.api.tasks.TaskAction;
import se.nbis.lega.deployment.Groups;
import se.nbis.lega.deployment.LocalEGATask;

import java.io.File;
import java.io.IOException;

public class UploadFileTask extends LocalEGATask {

    private String host;

    public UploadFileTask() {
        super();
        this.setGroup(Groups.TEST.name());
        this.dependsOn("encrypt");
    }

    @TaskAction
    public void run() throws IOException {
        host = System.getenv("DOCKER_HOST").substring(6).split(":")[0];
        SSHClient ssh = new SSHClient();
        ssh.addHostKeyVerifier(new PromiscuousVerifier());
        ssh.connect(host, 2222);
        ssh.authPublickey("john", getProject().file("cega/.tmp/users/john.sec").getAbsolutePath());
        SFTPClient client = ssh.newSFTPClient();
        client.put(getEncFile().getAbsolutePath(), "data.raw.enc");
        ssh.close();
    }

    @InputFile
    public File getEncFile() {
        return getProject().file(".tmp/data.raw.enc");
    }

}
