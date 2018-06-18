Feature: Checksumming
  Deprecated, keeping it around just in case

#  Scenario: User ingests file encrypted with Crypt4GH using a correct key, but raw checksum doesn't match with the supplied one
#    Given I have an account at Central EGA
#    And I have correct private key
#    And I connect to the LocalEGA inbox via SFTP using private key
#    And I have a file encrypted with Crypt4GH using a LocalEGA's pubic key
#    And I upload encrypted file to the LocalEGA inbox via SFTP
#    And I have CEGA MQ username and password
#    And I ingest file from the LocalEGA inbox using wrong raw checksum
#    When I retrieve ingestion information
#    Then the ingestion status is "Error"

#  Scenario: User ingests file encrypted with Crypt4GH using a correct key, but encrypted checksum doesn't match with the supplied one
#    Given I have an account at Central EGA
#    And I have correct private key
#    And I connect to the LocalEGA inbox via SFTP using private key
#    And I have a file encrypted with Crypt4GH using a LocalEGA's pubic key
#    And I upload encrypted file to the LocalEGA inbox via SFTP
#    And I have CEGA MQ username and password
#    And I ingest file from the LocalEGA inbox using wrong encrypted checksum
#    When I retrieve ingestion information
#    Then the ingestion status is "Error"

#  Scenario: User ingests file encrypted with Crypt4GH using a correct key, but raw checksum isn't provided
#    Given I have an account at Central EGA
#    And I have correct private key
#    And I connect to the LocalEGA inbox via SFTP using private key
#    And I have a file encrypted with Crypt4GH using a LocalEGA's pubic key
#    And I upload encrypted file to the LocalEGA inbox via SFTP
#    And I have CEGA MQ username and password
#    And I ingest file from the LocalEGA inbox without providing raw checksum
#    When I retrieve ingestion information
#    Then the ingestion status is "Error"

#  Scenario: User ingests file encrypted with Crypt4GH using a correct key, but encrypted checksum isn't provided
#    Given I have an account at Central EGA
#    And I have correct private key
#    And I connect to the LocalEGA inbox via SFTP using private key
#    And I have a file encrypted with Crypt4GH using a LocalEGA's pubic key
#    And I upload encrypted file to the LocalEGA inbox via SFTP
#    And I have CEGA MQ username and password
#    And I ingest file from the LocalEGA inbox without providing encrypted checksum
#    When I retrieve ingestion information
#    Then the ingestion status is "Error"

#  Scenario: User ingests file encrypted with Crypt4GH using a correct key and providing checksums as companion files
#    Given I have an account at Central EGA
#    And I have correct private key
#    And I connect to the LocalEGA inbox via SFTP using private key
#    And I have a file encrypted with Crypt4GH using a LocalEGA's pubic key
#    And I upload encrypted file to the LocalEGA inbox via SFTP
#    And I upload companion files to the LocalEGA inbox via SFTP
#    And I have CEGA MQ username and password
#    And I ingest file from the LocalEGA inbox without providing checksums
#    When I retrieve ingestion information
#    Then the ingestion status is "Completed"
