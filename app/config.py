import os

from dotenv import load_dotenv

load_dotenv()

NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY", "")
NEBIUS_BASE_URL = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/")
NEMOTRON_MODEL = os.getenv("NEMOTRON_MODEL", "nvidia/nemotron-3-super-120b-a12b")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
MOCK_MODE = os.getenv("MOCK_MODE", "0") == "1"


MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "9000"))
