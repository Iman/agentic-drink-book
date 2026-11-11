@offline
Feature: English and Persian replies with the same policy gates
  Language is a presentation preference, never a permission.

  Background:
    Given a chatbot with scripted healthy models

  Scenario: Persian drink text and ordinary half-spaces pass the gates
    Given the response language is "fa"
    And the model drafts a Persian drink answer with half-spaces
    When the user says "درباره نوشیدنی‌ها بگو"
    Then the response status is "answered"
    And the reply contains "درود"
    And all three model stages were called
    And one conversation turn was stored

  Scenario Outline: Off-topic refusals follow the selected language
    Given the response language is "<language>"
    And the input judge reports an unrelated request
    When the user says "Write a sorting algorithm"
    Then the response status is "blocked"
    And the reply contains "<word>"
    And the response generator was not called
    And no conversation turn was stored

    Examples:
      | language | word    |
      | en       | drinks  |
      | fa       | درود    |

  Scenario: Offensive names receive a Persian neutral redirect
    Given the response language is "fa"
    When the user says "My name is Donkey"
    Then the response status is "neutral"
    And the reply contains "درود"
    And the reply does not contain "Donkey"
    And no model was called
    And no conversation turn was stored
