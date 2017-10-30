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
import net.schmizz.sshj.sftp.SFTPClient;
import net.schmizz.sshj.transport.verification.PromiscuousVerifier;
import org.apache.commons.io.FileUtils;
import org.assertj.core.api.Assertions;
import org.junit.Assert;
import se.nbis.lega.cucumber.TestUtils;

import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Paths;

@Slf4j
public class Definitions implements En {

    private TestUtils testUtils = new TestUtils();

    private String user;
    private File privateKey;
    private String cegaMQUser;
    private String cegaMQPassword;
    private SFTPClient sftp;
    private File dataFolder;
    private File rawFile;
    private File encryptedFile;

    @Before
    public void setUp() throws IOException {
        dataFolder = new File("data");
        dataFolder.mkdir();
        rawFile = File.createTempFile("data", ".raw", dataFolder);
        FileUtils.writeStringToFile(rawFile, "hello", Charset.defaultCharset());
    }

    @After
    public void tearDown() throws IOException {
        FileUtils.deleteDirectory(dataFolder);
    }

    public Definitions() {
        Given("^I am a user \"([^\"]*)\"$", (String user) -> this.user = user);

        Given("^I have a private key$",
                () -> privateKey = new File(Paths.get("").toAbsolutePath().getParent().toString() + String.format("/docker/bootstrap/private/cega/users/%s.sec", user)));

        When("^I connect to the LocalEGA inbox via SFTP using private key$", () -> {
            try {
                SSHClient ssh = new SSHClient();
                ssh.addHostKeyVerifier(new PromiscuousVerifier());
                ssh.connect("localhost", 2222);
                ssh.authPublickey(user, privateKey.getPath());
                sftp = ssh.newSFTPClient();
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Then("^I'm logged in successfully$", () -> {
            try {
                Assert.assertEquals("inbox", sftp.ls("/").iterator().next().getName());
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Given("^I have an encrypted file$", () -> {
            DockerClient dockerClient = testUtils.getDockerClient();
            try {
                Volume dataVolume = new Volume("/data");
                Volume gpgVolume = new Volume("/root/.gnupg");
                CreateContainerResponse createContainerResponse = dockerClient.
                        createContainerCmd("nbis/ega:worker").
                        withVolumes(dataVolume, gpgVolume).
                        withBinds(new Bind(dataFolder.getAbsolutePath(), dataVolume),
                                new Bind(Paths.get("").toAbsolutePath().getParent().toString() + "/docker/bootstrap/private/gpg", gpgVolume, AccessMode.ro)).
                        withCmd(testUtils.readTraceProperty("GPG exec"), "-r", testUtils.readTraceProperty("GPG_EMAIL"), "-e", "-o", "/data/" + rawFile.getName() + ".enc", "/data/" + rawFile.getName()).
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
            encryptedFile = new File(rawFile.getAbsolutePath() + ".enc");
        });

        When("^I upload encrypted file to the LocalEGA inbox via SFTP$", () -> {
            try {
                sftp.put(encryptedFile.getAbsolutePath(), encryptedFile.getName());
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Then("^the file is uploaded successfully$", () -> {
            try {
                Assert.assertTrue(sftp.ls("/inbox").stream().map(RemoteResourceInfo::getName).anyMatch(n -> encryptedFile.getName().equals(n)));
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Given("^I have CEGA username and password$", () -> {
            try {
                cegaMQUser = testUtils.readTraceProperty("CEGA_MQ_USER");
                cegaMQPassword = testUtils.readTraceProperty("CEGA_MQ_PASSWORD");
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        When("^I ingest file from the LocalEGA inbox$", () -> {
            try {
                testUtils.executeWithinContainer(testUtils.findContainer("nbis/ega:cega_mq", "/cega_mq"),
                        String.format("publish --connection amqp://%s:%s@localhost:5672/%s %s %s --unenc %s --enc %s",
                                cegaMQUser, cegaMQPassword, testUtils.readTraceProperty("CEGA_MQ_VHOST"), user, encryptedFile.getName(), testUtils.calculateMD5(rawFile), testUtils.calculateMD5(encryptedFile)).split(" "));
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Then("^the file is ingested successfully$", () -> {
            try {
                Thread.sleep(1000);
                String query = String.format("select stable_id from files where filename = '%s'", encryptedFile.getName());
                String output = testUtils.executeWithinContainer(testUtils.findContainer("nbis/ega:db", "/ega_db"),
                        "psql", "-U", testUtils.readTraceProperty("DB_USER"), "-d", "lega", "-c", query);
                String vaultFileName = output.split(System.getProperty("line.separator"))[2];
                String cat = testUtils.executeWithinContainer(testUtils.findContainer("nbis/ega:common", "/ega_vault"), "cat", vaultFileName.trim());
                Assertions.assertThat(cat).startsWith("bytearray(b'1')|256|8|b'CTR'");
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });
    }

}