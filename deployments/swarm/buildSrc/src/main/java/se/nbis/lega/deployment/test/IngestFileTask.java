package se.nbis.lega.deployment.test;

import com.rabbitmq.client.AMQP;
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;
import io.minio.MinioClient;
import io.minio.errors.*;
import org.apache.commons.collections4.IterableUtils;
import org.gradle.api.GradleException;
import org.gradle.api.tasks.TaskAction;
import org.xmlpull.v1.XmlPullParserException;
import se.nbis.lega.deployment.Groups;
import se.nbis.lega.deployment.LocalEGATask;

import java.io.IOException;
import java.net.URISyntaxException;
import java.nio.charset.StandardCharsets;
import java.security.InvalidKeyException;
import java.security.KeyManagementException;
import java.security.NoSuchAlgorithmException;
import java.util.UUID;
import java.util.concurrent.TimeoutException;

public class IngestFileTask extends LocalEGATask {

    private String host;

    public IngestFileTask() {
        super();
        this.setGroup(Groups.TEST.name());
        this.dependsOn("upload");
    }

    @TaskAction
    public void run() throws IOException, NoSuchAlgorithmException, KeyManagementException, URISyntaxException, TimeoutException, InvalidKeyException, XmlPullParserException, InvalidPortException, ErrorResponseException, NoResponseException, InvalidBucketNameException, InsufficientDataException, InvalidEndpointException, InternalException, InterruptedException {
        host = System.getenv("DOCKER_HOST").substring(6).split(":")[0];
        int before = getFilesAmount();
        ingest();
        Thread.sleep(5000);
        int after = getFilesAmount();
        if (after != before + 1) {
            throw new GradleException("File was not ingested!");
        }
    }

    private void ingest() throws IOException, URISyntaxException, NoSuchAlgorithmException, KeyManagementException, TimeoutException {
        String mqPassword = readTrace(getProject().file("cega/.tmp/.trace"), "CEGA_MQ_PASSWORD");
        ConnectionFactory factory = new ConnectionFactory();
        factory.setUri(String.format("amqp://lega:%s@%s:5672/lega", mqPassword, host));
        Connection connectionFactory = factory.newConnection();
        Channel channel = connectionFactory.createChannel();
        AMQP.BasicProperties properties = new AMQP.BasicProperties().builder().
                deliveryMode(2).
                contentType("application/json").
                contentEncoding(StandardCharsets.UTF_8.displayName()).
                build();


        String stableId = "EGAF" + UUID.randomUUID().toString().replace("-", "");
        channel.basicPublish("localega.v1",
                "files",
                properties,
                String.format("{\"user\":\"john\",\"filepath\":\"data.raw.enc\",\"stable_id\":\"%s\"}", stableId).getBytes());

        channel.close();
        connectionFactory.close();
    }

    private int getFilesAmount() throws XmlPullParserException, IOException, InvalidPortException, InvalidEndpointException, InsufficientDataException, NoSuchAlgorithmException, NoResponseException, InternalException, InvalidKeyException, InvalidBucketNameException, ErrorResponseException {
        String accessKey = readTrace(getProject().file("lega/.tmp/.trace"), "S3_ACCESS_KEY");
        String secretKey = readTrace(getProject().file("lega/.tmp/.trace"), "S3_SECRET_KEY");
        MinioClient minioClient = new MinioClient(String.format("http://%s:9000", host), accessKey, secretKey);
        if (!minioClient.bucketExists("lega")) {
            return 0;
        }
        return IterableUtils.size(minioClient.listObjects("lega"));
    }

}
