Feature: Authentication
  As a user I want to be able to authenticate against LocalEGA inbox

  Scenario: User population in LocalEGA DB from Central EGA
    Given I am a user
    And I have an account at Central EGA
    And I have correct private key
    When I connect to the LocalEGA inbox via SFTP using private key
    Then I am in the local database

  Scenario: User doesn't exist in Central EGA, but tries to authenticate against LocalEGA inbox
    Given I am a user
    And I have correct private key
    When I connect to the LocalEGA inbox via SFTP using private key
    Then authentication fails

  Scenario: User exists in Central EGA, but uses incorrect private key for authentication
    Given I am a user
    And I have an account at Central EGA
    And I have incorrect private key
    When I connect to the LocalEGA inbox via SFTP using private key
    Then authentication fails

  Scenario: User exists in Central EGA, but his account has expired
    Given I am a user
    And I have an account at Central EGA
    And I have correct private key
    When my account expires
    Then I am not in the local database

  Scenario: User exists in Central EGA and uses correct private key for authentication
    Given I am a user
    And I have an account at Central EGA
    And I have correct private key
    When I connect to the LocalEGA inbox via SFTP using private key
    Then I'm logged in successfully