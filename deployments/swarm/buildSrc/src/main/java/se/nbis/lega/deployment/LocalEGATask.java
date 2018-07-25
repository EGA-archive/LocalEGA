package se.nbis.lega.deployment;

import de.gesellix.docker.client.DockerClientImpl;
import org.apache.commons.exec.CommandLine;
import org.apache.commons.exec.DefaultExecutor;
import org.apache.commons.io.FileUtils;
import org.gradle.api.DefaultTask;
import se.nbis.lega.deployment.cega.DockerClientHolder;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.nio.charset.Charset;
import java.util.Collections;
import java.util.List;
import java.util.Map;

public class LocalEGATask extends DefaultTask {

    private DockerClientImpl docker = DockerClientHolder.getInstance().getDocker();
    private DefaultExecutor executor = new DefaultExecutor();

    protected void writeTrace(String key, String value) throws IOException {
        File traceFile = getProject().file(".tmp/.trace");
        String existingValue = readTrace(traceFile, key);
        if (existingValue == null) {
            FileUtils.writeLines(traceFile, Collections.singleton(String.format("%s=%s", key, value)), true);
        }
    }

    protected String readTrace(File traceFile, String key) throws IOException {
        try {
            List<String> lines = FileUtils.readLines(traceFile, Charset.defaultCharset());
            for (String line : lines) {
                if (line.startsWith(key)) {
                    return line.split("=")[1].trim();
                }
            }
            return null;
        } catch (FileNotFoundException e) {
            return null;
        }
    }

    protected String readTrace(String key) throws IOException {
        File traceFile = getProject().file(".tmp/.trace");
        return readTrace(traceFile, key);
    }

    protected void removeConfig(String name) {
        docker.rmConfig(name);
    }

    protected void createConfig(String name, File file) throws IOException {
        exec("docker config create", name, file.getAbsolutePath());
    }

    protected int exec(String command, String... arguments) throws IOException {
        return exec(null, command, arguments);
    }

    protected int exec(Map<String, String> environment, String command, String... arguments) throws IOException {
        CommandLine commandLine = CommandLine.parse(command);
        commandLine.addArguments(arguments);
        return executor.execute(commandLine, environment);
    }

}
