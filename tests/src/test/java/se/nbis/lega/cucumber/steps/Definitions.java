package se.nbis.lega.cucumber.steps;

import com.github.dockerjava.api.DockerClient;
import com.github.dockerjava.api.command.CreateContainerResponse;
import com.github.dockerjava.api.model.AccessMode;
import com.github.dockerjava.api.model.Bind;
import com.github.dockerjava.api.model.Volume;
import com.github.dockerjava.core.command.WaitContainerResultCallback;
import cucumber.api.java.After;
import cucumber.api.java.Before;
import cucumber.api.java8.En;
import lombok.extern.slf4j.Slf4j;
import net.schmizz.sshj.SSHClient;
import net.schmizz.sshj.sftp.RemoteResourceInfo;
import net.schmizz.sshj.transport.verification.PromiscuousVerifier;
import org.apache.commons.io.FileUtils;
import org.assertj.core.api.Assertions;
import org.junit.Assert;
import se.nbis.lega.cucumber.Context;
import se.nbis.lega.cucumber.Utils;

import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Paths;

@Slf4j
public class Definitions implements En {

    private Context context;
    private Utils utils;

    public Definitions(Context context) {
        this();
        this.context = context;
        this.utils = new Utils();
    }

    @Before
    public void setUp() throws IOException {
        File dataFolder = new File("data");
        dataFolder.mkdir();
        File rawFile = File.createTempFile("data", ".raw", dataFolder);
        FileUtils.writeStringToFile(rawFile, "hello", Charset.defaultCharset());
        context.setDataFolder(dataFolder);
        context.setRawFile(rawFile);
    }

    @After
    public void tearDown() throws IOException {
        FileUtils.deleteDirectory(context.getDataFolder());
    }

    private Definitions() {
        Given("^I am a user \"([^\"]*)\"$", (String user) -> context.setUser(user));

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

        Given("^I have an encrypted file$", () -> {
            DockerClient dockerClient = utils.getDockerClient();
            File rawFile = context.getRawFile();
            try {
                Volume dataVolume = new Volume("/data");
                Volume gpgVolume = new Volume("/root/.gnupg");
                CreateContainerResponse createContainerResponse = dockerClient.
                        createContainerCmd("nbis/ega:worker").
                        withVolumes(dataVolume, gpgVolume).
                        withBinds(new Bind(context.getDataFolder().getAbsolutePath(), dataVolume),
                                new Bind(Paths.get("").toAbsolutePath().getParent().toString() + "/docker/bootstrap/private/gpg", gpgVolume, AccessMode.ro)).
                        withCmd(utils.readTraceProperty("GPG exec"), "-r", utils.readTraceProperty("GPG_EMAIL"), "-e", "-o", "/data/" + rawFile.getName() + ".enc", "/data/" + rawFile.getName()).
                        exec();
                dockerClient.startContainerCmd(createContainerResponse.getId()).exec();
                WaitContainerResultCallback resultCallback = new WaitContainerResultCallback();
                dockerClient.waitContainerCmd(createContainerResponse.getId()).exec(resultCallback);
                resultCallback.awaitCompletion();
                dockerClient.removeContainerCmd(createContainerResponse.getId()).exec();
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
            context.setEncryptedFile(new File(rawFile.getAbsolutePath() + ".enc"));
        });

        When("^I upload encrypted file to the LocalEGA inbox via SFTP$", () -> {
            try {
                File encryptedFile = context.getEncryptedFile();
                context.getSftp().put(encryptedFile.getAbsolutePath(), encryptedFile.getName());
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Then("^the file is uploaded successfully$", () -> {
            try {
                Assert.assertTrue(context.getSftp().ls("/inbox").stream().map(RemoteResourceInfo::getName).anyMatch(n -> context.getEncryptedFile().getName().equals(n)));
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Given("^I have CEGA username and password$", () -> {
            try {
                context.setCegaMQUser(utils.readTraceProperty("CEGA_MQ_USER"));
                context.setCegaMQPassword(utils.readTraceProperty("CEGA_MQ_PASSWORD"));
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        When("^I ingest file from the LocalEGA inbox$", () -> {
            try {
                File encryptedFile = context.getEncryptedFile();
                utils.executeWithinContainer(utils.findContainer("nbis/ega:cega_mq", "/cega_mq"),
                        String.format("publish --connection amqp://%s:%s@localhost:5672/%s %s %s --unenc %s --enc %s",
                                context.getCegaMQUser(),
                                context.getCegaMQPassword(),
                                utils.readTraceProperty("CEGA_MQ_VHOST"),
                                context.getUser(),
                                encryptedFile.getName(),
                                utils.calculateMD5(context.getRawFile()),
                                utils.calculateMD5(encryptedFile)).split(" "));
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Then("^the file is ingested successfully$", () -> {
            try {
                Thread.sleep(1000);
                String query = String.format("select stable_id from files where filename = '%s'", context.getEncryptedFile().getName());
                String output = utils.executeWithinContainer(utils.findContainer("nbis/ega:db", "/ega_db"),
                        "psql", "-U", utils.readTraceProperty("DB_USER"), "-d", "lega", "-c", query);
                String vaultFileName = output.split(System.getProperty("line.separator"))[2];
                String cat = utils.executeWithinContainer(utils.findContainer("nbis/ega:common", "/ega_vault"), "cat", vaultFileName.trim());
                Assertions.assertThat(cat).startsWith("bytearray(b'1')|256|8|b'CTR'");
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });
    }

}