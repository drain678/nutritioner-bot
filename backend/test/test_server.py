"""File for testing the server."""

import datetime
import http
import threading
from unittest import TestCase, mock

import requests
from lib.database.models import Meal
from lib.server import nutrition_handler_factory
from lib.service.interfaces.nutrition import NutritionInfo

from . import config


class TestHTTPServer(TestCase):
    """Class with tests for the server.

    Args:
        unittest (TestCase): Module for testing.
    """

    def setUp(self):
        """Set up a test environment before running tests."""
        self.repo_mock = mock.Mock()
        self.provider_mock = mock.Mock()

        nutrition_handler = nutrition_handler_factory(self.provider_mock, self.repo_mock)
        self.server = http.server.HTTPServer(('localhost', 0), nutrition_handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()

    def tearDown(self):
        """Tear down the test environment after running tests."""
        self.server.shutdown()
        self.thread.join()

    def test_POST(self):
        """Test the POST request for creating a meal."""
        nutrition_info = NutritionInfo(calories=config.CAL42)
        self.provider_mock.get_nutrition = mock.MagicMock(return_value=nutrition_info)
        self.repo_mock.insert_meal = mock.MagicMock(return_value={'status': 'ok'})
        test_description = 'test meal description'
        user_id = '42'
        response = requests.post(
            f'{self._get_url()}/api/v1/meals', json={
                'user_id': user_id,
                'description': test_description,
            },
            timeout=config.TIME_OUT,
        )
        self.assertEqual(response.status_code, config.OK)
        self.assertEqual(response.json()['calories'], nutrition_info.calories)

        self.provider_mock.get_nutrition.assert_called_once_with(meal_description=test_description)
        repo_call = self.repo_mock.insert_meal.call_args.kwargs
        self.assertEqual(repo_call['user_id'], user_id)
        self.assertEqual(repo_call['description'], test_description)
        self.assertEqual(repo_call['calories'], nutrition_info.calories)
        self.assertEqual(repo_call['created_date'].date(), datetime.datetime.now().date())

    def test_POST(self):
        """Test the GET request for recommendations."""
        user_id = '42'
        now = datetime.datetime.now()
        saved_meals = [
            Meal(calories=config.CAL100, created_date=now),
            Meal(calories=config.CAL200, created_date=now - datetime.timedelta(milliseconds=5)),
            Meal(calories=config.CAL400, created_date=now - datetime.timedelta(days=2)),
            Meal(calories=config.CAL1000, created_date=now - datetime.timedelta(days=4)),
        ]
        expected_flattened = [
            NutritionInfo(calories=config.MULTIPLE_CHOICES), None,
            NutritionInfo(calories=config.BAD_REQUEST), None,
            NutritionInfo(calories=config.CAL1000),
            None, None,
        ]
        self.repo_mock.get_meals_for_last_week = mock.MagicMock(return_value=saved_meals)

        test_recommendations = 'test recommendations'
        self.provider_mock.get_recommendations = mock.MagicMock(return_value=test_recommendations)

        response = requests.get(
            f'{self._get_url()}/api/v1/stats', params={
                'user_id': user_id,
            },
            timeout=config.TIME_OUT,
        )
        self.assertEqual(response.status_code, config.OK)
        self.assertEqual(response.json()['recommendations'], test_recommendations)

        self.repo_mock.get_meals_for_last_week.assert_called_once_with(user_id)
        self.provider_mock.get_recommendations.assert_called_once_with(expected_flattened)

    def _get_url(self) -> str:
        """Get the URL for the test server.

        Returns:
            str: URL for the test server.
        """
        return f'http://localhost:{self.port}'
