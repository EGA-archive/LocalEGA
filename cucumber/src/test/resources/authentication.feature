Feature: Authentication
  As a user I want to be able to authenticate against LocalEGA inbox

  Scenario: Authenticate against LocalEGA inbox using private key
    Given I have a private key
    When I try to connect to the LocalEGA inbox via SFTP using private key
    Then the operation is successful