"""File with class NutritionRepository for interactions with the database."""

import abc
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from lib.database.models import Meal

from config import ERROR


@dataclass
class MealData:
    """Class that stores data."""

    user_id: str
    description: str
    calories: float
    created_date: date


class BaseNutritionRepository(abc.ABC):
    """Class with interface for NutritionRepository."""

    @abc.abstractmethod
    def __init__(self, session) -> None:
        """Create interface for NutritionRepository.

        Args:
            session (_type_): SessionLocal.
        """

    @abc.abstractmethod
    def insert_meal(self, user_id: str, description: str, calories: float) -> dict:
        """Insert a meal into the database.

        Args:
            user_id (str): ID of the user.
            description (str): description of the meal.
            calories (float): number of calories in the meal.
        """

    @abc.abstractmethod
    def get_meals_for_last_week(self, user_id: str):
        """Get meals for the last week for a given user.

        Args:
            user_id (str): ID of the user.
        """


class NutritionRepository(BaseNutritionRepository):
    """Class with session."""

    def __init__(self, session) -> None:
        """Get session for interactions with the database..

        Args:
            session (_type_): SessionLocal.
        """
        self.session = session

    def insert_meal(self, user_id: str, description: str, calories: float, created_date: date):
        """Insert a new meal entry into the database.

        Args:
            user_id (str): The ID of the user for whom to insert the meal.
            description (str): The description of the meal.
            calories (float): The number of calories in the meal.
            created_date (date): The date when the meal was created.

        Returns:
            dict: A dictionary indicating the status of the operation.
        """
        session = self.session()
        meal_data = MealData(user_id, description, calories, created_date)
        try:
            return self._insert_meal(session, meal_data)
        except Exception as err:
            session.rollback()
            return {
                'status': ERROR,
                ERROR: 'Database error',
                'details': str(err),
            }
        finally:
            session.close()

    def get_meals_for_last_week(self, user_id: str):
        """Retrieve meals for the last week for a given user.

        Args:
            user_id (str): The ID of the user for whom to retrieve meals.

        Returns:
            list[Meal] or dict: A list of Meal objects representing the meals for the last week,
            or a dictionary with an error message if an error occurs during database retrieval.
        """
        session = self.session()
        try:
            return self._get_meals_for_last_week(session, user_id)
        except Exception as err:
            return {
                'status': ERROR,
                ERROR: 'Database error',
                'details': str(err),
            }
        finally:
            session.close()

    def _insert_meal(self, session, meal_data: MealData):
        meal = Meal(
            user_id=meal_data.user_id,
            description=meal_data.description,
            calories=meal_data.calories,
            created_date=meal_data.created_date,
        )
        session.add(meal)
        session.commit()
        return {'status': 'success'}

    def _get_meals_for_last_week(self, session, user_id: str):
        one_week_ago = datetime.now() - timedelta(days=7)
        return session.query(Meal).filter(
            Meal.user_id == user_id, Meal.created_date >= one_week_ago.date(),
        ).all()
