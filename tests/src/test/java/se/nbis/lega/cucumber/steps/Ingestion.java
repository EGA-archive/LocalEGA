package se.nbis.lega.cucumber.steps;

import cucumber.api.java8.En;
import lombok.extern.slf4j.Slf4j;
import org.assertj.core.api.Assertions;
import org.junit.Assert;
import se.nbis.lega.cucumber.Context;
import se.nbis.lega.cucumber.Utils;

import java.io.File;
import java.io.IOException;

@Slf4j
public class Ingestion implements En {

    public Ingestion(Context context) {
        Utils utils = context.getUtils();

        Given("^I have CEGA MQ username and password$", () -> {
            try {
                context.setCegaMQUser(utils.readTraceProperty(context.getTargetInstance(), "CEGA_MQ_USER"));
                context.setCegaMQPassword(utils.readTraceProperty(context.getTargetInstance(), "CEGA_MQ_PASSWORD"));
                context.setCegaMQVHost(context.getTargetInstance());
                context.setRoutingKey(context.getTargetInstance());
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        When("^I ingest file from the LocalEGA inbox using correct encrypted checksum$", () -> {
            try {
                File encryptedFile = context.getEncryptedFile();
                String rawChecksum = utils.calculateMD5(context.getRawFile());
                String encryptedChecksum = utils.calculateMD5(encryptedFile);
                ingestFile(context, utils, encryptedFile.getName(), rawChecksum, encryptedChecksum);
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        When("^I ingest file from the LocalEGA inbox using wrong encrypted checksum$", () -> {
            try {
                ingestFile(context,
                        utils,
                        context.getEncryptedFile().getName(),
                        utils.calculateMD5(context.getRawFile()), "wrong");
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Then("^the file is ingested successfully$", () -> {
            try {
                String output = utils.executeDBQuery(context.getTargetInstance(),
                        String.format("select stable_id from files where filename = '%s'", context.getEncryptedFile().getName()));
                String vaultFileName = output.split(System.getProperty("line.separator"))[2].trim();
                String cat = utils.executeWithinContainer(utils.findContainer(utils.getProperty("images.name.vault"),
                        utils.getProperty("container.prefix.vault") + context.getTargetInstance()), "cat", vaultFileName);
                Assertions.assertThat(cat).startsWith("bytearray(b'1')|256|8|b'CTR'");
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Then("^ingestion failed$", () -> {
            try {
                String output = utils.executeDBQuery(context.getTargetInstance(),
                        String.format("select stable_id from files where filename = '%s'", context.getEncryptedFile().getName()));
                String vaultFileName = output.split(System.getProperty("line.separator"))[2].trim();
                Assertions.assertThat(vaultFileName).isEmpty();
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });
    }

    private void ingestFile(Context context, Utils utils, String encryptedFileName, String rawChecksum, String encryptedChecksum) {
        try {
            utils.executeWithinContainer(utils.findContainer(utils.getProperty("images.name.cega_mq"), utils.getProperty("container.prefix.cega_mq")),
                    String.format("publish --connection amqp://%s:%s@localhost:5672/%s %s %s %s --unenc %s --enc %s",
                            context.getCegaMQUser(),
                            context.getCegaMQPassword(),
                            context.getCegaMQVHost(),
                            context.getRoutingKey(),
                            context.getUser(),
                            encryptedFileName,
                            rawChecksum,
                            encryptedChecksum).split(" "));
            Thread.sleep(1000);
        } catch (InterruptedException e) {
            log.error(e.getMessage(), e);
            Assert.fail(e.getMessage());
        }
    }

}
