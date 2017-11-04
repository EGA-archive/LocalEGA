Feature: Uploading
  As a user I want to be able to upload files to the LocalEGA inbox

  Scenario: Upload files to the LocalEGA inbox
    Given I am a user
    And I have an account at Central EGA
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have an encrypted file
    When I upload encrypted file to the LocalEGA inbox via SFTP
    Then the file is uploaded successfully