import util

# Test just the image extraction first
print("Testing image extraction...")
image_list = util.extract_images_from_office("Urinary_System_chpt26 .pptx")
print(f"Found {len(image_list)} images:")
for img in image_list:
    print(f"  - {img}")

# Test OCR on first image only
if image_list:
    print(f"\nTesting OCR on first image: {image_list[0]}")
    ocr_result = util.ExtractText_OCR(image_list[0])
    print(f"OCR result: '{ocr_result[:50]}...'")  # First 50 chars only

    # Test Gemini on first image only  
    print(f"\nTesting Gemini on first image...")
    try:
        gemini_result = util.GenerateTextFormated(image_list[0])
        print(f"Gemini result: '{gemini_result}'")
    except Exception as e:
        print(f"Gemini error: {e}")
else:
    print("No images found!") 