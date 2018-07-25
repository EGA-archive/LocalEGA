package se.nbis.lega.deployment.cega;

import org.apache.commons.codec.digest.DigestUtils;
import org.apache.commons.io.FileUtils;
import org.gradle.api.tasks.TaskAction;
import se.nbis.lega.deployment.Groups;
import se.nbis.lega.deployment.LocalEGATask;

import java.io.File;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.Charset;
import java.security.SecureRandom;
import java.util.Base64;
import java.util.UUID;

public class CreateMQConfigurationTask extends LocalEGATask {

    public CreateMQConfigurationTask() {
        super();
        this.setGroup(Groups.CEGA.name());
    }

    @TaskAction
    public void run() throws IOException {
        String password = generateCEGAMQConfiguration();
        createConfig(Config.DEFS_JSON.getName(), getProject().file(".tmp/mq/defs.json"));
        createConfig(Config.RABBITMQ_CONFIG.getName(), getProject().file(".tmp/mq/rabbitmq.config"));
        writeTrace("CEGA_MQ_PASSWORD", password);
        writeTrace("CEGA_REST_PASSWORD", UUID.randomUUID().toString().replace("-", ""));
    }

    public String generateCEGAMQConfiguration() throws IOException {
        File rabbitmqConfig = getProject().file(".tmp/mq/rabbitmq.config");
        FileUtils.write(rabbitmqConfig, "%% -*- mode: erlang -*-\n" +
                "%%\n" +
                "[{rabbit,[{loopback_users, [ ] },\n" +
                "\t  {disk_free_limit, \"1GB\"}]},\n" +
                " {rabbitmq_management, [ {load_definitions, \"/etc/rabbitmq/defs.json\"} ]}\n" +
                "].", Charset.defaultCharset());

        byte[] saltBytes = new byte[4];
        new SecureRandom().nextBytes(saltBytes);
        String password = UUID.randomUUID().toString().replace("-", "");
        byte[] passwordBytes = password.getBytes();
        byte[] concat = ByteBuffer.allocate(saltBytes.length + passwordBytes.length).put(saltBytes).put(passwordBytes).array();
        byte[] hash = DigestUtils.sha256(concat);
        concat = ByteBuffer.allocate(saltBytes.length + hash.length).put(saltBytes).put(hash).array();
        String saltedHash = Base64.getEncoder().encodeToString(concat);
        File defsJSON = getProject().file(".tmp/mq/defs.json");
        FileUtils.write(defsJSON, String.format("{\"rabbit_version\":\"3.6.11\",\n" +
                " \"users\":[{\"name\":\"lega\",\"password_hash\":\"%s\",\"hashing_algorithm\":\"rabbit_password_hashing_sha256\",\"tags\":\"administrator\"}],\n" +
                " \"vhosts\":[{\"name\":\"lega\"}],\n" +
                " \"permissions\":[{\"user\":\"lega\", \"vhost\":\"lega\", \"configure\":\".*\", \"write\":\".*\", \"read\":\".*\"}],\n" +
                " \"parameters\":[],\n" +
                " \"global_parameters\":[{\"name\":\"cluster_name\", \"value\":\"rabbit@localhost\"}],\n" +
                " \"policies\":[],\n" +
                " \"queues\":[{\"name\":\"inbox\",           \"vhost\":\"lega\", \"durable\":true, \"auto_delete\":false, \"arguments\":{}},\n" +
                "           {\"name\":\"inbox.checksums\", \"vhost\":\"lega\", \"durable\":true, \"auto_delete\":false, \"arguments\":{}},\n" +
                "\t   {\"name\":\"files\",           \"vhost\":\"lega\", \"durable\":true, \"auto_delete\":false, \"arguments\":{}},\n" +
                "\t   {\"name\":\"completed\",       \"vhost\":\"lega\", \"durable\":true, \"auto_delete\":false, \"arguments\":{}},\n" +
                "\t   {\"name\":\"errors\",          \"vhost\":\"lega\", \"durable\":true, \"auto_delete\":false, \"arguments\":{}}],\n" +
                " \"exchanges\":[{\"name\":\"localega.v1\", \"vhost\":\"lega\", \"type\":\"topic\", \"durable\":true, \"auto_delete\":false, \"internal\":false, \"arguments\":{}}],\n" +
                " \"bindings\":[{\"source\":\"localega.v1\",\"vhost\":\"lega\",\"destination_type\":\"queue\",\"arguments\":{},\"destination\":\"inbox\",\"routing_key\":\"files.inbox\"},\n" +
                "\t     {\"source\":\"localega.v1\",\"vhost\":\"lega\",\"destination_type\":\"queue\",\"arguments\":{},\"destination\":\"inbox.checksums\",\"routing_key\":\"files.inbox.checksums\"},\n" +
                "\t     {\"source\":\"localega.v1\",\"vhost\":\"lega\",\"destination_type\":\"queue\",\"arguments\":{},\"destination\":\"files\",\"routing_key\":\"files\"},\n" +
                "\t     {\"source\":\"localega.v1\",\"vhost\":\"lega\",\"destination_type\":\"queue\",\"arguments\":{},\"destination\":\"completed\",\"routing_key\":\"files.completed\"},\n" +
                "\t     {\"source\":\"localega.v1\",\"vhost\":\"lega\",\"destination_type\":\"queue\",\"arguments\":{},\"destination\":\"errors\",\"routing_key\":\"files.error\"}]\n" +
                "}", saltedHash), Charset.defaultCharset());
        return password;
    }

}
