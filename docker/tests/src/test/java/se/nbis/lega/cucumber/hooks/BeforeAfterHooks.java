package se.nbis.lega.cucumber.hooks;

import com.github.dockerjava.api.model.Container;
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
import java.util.Collection;
import java.util.UUID;
import java.util.concurrent.TimeoutException;

@Slf4j
public class BeforeAfterHooks implements En {

    private Context context;

    public BeforeAfterHooks(Context context) {
        this.context = context;
    }

    @SuppressWarnings("ResultOfMethodCallIgnored")
    @Before
    public void setUp() throws IOException, TimeoutException, InterruptedException {
        waitForInitializationToComplete(context.getUtils());
        File dataFolder = new File("data");
        dataFolder.mkdir();
        File rawFile = File.createTempFile("data", ".raw", dataFolder);
        FileUtils.writeStringToFile(rawFile, "hello", Charset.defaultCharset());
        context.setDataFolder(dataFolder);
        context.setRawFile(rawFile);
        context.setUser(UUID.randomUUID().toString());
    }

    public void waitForInitializationToComplete(Utils utils) throws InterruptedException, TimeoutException {
        Collection<Container> containers = utils.getAllLocalEGAContainers();
        long maxTimeout = Long.parseLong(utils.getProperty("initialization.max-timeout"));
        long timeout = 0;
        while (containers.isEmpty() || !containers.stream().map(Container::getStatus).allMatch(s -> s.startsWith("Up"))) {
            if (containers.isEmpty()) {
                containers = utils.getAllLocalEGAContainers();
            }
            Thread.sleep(1000);
            timeout += 1000;
            if (timeout > maxTimeout) {
                throw new TimeoutException(String.format("The system was not initialized in time: initialization.max-timeout = %s", maxTimeout));
            }
        }
        // Sleep a bit more to let containers not only start up, but finish initialization.
        Thread.sleep(Long.parseLong(utils.getProperty("initialization.delay")));
    }

    @SuppressWarnings({"ConstantConditions", "ResultOfMethodCallIgnored"})
    @After
    public void tearDown() throws IOException {
        Utils utils = context.getUtils();

        FileUtils.deleteDirectory(context.getDataFolder());
        File cegaUsersFolder = new File(utils.getPrivateFolderPath() + "/cega/users/" + utils.getProperty("instance.name"));
        String user = context.getUser();
        Arrays.stream(cegaUsersFolder.listFiles((dir, name) -> name.startsWith(user))).forEach(File::delete);
//        utils.removeUserInbox(user);
    }

}
