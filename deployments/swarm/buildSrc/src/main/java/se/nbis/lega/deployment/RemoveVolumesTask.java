package se.nbis.lega.deployment;

import org.gradle.api.tasks.TaskAction;

import java.io.IOException;
import java.util.Set;

public class RemoveVolumesTask extends LocalEGATask {

    private Set<String> volumes;

    @TaskAction
    public void run() throws IOException {
        for (String volume : volumes) {
            removeVolume(volume);
        }
    }

    public void setVolumes(Set<String> volumes) {
        this.volumes = volumes;
    }

}
