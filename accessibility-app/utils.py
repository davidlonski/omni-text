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
import wave
import pyttsx3
from moviepy import ImageClip, AudioFileClip
import tempfile
import re

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

def describe_image(image_bytes, image_format):
    llm_description = ExtractText_LLM(image_bytes, image_format)
    ocr_description = ExtractText_OCR(image_bytes)

    cleaned_llm_text = clean_text(llm_description)
    cleaned_ocr_text = clean_text(ocr_description)

    description = cleaned_llm_text + "\n" + cleaned_ocr_text

    cleaned_text = clean_text_with_llm(description)

    return cleaned_text

    
def create_static_video(image_bytes, audio_bytes, fps=1):
    """
    Create a static MP4 video from image bytes and audio bytes.

    Parameters:
    - image_bytes: bytes, the image data
    - audio_bytes: bytes, the audio data
    - fps: int, frames per second (default: 1 for static image)

    Returns:
    - bytes: The video data as bytes, or None if an error occurs
    """
    try:
        # Create temporary files for processing
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio_path = temp_audio.name
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_image:
            temp_image.write(image_bytes)
            temp_image_path = temp_image.name
        
        # Load audio
        audio = AudioFileClip(temp_audio_path)

        # Create an ImageClip with the duration of the audio
        clip = ImageClip(temp_image_path, duration=audio.duration)

        # Set audio to the clip and fps
        clip = clip.with_audio(audio).with_fps(fps)

        # Create temporary file for output video
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
            temp_video_path = temp_video.name

        # Write video to temporary file
        clip.write_videofile(temp_video_path, codec="libx264", audio_codec="aac")
        
        # Read the video data
        with open(temp_video_path, 'rb') as video_file:
            video_data = video_file.read()
        
        # Clean up
        clip.close()
        audio.close()
        os.unlink(temp_audio_path)
        os.unlink(temp_image_path)
        os.unlink(temp_video_path)
        
        return video_data
        
    except Exception as e:
        print(f"Error creating static video: {e}")
        return None

    

def generate_audio(text, voice_name='Kore'):
    """
    Generates audio from text using pyttsx3 (text-to-speech).

    Args:
        text (str): The text to generate audio from.
        voice_name (str): The name of the voice to use.

    Returns:
        bytes: The audio data as base64 encoded string.
    """
    # if text contains any special characters, remove them
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    
    try:
        engine = pyttsx3.init()
        
        # Configure voice if available
        voices = engine.getProperty('voices')
        if voices:
            engine.setProperty('voice', voices[0].id)  # Use first available voice
        
        # Set speech rate and volume
        engine.setProperty('rate', 150)  # Speed of speech
        engine.setProperty('volume', 0.9)  # Volume level
        
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        # Generate audio to the temporary file
        engine.save_to_file(text, temp_filename)
        engine.runAndWait()
        
        # Read the generated audio file
        with open(temp_filename, 'rb') as audio_file:
            audio_data = audio_file.read()
        
        # Clean up the temporary file
        os.unlink(temp_filename)

        # return audio data as bytes
        return audio_data
    
    except Exception as e:
        print(f"Error generating audio: {e}")
        return None
