package se.nbis.lega.deployment;

import org.gradle.api.tasks.TaskAction;

import java.io.IOException;

public class RemoveStackTask extends LocalEGATask {

    private String stackName;

    @TaskAction
    public void run() throws IOException {
        exec("docker stack rm", stackName);
    }

    public void setStackName(String stackName) {
        this.stackName = stackName;
    }

}
