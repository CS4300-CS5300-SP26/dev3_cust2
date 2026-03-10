Feature: Game Upload
  As a developer
  I want to upload my game to Hidden Gems
  So that users can discover and play it

  Scenario: Successfully view the upload page
    Given I am a logged in user
    When I visit the upload page
    Then I should see the upload form

  Scenario: Submit form with missing title
    Given I am a logged in user
    When I submit the upload form without a title
    Then the game should not be saved

  Scenario: Submit form with invalid price
    Given I am a logged in user
    When I submit the upload form with price "free"
    Then the game should not be saved

  Scenario: Unauthenticated user tries to upload
    Given I am not logged in
    When I visit the upload page
    Then I should not see the upload form
