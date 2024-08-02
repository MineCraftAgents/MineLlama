import os
from dotenv import load_dotenv
load_dotenv()

OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
HUGGING_FACE_AUTH_KEY = os.getenv("HUGGING_FACE_AUTH_KEY")