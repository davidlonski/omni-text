
import os
import google.generativeai as genai
import time
from PIL import Image as pl
import pytesseract
from dotenv import load_dotenv
import base64
import re
from google.generativeai.types import GenerationConfig
import zipfile
from pathlib import Path

# Load environment variables
load_dotenv()

# Initialize the model
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))  
# Choose a Gemini model.
model = genai.GenerativeModel(model_name="gemini-2.0-flash-lite")




###########################################
# Main Extract                            #
###########################################
def Extract_Office(filePath):
    list = extract_images_from_office(filePath)

    if not list:
        print(f"No images found in {filePath}")
        return [], [], []

    sorted_list = sorted(list, key=natural_sort_key)

    description_list = []
    generated_description_list = []
    image_paths = []

    for item in sorted_list:
        
        try:
            # OCR
            ocr_text = ExtractText_OCR(item)
            description = f"OCR text for {ocr_text}"  # Limit length to prevent huge strings
            
            # Gemini
            gemini_text = ExtractText_LLM(item)
            if not gemini_text:
                continue  # Skip if Gemini didn't return anything
                
            generateDescription = f"Generated text for {gemini_text}"
            
            # Remove multiple newlines and strip leading/trailing whitespace
            cleaned_description = '\n'.join(line for line in description.splitlines() if line.strip())
            cleaned_generatedDescription = '\n'.join(line for line in generateDescription.splitlines() if line.strip())

            # Ensure both descriptions are not empty before appending
            if cleaned_description.strip() and cleaned_generatedDescription.strip():
                description_list.append(cleaned_description)
                generated_description_list.append(cleaned_generatedDescription)
                image_paths.append(item)
              
        except Exception as e:
            print(f"Error processing {item}: {str(e)[:100]}...")
            continue  # Continue with next image instead of breaking

    return description_list, generated_description_list, image_paths

def ExtractText_LLM(filePath, max_retries=3, delay=1, quota_refill_delay=60):
    
    # Generate structured text from image with retry logic and formatting.
    generation_config = GenerationConfig(max_output_tokens=100)

    for attempt in range(max_retries):
        try:
            # Read image and convert to base64 instead of uploading
            with open(filePath, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Determine image format from file extension
            image_format = filePath.split('.')[-1].lower()
            if image_format == 'jpg':
                image_format = 'jpeg'
            
            # Create image part directly
            image_part = {
                'inline_data': {
                    'mime_type': f'image/{image_format}',
                    'data': image_data
                }
            }
            
            result = model.generate_content(
                contents=[
                    image_part,
                    "\n",
                    "Return a very short detailed description of the image provided\n"
                    "Only return one or two sentances about 40 words, Nothing else!"
                ],
                generation_config=generation_config
            )

            return result.text

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



def ExtractText_OCR(image_path):
    try:
        if image_path is None or not image_path:
            return ""
        
        if not os.path.exists(image_path):
            print(f"File not found: {image_path}")
            return ""
            
        img = pl.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
        
    except Exception as e:
        print(f"Error during OCR extraction for {image_path}: {e}")
        return ""
    


def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]



def extract_images_from_office(file_path, output_dir="extracted_images"):
    ext = Path(file_path).suffix.lower()
    os.makedirs(output_dir, exist_ok=True)
    extracted_image_paths = []

    def extract_from_zip(zip_path, media_folder):
        with zipfile.ZipFile(zip_path, 'r') as archive:
            for file in archive.namelist():
                if file.startswith(media_folder) and file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tif', '.bmp', '.svg')):
                    image_data = archive.read(file)
                    image_name = os.path.basename(file)
                    rel_path = os.path.join(output_dir, image_name)
                    with open(rel_path, 'wb') as img_file:
                        img_file.write(image_data)
                    extracted_image_paths.append(rel_path.replace("\\", "/"))  # Normalize to forward slashes

    if ext == ".pptx":
        extract_from_zip(file_path, "ppt/media/")
    elif ext == ".docx":
        extract_from_zip(file_path, "word/media/")
    else:
        raise ValueError("Unsupported file type. Only .pptx and .docx are supported.")

    return extracted_image_paths