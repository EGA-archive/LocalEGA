package se.nbis.lega.deployment;

import de.gesellix.docker.client.DockerClientImpl;

public class DockerClientHolder {

    private static DockerClientHolder ourInstance = new DockerClientHolder();

    public static DockerClientHolder getInstance() {
        return ourInstance;
    }

    private DockerClientImpl docker;

    private DockerClientHolder() {
        docker = new DockerClientImpl();
    }

    public DockerClientImpl getDocker() {
        return docker;
    }

}
