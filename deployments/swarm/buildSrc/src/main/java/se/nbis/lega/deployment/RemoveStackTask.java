package se.nbis.lega.deployment;

import lombok.Data;
import org.gradle.api.tasks.TaskAction;

import java.io.IOException;

@Data
public class RemoveStackTask extends LocalEGATask {

    private String stackName;

    @TaskAction
    public void run() throws IOException {
        exec("docker stack rm", stackName);
    }

}
