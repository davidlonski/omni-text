import os
import exiftool
import json

def add_metadata_to_image(image_path, field_name, field_value):
    """Add custom metadata to a single image"""
    try:
        # Check if image exists
        if not os.path.exists(image_path):
            print(f"❌ Image file not found: {image_path}")
            return False
        
        # Check if it's a supported image format
        ext = os.path.splitext(image_path)[1].lower()
        if ext not in {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}:
            print(f"❌ Unsupported image format: {ext}")
            return False
        
        # Add default prefix if field name doesn't have one
        if not any(field_name.startswith(prefix) for prefix in ['XMP:', 'IPTC:', 'EXIF:', 'File:', 'Composite:', 'JFIF:', 'Photoshop:', 'APP14:']):
            field_name = f"XMP:{field_name}"
            print(f"ℹ️  Added 'XMP:' prefix to field name: {field_name}")
        
        with exiftool.ExifTool() as et:
            # Add the metadata
            result = et.execute(f"-{field_name}={field_value}", image_path)
            print(f"✅ Metadata added successfully!")
            print(f"   Field: {field_name}")
            print(f"   Value: {field_value}")
            print(f"   Image: {os.path.basename(image_path)}")
            return True
            
    except FileNotFoundError:
        print("❌ ExifTool not found!")
        return False
    except Exception as e:
        print(f"❌ Error adding metadata: {e}")
        return False

def print_metadata(image_path):
    """Print metadata of an image"""
    try:
        with exiftool.ExifTool() as et:
            metadata = et.execute_json(image_path)
            print(json.dumps(metadata, indent=4))
    except Exception as e:
        print(f"Error printing metadata: {e}")

def main():
    print("=== Add Metadata to Image ===")
    print()

    # Get image path
    image_path = input("Enter image path: ").strip()
    if not image_path:
        print("❌ No image path provided")
        return

    print()
    print("Current metadata:")
    print_metadata(image_path)
    print()

    # Get metadata field name
    field_name = input("Enter metadata field name: ").strip()
    if not field_name:
        print("❌ No field name provided")
        return
    
    # Get metadata value
    field_value = input("Enter metadata value: ").strip()
    if not field_value:
        print("❌ No field value provided")
        return
    
    print()
    print("Common metadata fields:")
    print("- Artist: Image creator")
    print("- Copyright: Copyright information")
    print("- Description: Image description")
    print("- Keywords: Comma-separated keywords")
    print("- UserComment: Custom comment")
    print()
    print("Note: If no prefix is provided, 'XMP:' will be added automatically")
    print()
    
    # Confirm action
    confirm = input(f"Add '{field_name}={field_value}' to {os.path.basename(image_path)}? (y/n): ").strip().lower()
    
    if confirm in ['y', 'yes']:
        add_metadata_to_image(image_path, field_name, field_value)
    else:
        print("❌ Operation cancelled")

    print_metadata(image_path)

if __name__ == "__main__":
    main() 