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

        Given("^I have CEGA username and password$", () -> {
            try {
                context.setCegaMQUser(utils.readTraceProperty("CEGA_MQ_USER"));
                context.setCegaMQPassword(utils.readTraceProperty("CEGA_MQ_PASSWORD"));
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        When("^I ingest file from the LocalEGA inbox$", () -> {
            try {
                File encryptedFile = context.getEncryptedFile();
                utils.executeWithinContainer(utils.findContainer("nbis/ega:cega_mq", "cega_mq"),
                        String.format("publish --connection amqp://%s:%s@localhost:5672/%s %s %s --unenc %s --enc %s",
                                context.getCegaMQUser(),
                                context.getCegaMQPassword(),
                                utils.readTraceProperty("CEGA_MQ_VHOST"),
                                context.getUser(),
                                encryptedFile.getName(),
                                utils.calculateMD5(context.getRawFile()),
                                utils.calculateMD5(encryptedFile)).split(" "));
                Thread.sleep(1000);
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Then("^the file is ingested successfully$", () -> {
            try {
                String output = utils.executeDBQuery(String.format("select stable_id from files where filename = '%s'", context.getEncryptedFile().getName()));
                String vaultFileName = output.split(System.getProperty("line.separator"))[2];
                String cat = utils.executeWithinContainer(utils.findContainer("nbis/ega:common", "ega_vault"), "cat", vaultFileName.trim());
                Assertions.assertThat(cat).startsWith("bytearray(b'1')|256|8|b'CTR'");
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });
    }

}