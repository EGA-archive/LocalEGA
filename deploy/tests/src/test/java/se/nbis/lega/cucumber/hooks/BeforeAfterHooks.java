package se.nbis.lega.cucumber.hooks;

import cucumber.api.java.After;
import cucumber.api.java.Before;
import cucumber.api.java8.En;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.io.FileUtils;
import se.nbis.lega.cucumber.Context;
import se.nbis.lega.cucumber.Utils;

import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;
import java.util.Arrays;
import java.util.UUID;

@Slf4j
public class BeforeAfterHooks implements En {

    private Context context;

    public BeforeAfterHooks(Context context) {
        this.context = context;
    }

    @SuppressWarnings("ResultOfMethodCallIgnored")
    @Before
    public void setUp() throws IOException {
        File dataFolder = new File("data");
        dataFolder.mkdir();
        File rawFile = File.createTempFile("data", ".raw", dataFolder);
        context.setDataFolder(dataFolder);
        context.setRawFile(rawFile);
        context.setUser(UUID.randomUUID().toString());
    }

    @After
    public void tearDown() throws IOException {
        FileUtils.deleteDirectory(context.getDataFolder());
    }

}
