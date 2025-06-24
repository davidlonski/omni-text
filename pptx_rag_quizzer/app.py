import warnings

import streamlit as st
import io
from PIL import Image
import os
from dotenv import load_dotenv

# Import the modules from our package
from pptx_rag_quizzer.utils import configure_gemini, ExtractText_LLM, ExtractText_OCR, clean_text, clean_text_with_llm
from pptx_rag_quizzer.file_parser import parse_powerpoint
from pptx_rag_quizzer.rag_core import RAGCore
from pptx_rag_quizzer.quiz_master import QuizMaster

# --- Page Configuration ---
st.set_page_config(
    page_title="PowerPoint RAG Quizzer",
    page_icon="🧠",
    layout="wide"
)

# Load environment variables
load_dotenv()

# Configure Gemini model
configure_gemini()

# --- Application Title ---
st.title("🧠 PowerPoint RAG Quizzer")
st.markdown("Upload a PowerPoint, describe its images, and test your knowledge with an AI-powered quiz.")

# --- Session State Initialization ---
def init_session_state():
    """Initialize session state variables."""
    if 'app_stage' not in st.session_state:
        st.session_state.app_stage = 'upload'
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = []
    if 'images_to_describe' not in st.session_state:
        st.session_state.images_to_describe = []
    if 'current_image_index' not in st.session_state:
        st.session_state.current_image_index = 0
    if 'rag_core' not in st.session_state:
        st.session_state.rag_core = None
    if 'quiz_master' not in st.session_state:
        st.session_state.quiz_master = None
    if 'quiz_data' not in st.session_state:
        st.session_state.quiz_data = {}
    if 'quiz_state' not in st.session_state:
        st.session_state.quiz_state = 'ready' # ready, question_generated, grading, hint, correct

init_session_state()

# --- Helper Functions ---
def reset_app():
    """Resets the application to its initial state."""
    st.cache_data.clear()
    st.cache_resource.clear()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- Sidebar ---
with st.sidebar:
    st.header("Configuration & Control")
    if st.button("Start Over"):
        reset_app()

# --- Main Application Flow ---

# STAGE 1: File Upload
if st.session_state.app_stage == 'upload':
    st.header("1. Upload Your PowerPoint")
    uploaded_file = st.file_uploader("Choose a .pptx file", type="pptx")
    if uploaded_file:
        with st.spinner("Parsing your PowerPoint..."):
            file_in_memory = io.BytesIO(uploaded_file.getvalue())
            st.session_state.extracted_data = parse_powerpoint(file_in_memory)
            st.session_state.images_to_describe = [
                item for item in st.session_state.extracted_data if item['type'] == 'image'
            ]
            st.session_state.current_image_index = 0
            st.success(f"Parsed! Found {len(st.session_state.extracted_data) - len(st.session_state.images_to_describe)} text blocks and {len(st.session_state.images_to_describe)} images.")
            
            if st.session_state.images_to_describe:
                st.session_state.app_stage = 'describe_images'
            else:
                st.session_state.app_stage = 'initialize_rag'
            st.rerun()

# STAGE 2: Describe Images
elif st.session_state.app_stage == 'describe_images':
    st.header("2. Describe the Images")
    total = len(st.session_state.images_to_describe)
    idx = st.session_state.current_image_index

    if idx < total:
        img_item = st.session_state.images_to_describe[idx]
        st.progress((idx + 1) / total)
        st.write(f"**Image {idx + 1} of {total}** (from Slide {img_item['slide_number']})")
        st.image(Image.open(io.BytesIO(img_item['content'])), use_column_width=True)

        # Extract text using LLM (Gemini)
        llm_description = ExtractText_LLM(img_item['content'], img_item['extension'])
        ocr_description = ExtractText_OCR(img_item['content'])

        cleaned_llm_text = clean_text(llm_description)
        cleaned_ocr_text = clean_text(ocr_description)

        description = cleaned_llm_text + "\n" + cleaned_ocr_text

        cleaned_text = clean_text_with_llm(description)



        
        description = st.text_area("What is important about this image?", key=f"desc_{img_item['id']}", value=cleaned_text)
        
        if st.button("Submit Description", key=f"submit_{idx}"):
            if description:
                # Add description to the main data list
                st.session_state.extracted_data.append({
                    "id": f"desc_{img_item['id']}",
                    "type": "text",
                    "content": f"Description for image on slide {img_item['slide_number']}: {description}",
                    "slide_number": img_item['slide_number'],
                    "source": "image_description"
                })
                st.session_state.current_image_index += 1
                st.rerun()
            else:
                st.warning("Please provide a description.")
    else:
        st.success("All images described!")
        st.session_state.app_stage = 'initialize_rag'
        st.rerun()

# STAGE 3: Initialize RAG
elif st.session_state.app_stage == 'initialize_rag':
    with st.spinner("Building the knowledge base... This may take a moment."):
        rag_core = RAGCore(st.session_state.extracted_data)
        if rag_core.build():
            st.session_state.rag_core = rag_core
            st.session_state.quiz_master = QuizMaster(rag_core)
            st.session_state.app_stage = 'quiz'
            st.success("Knowledge base ready! Let's start the quiz.")
            st.rerun()
        else:
            st.error("Failed to build knowledge base. No text content found.")
            st.session_state.app_stage = 'upload' # Go back to upload

# STAGE 4: Quiz
elif st.session_state.app_stage == 'quiz':
    st.header("3. Take the Quiz!")
    quiz_master = st.session_state.quiz_master
    
    col1, col2 = st.columns([2, 1])

    with col2:
        st.subheader("Quiz Controls")
        if st.button("Generate New Question", type="primary"):
            with st.spinner("Finding a topic and generating a question..."):
                quiz_data = quiz_master.generate_question()
                if quiz_data is None:
                    st.error("Failed to generate a question. Please make sure your PowerPoint was properly loaded and contains text content.")
                else:
                    st.session_state.quiz_data = quiz_data
                    st.session_state.quiz_state = 'question_generated'
                    st.rerun()

    with col1:
        if st.session_state.quiz_state == 'question_generated':
            q_data = st.session_state.quiz_data
            st.subheader("Your Question:")
            st.markdown(f"**{q_data['question']}**")

            with st.form(key='answer_form'):
                user_answer = st.text_area("Your Answer:")
                submit_button = st.form_submit_button(label='Submit Answer')

                if submit_button and user_answer:
                    with st.spinner("Grading your answer..."):
                        is_correct = quiz_master.grade_answer(q_data, user_answer)
                        if is_correct:
                            st.session_state.quiz_state = 'correct'
                        else:
                            st.session_state.user_answer = user_answer
                            st.session_state.quiz_state = 'hint'
                        st.rerun()
        
        elif st.session_state.quiz_state == 'correct':
            st.success("🎉 Correct! Well done!")
            st.balloons()
            st.info("Click 'Generate New Question' for your next challenge.")

        elif st.session_state.quiz_state == 'hint':
            st.error(f"That's not quite right. Your answer was: '{st.session_state.user_answer}'")
            with st.spinner("Generating a hint..."):
                hint = quiz_master.get_hint(st.session_state.quiz_data, st.session_state.user_answer)
                st.info(f"**Hint:** {hint}")
            # Reset to allow another try at the same question
            st.session_state.quiz_state = 'question_generated'
        
        else:
            st.info("Click 'Generate New Question' on the right to start the quiz!")
