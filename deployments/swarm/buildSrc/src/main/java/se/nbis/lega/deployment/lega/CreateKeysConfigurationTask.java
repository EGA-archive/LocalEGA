package se.nbis.lega.deployment.lega;

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
import org.gradle.api.tasks.TaskAction;
import se.nbis.lega.deployment.Groups;
import se.nbis.lega.deployment.LocalEGATask;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.attribute.PosixFilePermission;
import java.security.*;
import java.security.cert.CertificateException;
import java.security.cert.X509Certificate;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.Date;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

public class CreateKeysConfigurationTask extends LocalEGATask {

    public CreateKeysConfigurationTask() {
        super();
        this.setGroup(Groups.LEGA.name());
    }

    @TaskAction
    public void run() throws Exception {
        getProject().file(".tmp/ssl/").mkdirs();
        getProject().file(".tmp/pgp/").mkdirs();
        generateSSLCertificate();
        createConfig(Config.SSL_CERT.getName(), getProject().file(".tmp/ssl/ssl.cert"));
        createConfig(Config.SSL_KEY.getName(), getProject().file(".tmp/ssl/ssl.key"));
        String pgpPassphrase = UUID.randomUUID().toString().replace("-", "");
        generatePGPKeyPair("ega", pgpPassphrase);
        createConfig(Config.EGA_SEC.getName(), getProject().file(".tmp/pgp/ega.sec"));
        generatePGPKeyPair("ega2", pgpPassphrase);
        createConfig(Config.EGA2_SEC.getName(), getProject().file(".tmp/pgp/ega2.sec"));
        writeTrace("PGP_PASSPHRASE", pgpPassphrase);
        String masterPassphrase = UUID.randomUUID().toString().replace("-", "");
        writeTrace("LEGA_PASSWORD", masterPassphrase);
    }

    private void generateSSLCertificate() throws IOException, CertificateException, OperatorCreationException, NoSuchProviderException, NoSuchAlgorithmException {
        KeyPairGenerator keyPairGenerator = KeyPairGenerator.getInstance("RSA");
        keyPairGenerator.initialize(4096, new SecureRandom());
        KeyPair keyPair = keyPairGenerator.genKeyPair();

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

        FileWriter fileWriter = new FileWriter(getProject().file(".tmp/ssl/ssl.cert"));
        JcaPEMWriter pemWriter = new JcaPEMWriter(fileWriter);
        pemWriter.writeObject(x509);
        pemWriter.close();

        writePrivateKey(keyPair, getProject().file(".tmp/ssl/ssl.key"));
    }

    private void generatePGPKeyPair(String userId, String passphrase) throws Exception {
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

        File pubFile = getProject().file(String.format(".tmp/pgp/%s.pub", userId));
        FileUtils.write(pubFile, new String(armoredPublicBytes), Charset.defaultCharset());

        File secFile = getProject().file(String.format(".tmp/pgp/%s.sec", userId));
        FileUtils.write(secFile, new String(armoredSecretBytes), Charset.defaultCharset());
        Set<PosixFilePermission> perms = new HashSet<>();
        perms.add(PosixFilePermission.OWNER_READ);
        Files.setPosixFilePermissions(secFile.toPath(), perms);
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

}
