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
                context.setCegaMQUser("cega_swe1");
                context.setCegaMQPassword(utils.readTraceProperty(".trace.cega", "CEGA_MQ_swe1_PASSWORD"));
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        When("^I ingest file from the LocalEGA inbox$", () -> {
            try {
                File encryptedFile = context.getEncryptedFile();
                utils.executeWithinContainer(utils.findContainer("nbisweden/ega-cega_mq", "/cega_mq"),
                        String.format("publish --connection amqp://%s:%s@localhost:5672/%s %s %s %s --unenc %s --enc %s",
                                context.getCegaMQUser(),
                                context.getCegaMQPassword(),
                                "swe1",
                                "swe1",
                                context.getUser(),
                                encryptedFile.getName(),
                                utils.calculateMD5(context.getRawFile()),
                                utils.calculateMD5(encryptedFile)).split(" "));
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Then("^the file is ingested successfully$", () -> {
            try {
                Thread.sleep(1000);
                String query = String.format("select stable_id from files where filename = '%s'", context.getEncryptedFile().getName());
                String output = utils.executeWithinContainer(utils.findContainer("nbisweden/ega-db", "/ega_db_swe1"),
                        "psql", "-U", utils.readTraceProperty(".trace.swe1", "DB_USER"), "-d", "lega", "-c", query);
                String vaultFileName = output.split(System.getProperty("line.separator"))[2];
                String cat = utils.executeWithinContainer(utils.findContainer("nbisweden/ega-common", "/ega_vault_swe1"), "cat", vaultFileName.trim());
                Assertions.assertThat(cat).startsWith("bytearray(b'1')|256|8|b'CTR'");
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });
    }

}