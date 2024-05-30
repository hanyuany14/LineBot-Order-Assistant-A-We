from rich.console import Console
from rich.markdown import Markdown
import re
import pandas as pd
import json
from io import BytesIO
from PIL import Image
import base64

from utils import LLMUtils
from configs import OpenAIConfigs


class LineBot:
    def __init__(self): ...

    def bot_response(self, query: str) -> str: ...
