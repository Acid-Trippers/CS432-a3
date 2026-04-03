import asyncio
import importlib

ing = importlib.import_module("src.phase_1_to_4.01_ingestion")
print(asyncio.run(ing.fetch_data(5)))
