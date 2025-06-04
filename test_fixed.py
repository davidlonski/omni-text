import util

def test_detailed_content():
    """Print detailed content with object IDs for debugging"""
    
    image_list, text_list, structure = util.extract_pptx_structure("Urinary_System_chpt26 .pptx")
    
    print("=" * 80)
    print("DETAILED CONTENT ANALYSIS")
    print("=" * 80)
    
    for i, element in enumerate(structure):
        print(f"\nElement {i+1}:")
        print(f"  Type: {element['type']}")
        print(f"  Page: {element['page_number']}")
        print(f"  Order: {element['element_order']}")
        print(f"  Preview: {element['content_preview']}")
        
        if element['type'] == 'text':
            # Find and display full text
            text_obj = next((t for t in text_list if t.id == element['object_id']), None)
            if text_obj:
                print(f"  Full Text: {repr(text_obj.text)}")
        
        elif element['type'] == 'image':
            print(f"  File Path: {element['file_path']}")
            # Find image object for additional details
            img_obj = next((img for img in image_list if img.id == element['object_id']), None)
            if img_obj:
                print(f"  Status: {img_obj.status}")

            OCR_text = util.ExtractText_OCR(img_obj.file_path)
            OCR_text = '\n'.join(line for line in OCR_text.splitlines() if line.strip())
            print(f"  OCR Text: {OCR_text}")


            LLM_text = util.ExtractText_LLM(img_obj.file_path)
            LLM_text = '\n'.join(line for line in LLM_text.splitlines() if line.strip())
            print(f"  LLM Text: {LLM_text}")


# Run the tests
if __name__ == "__main__":
    print("Running detailed analysis...")
    test_detailed_content()
    



