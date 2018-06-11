Feature: Ingestion
  As a user I want to be able to ingest files from the LocalEGA inbox

  Background:
    Given My username is "test"

  Scenario Outline: I.0 User ingests file encrypted with OpenPGP using a correct key
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I ingest file from the LocalEGA inbox using correct <algo> checksums
    When I retrieve ingestion information
    Then the ingestion status is "Archived"

    Examples:
      | algo   |
      | MD5    |
      | SHA256 |

  Scenario: I.1 User ingests file encrypted not with OpenPGP
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted not with Crypt4GH
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I ingest file from the LocalEGA inbox using correct MD5 checksums
    When I retrieve ingestion information
    Then the ingestion status is "Error"

  Scenario: I.3 User ingests file encrypted with OpenPGP, but inbox is not created
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And inbox is deleted for my user
    And I ingest file from the LocalEGA inbox using correct MD5 checksums
    When I retrieve ingestion information
    Then the ingestion status is "Error"

  Scenario: I.4 User ingests file encrypted with OpenPGP, but file was not found in the inbox
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And file is removed from the inbox
    And I ingest file from the LocalEGA inbox using correct MD5 checksums
    When I retrieve ingestion information
    Then the ingestion status is "Error"

  Scenario: I.5 User ingests file encrypted with OpenPGP using a correct key, but raw checksum doesn't match with the supplied one
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I ingest file from the LocalEGA inbox using wrong raw checksum
    When I retrieve ingestion information
    Then the ingestion status is "Error"

  Scenario: I.6 User ingests file encrypted with OpenPGP using a correct key, but encrypted checksum doesn't match with the supplied one
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I ingest file from the LocalEGA inbox using wrong encrypted checksum
    When I retrieve ingestion information
    Then the ingestion status is "Error"

  Scenario: I.7 User ingests file encrypted with OpenPGP using a correct key, but raw checksum isn't provided
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I ingest file from the LocalEGA inbox without providing raw checksum
    When I retrieve ingestion information
    Then the ingestion status is "Error"

  Scenario: I.8 User ingests file encrypted with OpenPGP using a correct key, but encrypted checksum isn't provided
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I ingest file from the LocalEGA inbox without providing encrypted checksum
    When I retrieve ingestion information
    Then the ingestion status is "Error"

  Scenario: I.9 User ingests file encrypted with OpenPGP using a correct key and providing checksums as companion files
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I upload companion files to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I ingest file from the LocalEGA inbox without providing checksums
    When I retrieve ingestion information
    Then the ingestion status is "Archived"

  Scenario: I.10 User ingests file encrypted with OpenPGP using a correct key and checksums, but the keyserver doesn't respond
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I upload companion files to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I turn off the keyserver
    And I ingest file from the LocalEGA inbox without providing checksums
    And I turn on the keyserver
    When I retrieve ingestion information
    Then the ingestion status is "Error"

  Scenario: I.13 User ingests file encrypted with OpenPGP using a correct key and checksums, but the vault listener is down
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I upload companion files to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I turn off the vault listener
    And I ingest file from the LocalEGA inbox without providing checksums
    And I turn on the vault listener
    When I retrieve ingestion information
    Then the ingestion status is "NoEntry"

  Scenario: I.15 User ingests file encrypted with OpenPGP using a correct key and checksums, but the database doesn't respond
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I upload companion files to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I turn off the database
    And I ingest file from the LocalEGA inbox without providing checksums
    And I turn on the database
    When I retrieve ingestion information
    Then the ingestion status is "NoEntry"