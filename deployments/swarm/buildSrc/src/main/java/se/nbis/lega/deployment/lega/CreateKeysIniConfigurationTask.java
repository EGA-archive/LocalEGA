package se.nbis.lega.deployment.lega;

import org.apache.commons.io.FileUtils;
import org.gradle.api.tasks.TaskAction;
import se.nbis.lega.deployment.Groups;
import se.nbis.lega.deployment.LocalEGATask;

import javax.crypto.*;
import javax.crypto.spec.PBEKeySpec;
import javax.crypto.spec.PBEParameterSpec;
import java.io.File;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.Charset;
import java.security.InvalidAlgorithmParameterException;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.security.spec.InvalidKeySpecException;
import java.util.UUID;

public class CreateKeysIniConfigurationTask extends LocalEGATask {

    public CreateKeysIniConfigurationTask() {
        super();
        this.setGroup(Groups.LEGA.name());
        this.dependsOn("clearConfiguration",
                "createMQConfiguration",
                "createDBConfiguration",
                "createInboxConfiguration",
                "createIngestConfiguration",
                "createKeysConfiguration",
                "createMinioConfiguration");
    }

    @TaskAction
    public void run() throws IOException, NoSuchPaddingException, InvalidKeyException, NoSuchAlgorithmException, IllegalBlockSizeException, BadPaddingException, InvalidAlgorithmParameterException, InvalidKeySpecException {
        generateKeysIni();
        String keysPassphrase = UUID.randomUUID().toString().replace("-", "");
        writeTrace("KEYS_PASSWORD", keysPassphrase);

        encryptAES(getProject().file(".tmp/keys.ini"), getProject().file(".tmp/keys.ini.enc"), keysPassphrase);

        createConfig(Config.KEYS_INI_ENC.getName(), getProject().file(".tmp/keys.ini.enc"));
    }

    private void generateKeysIni() throws IOException {
        String pgpPassphrase = readTrace("PGP_PASSPHRASE");
        File keysIni = getProject().file(".tmp/keys.ini");
        FileUtils.write(keysIni, String.format("[DEFAULT]\n" +
                        "active : key.1\n" +
                        "\n" +
                        "[key.1]\n" +
                        "path : /etc/ega/pgp/ega.sec\n" +
                        "passphrase : %s\n" +
                        "expire: 30/MAR/19 08:00:00\n" +
                        "\n" +
                        "[key.2]\n" +
                        "path : /etc/ega/pgp/ega2.sec\n" +
                        "passphrase : %s\n" +
                        "expire: 30/MAR/18 08:00:00", pgpPassphrase, pgpPassphrase),
                Charset.defaultCharset());
    }

    private void encryptAES(File fileIn, File fileOut, String passphrase) throws NoSuchAlgorithmException, InvalidKeySpecException, NoSuchPaddingException, InvalidAlgorithmParameterException, InvalidKeyException, IOException, BadPaddingException, IllegalBlockSizeException {
        byte[] magicNumber = "Salted__".getBytes();
        String algorithm = "PBEWITHMD5AND256BITAES-CBC-OPENSSL";
        PBEKeySpec keySpec = new PBEKeySpec(passphrase.toCharArray());
        SecretKeyFactory factory = SecretKeyFactory.getInstance(algorithm);
        SecretKey key = factory.generateSecret(keySpec);

        Cipher cipher = Cipher.getInstance(algorithm);
        byte[] salt = new SecureRandom().generateSeed(8);
        cipher.init(Cipher.ENCRYPT_MODE, key, new PBEParameterSpec(salt, 1));

        byte[] encryptedContent = cipher.doFinal(FileUtils.readFileToByteArray(fileIn));

        ByteBuffer buffer = ByteBuffer.allocate(magicNumber.length + salt.length + encryptedContent.length);
        buffer.put(magicNumber);
        buffer.put(salt);
        buffer.put(encryptedContent);

        FileUtils.writeByteArrayToFile(fileOut, buffer.array());
    }

}
