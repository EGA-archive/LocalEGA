package se.nbis.lega.deployment.cega;

import de.gesellix.docker.client.DockerClientException;
import org.apache.commons.io.FileUtils;
import org.gradle.api.tasks.TaskAction;
import se.nbis.lega.deployment.Groups;
import se.nbis.lega.deployment.LocalEGATask;

import java.io.IOException;

public class ClearConfigurationTask extends LocalEGATask {

    public ClearConfigurationTask() {
        super();
        this.setGroup(Groups.CEGA.name());
    }

    @TaskAction
    public void run() throws IOException {
        for (Config config : Config.values()) {
            try {
                removeConfig(config.getName());
            } catch (DockerClientException ignored) {
            }
        }
        FileUtils.deleteDirectory(getProject().file(".tmp/"));
    }

}
