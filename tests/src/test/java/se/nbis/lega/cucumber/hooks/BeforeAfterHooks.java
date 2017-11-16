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
        FileUtils.writeStringToFile(rawFile, "hello", Charset.defaultCharset());
        context.setDataFolder(dataFolder);
        context.setRawFile(rawFile);
    }

    @SuppressWarnings({"ConstantConditions", "ResultOfMethodCallIgnored"})
    @After
    public void tearDown() throws IOException, InterruptedException {
        Utils utils = context.getUtils();
        String targetInstance = context.getTargetInstance();

        // fix database connectivity
        utils.executeWithinContainer(utils.findContainer("nbisweden/ega-inbox", "ega_inbox_" + context.getTargetInstance()),
                "sed -i s/dbname=wrong/dbname=lega/g /etc/ega/auth.conf".split(" "));

        FileUtils.deleteDirectory(context.getDataFolder());
        File cegaUsersFolder = new File(utils.getPrivateFolderPath() + "/cega/users/" + targetInstance);
        String user = context.getUser();
        Arrays.stream(cegaUsersFolder.listFiles((dir, name) -> name.startsWith(user))).forEach(File::delete);
        utils.removeUserFromDB(targetInstance, user);
        utils.removeUserFromInbox(targetInstance, user);
    }

}
