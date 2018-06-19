package se.nbis.lega.cucumber.steps;

import com.github.dockerjava.api.exception.ConflictException;
import com.github.dockerjava.api.exception.InternalServerErrorException;
import cucumber.api.java8.En;
import lombok.extern.slf4j.Slf4j;
import org.assertj.core.api.Assertions;
import org.junit.Assert;
import se.nbis.lega.cucumber.Context;
import se.nbis.lega.cucumber.Utils;

import java.io.IOException;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
public class Ingestion implements En {

    public Ingestion(Context context) {
        Utils utils = context.getUtils();

        Given("^I have CEGA MQ username and password$", () -> {
            try {
                context.setCegaMQUser(utils.readTraceProperty("CEGA_MQ_USER"));
                context.setCegaMQPassword(utils.readTraceProperty("CEGA_MQ_PASSWORD"));
                context.setCegaMQVHost(utils.getProperty("instance.name"));
                context.setRoutingKey(utils.getProperty("instance.name"));
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        When("^I turn off the keyserver$", () -> utils.stopContainer(utils.findContainer(utils.getProperty("images.name.keys"),
                utils.getProperty("container.name.keys"))));

        When("^I turn on the keyserver$", () -> utils.startContainer(utils.findContainer(utils.getProperty("images.name.keys"),
                utils.getProperty("container.name.keys"))));

        When("^I turn off the database", () -> utils.stopContainer(utils.findContainer(utils.getProperty("images.name.db"),
                utils.getProperty("container.name.db"))));

        When("^I turn on the database", () -> utils.startContainer(utils.findContainer(utils.getProperty("images.name.db"),
                utils.getProperty("container.name.db"))));

        When("^I turn off the vault listener", () -> utils.stopContainer(utils.findContainer(utils.getProperty("images.name.mq"),
                utils.getProperty("container.name.mq"))));

        When("^I turn on the vault listener", () -> utils.startContainer(utils.findContainer(utils.getProperty("images.name.mq"),
                utils.getProperty("container.name.mq"))));

        When("^I ingest file from the LocalEGA inbox$", () -> {
//            HashingAlgorithm hashingAlgorithm = HashingAlgorithm.valueOf(algorithm);
//            context.setHashingAlgorithm(hashingAlgorithm);
//            context.setRawChecksum(utils.calculateChecksum(context.getRawFile(), hashingAlgorithm));
//            context.setEncChecksum(utils.calculateChecksum(context.getEncryptedFile(), hashingAlgorithm));
            ingestFile(context);
        });

//        When("^I ingest file from the LocalEGA inbox using wrong raw checksum$", () -> {
//            try {
//                HashingAlgorithm hashingAlgorithm = HashingAlgorithm.MD5;
//                context.setHashingAlgorithm(hashingAlgorithm);
//                context.setRawChecksum("wrong");
//                context.setEncChecksum(utils.calculateChecksum(context.getEncryptedFile(), hashingAlgorithm));
//                ingestFile(context);
//            } catch (IOException e) {
//                log.error(e.getMessage(), e);
//                Assert.fail(e.getMessage());
//            }
//        });
//
//        When("^I ingest file from the LocalEGA inbox using wrong encrypted checksum$", () -> {
//            try {
//                HashingAlgorithm hashingAlgorithm = HashingAlgorithm.MD5;
//                context.setHashingAlgorithm(hashingAlgorithm);
//                context.setRawChecksum(utils.calculateChecksum(context.getRawFile(), hashingAlgorithm));
//                context.setEncChecksum("wrong");
//                ingestFile(context);
//            } catch (IOException e) {
//                log.error(e.getMessage(), e);
//                Assert.fail(e.getMessage());
//            }
//        });
//
//        When("^I ingest file from the LocalEGA inbox without providing raw checksum$", () -> {
//            try {
//                HashingAlgorithm hashingAlgorithm = HashingAlgorithm.MD5;
//                context.setHashingAlgorithm(hashingAlgorithm);
//                context.setRawChecksum(null);
//                context.setEncChecksum(utils.calculateChecksum(context.getEncryptedFile(), hashingAlgorithm));
//                ingestFile(context);
//            } catch (IOException e) {
//                log.error(e.getMessage(), e);
//                Assert.fail(e.getMessage());
//            }
//        });
//
//        When("^I ingest file from the LocalEGA inbox without providing encrypted checksum$", () -> {
//            try {
//                HashingAlgorithm hashingAlgorithm = HashingAlgorithm.MD5;
//                context.setHashingAlgorithm(hashingAlgorithm);
//                context.setRawChecksum(utils.calculateChecksum(context.getRawFile(), hashingAlgorithm));
//                context.setEncChecksum(null);
//                ingestFile(context);
//            } catch (IOException e) {
//                log.error(e.getMessage(), e);
//                Assert.fail(e.getMessage());
//            }
//        });

//        When("^I ingest file from the LocalEGA inbox without providing checksums$", () -> {
//            String rawChecksum = context.getRawChecksum();
//            String encChecksum = context.getEncChecksum();
//            context.setRawChecksum(null);
//            context.setEncChecksum(null);
//            ingestFile(context);
//            context.setRawChecksum(rawChecksum);
//            context.setEncChecksum(encChecksum);
//        });

        Then("^I retrieve ingestion information", () -> {
            try {
                String output = utils.executeDBQuery(String.format("select * from files where inbox_path = '%s'", context.getEncryptedFile().getName()));
                List<String> header = Arrays.stream(output.split(System.getProperty("line.separator"))[0].split(" \\| ")).map(String::trim).collect(Collectors.toList());
                List<String> fields = Arrays.stream(output.split(System.getProperty("line.separator"))[2].split(" \\| ")).map(String::trim).collect(Collectors.toList());
                HashMap<String, String> ingestionInformation = new HashMap<>();
                for (int i = 0; i < header.size(); i++) {
                    ingestionInformation.put(header.get(i), fields.get(i));
                }
                context.setIngestionInformation(ingestionInformation);
            } catch (IndexOutOfBoundsException e) {
                context.setIngestionInformation(Collections.singletonMap("status", "NoEntry"));
            } catch (InterruptedException | IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Then("^the ingestion status is \"([^\"]*)\"$", (String status) -> Assertions.assertThat(context.getIngestionInformation().get("status")).isEqualToIgnoringCase(status));

    }

    private void ingestFile(Context context) {
        try {
            Utils utils = context.getUtils();
            utils.publishCEGA(String.format("amqp://%s:%s@localhost:5672/%s",
                    context.getCegaMQUser(),
                    context.getCegaMQPassword(),
                    context.getCegaMQVHost()),
                    context.getUser(),
                    context.getEncryptedFile().getName());
            // It may take a while for relatively big files to be ingested.
            // So we wait until ingestion status changes to something different from "In progress".
            long maxTimeout = Long.parseLong(utils.getProperty("ingest.max-timeout"));
            long timeout = 0;
            String ingestionStatus = getIngestionStatus(context, utils);
            while ("In progress".equals(ingestionStatus) || "Archived".equals(ingestionStatus)) {
                Thread.sleep(1000);
                timeout += 1000;
                if (timeout > maxTimeout) {
                    break;
                }
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
            String output = utils.executeDBQuery(String.format("select status from files where inbox_path = '%s'", context.getEncryptedFile().getName()));
            return output.split(System.getProperty("line.separator"))[2].trim();
        } catch (InternalServerErrorException | ConflictException e) {
            return "Error";
        }
    }

}
