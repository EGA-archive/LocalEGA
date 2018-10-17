Feature: Outgestion
  As a user I want to be able to retrieve files from the LocalEGA

  Scenario: O.0 User retrieves the file, previously ingested with Crypt4GH format
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a 1 MB file encrypted with Crypt4GH using a LocalEGA's pubic key
    And I upload encrypted file to the LocalEGA inbox via SFTP
    And I have CEGA MQ username and password
    And I ingest file from the LocalEGA inbox
    And I retrieve ingestion information
    When I download archived file
    Then checksums of raw and downloaded files match
