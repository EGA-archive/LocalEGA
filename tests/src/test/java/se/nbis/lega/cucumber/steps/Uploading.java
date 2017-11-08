package se.nbis.lega.cucumber.steps;

import com.github.dockerjava.api.DockerClient;
import com.github.dockerjava.api.command.CreateContainerResponse;
import com.github.dockerjava.api.model.AccessMode;
import com.github.dockerjava.api.model.Bind;
import com.github.dockerjava.api.model.Volume;
import com.github.dockerjava.core.command.WaitContainerResultCallback;
import cucumber.api.java8.En;
import lombok.extern.slf4j.Slf4j;
import net.schmizz.sshj.sftp.RemoteResourceInfo;
import org.junit.Assert;
import se.nbis.lega.cucumber.Context;
import se.nbis.lega.cucumber.Utils;

import java.io.File;
import java.io.IOException;
import java.nio.file.Paths;

@Slf4j
public class Uploading implements En {

    public Uploading(Context context) {
        Utils utils = context.getUtils();

        Given("^I have an encrypted file$", () -> {
            DockerClient dockerClient = utils.getDockerClient();
            File rawFile = context.getRawFile();
            try {
                Volume dataVolume = new Volume("/data");
                Volume gpgVolume = new Volume("/root/.gnupg");
                CreateContainerResponse createContainerResponse = dockerClient.
                        createContainerCmd("nbisweden/ega-worker").
                        withVolumes(dataVolume, gpgVolume).
                        withBinds(new Bind(context.getDataFolder().getAbsolutePath(), dataVolume),
                                new Bind(Paths.get("").toAbsolutePath().getParent().toString() + "/docker/bootstrap/private/gpg", gpgVolume, AccessMode.ro)).
                        withCmd(utils.readTraceProperty(".trace.swe1", "GPG exec"), "-r", utils.readTraceProperty(".trace.swe1", "GPG_EMAIL"), "-e", "-o", "/data/" + rawFile.getName() + ".enc", "/data/" + rawFile.getName()).
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
    }

}