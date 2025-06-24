import streamlit as st
import google.generativeai as genai
import google.generativeai.types as types
from google.generativeai.types import GenerationConfig
import base64
import os
from dotenv import load_dotenv
import pytesseract
from PIL import Image
import time
import io


# Load environment variables
load_dotenv()

def configure_gemini():
    """
    Configures the Google Generative AI model using the GOOGLE_API_KEY environment variable.

    Returns:
        bool: True if configuration is successful, False otherwise.
    """
    try:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            st.error("GOOGLE_API_KEY environment variable not found. Please set it in your .env file.")
            return False
        genai.configure(api_key=api_key)
        # Initialize and store the model in session state
        st.session_state.gemini_model = genai.GenerativeModel("gemini-2.0-flash-lite")
        return True
    except Exception as e:
        st.error(f"Failed to configure Gemini API: {e}")
        return False

def get_gemini_response(prompt, model_name="gemini-2.0-flash-lite"):
    """
    Generates content from the Gemini model based on a prompt.

    Args:
        prompt (str): The input prompt for the model.
        model_name (str): The name of the Gemini model to use.

    Returns:
        str or None: The generated text from the model, or None if an error occurs.
    """
    if 'gemini_model' not in st.session_state or st.session_state.gemini_model is None:
        st.error("Gemini model is not initialized. Please check your API key.")
        return None
    try:
        response = st.session_state.gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"An error occurred while calling the Gemini API: {e}")
        return None


def ExtractText_OCR(img_bytes):
    """
    Extracts text from an image using OCR (Tesseract).

    Args:
        img_bytes (bytes): The image data in bytes.

    Returns:
        str: The extracted text from the image.
    """
    try:
        # Extract text using OCR (Tesseract)
        img = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(img)
        return text.strip()

    except Exception as e:
        print(f"Error during OCR extraction: {e}")
        return ""


def ExtractText_LLM(image_bytes: bytes, image_format: str = 'png', max_retries=3, delay=1, quota_refill_delay=60):
    """
    Extracts text from an image using LLM (Gemini).

    Args:
        image_bytes (bytes): The image data in bytes.
        image_format (str): The format of the image.
        max_retries (int): The maximum number of retries.
        delay (int): The delay between retries.
        quota_refill_delay (int): The delay for quota refill.

    Returns:
        str: The extracted text from the image.
    """
    image_bytes = base64.b64encode(image_bytes).decode('utf-8')
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    generation_config = GenerationConfig(max_output_tokens=100)

    for attempt in range(max_retries):
        try:
            # Extract text using LLM (Gemini)
            image_part = {
                'inline_data': {
                    'mime_type': f'image/{image_format}',
                    'data': image_bytes
                }
            }

            result = model.generate_content(
                contents=[
                    image_part,
                    "\n",
                    "Return a very short detailed description of the image provided. "
                    "Only return one or two sentences, about 40 words. Nothing else!"
                ],
                generation_config=generation_config,
                request_options={"timeout": 10}
            )

            return result.text.strip()

        except Exception as e:
            if "Resource has been exhausted" in str(e):
                print(f"Quota exhausted, waiting {quota_refill_delay} seconds for refill...")
                time.sleep(quota_refill_delay)
            else:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                else:
                    raise


def clean_text(text):
    """
    Cleans the text by removing any non-essential information.
    """
    return '\n'.join(line for line in text.splitlines() if line.strip())

def clean_text_with_llm(text):
    """
    Cleans the text by removing any non-essential information using LLM (Gemini-2.0-flash-lite).
    """
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    generation_config = GenerationConfig(max_output_tokens=100)

    result = model.generate_content(
        contents=[
            text,
            "\n",
            "given the following text, remove any non-essential information and return the text in a clean format. "
            "Only return the text in a clean format. Nothing else!"
        ],
        generation_config=generation_config,
    )
    return result.text.strip()
