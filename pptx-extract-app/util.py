import PyPDF2
import os
import google.generativeai as genai
import time
from google.generativeai.types import GenerationConfig
import io
from PIL import Image as pl
import pytesseract
from docx import Document
from pptx import Presentation
import zipfile
from pathlib import Path
import re
from dotenv import load_dotenv
import base64
from models import Image, Text, ImageStatus

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


###########################################
# Genrate text from image with Gemini     #
###########################################
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


###########################################
# OCR extract                             #
###########################################
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
    

    
###########################################
# URL sort key                            #
###########################################
def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]


############################################
# Extracts images from any office file ext #
############################################
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

###########################################
# Extracts text from pptx                 #
###########################################
def extract_text_from_pptx(pptx_path):
    presentation = Presentation(pptx_path)
    text = ""

    for slide in presentation.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text += shape.text.replace("\n", " ")

    return text.strip()


###########################################
# Extracts text from docx                 #
###########################################
def extract_text_from_docx(docx_path):
        """Extracts text from a .docx file."""
        document = Document(docx_path)
        text = ""
        for paragraph in document.paragraphs:
            text += paragraph.text
        return text


###########################################
# Extracts text from pdf                  #
###########################################
def extract_text_from_pdf(pdf_path):

    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

'''
    Extracts images and saves as a path
    @param pdf_path: The path to the PDF file
    @param output_dir: The directory to save the images
    @return: A list of image paths
'''
def extract_images_and_save(pdf_path, output_dir="extracted_images"):
    image_paths = []  # Create an empty list to store image paths

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page_num, page in enumerate(reader.pages):
            for img_num, image_file_object in enumerate(page.images):
                try:
                    # Create a unique filename
                    image_filename = f"image_page{page_num+1}_img{img_num}.png"
                    image_path = os.path.join(output_dir, image_filename)

                    # Open and save the image data using PIL
                    img = pl.open(io.BytesIO(image_file_object.data))
                    img.save(image_path)

                    # Append the image path to the list
                    image_paths.append(image_path)

                except Exception as e:
                    print(f"Error saving image from page {page_num+1}, image {img_num+1}: {e}")

    return image_paths # Return the list of image paths

'''
    Extracts images from zip
    @param zip_path: The path to the zip file
    @param media_folder: The folder to extract the images from
    @param output_dir: The directory to save the images
    @return: A list of image paths
'''
def extract_images_from_zip(zip_path, media_folder, output_dir):
    """Helper function to extract images from zip-based office files"""
    extracted_image_paths = []
    
    with zipfile.ZipFile(zip_path, 'r') as archive:
        for file in archive.namelist():
            if file.startswith(media_folder) and file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tif', '.svg')):
                image_data = archive.read(file)
                image_name = os.path.basename(file)
                rel_path = os.path.join(output_dir, image_name)
                with open(rel_path, 'wb') as img_file:
                    img_file.write(image_data)
                extracted_image_paths.append(rel_path.replace("\\", "/"))
    
    return extracted_image_paths


###########################################
# Extracts structured content from pptx   #
###########################################
def extract_pptx_structure(file_path, output_dir="extracted_images"):
    """Extract structured content from PPTX files with proper slide-image association"""
    os.makedirs(output_dir, exist_ok=True)

    images_list = []
    text_list = []
    document_structure = []
    
    # Parse presentation for text and slide structure
    presentation = Presentation(file_path)
    
    element_order = 0
    
    # Process each slide individually
    for slide_idx, slide in enumerate(presentation.slides):
        slide_number = slide_idx + 1
        
        # Process all shapes on this slide
        for shape_idx, shape in enumerate(slide.shapes):
            # Handle text shapes
            if hasattr(shape, "text") and shape.text.strip():
                text_obj = Text(
                    text=shape.text,
                    page_number=slide_number,
                    status=ImageStatus.PENDING
                )
                text_list.append(text_obj)
                
                document_structure.append({
                    'type': 'text',
                    'element_order': element_order,
                    'page_number': slide_number,
                    'slide_index': slide_idx,
                    'shape_index': shape_idx,
                    'object_id': text_obj.id,
                    'content_preview': shape.text[:50] + "..." if len(shape.text) > 50 else shape.text
                })
                element_order += 1
            
            # Handle image shapes
            elif hasattr(shape, 'image'):
                try:
                    # Extract image data
                    image_data = shape.image.blob
                    
                    # Create filename
                    image_extension = shape.image.ext
                    image_filename = f"slide_{slide_number}_image_{shape_idx}.{image_extension}"
                    image_path = os.path.join(output_dir, image_filename)
                    
                    # Save image
                    with open(image_path, 'wb') as img_file:
                        img_file.write(image_data)
                    
                    # Create base64 encoding
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                    
                    # Create image object
                    image_obj = Image(
                        page_number=slide_number,
                        base64_image=base64_image,
                        file_path=image_path.replace("\\", "/"),
                        status=ImageStatus.PENDING
                    )
                    images_list.append(image_obj)
                    
                    document_structure.append({
                        'type': 'image',
                        'element_order': element_order,
                        'page_number': slide_number,
                        'slide_index': slide_idx,
                        'shape_index': shape_idx,
                        'object_id': image_obj.id,
                        'file_path': image_path.replace("\\", "/"),
                        'content_preview': f"Image on Slide {slide_number}"
                    })
                    element_order += 1
                    
                except Exception as e:
                    print(f"Error extracting image from slide {slide_number}, shape {shape_idx}: {e}")
                    continue


    # Sort document structure by page number and element order
    document_structure.sort(key=lambda x: (x['page_number'], x['element_order']))
    
    return images_list, text_list, document_structure