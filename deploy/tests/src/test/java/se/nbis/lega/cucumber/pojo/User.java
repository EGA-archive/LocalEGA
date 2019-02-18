package se.nbis.lega.cucumber.pojo;

import lombok.Data;

@Data
public class User {

    private String username;
    private int uid;
    private String passwordHash;
    private String gecos;
    private String sshPublicKey;
    private Boolean enabled;

}
