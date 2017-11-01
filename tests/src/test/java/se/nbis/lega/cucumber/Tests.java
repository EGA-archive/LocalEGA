package se.nbis.lega.cucumber;

import cucumber.api.CucumberOptions;
import cucumber.api.junit.Cucumber;
import org.apache.commons.io.FileUtils;
import org.junit.AfterClass;
import org.junit.runner.RunWith;

import java.io.File;
import java.io.IOException;

@RunWith(Cucumber.class)
@CucumberOptions(
        format = {"pretty", "html:target/cucumber"},
        features = "src/test/resources/cucumber/features"
)
public class Tests {

    public static final String DATA_FOLDER_PATH = "data";

    @AfterClass
    public static void teardown() throws IOException {
        FileUtils.deleteDirectory(new File(DATA_FOLDER_PATH));
    }

}
