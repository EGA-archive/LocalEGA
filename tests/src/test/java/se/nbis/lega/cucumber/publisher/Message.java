package se.nbis.lega.cucumber.publisher;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.NoArgsConstructor;

@NoArgsConstructor
@Data
public class Message {

  @JsonProperty("user")
  private String user;

  @JsonProperty("filepath")
  private String filepath;

  @JsonProperty("stable_id")
  private String stableID;

  @JsonProperty("encrypted_integrity")
  private Checksum encryptedIntegrity;

  @JsonProperty("unencrypted_integrity")
  private Checksum unencryptedIntegrity;

}
