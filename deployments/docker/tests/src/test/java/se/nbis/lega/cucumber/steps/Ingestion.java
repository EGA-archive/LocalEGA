package se.nbis.lega.cucumber.steps;

import com.github.dockerjava.api.exception.InternalServerErrorException;
import cucumber.api.java8.En;
import lombok.extern.slf4j.Slf4j;
import org.assertj.core.api.Assertions;
import org.c02e.jpgpj.HashingAlgorithm;
import org.junit.Assert;
import se.nbis.lega.cucumber.Context;
import se.nbis.lega.cucumber.Utils;

import java.io.IOException;
import java.util.*;
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

        When("^I turn off the keyserver$", () -> utils.stopContainer(utils.findContainer(utils.getProperty("images.name.keys"),
                utils.getProperty("container.prefix.keys") + context.getTargetInstance())));

        When("^I turn on the keyserver$", () -> utils.startContainer(utils.findContainer(utils.getProperty("images.name.keys"),
                utils.getProperty("container.prefix.keys") + context.getTargetInstance())));

        When("^I turn off the database", () -> utils.stopContainer(utils.findContainer(utils.getProperty("images.name.db"),
                utils.getProperty("container.prefix.db") + context.getTargetInstance())));

        When("^I turn on the database", () -> utils.startContainer(utils.findContainer(utils.getProperty("images.name.db"),
                utils.getProperty("container.prefix.db") + context.getTargetInstance())));

        When("^I ingest file from the LocalEGA inbox using correct ([^\"]*) checksums$", (String algorithm) -> {
            try {
                HashingAlgorithm hashingAlgorithm = HashingAlgorithm.valueOf(algorithm);
                context.setHashingAlgorithm(hashingAlgorithm);
                context.setRawChecksum(utils.calculateChecksum(context.getRawFile(), hashingAlgorithm));
                context.setEncChecksum(utils.calculateChecksum(context.getEncryptedFile(), hashingAlgorithm));
                ingestFile(context);
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        When("^I ingest file from the LocalEGA inbox using wrong raw checksum$", () -> {
            try {
                HashingAlgorithm hashingAlgorithm = HashingAlgorithm.MD5;
                context.setHashingAlgorithm(hashingAlgorithm);
                context.setRawChecksum("wrong");
                context.setEncChecksum(utils.calculateChecksum(context.getEncryptedFile(), hashingAlgorithm));
                ingestFile(context);
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        When("^I ingest file from the LocalEGA inbox using wrong encrypted checksum$", () -> {
            try {
                HashingAlgorithm hashingAlgorithm = HashingAlgorithm.MD5;
                context.setHashingAlgorithm(hashingAlgorithm);
                context.setRawChecksum(utils.calculateChecksum(context.getRawFile(), hashingAlgorithm));
                context.setEncChecksum("wrong");
                ingestFile(context);
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        When("^I ingest file from the LocalEGA inbox without providing raw checksum$", () -> {
            try {
                HashingAlgorithm hashingAlgorithm = HashingAlgorithm.MD5;
                context.setHashingAlgorithm(hashingAlgorithm);
                context.setRawChecksum(null);
                context.setEncChecksum(utils.calculateChecksum(context.getEncryptedFile(), hashingAlgorithm));
                ingestFile(context);
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        When("^I ingest file from the LocalEGA inbox without providing encrypted checksum$", () -> {
            try {
                HashingAlgorithm hashingAlgorithm = HashingAlgorithm.MD5;
                context.setHashingAlgorithm(hashingAlgorithm);
                context.setRawChecksum(utils.calculateChecksum(context.getRawFile(), hashingAlgorithm));
                context.setEncChecksum(null);
                ingestFile(context);
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
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
            } catch (Exception e) {
                log.error(e.getMessage(), e);
                context.setIngestionInformation(Collections.singletonMap("status", "Error"));
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
                    context.getHashingAlgorithm().name(),
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
        try {
            String output = utils.executeDBQuery(context.getTargetInstance(),
                    String.format("select status from files where filename = '%s'", context.getEncryptedFile().getName()));
            return output.split(System.getProperty("line.separator"))[2].trim();
        } catch (InternalServerErrorException e) {
            return "Error";
        }
    }

}
