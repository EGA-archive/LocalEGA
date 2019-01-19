package se.nbis.lega.cucumber.steps;

import cucumber.api.java8.En;
import lombok.extern.slf4j.Slf4j;
import net.schmizz.sshj.sftp.RemoteResourceInfo;
import no.uio.ifi.crypt4gh.stream.Crypt4GHOutputStream;
import org.apache.commons.codec.binary.Hex;
import org.apache.commons.codec.digest.DigestUtils;
import org.apache.commons.io.FileUtils;
import org.junit.Assert;
import se.nbis.lega.cucumber.Context;
import se.nbis.lega.cucumber.Utils;

import javax.crypto.*;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.charset.Charset;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;

@Slf4j
public class Uploading implements En {

    public Uploading(Context context) {
        Utils utils = context.getUtils();

        Given("^I have a ([^\"]*) MB file encrypted with Crypt4GH using a LocalEGA's pubic key$", (String fileSize) -> {
            try {
                int size = Integer.parseInt(fileSize);
                File rawFile = context.getRawFile();
                try (RandomAccessFile randomAccessFile = new RandomAccessFile(rawFile, "rw")) {
                    randomAccessFile.setLength(1024 * 1024 * size);
                }
                File encryptedFile = new File(rawFile.getAbsolutePath() + ".enc");
                byte[] digest = DigestUtils.sha256(FileUtils.openInputStream(rawFile));
                String key = FileUtils.readFileToString(new File(String.format("%s/%s/pgp/ega.pub", utils.getPrivateFolderPath(), utils.getProperty("instance.name"))), Charset.defaultCharset());
                FileOutputStream fileOutputStream = new FileOutputStream(encryptedFile);
                Crypt4GHOutputStream crypt4GHOutputStream = new Crypt4GHOutputStream(fileOutputStream, key, digest);
                context.setSessionKey(Hex.encodeHexString(crypt4GHOutputStream.getSessionKeyBytes()));
                context.setIv(Hex.encodeHexString(crypt4GHOutputStream.getIvBytes()));
                FileUtils.copyFile(rawFile, crypt4GHOutputStream);
                crypt4GHOutputStream.close();
                context.setEncryptedFile(encryptedFile);
            } catch (Exception e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Given("^I have a file encrypted not with Crypt4GH", () -> {
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
                log.error(e.getMessage(), e);
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

//        When("^I upload companion files to the LocalEGA inbox via SFTP$", () -> {
//            try {
//                HashingAlgorithm hashingAlgorithm = HashingAlgorithm.MD5;
//                context.setHashingAlgorithm(hashingAlgorithm);
//                String encFilePath = context.getEncryptedFile().getAbsolutePath();
//                File rawChecksumFile = new File(encFilePath.substring(0, encFilePath.lastIndexOf(".")) + "." + hashingAlgorithm.name().toLowerCase());
//                File encChecksumFile = new File(encFilePath + "." + hashingAlgorithm.name().toLowerCase());
//                String rawChecksum = utils.calculateChecksum(context.getRawFile(), hashingAlgorithm);
//                context.setRawChecksum(rawChecksum);
//                FileUtils.write(rawChecksumFile, rawChecksum, Charset.defaultCharset());
//                String encChecksum = utils.calculateChecksum(context.getEncryptedFile(), hashingAlgorithm);
//                context.setEncChecksum(encChecksum);
//                FileUtils.write(encChecksumFile, encChecksum, Charset.defaultCharset());
//                context.getSftp().put(rawChecksumFile.getAbsolutePath(), rawChecksumFile.getName());
//                context.getSftp().put(encChecksumFile.getAbsolutePath(), encChecksumFile.getName());
//            } catch (IOException e) {
//                log.error(e.getMessage(), e);
//            }
//        });

        Then("^the file is uploaded successfully$", () -> {
            try {
                Assert.assertTrue(context.getSftp().ls("/").stream().map(RemoteResourceInfo::getName).anyMatch(n -> context.getEncryptedFile().getName().equals(n)));
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });
    }

}
