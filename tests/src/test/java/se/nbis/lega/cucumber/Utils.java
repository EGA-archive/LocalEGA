package se.nbis.lega.cucumber;

import com.github.dockerjava.api.DockerClient;
import com.github.dockerjava.api.command.CreateContainerResponse;
import com.github.dockerjava.api.model.AccessMode;
import com.github.dockerjava.api.model.Bind;
import com.github.dockerjava.api.model.Container;
import com.github.dockerjava.api.model.Volume;
import com.github.dockerjava.core.DefaultDockerClientConfig;
import com.github.dockerjava.core.DockerClientBuilder;
import com.github.dockerjava.core.command.ExecStartResultCallback;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.codec.digest.DigestUtils;
import org.apache.commons.io.FileUtils;
import org.apache.commons.lang.ArrayUtils;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * Utility methods for the test-suite.
 */
@Slf4j
public class Utils {

    private DockerClient dockerClient;

    /**
     * Public constructor with Docker client initialization.
     */
    public Utils() {
        this.dockerClient = DockerClientBuilder.getInstance(DefaultDockerClientConfig.createDefaultConfigBuilder().build()).build();
    }

    /**
     * Gets absolute path or a private folder.
     *
     * @return Absolute path or a private folder.
     */
    public String getPrivateFolderPath() {
        return Paths.get("").toAbsolutePath().getParent().toString() + "/deployments/docker/private";
    }

    /**
     * Executes shell command within specified container.
     *
     * @param container Container to execute command in.
     * @param command   Command to execute.
     * @return Command output.
     * @throws IOException          In case of output error.
     * @throws InterruptedException In case the command execution is interrupted.
     */
    public String executeWithinContainer(Container container, String... command) throws IOException, InterruptedException {
        String execId = dockerClient.
                execCreateCmd(container.getId()).
                withCmd(command).
                withAttachStdout(true).
                withAttachStderr(true).
                exec().
                getId();
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        ExecStartResultCallback resultCallback = new ExecStartResultCallback(outputStream, System.err);
        dockerClient.execStartCmd(execId).exec(resultCallback);
        resultCallback.awaitCompletion();
        return new String(outputStream.toByteArray());
    }

    /**
     * Executes PSQL query.
     *
     * @param instance LocalEGA site.
     * @param query    Query to execute.
     * @return Query output.
     * @throws IOException          In case of output error.
     * @throws InterruptedException In case the query execution is interrupted.
     */
    public String executeDBQuery(String instance, String query) throws IOException, InterruptedException {
        return executeWithinContainer(findContainer("nbisweden/ega-db", "ega_db_" + instance), "psql", "-U", readTraceProperty(instance, "DB_USER"), "-d", "lega", "-c", query);
    }

    /**
     * Checks if the user exists in the local database.
     *
     * @param instance LocalEGA site.
     * @param user     Username.
     * @return <code>true</code> if user exists, <code>false</code> otherwise.
     * @throws IOException          In case of output error.
     * @throws InterruptedException In case the query execution is interrupted.
     */
    public boolean isUserExistInDB(String instance, String user) throws IOException, InterruptedException {
        String output = executeDBQuery(instance, String.format("select count(*) from users where elixir_id = '%s'", user));
        return "1".equals(output.split(System.getProperty("line.separator"))[2].trim());
    }

    /**
     * Removes the user from the local database.
     *
     * @param instance LocalEGA site.
     * @param user     Username.
     * @throws IOException          In case of output error.
     * @throws InterruptedException In case the query execution is interrupted.
     */
    public void removeUserFromDB(String instance, String user) throws IOException, InterruptedException {
        executeDBQuery(instance, String.format("delete from users where elixir_id = '%s'", user));
    }

    /**
     * Removes the user from the inbox.
     *
     * @param instance LocalEGA site.
     * @param user     Username.
     * @throws IOException          In case of output error.
     * @throws InterruptedException In case the query execution is interrupted.
     */
    public void removeUserFromInbox(String instance, String user) throws IOException, InterruptedException {
        executeWithinContainer(findContainer("nbisweden/ega-inbox", "ega_inbox_" + instance), String.format("rm -rf /ega/inbox/%s", user).split(" "));
    }

    /**
     * Spawns "nbisweden/ega-worker" container, mounts data folder there and executes a command.
     *
     * @param instance LocalEGA site.
     * @param from     Folder to mount from.
     * @param to       Folder to mount to.
     * @param commands Command to execute.
     * @return Execution result per command.
     * @throws InterruptedException In case the command execution is interrupted.
     */
    public List<String> spawnTempWorkerAndExecute(String instance, String from, String to, String... commands) throws InterruptedException {
        List<String> results = new ArrayList<>();
        String name = UUID.randomUUID().toString();
        Volume dataVolume = new Volume(to);
        Volume gpgVolume = new Volume("/root/.gnupg");
        CreateContainerResponse createContainerResponse = dockerClient.
                createContainerCmd("nbisweden/ega-worker").
                withVolumes(dataVolume, gpgVolume).
                withBinds(new Bind(from, dataVolume),
                        new Bind(String.format("%s/%s/gpg", getPrivateFolderPath(), instance), gpgVolume, AccessMode.ro)).
                withEnv("MQ_INSTANCE=ega_mq_" + instance, "KEYSERVER_HOST=ega_keys_" + instance, "KEYSERVER_PORT=9010").
                withName(name).
                exec();
        dockerClient.startContainerCmd(createContainerResponse.getId()).exec();
        try {
            Container tempWorker = findContainer("nbisweden/ega-worker", name);
            for (String command : commands) {
                results.add(executeWithinContainer(tempWorker, command.split(" ")));
            }
        } catch (IOException | InterruptedException e) {
            log.error(e.getMessage(), e);
        } finally {
            dockerClient.removeContainerCmd(createContainerResponse.getId()).withForce(true).exec();
        }
        return results;
    }

    /**
     * Reads property from the trace file.
     *
     * @param instance LocalEGA site.
     * @param property Property name.
     * @return Property value.
     * @throws IOException In case it's not possible to read trace file.
     */
    public String readTraceProperty(String instance, String property) throws IOException {
        File trace = new File(String.format("%s/%s/.trace", getPrivateFolderPath(), instance));
        return FileUtils.readLines(trace, Charset.defaultCharset()).
                stream().
                filter(l -> l.startsWith(property)).
                map(p -> p.split(" = ")[1]).
                findAny().
                orElseThrow(() -> new RuntimeException(String.format("Property %s not found for instance %s", property, instance))).
                trim();
    }

    /**
     * Finds container by image name and container name.
     *
     * @param imageName     Image name.
     * @param containerName Container name.
     * @return Docker container.
     */
    public Container findContainer(String imageName, String containerName) {
        return dockerClient.listContainersCmd().withShowAll(true).exec().
                stream().
                filter(c -> c.getImage().equals(imageName)).
                filter(c -> ArrayUtils.contains(c.getNames(), "/" + containerName)).
                findAny().
                orElse(null);
    }

    /**
     * Calculates MD5 hash of a file.
     *
     * @param file File to calculate hash for.
     * @return MD5 hash.
     * @throws IOException In case it's not possible ot read the file.
     */
    public String calculateMD5(File file) throws IOException {
        FileInputStream fileInputStream = new FileInputStream(file);
        String md5 = DigestUtils.md5Hex(fileInputStream);
        fileInputStream.close();
        return md5;
    }

    public DockerClient getDockerClient() {
        return dockerClient;
    }

}
