Test suite
===================

![enter image description here](https://www.javacodegeeks.com/wp-content/uploads/2015/04/cucumber-strip.png)

Our tests are written with [Cucumber framework](https://cucumber.io/) and they help us to maintain stable behaviour of the system using human-readable scenarios.

----------

Syntax
-------------

Cucumber tests use [Gherkin](https://cucumber.io/docs/reference) syntax for describing scenarios of the application:

> Gherkin is plain-text English (or one of 60+ other languages) with a little extra structure. Gherkin is designed to be easy to learn by non-programmers, yet structured enough to allow concise description of examples to illustrate business rules in most real-world domains.

#### Example

```gherkin
Feature: Authentication
  As a user I want to be able to authenticate against LocalEGA inbox

  Scenario: Authenticate against LocalEGA inbox using private key
    Given I am a user "john"
    And I have a private key
    When I connect to the LocalEGA inbox via SFTP using private key
    Then I'm logged in successfully
```

----------


Mapping
-------------------

Next step is about mapping Gherkin scenarios to executable code. Currently we use Java 8 to actually run tests-logic.

#### Example

```java
        Given("^I am a user \"([^\"]*)\"$", (String user) -> this.user = user);

        Given("^I have a private key$",
                () -> privateKey = new File(Paths.get("").toAbsolutePath().getParent().toString() + String.format("deployments/docker/bootstrap/private/cega/users/%s.sec", user)));

        When("^I connect to the LocalEGA inbox via SFTP using private key$", () -> {
            try {
                SSHClient ssh = new SSHClient();
                ssh.addHostKeyVerifier(new PromiscuousVerifier());
                ssh.connect("localhost", 2222);
                ssh.authPublickey(user, privateKey.getPath());
                sftp = ssh.newSFTPClient();
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });

        Then("^I'm logged in successfully$", () -> {
            try {
                Assert.assertEquals("inbox", sftp.ls("/").iterator().next().getName());
            } catch (IOException e) {
                log.error(e.getMessage(), e);
                Assert.fail(e.getMessage());
            }
        });
```

----------


Execution
-------------

Test-suite is executed using Maven: `mvn clean test` from within the `tests` folder. Note that you obviously need to have LocalEGA up and running locally in order to execute the tests.

#### Example

```
Feature: Uploading
  As a user I want to be able to upload files to the LocalEGA inbox
  
  Scenario: Upload files to the LocalEGA inbox                     # src/test/resources/cucumber/features/uploading.feature:4
    Given I am a user "john"                                       # Definitions.java:55
    And I have a private key                                       # Definitions.java:57
    And I connect to the LocalEGA inbox via SFTP using private key # Definitions.java:60
    And I have an encrypted file                                   # Definitions.java:82
    When I upload encrypted file to the LocalEGA inbox via SFTP    # Definitions.java:106
    Then the file is uploaded successfully                         # Definitions.java:115

1 Scenarios (1 passed)
6 Steps (6 passed)
0m2.609s
```

----------


Automation
--------------------

We've created the CI pipeline in order to automate test execution and maintain stability of the build. The job can be found here: https://travis-ci.org/NBISweden/LocalEGA

Flow
--------------------

Behavior-driven development is a software development methodology which essentially states that for each feature of software, a software developer must:
 - define a scenarios set for the feature first; 
 - make the scenarios fail; 
 - then implement the feature; 
 - finally verify that the implementation of the feature makes the scenarios succeed.

So *ideally* one should always contribute new functionality along with a correspondent implemented test-case.
