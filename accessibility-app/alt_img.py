import io
import base64
from PIL import Image
import pyttsx3
import wave
from pathlib import Path
from utils import generate_audio

def embed_alt_audio(image_bytes: bytes, alt_text: str) -> bytes:
    """
    Embeds alt text as audio in JPEG/PNG images, playable on click in a browser.
    
    Args:
        image_bytes (bytes): The image data in bytes (JPEG or PNG).
        alt_text (str): The alt text to convert to audio.
    
    Returns:
        bytes: Modified image bytes with embedded audio metadata.
    
    Raises:
        ValueError: If the image format is not JPEG or PNG, or if input is invalid.
    """
    # Validate inputs
    if not image_bytes or not alt_text:
        raise ValueError("Image bytes and alt text must not be empty")
    
    # Load image to check format
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img_format = img.format.upper()
        if img_format not in ['JPEG', 'PNG']:
            raise ValueError("Only JPEG and PNG images are supported")
    except Exception as e:
        raise ValueError(f"Invalid image data: {str(e)}")

    audio_data = generate_audio(alt_text)
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
    
    # Create HTML wrapper with embedded audio
    html_content = f"""
    <html>
    <body>
        <img src="data:image/{img_format.lower()};base64,{base64.b64encode(image_bytes).decode('utf-8')}"
             onclick="new Audio('data:audio/wav;base64,{audio_base64}').play()"
             alt="{alt_text}">
    </body>
    </html>
    """
    
    # Save HTML to bytes
    output_buffer = io.BytesIO()
    output_buffer.write(html_content.encode('utf-8'))
    output_buffer.seek(0)
    
    return output_buffer.getvalue()