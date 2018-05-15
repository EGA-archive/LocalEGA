package se.nbis.lega.cucumber.steps;

import cucumber.api.java8.En;
import lombok.extern.slf4j.Slf4j;
import org.bouncycastle.openpgp.PGPException;
import org.c02e.jpgpj.CompressionAlgorithm;
import org.c02e.jpgpj.EncryptionAlgorithm;
import org.c02e.jpgpj.Encryptor;
import org.c02e.jpgpj.Key;
import org.junit.Assert;
import se.nbis.lega.cucumber.Context;
import se.nbis.lega.cucumber.Utils;

import java.io.File;
import java.io.IOException;
import java.io.RandomAccessFile;

@Slf4j
public class Robustness implements En {

    public Robustness(Context context) {
        Utils utils = context.getUtils();

        When("^the system is restarted$", utils::restartAllLocalEGAContainers);

        Given("^I have a big file encrypted with OpenPGP using a \"([^\"]*)\" key$", (String instance) -> {
            try {
                File rawFile = context.getRawFile();
                try (RandomAccessFile randomAccessFile = new RandomAccessFile(rawFile, "rw")) {
                    randomAccessFile.setLength(1024 * 1024 * 10);
                }
                File encryptedFile = new File(rawFile.getAbsolutePath() + ".enc");
                Encryptor encryptor = new Encryptor(new Key(new File(String.format("%s/%s/pgp/ega.pub", utils.getPrivateFolderPath(), instance))));
                encryptor.setEncryptionAlgorithm(EncryptionAlgorithm.AES256);
                encryptor.setCompressionAlgorithm(CompressionAlgorithm.Uncompressed);
                encryptor.setSigningAlgorithm(null);
                encryptor.encrypt(rawFile, encryptedFile);
                context.setEncryptedFile(encryptedFile);
            } catch (IOException | PGPException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

    }

}
