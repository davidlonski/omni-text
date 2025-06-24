import os
import json
import exiftool

# Folder containing images
IMAGE_DIR = "../extracted_images"

# Supported extensions
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}

def extract_metadata(image_path):
    """Extract metadata from image using exiftool"""
    try:
        with exiftool.ExifTool() as et:
            # Use the correct method name
            metadata = et.execute_json(image_path)
            return metadata[0] if metadata else {}
    except FileNotFoundError:
        return {'error': 'ExifTool not installed'}
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return {'error': str(e)}

def scan_folder_and_extract_metadata(folder):
    """Scan folder and extract metadata from all supported images"""
    results = []
    
    if not os.path.exists(folder):
        print(f"❌ Folder {folder} does not exist!")
        return results
    
    for root, _, files in os.walk(folder):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                file_path = os.path.join(root, file)
                print(f"Processing: {file}")
                metadata = extract_metadata(file_path)
                results.append({
                    "file": file_path,
                    "metadata": metadata
                })
    return results

def save_results_to_json(data, output_file="image_metadata.json"):
    """Save metadata results to JSON file"""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    print("Scanning and extracting metadata...")
    metadata_list = scan_folder_and_extract_metadata(IMAGE_DIR)
    
    if metadata_list:
        save_results_to_json(metadata_list)
        print(f"✅ Metadata saved to 'image_metadata.json' for {len(metadata_list)} images.")
    else:
        print("❌ No images found or processed.")
