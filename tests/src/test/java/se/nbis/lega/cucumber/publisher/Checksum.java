package se.nbis.lega.cucumber.publisher;

import lombok.Data;
import lombok.NoArgsConstructor;

@NoArgsConstructor
@Data
public class Checksum {

  private String hash;

  private String algorithm;

}
