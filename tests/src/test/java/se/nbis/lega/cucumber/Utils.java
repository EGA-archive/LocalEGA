package se.nbis.lega.cucumber;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.dockerjava.api.DockerClient;
import com.github.dockerjava.api.command.CreateContainerResponse;
import com.github.dockerjava.api.model.Bind;
import com.github.dockerjava.api.model.Container;
import com.github.dockerjava.api.model.Volume;
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
import org.apache.commons.lang.ArrayUtils;
import org.apache.commons.lang.StringUtils;
import se.nbis.lega.cucumber.publisher.Checksum;
import se.nbis.lega.cucumber.publisher.Message;

import javax.ws.rs.core.MediaType;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
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
     * Executes PSQL query.
     *
     * @param instance LocalEGA site.
     * @param query    Query to execute.
     * @return Query output.
     * @throws IOException          In case of output error.
     * @throws InterruptedException In case the query execution is interrupted.
     */
    public String executeDBQuery(String instance, String query) throws IOException, InterruptedException {
        return executeWithinContainer(findContainer(getProperty("images.name.db"), getProperty("container.prefix.db") + instance),
                "psql", "-U", readTraceProperty(instance, "DB_USER"), "-d", "lega", "-c", query);
    }

    /**
     * Removes the user from the local database.
     *
     * @param instance LocalEGA site.
     * @param user     Username.
     * @throws IOException          In case of output error.
     * @throws InterruptedException In case the query execution is interrupted.
     */
    public void removeUserFromCache(String instance, String user) throws IOException, InterruptedException {
        executeWithinContainer(findContainer(getProperty("images.name.inbox"), getProperty("container.prefix.inbox") + instance),
			       String.format("rm -rf %s/%s", getProperty("inbox.cache.path"), user).split(" "));
    }

    /**
     * Removes the user's inbox.
     *
     * @param instance LocalEGA site.
     * @param user     Username.
     * @throws InterruptedException In case the query execution is interrupted.
     */
    public void removeUserInbox(String instance, String user) throws InterruptedException {
        executeWithinContainer(findContainer(getProperty("images.name.inbox"), getProperty("container.prefix.inbox") + instance),
                String.format("umount -l %s/%s", getProperty("inbox.fuse.folder.path"), user).split(" "));
        executeWithinContainer(findContainer(getProperty("images.name.inbox"), getProperty("container.prefix.inbox") + instance),
                String.format("rm -rf %s/%s", getProperty("inbox.real.folder.path"), user).split(" "));
    }

    /**
     * Removes the uploaded file from the inbox.
     *
     * @param instance LocalEGA site.
     * @param user     Username.
     * @throws InterruptedException In case the query execution is interrupted.
     */
    public void removeUploadedFileFromInbox(String instance, String user, String fileName) throws InterruptedException {
        executeWithinContainer(findContainer(getProperty("images.name.inbox"), getProperty("container.prefix.inbox") + instance),
                String.format("rm %s/%s/%s", getProperty("inbox.fuse.folder.path"), user, fileName).split(" "));
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
        File trace = new File(String.format("%s/%s/%s", getPrivateFolderPath(), instance, getProperty("trace.file.name")));
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

    /**
     * Sends a JSON message to a RabbitMQ instance.
     *
     * @param connection The address of the broker.
     * @param user       Username.
     * @param filepath   Filepath.
     * @param enc        Encrypted file hash (MD5).
     * @param unenc      Unencrypted file hash (MD5).
     * @throws Exception In case of broken connection.
     */
    public void publishCEGA(String connection, String user, String filepath, String enc, String unenc) throws Exception {
        Message message = new Message();
        message.setUser(user);
        message.setFilepath(filepath);
	message.setStableID("EGAF_" + UUID.randomUUID().toString());

        Checksum unencrypted = new Checksum();
        unencrypted.setAlgorithm("md5");
        unencrypted.setChecksum(unenc);
        message.setUnencryptedIntegrity(unencrypted);

        Checksum encrypted = new Checksum();
        encrypted.setAlgorithm("md5");
        encrypted.setChecksum(enc);
        message.setEncryptedIntegrity(encrypted);

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
