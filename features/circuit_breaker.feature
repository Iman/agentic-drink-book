@offline
Feature: Provider circuit breaking
  Repeated failures stop calls temporarily, while a single probe checks recovery.

  Scenario: Open circuit rejects work without contacting the provider
    Given a provider circuit with a failure threshold of two
    When the provider fails twice
    And another call is attempted
    Then the circuit is "open"
    And exactly two provider calls were made

  Scenario: A successful probe restores service after cooldown
    Given a provider circuit with a failure threshold of two
    When the provider fails twice
    And the cooldown expires
    And the provider succeeds
    Then the circuit is "closed"

  Scenario: Excessive latency cancels a provider call
    Given a provider circuit with a short deadline
    When the provider exceeds the deadline
    Then the circuit is "open"
    And no provider slot remains occupied
