package se.nbis.lega.cucumber.hooks;

import com.github.dockerjava.api.exception.NotModifiedException;
import com.github.dockerjava.api.model.Container;
import cucumber.api.java.After;
import cucumber.api.java.Before;
import cucumber.api.java8.En;
import org.apache.commons.io.FileUtils;
import se.nbis.lega.cucumber.Context;
import se.nbis.lega.cucumber.Utils;

import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;
import java.util.Arrays;

public class BeforeAfterHooks implements En {

    private Context context;

    public BeforeAfterHooks(Context context) {
        this.context = context;
    }

    @Before
    public void setUp() throws IOException {
        File dataFolder = new File("data");
        dataFolder.mkdir();
        File rawFile = File.createTempFile("data", ".raw", dataFolder);
        FileUtils.writeStringToFile(rawFile, "hello", Charset.defaultCharset());
        context.setDataFolder(dataFolder);
        context.setRawFile(rawFile);
    }

    @After
    public void tearDown() throws IOException, InterruptedException {
        Utils utils = context.getUtils();

        try { // bring DB back in case it's gone down
            Container dbContainer = utils.findContainer("nbisweden/ega-db", "ega_db_" + context.getTargetInstance());
            utils.getDockerClient().startContainerCmd(dbContainer.getId()).exec();
        } catch (NotModifiedException e) {
        }

        FileUtils.deleteDirectory(context.getDataFolder());
        String targetInstance = context.getTargetInstance();
        File cegaUsersFolder = new File(utils.getPrivateFolderPath() + "/cega/users/" + targetInstance);
        String user = context.getUser();
        Arrays.stream(cegaUsersFolder.listFiles((dir, name) -> name.startsWith(user))).forEach(File::delete);
        utils.removeUserFromDB(targetInstance, user);
        utils.removeUserFromInbox(targetInstance, user);
    }

}
