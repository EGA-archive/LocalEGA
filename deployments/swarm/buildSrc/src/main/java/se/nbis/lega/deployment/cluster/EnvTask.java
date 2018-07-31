package se.nbis.lega.deployment.cluster;

import org.gradle.api.tasks.TaskAction;

import java.io.IOException;

public class EnvTask extends ClusterTask {

    @TaskAction
    public void run() throws IOException {
        exec("docker-machine", "env", MANAGER_NAME);
    }

}
