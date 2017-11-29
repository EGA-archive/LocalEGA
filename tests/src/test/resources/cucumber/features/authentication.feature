Feature: Authentication
  As a user I want to be able to authenticate against LocalEGA inbox

  Background:
    Given I am a user of LocalEGA instances:
      | swe1 |

  Scenario: U.0 User population in LocalEGA DB from Central EGA
    Given I have an account at Central EGA
    And I want to work with instance "swe1"
    And I have correct private key
    When I connect to the LocalEGA inbox via SFTP using private key
    Then I am in the local database

  Scenario: U.1 User doesn't exist in Central EGA, but tries to authenticate against LocalEGA inbox
    Given I want to work with instance "swe1"
    And I have correct private key
    When I connect to the LocalEGA inbox via SFTP using private key
    Then authentication fails

  Scenario: U.2 User exists in Central EGA and uses correct private key for authentication, but the wrong instance
    Given I have an account at Central EGA
    And I want to work with instance "fin1"
    And I have correct private key
    When I connect to the LocalEGA inbox via SFTP using private key
    Then authentication fails

  Scenario: U.3 User exists in Central EGA, but his account has expired
    Given I have an account at Central EGA
    And I want to work with instance "swe1"
    And I have correct private key
    When my account expires
    Then I am not in the local database

  Scenario: U.4 User exists in Central EGA, but uses incorrect private key for authentication
    Given I have an account at Central EGA
    And I want to work with instance "swe1"
    And I have incorrect private key
    When I connect to the LocalEGA inbox via SFTP using private key
    Then authentication fails

  Scenario: U.5 User exists in Central EGA and tries to connect to LocalEGA, but the inbox was not created for him
    Given I have an account at Central EGA
    And I want to work with instance "swe1"
    And I have correct private key
    And I connect to the LocalEGA inbox via SFTP using private key
    And I disconnect from the LocalEGA inbox
    And inbox is deleted for my user
    When I connect to the LocalEGA inbox via SFTP using private key
    Then authentication fails

  Scenario: U.6 User exists in Central EGA and uses correct private key for authentication for the correct instance, but database is down
    Given I have an account at Central EGA
    And I want to work with instance "swe1"
    And I have correct private key
    And the database connectivity is broken
    When I connect to the LocalEGA inbox via SFTP using private key
    Then authentication fails

  Scenario: U.7 User exists in Central EGA and uses correct private key for authentication for the correct instance
    Given I have an account at Central EGA
    And I want to work with instance "swe1"
    And I have correct private key
    When I connect to the LocalEGA inbox via SFTP using private key
    Then I'm logged in successfully
