package se.nbis.lega.cucumber.steps;

import cucumber.api.java8.En;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.io.FileUtils;
import org.c02e.jpgpj.HashingAlgorithm;
import org.junit.Assert;
import se.nbis.lega.cucumber.Context;
import se.nbis.lega.cucumber.Utils;

import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.util.Map;

@Slf4j
public class Outgetsion implements En {

    public Outgetsion(Context context) {
        Utils utils = context.getUtils();

        When("^I download archived file$", () -> {
            try {
                Map<String, String> ingestionInformation = context.getIngestionInformation();
                String filePath = ingestionInformation.get("vault_path");
                URL resURL = new URL(String.format("http://localhost:8081/file?sourceKey=%s&sourceIV=%s&filePath=%s",
                        context.getSessionKey(),
                        context.getIv(),
                        filePath));
                File downloadedFile = new File(context.getRawFile().getAbsolutePath() + ".out");
                context.setDownloadedFile(downloadedFile);
                FileUtils.copyURLToFile(resURL, downloadedFile);
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Then("^checksums of raw and downloaded files match$", () -> {
            try {
                String rawChecksum = utils.calculateChecksum(context.getRawFile(), HashingAlgorithm.SHA256);
                String downloadedChecksum = utils.calculateChecksum(context.getDownloadedFile(), HashingAlgorithm.SHA256);
                Assert.assertEquals(rawChecksum, downloadedChecksum);
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });
    }

}
