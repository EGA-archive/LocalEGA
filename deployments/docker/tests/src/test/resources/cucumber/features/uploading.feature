Feature: Uploading
  As a user I want to be able to upload files to the LocalEGA inbox

  Background:
    Given My username is "test"

  Scenario: U.0 Upload files to the LocalEGA inbox
    Given I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with OpenPGP using a LocalEGA's pubic key
    When I upload encrypted file to the LocalEGA inbox via SFTP
    Then the file is uploaded successfully
