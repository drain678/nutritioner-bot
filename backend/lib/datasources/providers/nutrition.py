"""Class with NutritionProviderImpl."""

import json

import requests
from lib.service.interfaces import nutrition

import config

GET_CALORIES_PROMPT = r"""
You are a smart diet app.
User gives you a description of his meal and you give him the amount of
kilocalories, proteins, carbohydrates and fats that this meal had.
Use your knowledge about nutrition in food.
Return ONLY JSON with this format:
\{"kilocalories": int, "proteins": int, "carbs": int, "fats": int\}.
You can give a reasonable average estimate. If there is some real error
(like if provided meal is not food), just place 0 for calories.
"calories" should only be an integer number. not a string
Input: "[[INPUT]]"
"""

GET_RECOMMENDATIONS_PROMPT = """
You are a dietologist.
Provide recommendations for a client who entered some data into a nutrition app.
This client is an adult who has normal weight. He does not
have a goal of losing weight, he just wants to maintain it. If he consumes
less calories than needed for normal life, tell him about it. If he consumes
more, also tell him. Give not only general advice, but also advice for
specific days, if they differ from others very much. Answer no more than
150 words, no preface, no general words, more specific recommendations.

Here is a list of PAST kilocalorie intake for days from today to N days ago.
None signifies that there was no data for that day, you should ignore it.
Give general analytics on these past days, and some recommendations for the
future. Answer only in Russian.
Input: [[INPUT]]
"""


class LLMException(Exception):
    """Exception raised when the LLM fails to provide valid nutrition information."""


class NutritionProviderImpl(nutrition.NutritionProvider):
    """Implementation of the NutritionProvider interface using a LLM."""

    def __init__(self, ollama_url: str, ollama_model: str) -> None:
        """Initialize the NutritionProviderImpl.

        Args:
            ollama_url (str): The URL of the LLM API.
            ollama_model (str): The model name to be used for generating responses.
        """
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model

    def get_nutrition(self, meal_description: str) -> nutrition.NutritionInfo:
        """Get the nutritional information for a given meal description.

        Args:
            meal_description (str): The description of the meal.

        Returns:
            NutritionInfo: The nutritional information of the meal.

        Raises:
            LLMException: If the LLM fails to provide valid nutrition information.
        """
        prompt = GET_CALORIES_PROMPT.replace("[[INPUT]]", meal_description)
        body = json.dumps(
            {"model": self.ollama_model, "prompt": prompt, "stream": False, "format": "json"},
        )
        request = requests.post(
            f'{self.ollama_url}/api/generate', data=body, timeout=config.TIME_OUT,
        )
        resp = json.loads(request.json()["response"])
        calories = resp["kilocalories"]
        if calories == 0:
            raise LLMException()
        return nutrition.NutritionInfo(calories=float(calories))

    def get_recommendations(self, past_data: list[nutrition.NutritionInfo]) -> str:
        """Provide dietary recommendations based on past nutrition data.

        Args:
            past_data (list[NutritionInfo]): A list of past nutritional information.

        Returns:
            str: The dietary recommendations.
        """
        prompt = GET_RECOMMENDATIONS_PROMPT.replace(
            '[[INPUT]]', str([inf.__dict__ if inf is not None else None for inf in past_data]),
        )
        body = json.dumps({"model": self.ollama_model, "prompt": prompt, "stream": False})
        request = requests.post(
            f'{self.ollama_url}/api/generate', data=body, timeout=config.TIME_OUT,
        )
        return request.json()["response"]
