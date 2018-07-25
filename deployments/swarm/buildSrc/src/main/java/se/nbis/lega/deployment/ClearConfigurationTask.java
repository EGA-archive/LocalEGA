package se.nbis.lega.deployment;

import lombok.Data;
import org.apache.commons.io.FileUtils;
import org.gradle.api.tasks.TaskAction;

import java.io.IOException;
import java.util.Set;

@Data
public class ClearConfigurationTask extends LocalEGATask {

    private Set<String> configs;

    @TaskAction
    public void run() throws IOException {
        for (String config : configs) {
            removeConfig(config);
        }
        FileUtils.deleteDirectory(getProject().file(".tmp/"));
    }

}
