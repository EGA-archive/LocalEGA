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
        FileUtils.writeStringToFile(rawFile, "I am Duncan Macleod, born 400 years ago in the Highlands of Scotland. I am Immortal, and I am not alone. For centuries, we have waited for the time of the Gathering when the stroke of a sword and the fall of a head will release the power of the Quickening. In the end, there can be only one.\n" +
                "In an age when nature and magic rule the world, there is an extraordinary legend: the story of a warrior who communicates with animals, who fights sorcery and the unnatural. His name is Dar, last of his tribe. He is also called Beastmaster.\n" +
                "Sometimes the world looks perfect, nothing to rearrange. Sometimes you just, get a feeling like you need some kind of change. No matter what the odds are this time, nothing's going to stand in my way. This flame in my heart, and a long lost friend gives every dark street a light at the end. Standing tall, on the wings of my dream. Rise and fall, on the wings of my dream. The rain and thunder, the wind and haze. I'm bound for better days. It's my life and my dream, nothing's going to stop me now.", Charset.defaultCharset());
        context.setDataFolder(dataFolder);
        context.setRawFile(rawFile);
    }

//    @SuppressWarnings({"ConstantConditions", "ResultOfMethodCallIgnored"})
//    @After
//    public void tearDown() throws IOException, InterruptedException {
//        Utils utils = context.getUtils();
//        String targetInstance = context.getTargetInstance();
//
//        FileUtils.deleteDirectory(context.getDataFolder());
//        File cegaUsersFolder = new File(utils.getPrivateFolderPath() + "/cega/users/" + targetInstance);
//        String user = context.getUser();
//        Arrays.stream(cegaUsersFolder.listFiles((dir, name) -> name.startsWith(user))).forEach(File::delete);
//        utils.removeUserFromCache(targetInstance, user);
//        utils.removeUserInbox(targetInstance, user);
//    }

}
