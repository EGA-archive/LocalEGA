Feature: Ingestion
  As a user I want to be able to ingest files from the LocalEGA inbox

  Scenario: I.0 User ingests file encrypted with Crypt4GH using a correct key
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a 1 MB file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I ingest file from the LocalEGA inbox
    When I retrieve ingestion information
    Then the ingestion status is "COMPLETED"

  Scenario: I.1 User ingests big file encrypted with Crypt4GH using a correct key
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a 1024 MB file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I ingest file from the LocalEGA inbox
    When I retrieve ingestion information
    Then the ingestion status is "COMPLETED"

  Scenario: I.2 User ingests file encrypted not with Crypt4GH
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted not with Crypt4GH
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I ingest file from the LocalEGA inbox
    When I retrieve ingestion information
    Then the ingestion status is "ERROR"

  Scenario: I.3 User ingests file encrypted with Crypt4GH, but file was not found in the inbox
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a 1 MB file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And file is removed from the inbox
    And I ingest file from the LocalEGA inbox
    When I retrieve ingestion information
    Then the ingestion status is "ERROR"
