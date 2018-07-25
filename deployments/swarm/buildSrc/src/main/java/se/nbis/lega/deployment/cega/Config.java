package se.nbis.lega.deployment.cega;

public enum Config {

    DEFS_JSON("cega.defs.json"),
    RABBITMQ_CONFIG("cega.rabbitmq.config"),
    EUREKA_PY("eureka.py"),
    SERVER_PY("server.py"),
    USERS_HTML("users.html"),
    JOHN_YML("john.yml"),
    JANE_YML("jane.yml");

    private String name;

    Config(String name) {
        this.name = name;
    }

    public String getName() {
        return name;
    }

}
