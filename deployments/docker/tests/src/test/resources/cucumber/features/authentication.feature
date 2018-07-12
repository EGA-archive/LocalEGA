Feature: Authentication
  As a user I want to be able to authenticate against LocalEGA inbox

  Scenario: A.0 User exists in Central EGA and uses correct private key for authentication for the correct instance
    Given I have an account at Central EGA
    And I have correct private key
    When I connect to the LocalEGA inbox via SFTP using private key
    Then I'm logged in successfully

  Scenario: A.1 User doesn't exist in Central EGA, but tries to authenticate against LocalEGA inbox
    And I have correct private key
    When I connect to the LocalEGA inbox via SFTP using private key
    Then authentication fails

  Scenario: A.2 User exists in Central EGA, but uses incorrect private key for authentication
    Given I have an account at Central EGA
    But I have incorrect private key
    When I connect to the LocalEGA inbox via SFTP using private key
    Then authentication fails

#  TODO: Add cache expiry scenario.

#  Scenario: A.3 User exists in Central EGA and tries to connect to LocalEGA, but the inbox was not created for him
#    Given I have an account at Central EGA
#    And I have correct private key
#    And I connect to the LocalEGA inbox via SFTP using private key
#    And I disconnect from the LocalEGA inbox
#    And inbox is deleted for my user
#    When I connect to the LocalEGA inbox via SFTP using private key
#    Then authentication fails

