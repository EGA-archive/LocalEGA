package se.nbis.lega.deployment.cega;

import org.gradle.api.tasks.TaskAction;
import se.nbis.lega.deployment.Groups;
import se.nbis.lega.deployment.LocalEGATask;

import java.io.IOException;

public class CreateEurekaConfigurationTask extends LocalEGATask {

    public CreateEurekaConfigurationTask() {
        super();
        this.setGroup(Groups.CEGA.name());
    }

    @TaskAction
    public void run() throws IOException {
        createConfig(Config.EUREKA_PY.getName(), getProject().file("../../docker/images/cega/eureka.py"));
    }

}
