@offline
Feature: Bounded specialist routing and advisory audit
  Scripted observations test enforcement, not model judgment accuracy.

  Background:
    Given a chatbot with scripted healthy models

  Scenario Outline: One specialist works inside the safety gates
    Given the input judge selects "<specialist>"
    When the user says "<question>"
    Then the response status is "answered"
    And only the "<specialist>" specialist was called
    And all three model stages were called
    And one conversation turn was stored

    Examples:
      | specialist | question                                      |
      | mixing     | How do I mix a Negroni?                       |
      | production | How do I make wine and use it in a cocktail? |
      | mixing     | نوشیدنی را با چه نوع یخی سرو کنم؟             |
      | production | شراب را چطور تهیه کنم؟                       |

  Scenario: A model cannot route directly to memory commit
    Given the input judge selects "commit"
    When the user says "A drink question"
    Then the response status is "unavailable"
    And the response generator was not called
    And no conversation turn was stored

  Scenario: A production draft still needs output approval
    Given the input judge selects "production"
    And the output judge reports an unsafe draft
    When the user says "How is wine made?"
    Then the response status is "blocked"
    And the reply does not contain "UNRELEASED"
    And no conversation turn was stored

  Scenario Outline: Post-run audit cannot alter the completed turn
    Given the auditor returns "<kind>" evidence
    When the user says "How do I mix a drink?"
    And the completed synthetic turn is audited
    Then the audit status is "<status>"
    And the response status is "answered"
    And one conversation turn was stored

    Examples:
      | kind    | status          |
      | clear   | clear           |
      | concern | review_required |
      | invalid | unavailable     |
