package se.nbis.lega.deployment.test;

import no.ifi.uio.crypt4gh.stream.Crypt4GHOutputStream;
import org.apache.commons.codec.digest.DigestUtils;
import org.apache.commons.io.FileUtils;
import org.bouncycastle.openpgp.PGPException;
import org.gradle.api.tasks.TaskAction;
import se.nbis.lega.deployment.Groups;
import se.nbis.lega.deployment.LocalEGATask;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.Charset;
import java.security.NoSuchAlgorithmException;

public class EncryptFileTask extends LocalEGATask {

    public EncryptFileTask() {
        super();
        this.setGroup(Groups.TEST.name());
        this.dependsOn("file");
    }

    @TaskAction
    public void run() throws IOException, PGPException, NoSuchAlgorithmException {
        File rawFile = getProject().file(".tmp/data.raw");
        File encryptedFile = getProject().file(".tmp/data.raw.enc");
        byte[] digest = DigestUtils.sha256(FileUtils.openInputStream(rawFile));
        String key = FileUtils.readFileToString(new File("lega/.tmp/pgp/ega.pub"), Charset.defaultCharset());
        FileOutputStream fileOutputStream = new FileOutputStream(encryptedFile);
        Crypt4GHOutputStream crypt4GHOutputStream = new Crypt4GHOutputStream(fileOutputStream, key, digest);
        FileUtils.copyFile(rawFile, crypt4GHOutputStream);
        crypt4GHOutputStream.close();
    }

}
