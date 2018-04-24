package se.nbis.lega.cucumber.steps;

import cucumber.api.java8.En;
import lombok.extern.slf4j.Slf4j;
import org.assertj.core.api.Assertions;
import org.junit.Assert;
import se.nbis.lega.cucumber.Context;
import se.nbis.lega.cucumber.Utils;

import java.io.IOException;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

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

        When("^I ingest file from the LocalEGA inbox using correct encrypted checksum$", () -> ingestFile(context));

        When("^I ingest file from the LocalEGA inbox using wrong raw checksum$", () -> {
            String rawChecksum = context.getRawChecksum();
            context.setRawChecksum("wrong");
            ingestFile(context);
            context.setRawChecksum(rawChecksum);
        });

        When("^I ingest file from the LocalEGA inbox using wrong encrypted checksum$", () -> {
            String encChecksum = context.getEncChecksum();
            context.setEncChecksum("wrong");
            ingestFile(context);
            context.setEncChecksum(encChecksum);
        });

        When("^I ingest file from the LocalEGA inbox without providing raw checksum$", () -> {
            String rawChecksum = context.getRawChecksum();
            context.setRawChecksum(null);
            ingestFile(context);
            context.setRawChecksum(rawChecksum);
        });

        When("^I ingest file from the LocalEGA inbox without providing encrypted checksum$", () -> {
            String encChecksum = context.getEncChecksum();
            context.setEncChecksum(null);
            ingestFile(context);
            context.setEncChecksum(encChecksum);
        });

        When("^I ingest file from the LocalEGA inbox without providing checksums$", () -> {
            String rawChecksum = context.getRawChecksum();
            String encChecksum = context.getEncChecksum();
            context.setRawChecksum(null);
            context.setEncChecksum(null);
            ingestFile(context);
            context.setRawChecksum(rawChecksum);
            context.setEncChecksum(encChecksum);
        });

        Then("^I retrieve ingestion information", () -> {
            try {
                String output = utils.executeDBQuery(context.getTargetInstance(),
                        String.format("select * from files where filename = '%s'", context.getEncryptedFile().getName()));
                List<String> header = Arrays.stream(output.split(System.getProperty("line.separator"))[0].split(" \\| ")).map(String::trim).collect(Collectors.toList());
                List<String> fields = Arrays.stream(output.split(System.getProperty("line.separator"))[2].split(" \\| ")).map(String::trim).collect(Collectors.toList());
                HashMap<String, String> ingestionInformation = new HashMap<>();
                for (int i = 0; i < header.size(); i++) {
                    ingestionInformation.put(header.get(i), fields.get(i));
                }
                context.setIngestionInformation(ingestionInformation);
            } catch (IOException | InterruptedException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Then("^the ingestion status is \"([^\"]*)\"$", (String status) -> Assertions.assertThat(context.getIngestionInformation().get("status")).isEqualToIgnoringCase(status));

        Then("^the raw checksum matches$", () -> Assertions.assertThat(context.getIngestionInformation().get("org_checksum")).isEqualToIgnoringCase(context.getRawChecksum()));

        Then("^the encrypted checksum matches$", () -> Assertions.assertThat(context.getIngestionInformation().get("enc_checksum")).isEqualToIgnoringCase(context.getEncChecksum()));

        Then("^and the file header matches$", () -> {
            try {
                Map<String, String> ingestionInformation = context.getIngestionInformation();
                String cat = utils.executeWithinContainer(utils.findContainer(utils.getProperty("images.name.vault"),
                        utils.getProperty("container.prefix.vault") + context.getTargetInstance()), "cat", ingestionInformation.get("filepath"));
                Assertions.assertThat(cat).startsWith(ingestionInformation.get("reenc_info"));
            } catch (InterruptedException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

    }

    private void ingestFile(Context context) {
        try {
            Utils utils = context.getUtils();
            utils.publishCEGA(String.format("amqp://%s:%s@localhost:5672/%s",
                    context.getCegaMQUser(),
                    context.getCegaMQPassword(),
                    context.getCegaMQVHost()),
                    context.getUser(),
                    context.getEncryptedFile().getName(),
                    context.getRawChecksum(),
                    context.getEncChecksum());
            // It may take a while for relatively big files to be ingested.
            // So we wait until ingestion status changes to something different from "In progress".
            while ("In progress".equals(getIngestionStatus(context, utils))) {
                Thread.sleep(1000);
            }
            // And we sleep one more second for entry to be updated in the database.
            Thread.sleep(1000);
        } catch (Exception e) {
            log.error(e.getMessage(), e);
            Assert.fail(e.getMessage());
        }
    }

    private String getIngestionStatus(Context context, Utils utils) throws IOException, InterruptedException {
        String output = utils.executeDBQuery(context.getTargetInstance(),
                String.format("select status from files where filename = '%s'", context.getEncryptedFile().getName()));
        return output.split(System.getProperty("line.separator"))[2].trim();
    }

}
