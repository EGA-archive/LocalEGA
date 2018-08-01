package se.nbis.lega.deployment.cluster;

import org.gradle.api.internal.tasks.options.Option;
import org.gradle.api.tasks.TaskAction;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class CreateWorkersTask extends ClusterTask {

    private String machinesToCreate = "1";
    private String openStackConfig;

    @TaskAction
    public void run() throws IOException, InterruptedException {
        ExecutorService executorService = Executors.newCachedThreadPool();
        Map<String, Map<String, String>> workers = getMachines(WORKER_PREFIX);
        for (int i = 0; i < Integer.parseInt(machinesToCreate); i++) {
            String machineName = WORKER_PREFIX + (workers.size() + i);
            executorService.submit(() -> {
                try {
                    Map<String, String> env = createMachine(machineName, openStackConfig);
                    String joinString = getJoinString(MANAGER_NAME);
                    String[] split = joinString.split(" ");
                    exec(env, "docker swarm join", "--token", split[0], split[1]);
                } catch (IOException e) {
                    getLogger().error(e.getMessage(), e);
                }
            });
        }
        executorService.shutdown();
        executorService.awaitTermination(Long.MAX_VALUE, TimeUnit.NANOSECONDS);
    }

    @Option(option = "n", description = "Number of machines to create")
    public void setMachinesToCreate(String machinesToCreate) {
        this.machinesToCreate = machinesToCreate;
    }

    @Option(option = "openStackConfig", description = "Path to file with OpenStack configuration")
    public void setOpenStackConfig(String openStackConfig) {
        this.openStackConfig = openStackConfig;
    }

}
