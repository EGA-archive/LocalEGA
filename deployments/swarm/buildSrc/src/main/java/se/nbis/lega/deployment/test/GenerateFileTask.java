package se.nbis.lega.deployment.test;

import org.gradle.api.tasks.TaskAction;
import se.nbis.lega.deployment.Groups;
import se.nbis.lega.deployment.LocalEGATask;

import java.io.File;
import java.io.IOException;
import java.io.RandomAccessFile;

public class GenerateFileTask extends LocalEGATask {

    public GenerateFileTask() {
        super();
        this.setGroup(Groups.TEST.name());
    }

    @TaskAction
    public void run() throws IOException {
        getProject().file(".tmp").mkdirs();
        File rawFile = getProject().file(".tmp/data.raw");
        RandomAccessFile randomAccessFile = new RandomAccessFile(rawFile, "rw");
        randomAccessFile.setLength(1024 * 1024 * 10);
        randomAccessFile.close();
    }

}
