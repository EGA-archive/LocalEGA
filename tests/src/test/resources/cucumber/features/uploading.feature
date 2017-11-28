Feature: Uploading
  As a user I want to be able to upload files to the LocalEGA inbox

  Scenario: Upload files to the LocalEGA inbox
    Given I am a user of LocalEGA instances:
      | swe1 |
    And I have an account at Central EGA
    And I want to work with instance "swe1"
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I have a file encrypted with OpenPGP using a "swe1" key
    When I upload encrypted file to the LocalEGA inbox via SFTP
    Then the file is uploaded successfully
