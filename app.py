import streamlit as st
import os
from models import Document, Image, DocumentType, ImageStatus
from datetime import datetime 
from util import Extract_Office, extract_text_from_docx, extract_text_from_pptx, extract_text_from_pdf
import tempfile
from pathlib import Path
from PIL import Image as PILImage

# Set page config
st.set_page_config(
    page_title="Office Converter",
    page_icon="📝",
    layout="wide"
)

# Initialize session state
if 'documents' not in st.session_state:
    st.session_state.documents = []
if 'current_document' not in st.session_state:
    st.session_state.current_document = None
if 'processing' not in st.session_state:
    st.session_state.processing = False

def main():
    st.title("Office Converter")
    
    # Create main layout: sidebar and content
    sidebar_col, content_col = st.columns([1, 4])
    
    with sidebar_col:
        render_sidebar()
    
    with content_col:
        render_main_content()

def render_sidebar():
    st.header("📄 Controls")
    
    # Upload Doc
    st.subheader("Upload Doc")
    uploaded_file = st.file_uploader(
        "Choose a document",
        type=['docx', 'pptx', 'pdf'],
        key="file_uploader"
    )
    
    # Current Doc Upload section
    if uploaded_file:
        st.subheader("Current Doc Upload")
        st.write(f"**File:** {uploaded_file.name}")
        st.write(f"**Size:** {uploaded_file.size} bytes")
        st.write(f"**Type:** {uploaded_file.type}")
    
    # Process Doc
    if uploaded_file and not st.session_state.processing:
        if st.button("🔄 Process Doc", use_container_width=True):
            process_document(uploaded_file)
    
    # Export Doc As
    if st.session_state.current_document and st.session_state.current_document.status == "completed":
        if st.button("📥 Export Doc As", use_container_width=True):
            export_document(st.session_state.current_document)

def render_main_content():
    if not st.session_state.current_document:
        st.info("📋 Upload and process a document to get started!")
        return
    
    doc = st.session_state.current_document
    
    # Preview Doc header
    st.header("👁️ Preview Doc")
    
    if doc.status == "processing":
        st.warning("🔄 Document is being processed...")
        return
    
    # Doc Preview section with Doc Name
    st.subheader(f"📄 {doc.title}")
    
    # Use tabs instead of nested columns to avoid nesting issues
    tab1, tab2 = st.tabs(["📋 Doc Outlook", "📄 Doc Section"])
    
    with tab1:
        render_doc_outlook(doc)
    
    with tab2:
        render_doc_section(doc)

def render_doc_outlook(doc):
    st.markdown("### 📋 Content Overview")
    
    items = []
    
    # Add extracted text if available
    if doc.processed_text:
        items.append({
            'type': 'text',
            'content': doc.processed_text[:100] + "..." if len(doc.processed_text) > 100 else doc.processed_text,
            'full_content': doc.processed_text
        })
    
    # Add images
    for img in doc.images:
        items.append({
            'type': 'image',
            'content': f"Image from page {img.page_number}",
            'image_obj': img
        })
        
        # Add generated description if available
        if img.llm_description:
            items.append({
                'type': 'generated_text',
                'content': img.llm_description,
                'image_obj': img
            })
    
    # Display items in scrollable list
    for i, item in enumerate(items):
        with st.expander(f"Item {i+1}: {item['type'].replace('_', ' ').title()}", expanded=False):
            if item['type'] == 'text':
                st.text(item['content'])
            elif item['type'] == 'image':
                st.write(f"📷 {item['content']}")
                if os.path.exists(item['image_obj'].file_path):
                    try:
                        pil_img = PILImage.open(item['image_obj'].file_path)
                        st.image(pil_img, width=200)
                    except:
                        st.write("⚠️ Image preview unavailable")
            elif item['type'] == 'generated_text':
                st.write("🤖 AI Description:")
                st.text(item['content'])

def render_doc_section(doc):
    st.markdown("### 📄 Document Content")
    
    # Extracted Text Section
    if doc.processed_text:
        st.markdown("#### 📝 Extracted Text")
        
        # Use container instead of columns to avoid nesting
        with st.container():
            st.text_area(
                "Document Text",
                doc.processed_text,
                height=120,
                disabled=True,
                key="main_text_preview"
            )
            
            # Action buttons in a single row
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("👁️ Preview Text", key="preview_text_main"):
                    show_text_preview(doc.processed_text)
            with col2:
                if st.button("🗑️ Delete Text", key="delete_text_main"):
                    doc.processed_text = None
                    st.rerun()
            with col3:
                if st.button("💾 Save Text", key="save_text_main"):
                    st.success("✅ Text saved!")
        
        st.divider()
    
    # Images Section
    if doc.images:
        st.markdown("#### 🖼️ Images")
        
        for i, img in enumerate(doc.images):
            st.markdown(f"**Image {i+1} - Page {img.page_number}**")
            
            # Use container for each image instead of nested columns
            with st.container():
                # Display image
                if os.path.exists(img.file_path):
                    try:
                        pil_img = PILImage.open(img.file_path)
                        st.image(pil_img, width=400)
                    except Exception as e:
                        st.error(f"Error loading image: {e}")
                
                # Display OCR text if available
                if img.original_text:
                    st.text_area(
                        "OCR Text",
                        img.original_text,
                        height=80,
                        disabled=True,
                        key=f"ocr_main_{img.id}"
                    )
                
                # Display AI description if available
                if img.llm_description:
                    st.text_area(
                        "AI Generated Description",
                        img.llm_description,
                        height=80,
                        disabled=True,
                        key=f"ai_desc_main_{img.id}"
                    )
                
                # Action buttons in a single row
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button("👁️ Preview", key=f"preview_img_main_{img.id}"):
                        show_image_preview(img)
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_img_main_{img.id}"):
                        doc.images.remove(img)
                        st.rerun()
                with col3:
                    if st.button("💾 Save", key=f"save_img_main_{img.id}"):
                        img.status = ImageStatus.APPROVED
                        st.success("✅ Image saved!")
            
            st.divider()

def process_document(uploaded_file):
    """Process the uploaded document"""
    st.session_state.processing = True
    
    with st.spinner("Processing document..."):
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_path = tmp_file.name
            
            # Create document instance
            doc = Document(
                title=uploaded_file.name,
                document_type=DocumentType(uploaded_file.name.split('.')[-1].lower()),
                file_path=temp_path,
                total_pages=1,
                status="processing"
            )
            
            # Extract text based on document type
            if doc.document_type == DocumentType.DOCX:
                doc.processed_text = extract_text_from_docx(temp_path)
            elif doc.document_type == DocumentType.PPTX:
                doc.processed_text = extract_text_from_pptx(temp_path)
            elif doc.document_type == DocumentType.PDF:
                doc.processed_text = extract_text_from_pdf(temp_path)
            
            # Extract images and process them
            try:
                description_list, generated_description_list = Extract_Office(temp_path)
                
                # Create image objects
                for i, (ocr_text, ai_desc) in enumerate(zip(description_list, generated_description_list)):
                    img_obj = Image(
                        page_number=i + 1,
                        file_path=f"extracted_images/image_{i}.png",
                        base64_image=None,  # Add missing field
                        original_text=ocr_text,
                        llm_description=ai_desc,
                        status=ImageStatus.PENDING
                    )
                    doc.images.append(img_obj)
                    
            except Exception as e:
                st.warning(f"Could not extract images: {str(e)[:100]}...")
            
            # Update document status
            doc.status = "completed"
            
            # Add to session state
            st.session_state.documents.append(doc)
            st.session_state.current_document = doc
            st.session_state.processing = False
            
            st.success(f"✅ Document {uploaded_file.name} processed successfully!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error processing document: {str(e)}")
            st.session_state.processing = False

def export_document(doc):
    """Export the processed document"""
    try:
        # Create export content
        export_content = f"# {doc.title}\n\n"
        export_content += f"**Document Type:** {doc.document_type.value.upper()}\n"
        export_content += f"**Processed Date:** {doc.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if doc.processed_text:
            export_content += "## Extracted Text\n\n"
            export_content += doc.processed_text + "\n\n"
            
            if doc.images:
                export_content += "## Images and Descriptions\n\n"
            for i, img in enumerate(doc.images):
                export_content += f"### Image {i+1} (Page {img.page_number})\n\n"
                if img.original_text:
                    export_content += f"**OCR Text:** {img.original_text}\n\n"
                if img.llm_description:
                    export_content += f"**AI Description:** {img.llm_description}\n\n"
        
        # Provide download
        st.download_button(
            label="📥 Download Processed Document",
            data=export_content,
            file_name=f"{doc.title}_processed.md",
            mime="text/markdown"
        )
        
    except Exception as e:
        st.error(f"Error exporting document: {e}")

def show_text_preview(text):
    """Show text in an expanded view"""
    with st.expander("📝 Full Text Preview", expanded=True):
        st.text(text)

def show_image_preview(img):
    """Show image in an expanded view"""
    with st.expander(f"🖼️ Full Image Preview - Page {img.page_number}", expanded=True):
        if os.path.exists(img.file_path):
            try:
                pil_img = PILImage.open(img.file_path)
                st.image(pil_img, use_column_width=True)
            except Exception as e:
                st.error(f"Error loading image: {e}")
        
        if img.original_text:
            st.subheader("OCR Text")
            st.text(img.original_text)
        
        if img.llm_description:
            st.subheader("AI Description")
            st.text(img.llm_description)

if __name__ == "__main__":
    main() 