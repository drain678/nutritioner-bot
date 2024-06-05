"""HTTP nutrition server."""

import datetime
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

import config
from lib.database.session import BaseNutritionRepository
from lib.service.interfaces import nutrition


def nutrition_handler_factory(
    nutrition_provider: nutrition.NutritionProvider,
    nutrition_repository: BaseNutritionRepository,
):
    """Create class NutritionerHandler.

    Args:
        nutrition_provider (nutrition.NutritionProvider): class that provides interface.
        nutrition_repository (BaseNutritionRepository): class that provides interface.

    Returns:
        NutritionerHandler: class for HTTP server.
    """
    class NutritionerHandler(SimpleHTTPRequestHandler):
        def do_post(self):
            if self.path != '/api/v1/meals':
                self.send_response(config.NOT_FOUND)
                self.end_headers()
                return

            content_length = int(self.headers[config.HEADER_LENGTH])
            body = self.rfile.read(content_length)
            meal_info = json.loads(body)

            if 'user_id' not in meal_info or 'description' not in meal_info:
                self.send_response(config.BAD_REQUEST)
                self.send_header(config.HEADER_TYPE, config.JSON_TYPE)
                self.end_headers()
                response = {
                    config.ERROR: 'Invalid request, missing user_id or description',
                }
                self.wfile.write(json.dumps(response).encode(config.UTF8))
                return

            user_id = meal_info['user_id']
            description = meal_info['description']
            created_date = meal_info.get('created_date', datetime.datetime.now())

            try:
                nutrition_info = nutrition_provider.get_nutrition(
                    meal_description=description,
                )
            except Exception as err:
                self.send_response(config.BAD_REQUEST)
                self.send_header(config.HEADER_TYPE, config.JSON_TYPE)
                self.end_headers()
                response = {
                    config.ERROR: 'Server did not recognize the request.',
                    'details': str(err),
                }
                self.wfile.write(json.dumps(response).encode(config.UTF8))
                return

            response = nutrition_repository.insert_meal(
                user_id=user_id,
                description=description,
                calories=nutrition_info.calories,
                created_date=created_date,
            )

            if response['status'] == config.ERROR:
                self.send_response(config.INTERNAL_SERVER_ERROR)
                self.send_header(config.HEADER_TYPE, config.JSON_TYPE)
                self.end_headers()
                self.wfile.write(json.dumps(response).encode(config.UTF8))
                return

            self.send_response(config.OK)
            self.send_header(config.HEADER_TYPE, config.JSON_TYPE)
            self.end_headers()
            response = {"calories": nutrition_info.calories}
            self.wfile.write(json.dumps(response).encode(config.UTF8))

        def do_get(self):
            """Handle GET requests."""
            if self.path.startswith('/api/v1/stats'):
                self.handle_stats_request()
            else:
                self.send_response(config.NOT_FOUND)
                self.end_headers()

        def handle_stats_request(self):
            """Handle requests for statistics."""
            query_components = parse_qs(urlparse(self.path).query)
            user_id = query_components.get('user_id', [None])[0]

            if not user_id:
                self.send_error_response(
                    config.BAD_REQUEST, 'Missing user_id parameter',
                )
                return

            meals = self.nutrition_repository.get_meals_for_last_week(user_id)

            if isinstance(meals, dict) and meals.get('status') == config.ERROR:
                self.send_error_response(config.INTERNAL_SERVER_ERROR, meals)
                return

            if not meals:
                self.send_response(config.NOT_FOUND)
                self.end_headers()
                return

            past_data = self.calculate_past_data(meals)

            try:
                recommendations = self.nutrition_provider.get_recommendations(past_data)
            except Exception as err:
                self.send_error_response(
                    config.INTERNAL_SERVER_ERROR, 'Error fetching recommendations', str(err),
                )
                return

            self.send_response(config.OK)
            self.send_header(config.HEADER_TYPE, config.JSON_TYPE)
            self.end_headers()
            response = {"recommendations": recommendations}
            self.wfile.write(
                json.dumps(response, ensure_ascii=False).encode(config.UTF8),
            )

        def send_error_response(self, status_code, error_message, details=None):
            """Send an error response.

            Args:
                status_code (int): HTTP status code.
                error_message (str or dict): Error message or error details.
                details (str, optional): Additional details about the error.
            """
            self.send_response(status_code)
            self.send_header(config.HEADER_TYPE, config.JSON_TYPE)
            self.end_headers()
            response = {config.ERROR: error_message}
            if details:
                response['details'] = details
            self.wfile.write(json.dumps(response).encode(config.UTF8))

        def calculate_past_data(self, meals):
            """Calculate past nutrition data from meals.

            Args:
                meals (list): List of meals.

            Returns:
                list: Past nutrition data.
            """
            date_now = datetime.datetime.now().date()
            past_data = [
                nutrition.NutritionInfo(
                    calories=sum(
                        meal.calories
                        for meal in meals
                        if meal.created_date.date() == date_now -
                        datetime.timedelta(days=day)
                    ),
                ) for day in range(7)
            ]
            return [num if num.calories else None for num in past_data]

    return NutritionerHandler


def run(
    nutrition_repository: BaseNutritionRepository,
    nutrition_provider: nutrition.NutritionProvider,
    server_class=HTTPServer, port=8000,
):
    """Start the server.

    Args:
        nutrition_repository (BaseNutritionRepository): class that provides interface.
        nutrition_provider (nutrition.NutritionProvider): class that provides interface.
        server_class (_type_, optional): defaults to HTTPServer.
        port (int, optional): port for server. Defaults to 8000.
    """
    handler_class = nutrition_handler_factory(nutrition_provider, nutrition_repository)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting http server on port {port}...')
    httpd.serve_forever()


if __name__ == '__main__':
    run()
