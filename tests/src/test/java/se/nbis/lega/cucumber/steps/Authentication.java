package se.nbis.lega.cucumber.steps;

import cucumber.api.java8.En;
import lombok.extern.slf4j.Slf4j;
import net.schmizz.sshj.SSHClient;
import net.schmizz.sshj.transport.verification.PromiscuousVerifier;
import org.junit.Assert;
import se.nbis.lega.cucumber.Context;

import java.io.File;
import java.io.IOException;
import java.nio.file.Paths;

@Slf4j
public class Authentication implements En {

    public Authentication(Context context) {
        Given("^I am a user \"([^\"]*)\"$", context::setUser);

        Given("^I have a private key$",
                () -> context.setPrivateKey(new File(Paths.get("").toAbsolutePath().getParent().toString() + String.format("/docker/bootstrap/private/cega/users/%s.sec", context.getUser()))));

        When("^I connect to the LocalEGA inbox via SFTP using private key$", () -> {
            try {
                SSHClient ssh = new SSHClient();
                ssh.addHostKeyVerifier(new PromiscuousVerifier());
                ssh.connect("localhost", 2222);
                ssh.authPublickey(context.getUser(), context.getPrivateKey().getPath());
                context.setSftp(ssh.newSFTPClient());
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Then("^I'm logged in successfully$", () -> {
            try {
                Assert.assertEquals("inbox", context.getSftp().ls("/").iterator().next().getName());
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });
    }

}