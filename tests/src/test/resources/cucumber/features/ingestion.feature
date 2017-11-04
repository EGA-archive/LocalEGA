Feature: Ingestion
  As a user I want to be able to ingest files from the LocalEGA inbox

  Scenario: Ingest files from the LocalEGA inbox
    Given I am a user
    And I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have an encrypted file
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    When I ingest file from the LocalEGA inbox
    Then the file is ingested successfully
