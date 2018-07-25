package se.nbis.lega.deployment;

import com.rabbitmq.client.AMQP;
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;
import io.minio.MinioClient;
import io.minio.errors.*;
import net.schmizz.sshj.SSHClient;
import net.schmizz.sshj.sftp.SFTPClient;
import net.schmizz.sshj.transport.verification.PromiscuousVerifier;
import no.ifi.uio.crypt4gh.stream.Crypt4GHOutputStream;
import org.apache.commons.codec.digest.DigestUtils;
import org.apache.commons.collections4.IterableUtils;
import org.apache.commons.io.FileUtils;
import org.bouncycastle.asn1.x500.X500Name;
import org.bouncycastle.asn1.x500.X500NameBuilder;
import org.bouncycastle.asn1.x500.style.BCStyle;
import org.bouncycastle.bcpg.ArmoredOutputStream;
import org.bouncycastle.bcpg.HashAlgorithmTags;
import org.bouncycastle.bcpg.sig.Features;
import org.bouncycastle.bcpg.sig.KeyFlags;
import org.bouncycastle.cert.X509CertificateHolder;
import org.bouncycastle.cert.X509v3CertificateBuilder;
import org.bouncycastle.cert.jcajce.JcaX509CertificateConverter;
import org.bouncycastle.cert.jcajce.JcaX509v3CertificateBuilder;
import org.bouncycastle.crypto.generators.RSAKeyPairGenerator;
import org.bouncycastle.crypto.params.RSAKeyGenerationParameters;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.bouncycastle.openpgp.*;
import org.bouncycastle.openpgp.operator.PBESecretKeyEncryptor;
import org.bouncycastle.openpgp.operator.PGPDigestCalculator;
import org.bouncycastle.openpgp.operator.bc.BcPBESecretKeyEncryptorBuilder;
import org.bouncycastle.openpgp.operator.bc.BcPGPContentSignerBuilder;
import org.bouncycastle.openpgp.operator.bc.BcPGPDigestCalculatorProvider;
import org.bouncycastle.openpgp.operator.bc.BcPGPKeyPair;
import org.bouncycastle.openssl.jcajce.JcaPEMWriter;
import org.bouncycastle.operator.ContentSigner;
import org.bouncycastle.operator.OperatorCreationException;
import org.bouncycastle.operator.jcajce.JcaContentSignerBuilder;
import org.xmlpull.v1.XmlPullParserException;

import javax.crypto.*;
import javax.crypto.spec.PBEKeySpec;
import javax.crypto.spec.PBEParameterSpec;
import java.io.*;
import java.math.BigInteger;
import java.net.URISyntaxException;
import java.nio.ByteBuffer;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.attribute.PosixFilePermission;
import java.security.*;
import java.security.cert.CertificateException;
import java.security.cert.X509Certificate;
import java.security.spec.InvalidKeySpecException;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.*;
import java.util.concurrent.TimeoutException;

public class Utils {

    void writeTrace(String key, String value) throws IOException {
        File traceFile = new File("${project.projectDir.toString()}/.tmp/.trace");
        String existingValue = readTrace(traceFile, key);
        if (existingValue == null) {
            FileUtils.writeLines(traceFile, Collections.singleton(String.format("%s=%s", key, value)), true);
        }
    }

    String readTrace(File traceFile, String key) throws IOException {
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

    String readTrace(String key) throws IOException {
        File traceFile = new File("${project.projectDir.toString()}/.tmp/.trace");
        return readTrace(traceFile, key);
    }

    Map<String, String> getTraceAsMAp() throws IOException {
        File traceFile = new File("${project.projectDir.toString()}/.tmp/.trace");
        List<String> lines = FileUtils.readLines(traceFile, Charset.defaultCharset());
        Map<String, String> result = new HashMap<>();
        for (String line : lines) {
            result.put(line.split("=")[0].trim(), line.split("=")[1].trim());
        }
        return result;
    }

    private KeyPair generateRSAKeyPair() throws NoSuchProviderException, NoSuchAlgorithmException {
        KeyPairGenerator keyPairGenerator = KeyPairGenerator.getInstance("RSA", "BC");
        keyPairGenerator.initialize(2048, new SecureRandom());
        return keyPairGenerator.genKeyPair();
    }

    private PGPKeyRingGenerator createPGPKeyRingGenerator(String userId, char[] passphrase) throws Exception {
        RSAKeyPairGenerator keyPairGenerator = new RSAKeyPairGenerator();

        keyPairGenerator.init(
                new RSAKeyGenerationParameters(
                        BigInteger.valueOf(0x10001),
                        new SecureRandom(),
                        4096,
                        12
                )
        );

        PGPKeyPair rsaKeyPair = new BcPGPKeyPair(
                PGPPublicKey.RSA_GENERAL,
                keyPairGenerator.generateKeyPair(),
                new Date()
        );

        PGPSignatureSubpacketGenerator signHashGenerator = new PGPSignatureSubpacketGenerator();
        signHashGenerator.setKeyFlags(false, KeyFlags.SIGN_DATA | KeyFlags.CERTIFY_OTHER);
        signHashGenerator.setFeature(false, Features.FEATURE_MODIFICATION_DETECTION);

        PGPSignatureSubpacketGenerator encryptHashGenerator = new PGPSignatureSubpacketGenerator();
        encryptHashGenerator.setKeyFlags(false, KeyFlags.ENCRYPT_COMMS | KeyFlags.ENCRYPT_STORAGE);

        PGPDigestCalculator sha1DigestCalculator = new BcPGPDigestCalculatorProvider().get(HashAlgorithmTags.SHA1);
        PGPDigestCalculator sha512DigestCalculator = new BcPGPDigestCalculatorProvider().get(HashAlgorithmTags.SHA512);

        PBESecretKeyEncryptor secretKeyEncryptor = (
                new BcPBESecretKeyEncryptorBuilder(PGPEncryptedData.AES_256, sha512DigestCalculator)
        ).build(passphrase);

        return new PGPKeyRingGenerator(
                PGPSignature.NO_CERTIFICATION,
                rsaKeyPair,
                userId,
                sha1DigestCalculator,
                encryptHashGenerator.generate(),
                null,
                new BcPGPContentSignerBuilder(rsaKeyPair.getPublicKey().getAlgorithm(), HashAlgorithmTags.SHA512),
                secretKeyEncryptor
        );
    }

    private byte[] armorByteArray(byte[] data) throws IOException {
        ByteArrayOutputStream encOut = new ByteArrayOutputStream();
        ArmoredOutputStream armorOut = new ArmoredOutputStream(encOut);
        armorOut.write(data);
        armorOut.flush();
        armorOut.close();
        return encOut.toByteArray();
    }

    public static void writePublicKey(KeyPair keyPair, File file) throws IOException {
        FileWriter fileWriter = new FileWriter(file);
        JcaPEMWriter pemWriter = new JcaPEMWriter(fileWriter);
        pemWriter.writeObject(keyPair.getPublic());
        pemWriter.close();
    }

    public static void writePrivateKey(KeyPair keyPair, File file) throws IOException {
        FileWriter fileWriter = new FileWriter(file);
        JcaPEMWriter pemWriter = new JcaPEMWriter(fileWriter);
        pemWriter.writeObject(keyPair.getPrivate());
        pemWriter.close();
        Set<PosixFilePermission> perms = new HashSet<>();
        perms.add(PosixFilePermission.OWNER_READ);
        perms.add(PosixFilePermission.OWNER_WRITE);
        Files.setPosixFilePermissions(file.toPath(), perms);
    }

    public void generateSSLCertificate() throws IOException, CertificateException, OperatorCreationException, NoSuchProviderException, NoSuchAlgorithmException {
        KeyPair keyPair = generateRSAKeyPair();
        X500Name subject = new X500NameBuilder(BCStyle.INSTANCE).addRDN(BCStyle.CN, "keys").build();
        SecureRandom random = new SecureRandom();
        byte[] id = new byte[20];
        random.nextBytes(id);
        BigInteger serial = new BigInteger(160, random);
        X509v3CertificateBuilder certificate = new JcaX509v3CertificateBuilder(
                subject,
                serial,
                Date.from(LocalDate.of(2018, 1, 1).atStartOfDay(ZoneOffset.UTC).toInstant()),
                Date.from(LocalDate.of(2020, 1, 1).atStartOfDay(ZoneOffset.UTC).toInstant()),
                subject,
                keyPair.getPublic());

        ContentSigner signer = new JcaContentSignerBuilder("SHA256withRSA").build(keyPair.getPrivate());
        X509CertificateHolder holder = certificate.build(signer);

        JcaX509CertificateConverter converter = new JcaX509CertificateConverter();
        converter.setProvider(new BouncyCastleProvider());
        X509Certificate x509 = converter.getCertificate(holder);

        new File("${project.projectDir.toString()}/.tmp/ssl").mkdirs();
        FileWriter fileWriter = new FileWriter("${project.projectDir.toString()}/.tmp/ssl/ssl.cert");
        JcaPEMWriter pemWriter = new JcaPEMWriter(fileWriter);
        pemWriter.writeObject(x509);
        pemWriter.close();

        writePrivateKey(keyPair, new File("${project.projectDir.toString()}/.tmp/ssl/ssl.key"));
    }

    public void generatePGPKeyPair(String userId, String passphrase) throws Exception {
        PGPKeyRingGenerator generator = createPGPKeyRingGenerator(userId, passphrase.toCharArray());

        PGPPublicKeyRing pkr = generator.generatePublicKeyRing();
        ByteArrayOutputStream pubOut = new ByteArrayOutputStream();
        pkr.encode(pubOut);
        pubOut.close();

        PGPSecretKeyRing skr = generator.generateSecretKeyRing();
        ByteArrayOutputStream secOut = new ByteArrayOutputStream();
        skr.encode(secOut);
        secOut.close();

        byte[] armoredPublicBytes = armorByteArray(pubOut.toByteArray());
        byte[] armoredSecretBytes = armorByteArray(secOut.toByteArray());

        new File("${project.projectDir.toString()}/.tmp/pgp").mkdirs();
        File pubFile = new File("${project.projectDir.toString()}/.tmp/pgp/${userId}.pub");
        FileUtils.write(pubFile, new String(armoredPublicBytes), Charset.defaultCharset());

        File secFile = new File("${project.projectDir.toString()}/.tmp/pgp/${userId}.sec");
        FileUtils.write(secFile, new String(armoredSecretBytes), Charset.defaultCharset());
        Set<PosixFilePermission> perms = new HashSet<>();
        perms.add(PosixFilePermission.OWNER_READ);
        Files.setPosixFilePermissions(secFile.toPath(), perms);
    }

    public void generateConfIni() throws IOException {
        String s3AccessKey = readTrace("S3_ACCESS_KEY");
        String s3SecretKey = readTrace("S3_SECRET_KEY");
        String dbInstance = readTrace("DB_INSTANCE");
        String postgresUser = readTrace("POSTGRES_USER");
        String postgresPassword = readTrace("POSTGRES_PASSWORD");
        File confIni = new File("${project.projectDir.toString()}/.tmp/conf.ini");
        FileUtils.write(confIni, String.format("[DEFAULT]\n" +
                        "log = console\n" +
                        "\n" +
                        "[keyserver]\n" +
                        "port = 8443\n" +
                        "\n" +
                        "[quality_control]\n" +
                        "keyserver_endpoint = https://keys:8443/retrieve/%s/private\n" +
                        "\n" +
                        "[inbox]\n" +
                        "location = /ega/inbox/%s\n" +
                        "mode = 2750\n" +
                        "\n" +
                        "[vault]\n" +
                        "driver = S3Storage\n" +
                        "url = http://s3:9000\n" +
                        "access_key = %s\n" +
                        "secret_key = %s\n" +
                        "#region = lega\n" +
                        "\n" +
                        "\n" +
                        "[outgestion]\n" +
                        "# Just for test\n" +
                        "keyserver_endpoint = https://keys:8443/retrieve/%s/private\n" +
                        "\n" +
                        "## Connecting to Local EGA\n" +
                        "[broker]\n" +
                        "host = mq\n" +
                        "connection_attempts = 30\n" +
                        "# delay in seconds\n" +
                        "retry_delay = 10\n" +
                        "\n" +
                        "[postgres]\n" +
                        "host = %s\n" +
                        "user = %s\n" +
                        "password = %s\n" +
                        "try = 30\n" +
                        "\n" +
                        "[eureka]\n" +
                        "endpoint = http://cega-eureka:8761", s3AccessKey, s3SecretKey, dbInstance, postgresUser, postgresPassword),
                Charset.defaultCharset());
    }

    public void generateKeysIni() throws IOException {
        String pgpPassphrase = readTrace("PGP_PASSPHRASE");
        File keysIni = new File("${project.projectDir.toString()}/.tmp/keys.ini");
        FileUtils.write(keysIni, String.format("[DEFAULT]\n" +
                        "active : key.1\n" +
                        "\n" +
                        "[key.1]\n" +
                        "path : /etc/ega/pgp/ega.sec\n" +
                        "passphrase : %s\n" +
                        "expire: 30/MAR/19 08:00:00\n" +
                        "\n" +
                        "[key.2]\n" +
                        "path : /etc/ega/pgp/ega2.sec\n" +
                        "passphrase : %s\n" +
                        "expire: 30/MAR/18 08:00:00", pgpPassphrase, pgpPassphrase),
                Charset.defaultCharset());
    }

    public void encryptAES(File fileIn, File fileOut, String passphrase) throws NoSuchAlgorithmException, InvalidKeySpecException, NoSuchPaddingException, InvalidAlgorithmParameterException, InvalidKeyException, IOException, BadPaddingException, IllegalBlockSizeException {
        byte[] magicNumber = "Salted__".getBytes();
        String algorithm = "PBEWITHMD5AND256BITAES-CBC-OPENSSL";
        PBEKeySpec keySpec = new PBEKeySpec(passphrase.toCharArray());
        SecretKeyFactory factory = SecretKeyFactory.getInstance(algorithm);
        SecretKey key = factory.generateSecret(keySpec);

        Cipher cipher = Cipher.getInstance(algorithm);
        byte[] salt = new SecureRandom().generateSeed(8);
        cipher.init(Cipher.ENCRYPT_MODE, key, new PBEParameterSpec(salt, 1));

        byte[] encryptedContent = cipher.doFinal(FileUtils.readFileToByteArray(fileIn));

        ByteBuffer buffer = ByteBuffer.allocate(magicNumber.length + salt.length + encryptedContent.length);
        buffer.put(magicNumber);
        buffer.put(salt);
        buffer.put(encryptedContent);

        FileUtils.writeByteArrayToFile(fileOut, buffer.array());
    }

    public void generateFile() throws IOException {
        File rawFile = new File(".tmp/data.raw");
        RandomAccessFile randomAccessFile = new RandomAccessFile(rawFile, "rw");
        randomAccessFile.setLength(1024 * 1024 * 10);
        randomAccessFile.close();
    }

    public void encryptFile() throws IOException, PGPException, NoSuchAlgorithmException {
        File rawFile = new File(".tmp/data.raw");
        File encryptedFile = new File(".tmp/data.raw.enc");
        byte[] digest = DigestUtils.sha256(FileUtils.openInputStream(rawFile));
        String key = FileUtils.readFileToString(new File("lega/.tmp/pgp/ega.pub"), Charset.defaultCharset());
        FileOutputStream fileOutputStream = new FileOutputStream(encryptedFile);
        Crypt4GHOutputStream crypt4GHOutputStream = new Crypt4GHOutputStream(fileOutputStream, key, digest);
        FileUtils.copyFile(rawFile, crypt4GHOutputStream);
        crypt4GHOutputStream.close();
    }

    public void uploadFile() throws IOException {
        SSHClient ssh = new SSHClient();
        ssh.addHostKeyVerifier(new PromiscuousVerifier());
        ssh.connect("localhost", 2222);
        ssh.authPublickey("john", "cega/.tmp/users/john.sec");
        SFTPClient client = ssh.newSFTPClient();
        client.put(".tmp/data.raw.enc", "data.raw.enc");
        ssh.close();
    }

    public void ingestFile() throws NoSuchAlgorithmException, KeyManagementException, URISyntaxException, IOException, TimeoutException {
        ConnectionFactory factory = new ConnectionFactory();
        String mqPassword = readTrace(new File("cega/.tmp/.trace"), "CEGA_MQ_PASSWORD");
        factory.setUri(String.format("amqp://lega:%s@localhost:5672/lega", mqPassword));
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

    public int getFilesAmount() throws XmlPullParserException, IOException, InvalidPortException, InvalidEndpointException, InsufficientDataException, NoSuchAlgorithmException, NoResponseException, InternalException, InvalidKeyException, InvalidBucketNameException, ErrorResponseException {
        String accessKey = readTrace(new File("lega/.tmp/.trace"), "S3_ACCESS_KEY");
        String secretKey = readTrace(new File("lega/.tmp/.trace"), "S3_SECRET_KEY");
        MinioClient minioClient = new MinioClient("http://localhost:9000", accessKey, secretKey);
        if (!minioClient.bucketExists("lega")) {
            return 0;
        }
        return IterableUtils.size(minioClient.listObjects("lega"));
    }

}
