"""Main file for starting the server."""

import os

from lib import server
from lib.database.main_db import init_db
from lib.database.session import NutritionRepository
from lib.datasources.providers import nutrition

ollama_url = os.getenv('BASE_OLLAMA_URL')
ollama_model = os.getenv('OLLAMA_MODEL')

nutrition_provider = nutrition.NutritionProviderImpl(ollama_url, ollama_model)
session = init_db()
nutrition_repository = NutritionRepository(session)

server.run(nutrition_repository, nutrition_provider)
