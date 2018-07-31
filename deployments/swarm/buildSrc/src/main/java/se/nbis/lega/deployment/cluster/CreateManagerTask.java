package se.nbis.lega.deployment.cluster;

import org.gradle.api.internal.tasks.options.Option;
import org.gradle.api.tasks.OutputFile;
import org.gradle.api.tasks.TaskAction;

import java.io.File;
import java.io.IOException;
import java.util.Map;

public class CreateManagerTask extends ClusterTask {

    private String openStackConfig;

    @TaskAction
    public void run() throws IOException {
        Map<String, String> env = createMachine(MANAGER_NAME, openStackConfig);
        String machineIPAddress = getMachineIPAddress(MANAGER_NAME);
        exec(true, env, "docker swarm init", "--advertise-addr", machineIPAddress);
    }

    @Option(option = "openStackConfig", description = "Path to file with OpenStack configuration")
    public void setOpenStackConfig(String openStackConfig) {
        this.openStackConfig = openStackConfig;
    }

    @OutputFile
    public File getTraceFile() {
        return getProject().file(".tmp");
    }

}
