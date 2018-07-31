package se.nbis.lega.deployment.cluster;

import org.gradle.api.tasks.TaskAction;

import java.io.IOException;

public class LSTask extends ClusterTask {

    @TaskAction
    public void run() throws IOException {
        exec("docker-machine", "ls");
    }

}
