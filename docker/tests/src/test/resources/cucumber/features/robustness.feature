Feature: Robustness
  As a user I want the system to be robust and fault-tolerant

  Scenario: R.0 User ingests file encrypted with Crypt4GH using a correct key and providing checksums as companion files after full system restart
    Given I have an account at Central EGA
    And I have correct private key
    And the system is restarted
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a 1 MB file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I ingest file from the LocalEGA inbox
    When I retrieve ingestion information
    Then the ingestion status is "COMPLETED"

  Scenario: R.1 User ingests big file encrypted with Crypt4GH using a correct key
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a 1024 MB file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I ingest file from the LocalEGA inbox
    When I retrieve ingestion information
    Then the ingestion status is "COMPLETED"
