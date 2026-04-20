import django
from django.test import Client
from django.test.utils import setup_test_environment
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hiddengems.settings')
django.setup()

# Set up Django environment for Behave
def before_all(context):
    setup_test_environment()

def before_scenario(context, scenario):
    # Give each scenario a fresh test client and database
    from django.test.runner import DiscoverRunner
    context.test_runner = DiscoverRunner(verbosity=0)
    context.old_config = context.test_runner.setup_databases()
    context.client = Client()

def after_scenario(context, scenario):
    # Tear down the test database after each scenario
    context.test_runner.teardown_databases(context.old_config)
