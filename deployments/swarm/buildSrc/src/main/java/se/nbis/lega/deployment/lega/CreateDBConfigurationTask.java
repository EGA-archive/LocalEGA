package se.nbis.lega.deployment.lega;

import org.gradle.api.tasks.TaskAction;
import se.nbis.lega.deployment.Groups;
import se.nbis.lega.deployment.LocalEGATask;

import java.io.IOException;
import java.util.UUID;

public class CreateDBConfigurationTask extends LocalEGATask {

    public CreateDBConfigurationTask() {
        super();
        this.setGroup(Groups.LEGA.name());
    }

    @TaskAction
    public void run() throws IOException {
        createConfig(Config.DB_SQL.getName(), getProject().file("../../../extras/db.sql"));
        writeTrace("DB_INSTANCE", "db");
        writeTrace("POSTGRES_USER", "lega");
        writeTrace("POSTGRES_PASSWORD", UUID.randomUUID().toString().replace("-", ""));
        writeTrace("POSTGRES_DB", "lega");
    }

}
