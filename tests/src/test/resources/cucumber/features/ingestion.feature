Feature: Ingestion
  As a user I want to be able to ingest files from the LocalEGA inbox

  Scenario: F.0 User ingests file encrypted with OpenPGP using a correct key
    Given I am a user of LocalEGA instances:
      | swe1 |
    And I have an account at Central EGA
    And I want to work with instance "swe1"
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with OpenPGP using a "swe1" key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    When I ingest file from the LocalEGA inbox using correct encrypted checksum
    Then the file is ingested successfully

  Scenario: F.1 User ingests file encrypted not with OpenPGP
    Given I am a user of LocalEGA instances:
      | swe1 |
    And I have an account at Central EGA
    And I want to work with instance "swe1"
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted not with OpenPGP
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    When I ingest file from the LocalEGA inbox using correct encrypted checksum
    Then ingestion failed

  Scenario: F.2 User ingests file encrypted with OpenPGP using a wrong key
    Given I am a user of LocalEGA instances:
      | swe1 |
    And I have an account at Central EGA
    And I want to work with instance "swe1"
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with OpenPGP using a "fin1" key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    When I ingest file from the LocalEGA inbox using correct encrypted checksum
    Then ingestion failed

  Scenario: F.3 User ingests file encrypted with OpenPGP, but inbox is not created
    Given I am a user of LocalEGA instances:
      | swe1 |
    And I have an account at Central EGA
    And I want to work with instance "swe1"
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with OpenPGP using a "swe1" key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And inbox is deleted for my user
    When I ingest file from the LocalEGA inbox using correct encrypted checksum
    Then ingestion failed

  Scenario: F.4 User ingests file encrypted with OpenPGP, but file was not found in the inbox
    Given I am a user of LocalEGA instances:
      | swe1 |
    And I have an account at Central EGA
    And I want to work with instance "swe1"
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with OpenPGP using a "swe1" key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And file is removed from the inbox
    When I ingest file from the LocalEGA inbox using correct encrypted checksum
    Then ingestion failed

  Scenario: F.5 User ingests file encrypted with OpenPGP using a correct key, but its checksum doesn't match with the supplied one
    Given I am a user of LocalEGA instances:
      | swe1 |
    And I have an account at Central EGA
    And I want to work with instance "swe1"
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with OpenPGP using a "swe1" key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    When I ingest file from the LocalEGA inbox using wrong encrypted checksum
    Then ingestion failed
