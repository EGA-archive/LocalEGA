package se.nbis.lega.cucumber.publisher;

import lombok.Data;
import lombok.NoArgsConstructor;

@NoArgsConstructor
@Data
public class Checksum {

  String hash;

  String algorithm;

}
