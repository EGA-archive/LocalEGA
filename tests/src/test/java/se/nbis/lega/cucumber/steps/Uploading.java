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
            String dataFolderName = context.getDataFolder().getName();
            Volume dataVolume = new Volume("/" + dataFolderName);
            Volume gpgVolume = new Volume("/root/.gnupg");
            CreateContainerResponse createContainerResponse = null;
            try {
                String targetInstance = context.getTargetInstance();
                createContainerResponse = dockerClient.
                        createContainerCmd("nbisweden/ega-worker").
                        withVolumes(dataVolume, gpgVolume).
                        withBinds(new Bind(Paths.get(dataFolderName).toAbsolutePath().toString(), dataVolume),
                                new Bind(String.format("%s/%s/gpg", utils.getPrivateFolderPath(), targetInstance), gpgVolume, AccessMode.ro)).
                        withCmd("gpg2", "-r", utils.readTraceProperty(targetInstance, "GPG_EMAIL"), "-e", "-o", "/data/" + rawFile.getName() + ".enc", "/data/" + rawFile.getName()).
                        exec();
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
            try {
                dockerClient.startContainerCmd(createContainerResponse.getId()).exec();
                WaitContainerResultCallback resultCallback = new WaitContainerResultCallback();
                dockerClient.waitContainerCmd(createContainerResponse.getId()).exec(resultCallback);
                resultCallback.awaitCompletion();
            } catch (InterruptedException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            } finally {
                dockerClient.removeContainerCmd(createContainerResponse.getId()).withForce(true).exec();
            }
            context.setEncryptedFile(new File(rawFile.getAbsolutePath() + ".enc"));
        });

        When("^I upload encrypted file to the LocalEGA inbox via SFTP$", () -> {
            try {
                File encryptedFile = context.getEncryptedFile();
                context.getSftp().put(encryptedFile.getAbsolutePath(), encryptedFile.getName());
            } catch (IOException e) {
                log.error(e.getMessage(), e);
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
