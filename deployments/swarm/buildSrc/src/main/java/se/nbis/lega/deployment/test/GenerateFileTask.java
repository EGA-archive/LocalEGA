package se.nbis.lega.deployment.test;

import org.gradle.api.tasks.OutputFile;
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
        RandomAccessFile randomAccessFile = new RandomAccessFile(getRawFile(), "rw");
        randomAccessFile.setLength(1024 * 1024 * 10);
        randomAccessFile.close();
    }

    @OutputFile
    public File getRawFile() {
        return getProject().file(".tmp/data.raw");
    }

}
