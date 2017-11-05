package se.nbis.lega.cucumber.hooks;

import cucumber.api.java.After;
import cucumber.api.java.Before;
import cucumber.api.java8.En;
import org.apache.commons.io.FileUtils;
import se.nbis.lega.cucumber.Context;
import se.nbis.lega.cucumber.Utils;

import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Paths;
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
        FileUtils.deleteDirectory(context.getDataFolder());
        String cegaUsersFolderPath = Paths.get("").toAbsolutePath().getParent().toString() + "/docker/bootstrap/private/cega/users";
        File cegaUsersFolder = new File(cegaUsersFolderPath);
        Utils utils = context.getUtils();
        String user = context.getUser();
        Arrays.stream(cegaUsersFolder.listFiles((dir, name) -> name.startsWith(user))).forEach(File::delete);
        utils.executeDBQuery(String.format("delete from users where elixir_id = '%s'", user));
        utils.executeWithinContainer(utils.findContainer("nbis/ega:inbox", "ega_inbox"), String.format("rm -rf /ega/inbox/%s", user).split(" "));
    }

}
