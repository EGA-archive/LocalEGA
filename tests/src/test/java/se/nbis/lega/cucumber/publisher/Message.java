package se.nbis.lega.cucumber.publisher;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.NoArgsConstructor;

@NoArgsConstructor
@Data
public class Message {

  @JsonProperty("elixir_id")
  private String elixirId;

  private String filename;

  @JsonProperty("encrypted_integrity")
  private Checksum encryptedIntegrity;

  @JsonProperty("unencrypted_integrity")
  private Checksum unencryptedIntegrity;

}
