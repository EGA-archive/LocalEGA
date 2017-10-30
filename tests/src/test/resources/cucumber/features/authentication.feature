Feature: Authentication
  As a user I want to be able to authenticate against LocalEGA inbox

  Scenario: Authenticate against LocalEGA inbox using private key
    Given I am a user "john"
    And I have a private key
    When I connect to the LocalEGA inbox via SFTP using private key
    Then I'm logged in successfully