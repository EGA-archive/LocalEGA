Feature: Robustness
  As a user I want the system to be robust and fault-tolerant

  Scenario: R.0 User ingests file encrypted with OpenPGP using a correct key and providing checksums as companion files after full system restart
    Given I am a user of LocalEGA instances:
      | swe1 |
    And I have an account at Central EGA
    And I want to work with instance "swe1"
    And I have correct private key
    And the system is restarted
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with OpenPGP using a "swe1" key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I upload companion files to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I ingest file from the LocalEGA inbox without providing checksums
    When I retrieve ingestion information
    Then the ingestion status is "Archived"
    And the raw checksum matches
    And the encrypted checksum matches
    And and the file header matches
#
#  Scenario: R.2 User ingests a big file encrypted with OpenPGP using a correct key and providing checksums as companion files
#    Given I am a user of LocalEGA instances:
#      | swe1 |
#    And I have an account at Central EGA
#    And I want to work with instance "swe1"
#    And I have correct private key
#    And I connect to the LocalEGA inbox via SFTP using private key
#    And I have a big file encrypted with OpenPGP using a "swe1" key
#    And I upload encrypted file to the LocalEGA inbox via SFTP
#    And I upload companion files to the LocalEGA inbox via SFTP
#    And I have CEGA MQ username and password
#    And I ingest file from the LocalEGA inbox without providing checksums
#    When I retrieve ingestion information
#    Then the ingestion status is "Archived"
#    And the raw checksum matches
#    And the encrypted checksum matches
#    And and the file header matches