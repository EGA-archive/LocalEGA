package se.nbis.lega.deployment.lega;

import org.gradle.api.tasks.TaskAction;
import se.nbis.lega.deployment.Groups;
import se.nbis.lega.deployment.LocalEGATask;

import java.io.IOException;

public class CreateInboxConfigurationTask extends LocalEGATask {

    public CreateInboxConfigurationTask() {
        super();
        this.setGroup(Groups.LEGA.name());
    }

    @TaskAction
    public void run() throws IOException {
        writeTrace("CEGA_ENDPOINT", "http://cega-users/user/");
        String cegaRESTPassword = readTrace(getProject().file("../cega/.tmp/.trace"), "CEGA_REST_PASSWORD");
        writeTrace("CEGA_ENDPOINT_CREDS", "lega:" + cegaRESTPassword);
    }

}
