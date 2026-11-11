@offline
Feature: Drinks-only conversations
  Deterministic acceptance tests use scripted observations.
  Live model accuracy is evaluated separately.

  Background:
    Given a chatbot with scripted healthy models

  Scenario Outline: Drink production and cocktail questions pass the gates
    When the user says "<question>"
    Then the response status is "answered"
    And all three model stages were called
    And one conversation turn was stored

    Examples:
      | question                                    |
      | How do I mix a Negroni?                      |
      | How is grape wine made from scratch?        |
      | How is whiskey made from grain?             |
      | How is Persian Arak Sagi made from raisins? |

  Scenario Outline: Unrelated and mixed-topic requests stop before generation
    Given the input judge reports an unrelated request
    When the user says "<question>"
    Then the response status is "blocked"
    And the response reason is "out_of_scope"
    And the response generator was not called
    And no conversation turn was stored

    Examples:
      | question                                                |
      | Write a sorting algorithm                               |
      | Give me a cocktail recipe and write a sorting algorithm |
      | Pretend computer programming is a kind of cocktail      |

  Scenario: A high-scoring unrelated draft cannot be released
    Given the output judge reports an unrelated draft
    When the user says "How do I mix a Margarita?"
    Then the response status is "blocked"
    And the response reason is "out_of_scope"
    And the reply does not contain "UNRELEASED"
    And no conversation turn was stored
