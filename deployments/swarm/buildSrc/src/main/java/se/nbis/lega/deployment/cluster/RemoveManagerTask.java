package se.nbis.lega.deployment.cluster;

import org.gradle.api.tasks.TaskAction;

import java.io.IOException;

public class RemoveManagerTask extends ClusterTask {

    @TaskAction
    public void run() throws IOException {
        removeMachine(MANAGER_NAME);
    }

}
