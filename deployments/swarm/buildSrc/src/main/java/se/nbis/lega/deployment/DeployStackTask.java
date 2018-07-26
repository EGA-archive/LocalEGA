package se.nbis.lega.deployment;

import org.gradle.api.tasks.TaskAction;

import java.io.IOException;
import java.util.Map;

public class DeployStackTask extends LocalEGATask {

    private String composeFile;
    private String stackName;
    private Map<String, String> environment;

    @TaskAction
    public void run() throws IOException {
        exec(environment, "docker stack deploy", "--compose-file", composeFile, stackName);
    }

    public void setComposeFile(String composeFile) {
        this.composeFile = composeFile;
    }

    public void setStackName(String stackName) {
        this.stackName = stackName;
    }

    public void setEnvironment(Map<String, String> environment) {
        this.environment = environment;
    }

}
