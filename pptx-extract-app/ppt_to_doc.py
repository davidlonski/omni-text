import base64
from PIL import Image
from io import BytesIO
import pytesseract
from google.generativeai.types import GenerationConfig
import google.generativeai as genai
import time
from dotenv import load_dotenv
import os
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
import json

# Load environment variables
load_dotenv()
# Configure API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
# Choose a Gemini model.
model = genai.GenerativeModel(model_name="gemini-2.0-flash-lite")



def extract_ppt_images_text_to_json(pptx_path, output_path):
    """
    Extract images and text from PowerPoint presentation and save as JSON.
    
    Args:
        pptx_path (str): Path to the PowerPoint file
        output_path (str): Path where JSON output will be saved
    """
    try:
        prs = Presentation(pptx_path)
        presentation_data = {
            "presentation": {
                "source_file": os.path.basename(pptx_path),
                "total_slides": len(prs.slides),
                "pages": []
            }
        }
        
        for slide_index, slide in enumerate(prs.slides):
            slide_index += 1
            print(f"Processing slide {slide_index}/{len(prs.slides)}")
            
            page_data = {
                "page_index": slide_index,
                "shapes": []
            }
            
            image_number = 0
            text_number = 0
            
            for shape_index, shape in enumerate(slide.shapes):
                shape_index += 1
                try:
                    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                        image = shape.image
                        image_bytes = image.blob
                        img = Image.open(BytesIO(image_bytes))
                        img_base64 = base64.b64encode(image_bytes).decode('utf-8')
                        fmt = img.format.lower() if img.format else 'png'

                        # Extract text using both LLM and OCR
                        llm_note_text = ExtractText_LLM(img_base64, image_format=fmt)
                        ocr_note_text = ExtractText_OCR(img)

                        # Clean text (remove empty lines)
                        cleaned_llm_text = '\n'.join(line for line in llm_note_text.splitlines() if line.strip())
                        cleaned_ocr_text = '\n'.join(line for line in ocr_note_text.splitlines() if line.strip())
                        
                        image_number += 1
                        
                        shape_data = {
                            "shape_index": shape_index,
                            "type": "image",
                            "image_number": image_number,
                            "content": {
                                "llm_text": cleaned_llm_text,
                                "ocr_text": cleaned_ocr_text,
                                "image_format": fmt
                            }
                        }
                        
                        page_data["shapes"].append(shape_data)
                    elif shape.shape_type == MSO_SHAPE_TYPE.TEXT_BOX or (hasattr(shape, 'text') and shape.text):
                        text_number += 1
                        text_box = shape.text_frame
                        text_content = text_box.text
                        cleaned_text_content = '\n'.join(line for line in text_content.splitlines() if line.strip())
                        shape_data = {
                            "shape_index": shape_index,
                            "type": "text",
                            "text_number": text_number,
                            "content": {
                                "text": cleaned_text_content
                            }
                        }
                        
                        page_data["shapes"].append(shape_data)
                        
                except Exception as e:
                    print(f"Error processing shape {shape_index} on slide {slide_index}: {str(e)[:100]}...")
                    continue
            
            presentation_data["presentation"]["pages"].append(page_data)
        
        # Save JSON
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
        except OSError as e:
            print(f"Warning: Could not remove existing file: {e}")
        
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(presentation_data, file, indent=2, ensure_ascii=False)
        
        print(f"Successfully saved JSON to: {output_path}")
        return presentation_data
        
    except Exception as e:
        print(f"Error processing PowerPoint file: {str(e)[:100]}...")
        return {}


def ExtractText_OCR(img):
    try:
        # Extract text using OCR (Tesseract)
        text = pytesseract.image_to_string(img)
        return text.strip()

    except Exception as e:
        print(f"Error during OCR extraction: {e}")
        return ""


def ExtractText_LLM(image_base64: str, image_format: str = 'png', max_retries=3, delay=1, quota_refill_delay=60):
    generation_config = GenerationConfig(max_output_tokens=100)

    for attempt in range(max_retries):
        try:
            # Extract text using LLM (Gemini)
            image_part = {
                'inline_data': {
                    'mime_type': f'image/{image_format}',
                    'data': image_base64
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