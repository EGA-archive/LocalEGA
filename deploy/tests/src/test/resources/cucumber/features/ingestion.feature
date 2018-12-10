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

  Scenario: I.1 User ingests file encrypted not with Crypt4GH
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted not with Crypt4GH
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I ingest file from the LocalEGA inbox
    When I retrieve ingestion information
    Then the ingestion status is "ERROR"

  Scenario: I.2 User ingests file encrypted with Crypt4GH, but file was not found in the inbox
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

  Scenario: I.3 User ingests file encrypted with Crypt4GH using a correct key and checksums, but the keyserver doesn't respond
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a 1 MB file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I turn off the keyserver
    And I ingest file from the LocalEGA inbox
    And I turn on the keyserver
    When I retrieve ingestion information
    Then the ingestion status is "ERROR"

  Scenario: I.4 User ingests file encrypted with Crypt4GH using a correct key and checksums, but the message broker is down
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a 1 MB file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I turn off the message broker
    And I ingest file from the LocalEGA inbox
    And I turn on the message broker
    When I retrieve ingestion information
    Then the ingestion status is "NoEntry"

  Scenario: I.5 User ingests file encrypted with Crypt4GH using a correct key and checksums, but the database doesn't respond
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a 1 MB file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I turn off the database
    And I ingest file from the LocalEGA inbox
    And I turn on the database
    When I retrieve ingestion information
    Then the ingestion status is "NoEntry"
