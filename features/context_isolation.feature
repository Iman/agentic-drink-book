@offline
Feature: Context ownership and shared data
  Host-authenticated identities determine access; messages and models cannot grant it.

  Background:
    Given a chatbot with scripted healthy models

  Scenario: Another user cannot resume a conversation
    When another user attempts to use the conversation
    Then the response status is "denied"
    And no model was called

  Scenario: Shared context requires a publisher
    When an ordinary user attempts to publish shared context
    Then publishing is denied
    And no model was called

  Scenario: Shared context stays within its audience and tenant
    Given a publisher shares a document with the original user
    Then the original user can read the shared document
    And another user cannot read the shared document
    And the same subject in another tenant cannot read the shared document

  Scenario: Repeated requests are rate limited
    Given a one-request-per-minute policy
    When the user says "Hello"
    And the user says "Hello again"
    Then the response reason is "rate_limited"
