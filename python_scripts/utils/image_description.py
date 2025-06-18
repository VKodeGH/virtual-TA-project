import os
import base64
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

def describe_image_from_base64(base64_str, mime_type):
    """
    Generate a detailed description for a base64-encoded image using Gemini.
    Args:
        base64_str (str): The base64-encoded image string (no header).
        mime_type (str): The image MIME type (e.g., 'image/png', 'image/jpeg', 'image/webp').
    Returns:
        str: Gemini-generated description.
    """
    image_bytes = base64.b64decode(base64_str)
    response = model.generate_content([
        "Describe this educational image in detail for student assistance.",
        {"mime_type": mime_type, "data": image_bytes}
    ])
    return response.text.strip()
