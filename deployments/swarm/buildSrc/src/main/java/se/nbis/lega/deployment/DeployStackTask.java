package se.nbis.lega.deployment;

import lombok.Data;
import org.gradle.api.tasks.TaskAction;

import java.io.IOException;
import java.util.Map;

@Data
public class DeployStackTask extends LocalEGATask {

    private String composeFile;
    private String stackName;
    private Map<String, String> environment;

    @TaskAction
    public void run() throws IOException {
        exec(environment, "docker stack deploy", "--compose-file", composeFile, stackName);
    }

}
