package se.nbis.lega.deployment.lega;

import org.gradle.api.tasks.TaskAction;
import se.nbis.lega.deployment.Groups;
import se.nbis.lega.deployment.LocalEGATask;

import java.io.IOException;

public class CreateMinioConfigurationTask extends LocalEGATask {

    public CreateMinioConfigurationTask() {
        super();
        this.setGroup(Groups.LEGA.name());
    }

    @TaskAction
    public void run() throws IOException {
        writeTrace("MINIO_ACCESS_KEY", readTrace("S3_ACCESS_KEY"));
        writeTrace("MINIO_SECRET_KEY", readTrace("S3_SECRET_KEY"));
    }

}
