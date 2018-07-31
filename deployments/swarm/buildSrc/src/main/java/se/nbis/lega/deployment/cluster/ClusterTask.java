package se.nbis.lega.deployment.cluster;

import se.nbis.lega.deployment.Groups;
import se.nbis.lega.deployment.LocalEGATask;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public abstract class ClusterTask extends LocalEGATask {

    public static final String MANAGER_NAME = "lega-swarm-manager";
    public static final String WORKER_PREFIX = "lega-swarm-worker-";

    public static final List<String> DOCKER_ENV_VARS = Arrays.asList(
            "DOCKER_TLS_VERIFY",
            "DOCKER_HOST",
            "DOCKER_CERT_PATH",
            "DOCKER_MACHINE_NAME"
    );

    public ClusterTask() {
        super();
        this.setGroup(Groups.CLUSTER.name());
    }

    protected Map<String, Map<String, String>> getMachines(String prefix) throws IOException {
        Map<String, Map<String, String>> result = new HashMap<>();
        List<String> ls = exec("docker-machine", "ls");
        for (String line : ls) {
            if (line.startsWith(prefix)) {
                String machineName = line.split(" ")[0];
                Map<String, String> variables = getMachineEnvironment(machineName);
                result.put(machineName, variables);
            }
        }
        return result;
    }

    protected Map<String, String> getMachineEnvironment(String name) throws IOException {
        List<String> env = exec("docker-machine env", name);
        Map<String, String> variables = new HashMap<>();
        for (String variable : env) {
            String[] split = variable.substring(7).split("=");
            if (DOCKER_ENV_VARS.contains(split[0])) {
                variables.put(split[0], split[1].replace("\"", ""));
            }
        }
        return variables;
    }

    protected Map<String, String> createMachine(String name, String openStackConfig) throws IOException {
        if (openStackConfig == null) {
            exec(true, "docker-machine create", "--driver", "virtualbox", name);
        } else {
            Map<String, String> env = readFileAsMap(new File(openStackConfig));
            exec(true, env, "docker-machine create", "--driver", "openstack", name);
        }
        return getMachines(name).get(name);
    }

    protected String getMachineIPAddress(String name) throws IOException {
        return exec("docker-machine ip", name).iterator().next();
    }

    protected String getJoinString(String name) throws IOException {
        Map<String, String> env = getMachineEnvironment(name);
        List<String> lines = exec(env, "docker swarm join-token", "worker");
        String joinCommand = lines.get(2).trim();
        String[] split = joinCommand.split(" ");
        return split[4] + " " + split[5];
    }

}
