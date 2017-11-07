package se.nbis.lega.cucumber.steps;

import com.github.dockerjava.api.DockerClient;
import com.github.dockerjava.api.command.CreateContainerResponse;
import com.github.dockerjava.api.model.Bind;
import com.github.dockerjava.api.model.Container;
import com.github.dockerjava.api.model.Volume;
import cucumber.api.PendingException;
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
import java.nio.file.Paths;
import java.nio.file.attribute.PosixFilePermission;
import java.util.Arrays;
import java.util.Collections;
import java.util.UUID;

@Slf4j
public class Authentication implements En {

    public Authentication(Context context) {
        Utils utils = context.getUtils();

        Given("^I am a user$", () -> context.setUser("test"));

        Given("^I have an account at Central EGA$", () -> {
            DockerClient dockerClient = utils.getDockerClient();
            String cegaUsersFolderPath = Paths.get("").toAbsolutePath().getParent().toString() + "/docker/bootstrap/private/cega/users";
            String name = UUID.randomUUID().toString();
            String dataFolderName = context.getDataFolder().getName();
            CreateContainerResponse createContainerResponse = dockerClient.
                    createContainerCmd("nbis/ega:worker").
                    withName(name).
                    withCmd("sleep", "1000").
                    withBinds(new Bind(cegaUsersFolderPath, new Volume("/" + dataFolderName))).
                    exec();
            dockerClient.startContainerCmd(createContainerResponse.getId()).exec();
            try {
                Container tempWorker = utils.findContainer("nbis/ega:worker", name);
                double password = Math.random();
                String user = context.getUser();
                utils.executeWithinContainer(tempWorker, String.format("openssl genrsa -out /%s/%s.sec -passout pass:%f 2048", dataFolderName, user, password).split(" "));
                utils.executeWithinContainer(tempWorker, String.format("openssl rsa -in /%s/%s.sec -passin pass:%f -pubout -out /%s/%s.pub", dataFolderName, user, password, dataFolderName, user).split(" "));
                String publicKey = utils.executeWithinContainer(tempWorker, String.format("ssh-keygen -i -mPKCS8 -f /%s/%s.pub", dataFolderName, user).split(" "));
                File userYML = new File(String.format(cegaUsersFolderPath + "/%s.yml", user));
                FileUtils.writeLines(userYML, Arrays.asList("---", "pubkey: " + publicKey));
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
            } finally {
                dockerClient.removeContainerCmd(createContainerResponse.getId()).withForce(true).exec();
            }
        });

        Given("^I have correct private key$",
                () -> context.setPrivateKey(new File(Paths.get("").toAbsolutePath().getParent().toString() + String.format("/docker/bootstrap/private/cega/users/%s.sec", context.getUser()))));

        Given("^I have incorrect private key$",
                () -> context.setPrivateKey(new File(Paths.get("").toAbsolutePath().getParent().toString() + String.format("/docker/bootstrap/private/cega/users/%s.sec", "john"))));

        When("^my account expires$", () -> {
            connect(context);
            disconnect(context);
            try {
                Thread.sleep(1000);
                utils.executeDBQuery(String.format("update users set expiration = '1 second' where elixir_id = '%s'", context.getUser()));
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
            }
        });

        When("^I connect to the LocalEGA inbox via SFTP using private key$", () -> {
            connect(context);
        });

        When("^inbox is not created for me$", () -> {
            try {
                disconnect(context);
                utils.removeUserFromInbox(context.getUser());
                connect(context);
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
            }
        });

        Then("^I am in the local database$", () -> {
            try {
                Assert.assertTrue(utils.isUserExistInDB(context.getUser()));
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Then("^I am not in the local database$", () -> {
            try {
                Assert.assertFalse(utils.isUserExistInDB(context.getUser()));
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
            Files.setPosixFilePermissions(privateKey.toPath(), Collections.singleton(PosixFilePermission.OWNER_READ));
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