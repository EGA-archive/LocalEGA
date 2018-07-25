package se.nbis.lega.deployment.lega;

import org.gradle.api.tasks.TaskAction;
import se.nbis.lega.deployment.Groups;
import se.nbis.lega.deployment.LocalEGATask;

import java.io.IOException;
import java.util.UUID;

public class CreateIngestConfigurationTask extends LocalEGATask {

    public CreateIngestConfigurationTask() {
        super();
        this.setGroup(Groups.LEGA.name());
    }

    @TaskAction
    public void run() throws IOException {
        writeTrace("S3_ACCESS_KEY", UUID.randomUUID().toString().replace("-", ""));
        writeTrace("S3_SECRET_KEY", UUID.randomUUID().toString().replace("-", ""));
    }

}
