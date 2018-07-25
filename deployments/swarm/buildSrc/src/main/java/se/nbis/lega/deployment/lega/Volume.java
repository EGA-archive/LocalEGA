package se.nbis.lega.deployment.lega;

public enum Volume {

    LEGA_INBOX("lega_inbox"),
    LEGA_S3("lega_s3"),
    LEGA_PORTAINER("lega_portainer");

    private String name;

    Volume(String name) {
        this.name = name;
    }

    public String getName() {
        return name;
    }

}
