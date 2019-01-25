package se.nbis.lega.cucumber.steps;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import cucumber.api.java8.En;
import lombok.extern.slf4j.Slf4j;
import net.schmizz.sshj.SSHClient;
import net.schmizz.sshj.common.Buffer;
import net.schmizz.sshj.sftp.SFTPException;
import net.schmizz.sshj.transport.verification.PromiscuousVerifier;
import net.schmizz.sshj.userauth.UserAuthException;
import net.schmizz.sshj.userauth.keyprovider.KeyPairWrapper;
import org.apache.commons.io.FileUtils;
import org.junit.Assert;
import se.nbis.lega.cucumber.Context;
import se.nbis.lega.cucumber.Utils;
import se.nbis.lega.cucumber.pojo.User;

import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.util.Arrays;
import java.util.Base64;
import java.util.List;

@Slf4j
public class Authentication implements En {

    private ObjectMapper objectMapper = new ObjectMapper();

    {
        objectMapper.enable(SerializationFeature.INDENT_OUTPUT);
    }

    public Authentication(Context context) {
        Utils utils = context.getUtils();

        Given("^I have an account at Central EGA$", () -> {
            String cegaUsersFolderPath = utils.getCommonFolderPath();
            String username = context.getUser();
            try {
                generateKeypair(context);
                byte[] keyBytes = new Buffer.PlainBuffer().putPublicKey(context.getKeyProvider().getPublic()).getCompactData();
                String publicKey = Base64.getEncoder().encodeToString(keyBytes);
                User user = new User();
                user.setUsername(username);
                user.setUid(Math.abs(new SecureRandom().nextInt()));
                user.setSshPublicKey("ssh-rsa " + publicKey);
                File usersJSON = new File(cegaUsersFolderPath + "/users.json");
                List<String> lines = FileUtils.readLines(usersJSON, Charset.defaultCharset());
                lines = lines.subList(0, lines.size() - 1);
                lines.add("},");
                lines.add(objectMapper.writeValueAsString(user) + "]");
                FileUtils.writeLines(usersJSON, lines);
            } catch (IOException e) {
                throw new RuntimeException(e.getMessage(), e);
            }
        });

        Given("^I have correct private key$",
                () -> {
                    if (context.getKeyProvider() == null) {
                        generateKeypair(context);
                    }
                });

        Given("^I have incorrect private key$", () -> generateKeypair(context));

//        Given("^inbox is deleted for my user$", () -> {
//            try {
//                utils.removeUserInbox(context.getUser());
//            } catch (InterruptedException e) {
//                log.error(e.getMessage(), e);
//            }
//        });

        Given("^file is removed from the inbox$", () -> {
            try {
                utils.removeUploadedFileFromInbox(context.getUser(), context.getEncryptedFile().getName());
            } catch (InterruptedException e) {
                log.error(e.getMessage(), e);
            }
        });

        When("^I connect to the LocalEGA inbox via SFTP using private key$", () -> connect(context));

        When("^I disconnect from the LocalEGA inbox$", () -> disconnect(context));

        When("^I am disconnected from the LocalEGA inbox$", () -> Assert.assertFalse(isConnected(context)));

        Then("^I'm logged in successfully$", () -> Assert.assertFalse(context.isAuthenticationFailed()));

        Then("^authentication fails$", () -> Assert.assertTrue(context.isAuthenticationFailed()));

    }

    private void generateKeypair(Context context) {
        try {
            KeyPairGenerator keyPairGenerator = KeyPairGenerator.getInstance("RSA");
            keyPairGenerator.initialize(2048, new SecureRandom());
            KeyPair keyPair = keyPairGenerator.genKeyPair();
            context.setKeyProvider(new KeyPairWrapper(keyPair));
        } catch (NoSuchAlgorithmException e) {
            log.error(e.getMessage(), e);
        }
    }

    private void connect(Context context) {
        try {
            SSHClient ssh = new SSHClient();
            ssh.addHostKeyVerifier(new PromiscuousVerifier());
            ssh.connect("localhost", Integer.parseInt(context.getUtils().readTraceProperty("DOCKER_PORT_inbox")));
            ssh.authPublickey(context.getUser(), context.getKeyProvider());
            context.setSsh(ssh);
            context.setSftp(ssh.newSFTPClient());
            context.setAuthenticationFailed(false);
        } catch (UserAuthException | SFTPException e) {
            context.setAuthenticationFailed(true);
        } catch (IOException e) {
            throw new RuntimeException(e.getMessage(), e);
        }
    }

    private boolean isConnected(Context context) {
        return context.getSsh().isConnected();
    }

    private void disconnect(Context context) {
        try {
            context.getSftp().close();
            context.getSsh().disconnect();
        } catch (Exception e) {
            log.error(e.getMessage(), e);
        }
    }

}
