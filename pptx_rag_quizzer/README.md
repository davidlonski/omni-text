# PowerPoint RAG Quizzer

This Streamlit application transforms a PowerPoint presentation into an interactive study tool. It uses a Retrieval-Augmented Generation (RAG) pipeline with Google's Gemini model to create a quiz based on the document's content.

## Features

- **File Upload:** Upload any `.pptx` file.
- **Content Extraction:** Automatically extracts all text and images from the presentation in their natural reading order.
- **Image Contextualization:** Prompts the user to provide descriptions for each image, which are then added to the knowledge base.
- **RAG Pipeline:** Builds an in-memory vector database using `ChromaDB` and `Sentence-Transformers` for efficient information retrieval.
- **AI-Powered Quiz:**
  - Generates questions based on the document's content using the Gemini 2.0 Flash model.
  - Grades user answers.
  - Provides intelligent hints for incorrect answers, guiding the user toward the correct information.

## How to Run

1.  **Clone the repository or create the files** as specified in the project structure.

2.  **Set up a virtual environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the package in editable mode:**
    This command will also install all the dependencies from `requirements.txt`.
    ```bash
    pip install -e .
    ```

4.  **Set up your API Key:**
    Create a `.env` file in the project root directory and add your Google Gemini API key:
    ```
    GOOGLE_API_KEY=your_api_key_here
    ```

5.  **Run the Streamlit App:**
    ```bash
    streamlit run app.py
    ```

6.  **Open your browser** to the local URL provided by Streamlit (usually `http://localhost:8501`).

