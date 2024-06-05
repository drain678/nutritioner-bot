"""File with FakeNutritionProvider."""

from lib.service.interfaces import nutrition

from config import CAL500


class FakeNutritionProvider(nutrition.NutritionProvider):
    """A fake implementation of the NutritionProvider interface."""

    def __init__(self) -> None:
        """Initialize the FakeNutritionProvider instance."""

    def get_nutrition(self, meal_description: str) -> nutrition.NutritionInfo:
        """Mock implementation of the get_nutrition method.

        Args:
            meal_description (str): The description of the meal.

        Returns:
            nutrition.NutritionInfo: A fake NutritionInfo object with calories set to 500.0.
        """
        return nutrition.NutritionInfo(calories=CAL500)

    def get_recommendations(self, past_data: list[nutrition.NutritionInfo]) -> str:
        """Mock implementation of the get_recommendations method.

        Args:
            past_data (list[nutrition.NutritionInfo]): A list of past nutrition data.

        Returns:
            str: A fake recommendation message.
        """
        return 'надо меньше есть'
