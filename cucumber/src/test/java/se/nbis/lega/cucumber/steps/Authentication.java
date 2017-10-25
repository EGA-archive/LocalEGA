package se.nbis.lega.cucumber.steps;

import cucumber.api.java.Before;
import cucumber.api.java8.En;
import net.schmizz.sshj.SSHClient;
import net.schmizz.sshj.sftp.SFTPClient;
import net.schmizz.sshj.transport.verification.PromiscuousVerifier;
import org.junit.Assert;

import java.io.File;
import java.io.IOException;

public class Authentication implements En {

    private static final String USERNAME = "john";

    private File privateKey;

    private SFTPClient sftp;

    @Before
    public void setUp() throws IOException {
        privateKey = new File("../docker/bootstrap/private/cega/users/" + USERNAME + ".sec");
    }

    public Authentication() {
        Given("I have a private key", () -> Assert.assertNotNull(privateKey));

        When("I try to connect to the LocalEGA inbox via SFTP using private key", () -> {
            try {
                SSHClient ssh = new SSHClient();
                ssh.addHostKeyVerifier(new PromiscuousVerifier());
                ssh.connect("localhost", 2222);
                ssh.authPublickey(USERNAME, privateKey.getPath());
                sftp = ssh.newSFTPClient();
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });

        Then("the operation is successful", () -> {
            try {
                Assert.assertEquals("inbox", sftp.ls("/").iterator().next().getName());
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });
    }

}