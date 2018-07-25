package se.nbis.lega.deployment;

import de.gesellix.docker.client.DockerClientException;
import lombok.Data;
import org.gradle.api.tasks.TaskAction;

import java.util.Set;

@Data
public class RemoveVolumesTask extends LocalEGATask {

    private Set<String> volumes;

    @TaskAction
    public void run() {
        for (String volume : volumes) {
            try {
                removeVolume(volume);
            } catch (DockerClientException ignored) {
            }
        }
    }

}
