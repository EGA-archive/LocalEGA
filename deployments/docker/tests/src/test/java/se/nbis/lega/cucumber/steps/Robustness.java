package se.nbis.lega.cucumber.steps;

import cucumber.api.java8.En;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.io.FileUtils;
import org.junit.Assert;
import se.nbis.lega.cucumber.Context;
import se.nbis.lega.cucumber.Utils;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import java.io.File;
import java.io.RandomAccessFile;

@Slf4j
public class Robustness implements En {

    public Robustness(Context context) {
        Utils utils = context.getUtils();

        When("^the system is restarted$", utils::restartAllLocalEGAContainers);

        // TODO: Don't load large file in memory - stream it
        Given("^I have a big file encrypted with Crypt4GH using a LocalEGA's pubic key$", () -> {
            try {
                File rawFile = context.getRawFile();
                try (RandomAccessFile randomAccessFile = new RandomAccessFile(rawFile, "rw")) {
                    randomAccessFile.setLength(1024 * 1024 * 10);
                }
                KeyGenerator keygenerator = KeyGenerator.getInstance("DES");
                SecretKey desKey = keygenerator.generateKey();
                Cipher desCipher = Cipher.getInstance("DES");
                desCipher.init(Cipher.ENCRYPT_MODE, desKey);
                byte[] encryptedContents = desCipher.doFinal(FileUtils.readFileToByteArray(rawFile));
                File encryptedFile = new File(rawFile.getAbsolutePath() + ".enc");
                FileUtils.writeByteArrayToFile(encryptedFile, encryptedContents);
                context.setEncryptedFile(encryptedFile);
            } catch (Exception e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

    }

}
