Feature: Robustness
  As a user I want the system to be robust and fault-tolerant

  Scenario: R.0 User ingests file encrypted with Crypt4GH using a correct key, but the keyserver doesn't respond
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

  Scenario: R.1 User ingests file encrypted with Crypt4GH using a correct key, but the message broker is down
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

  Scenario: R.2 User ingests file encrypted with Crypt4GH using a correct key, but the database doesn't respond
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
