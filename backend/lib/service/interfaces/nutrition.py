"""Class with interface of NutritionProvider and dataclass NutritionInfo."""

import abc
from dataclasses import dataclass


@dataclass
class NutritionInfo:
    """Class to store nutritional information.

    Attributes:
        calories (float): The number of calories in the meal.
    """

    calories: float


class NutritionProvider(abc.ABC):
    """Abstract base class for a nutrition provider."""

    @abc.abstractmethod
    def get_nutrition(self, meal_description: str) -> NutritionInfo:
        """Get the nutritional information for a given meal description.

        Args:
            meal_description (str): The description of the meal.
        """
