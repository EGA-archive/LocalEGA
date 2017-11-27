package se.nbis.lega.cucumber.steps;

import com.github.dockerjava.api.DockerClient;
import cucumber.api.java8.En;
import lombok.extern.slf4j.Slf4j;
import net.schmizz.sshj.sftp.RemoteResourceInfo;
import org.apache.commons.io.FileUtils;
import org.junit.Assert;
import se.nbis.lega.cucumber.Context;
import se.nbis.lega.cucumber.Utils;

import javax.crypto.*;
import java.io.File;
import java.io.IOException;
import java.nio.file.Paths;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;

@Slf4j
public class Uploading implements En {

    public Uploading(Context context) {
        Utils utils = context.getUtils();

        Given("^I have a file encrypted with OpenPGP$", () -> {
            DockerClient dockerClient = utils.getDockerClient();
            File rawFile = context.getRawFile();
            String dataFolderName = context.getDataFolder().getName();
            try {
                String targetInstance = context.getTargetInstance();
                String encryptionCommand = "gpg2 -r " + utils.readTraceProperty(targetInstance, "GPG_EMAIL") + " -e -o /data/" + rawFile.getName() + ".enc /data/" + rawFile.getName();
                utils.spawnTempWorkerAndExecute(targetInstance, Paths.get(dataFolderName).toAbsolutePath().toString(), "/" + dataFolderName, encryptionCommand);
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
            context.setEncryptedFile(new File(rawFile.getAbsolutePath() + ".enc"));
        });

        Given("^I have a file encrypted not with OpenPGP$", () -> {
            try {
                File rawFile = context.getRawFile();
                KeyGenerator keygenerator = KeyGenerator.getInstance("DES");
                SecretKey desKey = keygenerator.generateKey();
                Cipher desCipher = Cipher.getInstance("DES");
                desCipher.init(Cipher.ENCRYPT_MODE, desKey);
                byte[] encryptedContents = desCipher.doFinal(FileUtils.readFileToByteArray(rawFile));
                File encryptedFile = new File(rawFile.getAbsolutePath() + ".enc");
                FileUtils.writeByteArrayToFile(encryptedFile, encryptedContents);
                context.setEncryptedFile(encryptedFile);
            } catch (NoSuchAlgorithmException | NoSuchPaddingException | InvalidKeyException | IllegalBlockSizeException | BadPaddingException | IOException e) {
                e.printStackTrace();
            }
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
