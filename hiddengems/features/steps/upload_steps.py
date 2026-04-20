from behave import given, when, then
from django.contrib.auth.models import User
from home.models import Game


@given('I am a logged in user')
def step_logged_in(context):
    # Create a test user and log them in
    context.user = User.objects.create_user(
        username='testdev', password='testpass123'
    )
    context.client.login(username='testdev', password='testpass123')


@given('I am not logged in')
def step_not_logged_in(context):
    # Make sure no user is logged in
    context.client.logout()


@when('I visit the upload page')
def step_visit_upload(context):
    # Make a GET request to the upload page
    context.response = context.client.get('/upload/')


@when('I submit the upload form without a title')
def step_submit_no_title(context):
    # POST form data missing the title field
    context.response = context.client.post('/upload/', {
        'title': '',
        'description': 'A cool game',
        'price': '9.99',
        'genre': 'RPG',
    })


@when('I submit the upload form with price "{price}"')
def step_submit_bad_price(context, price):
    # POST form data with an invalid price value
    context.response = context.client.post('/upload/', {
        'title': 'My Game',
        'description': 'A cool game',
        'price': price,
        'genre': 'RPG',
    })


@then('I should see the upload form')
def step_see_form(context):
    # Page should load successfully
    assert context.response.status_code == 200, \
        f"Expected 200, got {context.response.status_code}"


@then('the game should not be saved')
def step_game_not_saved(context):
    # No game should exist in the database
    assert not Game.objects.exists(), "Game was saved but should not have been"


@then('I should not see the upload form')
def step_no_form(context):
    # Unauthenticated users should not get a 200
    assert context.response.status_code != 200, \
        f"Expected redirect, got {context.response.status_code}"
