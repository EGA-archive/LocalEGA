package se.nbis.lega.cucumber;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.dockerjava.api.DockerClient;
import com.github.dockerjava.api.model.Container;
import com.github.dockerjava.core.DefaultDockerClientConfig;
import com.github.dockerjava.core.DockerClientBuilder;
import com.github.dockerjava.core.command.ExecStartResultCallback;
import com.rabbitmq.client.AMQP;
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.codec.digest.DigestUtils;
import org.apache.commons.io.FileUtils;
import org.apache.commons.lang.StringUtils;
import org.c02e.jpgpj.HashingAlgorithm;
import se.nbis.lega.cucumber.publisher.Message;

import javax.ws.rs.core.MediaType;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.nio.file.Paths;
import java.util.Collection;
import java.util.Collections;
import java.util.Properties;
import java.util.UUID;

/**
 * Utility methods for the test-suite.
 */
@Slf4j
public class Utils {

    private Properties properties;
    private DockerClient dockerClient;

    /**
     * Public constructor with Docker client initialization.
     */
    @SuppressWarnings("ConstantConditions")
    public Utils() throws IOException {
        Properties properties = new Properties();
        properties.load(FileUtils.openInputStream(new File(getClass().getClassLoader().getResource("config.properties").getFile())));
        this.properties = properties;
        this.dockerClient = DockerClientBuilder.getInstance(DefaultDockerClientConfig.createDefaultConfigBuilder().build()).build();
    }

    /**
     * Get property value from config.properties
     *
     * @param key Property name.
     * @return Property value.
     */
    public String getProperty(String key) {
        return properties.getProperty(key);
    }

    /**
     * Gets absolute path or a private folder.
     *
     * @return Absolute path or a private folder.
     */
    public String getPrivateFolderPath() {
        return Paths.get("").toAbsolutePath().getParent().toString() + getProperty("private.folder.name");
    }

    /**
     * Executes shell command within specified container.
     *
     * @param container Container to execute command in.
     * @param command   Command to execute.
     * @return Command output.
     * @throws InterruptedException In case the command execution is interrupted.
     */
    public String executeWithinContainer(Container container, String... command) throws InterruptedException {
        String execId = dockerClient.
                execCreateCmd(container.getId()).
                withCmd(command).
                withAttachStdout(true).
                withAttachStderr(true).
                exec().
                getId();
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        ByteArrayOutputStream errorStream = new ByteArrayOutputStream();
        ExecStartResultCallback resultCallback = new ExecStartResultCallback(outputStream, errorStream);
        dockerClient.execStartCmd(execId).exec(resultCallback);
        resultCallback.awaitCompletion();
        String output = new String(outputStream.toByteArray()).trim();
        String error = new String(errorStream.toByteArray()).trim();
        if (StringUtils.isNotEmpty(output)) {
            log.trace(output);
        }
        if (StringUtils.isNotEmpty(error)) {
            log.error(error);
        }
        return output;
    }

    /**
     * Executes SQL query.
     *
     * @param query Query to execute.
     * @return Query output.
     * @throws IOException          In case of output error.
     * @throws InterruptedException In case the query execution is interrupted.
     */
    public String executeDBQuery(String query) throws IOException, InterruptedException {
        Container dbContainer = findContainer(getProperty("container.label.db"));

        String connectionString = String.format("postgresql://%s:%s@localhost/lega",
                readTraceProperty("DB_LEGA_IN_USER"),
                readTraceProperty("DB_LEGA_IN_PASSWORD"));

        return executeWithinContainer(dbContainer, "psql", connectionString, "-c", query);
    }

//    /**
//     * Removes the user's inbox.
//     *
//     * @param user     Username.
//     * @throws InterruptedException In case the query execution is interrupted.
//     */
//    public void removeUserInbox(String user) throws InterruptedException {
//        executeWithinContainer(findContainer(getProperty("images.name.inbox"), getProperty("container.name.inbox")),
//                String.format("umount -l %s/%s", getProperty("inbox.fuse.folder.path"), user).split(" "));
//        executeWithinContainer(findContainer(getProperty("images.name.inbox"), getProperty("container.name.inbox")),
//                String.format("rm -rf %s/%s", getProperty("inbox.real.folder.path"), user).split(" "));
//    }

    /**
     * Removes the uploaded file from the inbox.
     *
     * @param user Username.
     * @throws InterruptedException In case the query execution is interrupted.
     */
    public void removeUploadedFileFromInbox(String user, String fileName) throws InterruptedException {
        executeWithinContainer(findContainer(getProperty("container.label.inbox")),
                String.format("rm %s/%s/%s", getProperty("inbox.folder.path"), user, fileName).split(" "));
    }

    /**
     * Reads property from the trace file.
     *
     * @param property Property name.
     * @return Property value.
     * @throws IOException In case it's not possible to read trace file.
     */
    public String readTraceProperty(String property) throws IOException {
        File trace = new File(String.format("%s/%s/%s", getPrivateFolderPath(), getProperty("instance.name"), getProperty("trace.file.name")));
        return FileUtils.readLines(trace, Charset.defaultCharset()).
                stream().
                filter(l -> l.startsWith(property)).
                map(p -> p.split(" = ")[1]).
                findAny().
                orElseThrow(() -> new RuntimeException(String.format("Property %s not found!", property))).
                trim();
    }

    /**
     * Finds container by image name and container name.
     *
     * @param label Container lavbel.
     * @return Docker container.
     */
    public Container findContainer(String label) {
        return dockerClient
                .listContainersCmd()
                .withShowAll(true)
                .withLabelFilter(Collections.singletonMap("lega_label", label)).exec()
                .stream()
                .findAny()
                .orElseThrow(() -> new RuntimeException(String.format("Container with label %s not found!", label)));
    }

    /**
     * Starts container.
     *
     * @param container Container to be started.
     * @return Container.
     */
    public Container startContainer(Container container) {
        dockerClient.startContainerCmd(container.getId()).exec();
        return container;
    }

    /**
     * Stops container.
     *
     * @param container Container to be stopped.
     * @return Container.
     */
    public Container stopContainer(Container container) {
        dockerClient.stopContainerCmd(container.getId()).exec();
        return container;
    }

    /**
     * Gets all LocalEGA Docker containers.
     *
     * @return All LocalEGA Docker containers.
     */
    public Collection<Container> getAllLocalEGAContainers() {
        return dockerClient.listContainersCmd().withShowAll(true).withLabelFilter("lega_label").exec();
    }

    /**
     * Restarts all the LocalEGA containers.
     */
    public void restartAllLocalEGAContainers() {
        getAllLocalEGAContainers().
                stream().
                peek(this::stopContainer).
                peek(c -> safeSleep(5000)).
                peek(this::startContainer).
                forEach(c -> safeSleep(5000));
        waitForInitializationToComplete();
    }

    /**
     * Waits for all LocalEGA containers to initialize.
     */
    public void waitForInitializationToComplete() {
        Collection<Container> containers = getAllLocalEGAContainers();
        long maxTimeout = Long.parseLong(getProperty("initialization.max-timeout"));
        long timeout = 0;
        while (containers.isEmpty() || !containers.stream().map(Container::getStatus).allMatch(s -> s.startsWith("Up"))) {
            if (containers.isEmpty()) {
                containers = getAllLocalEGAContainers();
            }
            safeSleep(1000);
            timeout += 1000;
            if (timeout > maxTimeout) {
                throw new RuntimeException(String.format("The system was not initialized in time: initialization.max-timeout = %s", maxTimeout));
            }
        }
        // Sleep a bit more to let containers not only start up, but finish initialization.
        safeSleep(Long.parseLong(getProperty("initialization.delay")));
    }

    /**
     * Sleeps for some time without throwing an exception (to make it easier to use in lambdas).
     *
     * @param millis Time to sleep in milliseconds.
     */
    private void safeSleep(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            log.error(e.getMessage(), e);
        }
    }

    /**
     * Calculates hash of a file.
     *
     * @param file             File to calculate hash for.
     * @param hashingAlgorithm Algorithm to use for hashing.
     * @return Hash. Defaults to MD5.
     * @throws IOException In case it's not possible ot read the file.
     */
    public String calculateChecksum(File file, HashingAlgorithm hashingAlgorithm) throws IOException {
        try (FileInputStream fileInputStream = new FileInputStream(file)) {
            switch (hashingAlgorithm) {
                case SHA256:
                    return DigestUtils.sha256Hex(fileInputStream);
                case MD5:
                    return DigestUtils.md5Hex(fileInputStream);
                default:
                    throw new RuntimeException(hashingAlgorithm + " hashing algorithm is not supported by the test-suite.");
            }
        }
    }

    /**
     * Sends a JSON message to a RabbitMQ instance.
     *
     * @param connection        The address of the broker.
     * @param user              Username.
     * @param encryptedFileName Encrypted file name.
     * @throws Exception In case of broken connection.
     */
    public void publishCEGA(String connection, String user, String encryptedFileName) throws Exception {
        Message message = new Message();
        message.setUser(user);
        message.setFilepath(encryptedFileName);
        message.setStableID("EGAF" + UUID.randomUUID().toString().toLowerCase());

//        if (StringUtils.isNotEmpty(rawChecksum)) {
//            Checksum unencrypted = new Checksum();
//            unencrypted.setAlgorithm(hashingAlgorithm.toLowerCase());
//            unencrypted.setChecksum(rawChecksum);
//            message.setUnencryptedIntegrity(unencrypted);
//        }
//
//        if (StringUtils.isNotEmpty(encChecksum)) {
//            Checksum encrypted = new Checksum();
//            encrypted.setAlgorithm(hashingAlgorithm.toLowerCase());
//            encrypted.setChecksum(encChecksum);
//            message.setEncryptedIntegrity(encrypted);
//        }

        ConnectionFactory factory = new ConnectionFactory();
        factory.setUri(connection);

        Connection connectionFactory = factory.newConnection();
        Channel channel = connectionFactory.createChannel();

        ObjectMapper objectMapper = new ObjectMapper();
        AMQP.BasicProperties properties = new AMQP.BasicProperties().builder().
                deliveryMode(2).
                contentType(MediaType.APPLICATION_JSON_TYPE.getType()).
                contentEncoding(StandardCharsets.UTF_8.displayName()).
                build();

        channel.basicPublish("localega.v1", "files", properties, objectMapper.writeValueAsBytes(message));

        channel.close();
        connectionFactory.close();
    }

}
