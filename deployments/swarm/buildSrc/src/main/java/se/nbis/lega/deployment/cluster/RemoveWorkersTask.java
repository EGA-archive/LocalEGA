package se.nbis.lega.deployment.cluster;

import org.gradle.api.tasks.TaskAction;

import java.io.IOException;
import java.util.Map;

public class RemoveWorkersTask extends ClusterTask {

    @TaskAction
    public void run() throws IOException {
        Map<String, Map<String, String>> workers = getMachines(WORKER_PREFIX);
        for (String worker : workers.keySet()) {
            removeMachine(worker);
        }
    }

}
