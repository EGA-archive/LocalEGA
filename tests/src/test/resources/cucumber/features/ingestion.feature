Feature: Ingestion
  As a user I want to be able to ingest files from the LocalEGA inbox

  Scenario: User ingests file encrypted with OpenPGP
    Given I am a user of LocalEGA instances:
      | swe1 |
    And I have an account at Central EGA
    And I want to work with instance "swe1"
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with OpenPGP
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    When I ingest file from the LocalEGA inbox
    Then the file is ingested successfully

  Scenario: User ingests file encrypted not with OpenPGP
    Given I am a user of LocalEGA instances:
      | swe1 |
    And I have an account at Central EGA
    And I want to work with instance "swe1"
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted not with OpenPGP
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    When I ingest file from the LocalEGA inbox
    Then ingestion failed
