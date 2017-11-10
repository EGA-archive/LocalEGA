package se.nbis.lega.cucumber.steps;

import com.github.dockerjava.api.DockerClient;
import com.github.dockerjava.api.command.CreateContainerResponse;
import com.github.dockerjava.api.model.Bind;
import com.github.dockerjava.api.model.Container;
import com.github.dockerjava.api.model.Volume;
import cucumber.api.DataTable;
import cucumber.api.java8.En;
import lombok.extern.slf4j.Slf4j;
import net.schmizz.sshj.SSHClient;
import net.schmizz.sshj.transport.verification.PromiscuousVerifier;
import org.apache.commons.io.FileUtils;
import org.junit.Assert;
import se.nbis.lega.cucumber.Context;
import se.nbis.lega.cucumber.Utils;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.attribute.PosixFilePermission;
import java.util.Arrays;
import java.util.Collections;
import java.util.UUID;

@Slf4j
public class Authentication implements En {

    public Authentication(Context context) {
        Utils utils = context.getUtils();

        Given("^I am a user of LocalEGA instances:$", (DataTable instances) -> {
            context.setUser("test");
            context.setInstances(instances.asList(String.class));
        });

        Given("^I have an account at Central EGA$", () -> {
            for (String instance : context.getInstances()) {
                DockerClient dockerClient = utils.getDockerClient();
                String cegaUsersFolderPath = utils.getPrivateFolderPath() + "/cega/users/" + instance;
                String name = UUID.randomUUID().toString();
                String dataFolderName = context.getDataFolder().getName();
                CreateContainerResponse createContainerResponse = dockerClient.
                        createContainerCmd("nbisweden/ega-worker").
                        withName(name).
                        withCmd("sleep", "1000").
                        withBinds(new Bind(cegaUsersFolderPath, new Volume("/" + dataFolderName))).
                        exec();
                dockerClient.startContainerCmd(createContainerResponse.getId()).exec();
                try {
                    Container tempWorker = utils.findContainer("nbisweden/ega-worker", name);
                    double password = Math.random();
                    String user = context.getUser();
                    String opensslCommand = utils.readTraceProperty(instance, "OPENSSL exec");
                    utils.executeWithinContainer(tempWorker, String.format("%s genrsa -out /%s/%s.sec -passout pass:%f 2048", opensslCommand, dataFolderName, user, password).split(" "));
                    utils.executeWithinContainer(tempWorker, String.format("%s rsa -in /%s/%s.sec -passin pass:%f -pubout -out /%s/%s.pub", opensslCommand, dataFolderName, user, password, dataFolderName, user).split(" "));
                    String publicKey = utils.executeWithinContainer(tempWorker, String.format("ssh-keygen -i -mPKCS8 -f /%s/%s.pub", dataFolderName, user).split(" "));
                    File userYML = new File(String.format(cegaUsersFolderPath + "/%s.yml", user));
                    FileUtils.writeLines(userYML, Arrays.asList("---", "pubkey: " + publicKey));
                } catch (IOException | InterruptedException e) {
                    log.error(e.getMessage(), e);
                } finally {
                    dockerClient.removeContainerCmd(createContainerResponse.getId()).withForce(true).exec();
                }
            }
        });

        Given("^I want to work with instance \"([^\"]*)\"$", context::setTargetInstance);

        Given("^I have correct private key$",
                () -> {
                    try {
                        File privateKey = new File(String.format("%s/cega/users/%s/%s.sec", utils.getPrivateFolderPath(), context.getTargetInstance(), context.getUser()));
                        Files.setPosixFilePermissions(privateKey.toPath(), Collections.singleton(PosixFilePermission.OWNER_READ));
                        context.setPrivateKey(privateKey);
                    } catch (IOException e) {
                        log.error(e.getMessage(), e);
                    }
                });

        Given("^I have incorrect private key$",
                () -> context.setPrivateKey(new File(String.format("%s/cega/users/%s.sec", utils.getPrivateFolderPath(), "john"))));

        Given("^Inbox is deleted for my user$", () -> {
            try {
                utils.removeUserFromInbox(context.getTargetInstance(), context.getUser());
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
            }
        });

        When("^my account expires$", () -> {
            connect(context);
            disconnect(context);
            try {
                Thread.sleep(1000);
                utils.executeDBQuery(context.getTargetInstance(),
                        String.format("update users set expiration = '1 second' where elixir_id = '%s'", context.getUser()));
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
            }
        });

        When("^I connect to the LocalEGA inbox via SFTP using private key$", () -> connect(context));

        When("^I disconnect from the LocalEGA inbox$", () -> disconnect(context));

        When("^inbox is not created for me$", () -> {
            try {
                disconnect(context);
                utils.removeUserFromInbox(context.getTargetInstance(), context.getUser());
                connect(context);
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
            }
        });

        Then("^I am in the local database$", () -> {
            try {
                Assert.assertTrue(utils.isUserExistInDB(context.getTargetInstance(), context.getUser()));
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Then("^I am not in the local database$", () -> {
            try {
                Assert.assertFalse(utils.isUserExistInDB(context.getTargetInstance(), context.getUser()));
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Then("^I'm logged in successfully$", () -> Assert.assertFalse(context.isAuthenticationFailed()));

        Then("^authentication fails$", () -> Assert.assertTrue(context.isAuthenticationFailed()));

    }

    private void connect(Context context) {
        try {
            SSHClient ssh = new SSHClient();
            ssh.addHostKeyVerifier(new PromiscuousVerifier());
            ssh.connect("localhost", 2222);
            File privateKey = context.getPrivateKey();
            ssh.authPublickey(context.getUser(), privateKey.getPath());

            context.setSsh(ssh);
            context.setSftp(ssh.newSFTPClient());
            context.setAuthenticationFailed(false);
        } catch (Exception e) {
            log.error(e.getMessage(), e);
            context.setAuthenticationFailed(true);
        }
    }

    private void disconnect(Context context) {
        try {
            context.getSftp().close();
            context.getSsh().disconnect();
        } catch (Exception e) {
            log.error(e.getMessage(), e);
        }
    }

}