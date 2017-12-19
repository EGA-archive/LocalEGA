package se.nbis.lega.cucumber.steps;

import cucumber.api.DataTable;
import cucumber.api.java8.En;
import lombok.extern.slf4j.Slf4j;
import net.schmizz.sshj.SSHClient;
import net.schmizz.sshj.transport.verification.PromiscuousVerifier;
import net.schmizz.sshj.userauth.UserAuthException;
import org.apache.commons.io.FileUtils;
import org.junit.Assert;
import se.nbis.lega.cucumber.Context;
import se.nbis.lega.cucumber.Utils;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;

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
                String cegaUsersFolderPath = utils.getPrivateFolderPath() + "/cega/users/" + instance;
                String dataFolderName = context.getDataFolder().getName();
                double password = Math.random();
                String user = context.getUser();
                String command1 = String.format("openssl genrsa -out /%s/%s.sec -passout pass:%f 2048", dataFolderName, user, password);
                String command2 = String.format("openssl rsa -in /%s/%s.sec -passin pass:%f -pubout -out /%s/%s.pub", dataFolderName, user, password, dataFolderName, user);
                String command3 = String.format("ssh-keygen -i -mPKCS8 -f /%s/%s.pub", dataFolderName, user);
                String command4 = String.format("chmod -R 0777 /%s", dataFolderName);
                try {
                    List<String> results = utils.spawnTempWorkerAndExecute(instance, cegaUsersFolderPath, "/" + dataFolderName, command1, command2, command3, command4);
                    String publicKey = results.get(2);
                    File userYML = new File(String.format(cegaUsersFolderPath + "/%s.yml", user));
                    FileUtils.writeLines(userYML, Arrays.asList("---", "pubkey: " + publicKey));
                } catch (IOException e) {
                    log.error(e.getMessage(), e);
                }
            }
        });

        Given("^I want to work with instance \"([^\"]*)\"$", context::setTargetInstance);

        Given("^I have correct private key$",
                () -> {
                    File privateKey = new File(String.format("%s/cega/users/%s/%s.sec", utils.getPrivateFolderPath(), context.getTargetInstance(), context.getUser()));
                    context.setPrivateKey(privateKey);
                });

        Given("^I have incorrect private key$",
                () -> context.setPrivateKey(new File(String.format("%s/cega/users/%s.sec", utils.getPrivateFolderPath(), "john"))));

        Given("^inbox is deleted for my user$", () -> {
            try {
                utils.removeUserInbox(context.getTargetInstance(), context.getUser());
            } catch (InterruptedException e) {
                log.error(e.getMessage(), e);
            }
        });

        Given("^file is removed from the inbox$", () -> {
            try {
                utils.removeUploadedFileFromInbox(context.getTargetInstance(), context.getUser(), context.getEncryptedFile().getName());
            } catch (InterruptedException e) {
                log.error(e.getMessage(), e);
            }
        });

        Given("^the database connectivity is broken$", () -> {
            try {
                utils.executeWithinContainer(utils.findContainer(utils.getProperty("images.name.inbox"),
                        utils.getProperty("container.prefix.inbox") + context.getTargetInstance()),
                        "sed -i s/dbname=lega/dbname=wrong/g /etc/ega/auth.conf".split(" "));
            } catch (InterruptedException e) {
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
                utils.removeUserInbox(context.getTargetInstance(), context.getUser());
                connect(context);
            } catch (InterruptedException e) {
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
            ssh.connect("localhost",
                    Integer.parseInt(context.getUtils().readTraceProperty(context.getTargetInstance(), "DOCKER_INBOX_PORT")));
            File privateKey = context.getPrivateKey();
            ssh.authPublickey(context.getUser(), privateKey.getPath());

            context.setSsh(ssh);
            context.setSftp(ssh.newSFTPClient());
            context.setAuthenticationFailed(false);
        } catch (UserAuthException e) {
            context.setAuthenticationFailed(true);
        } catch (IOException e) {
            log.error(e.getMessage(), e);
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
