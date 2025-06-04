# Omni-Text 📝

Omni-Text is a powerful document processing tool designed specifically for teachers. It converts office documents (DOCX, PPTX, XLSX, PDF) into accessible plain text while maintaining the document's structure and context.

## Features

- Converts various office document formats to plain text
- Extracts and processes images from documents
- Uses OCR to extract text from images
- Generates AI-powered descriptions of images
- Maintains document structure and page order
- Teacher approval workflow for image descriptions
- User-friendly interface built with Streamlit

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/omni-text.git
cd omni-text
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

4. Set up your environment variables:
   Create a `.env` file in the root directory and add your API keys:

```
OPENAI_API_KEY=your_openai_api_key
```

## Usage

1. Start the Streamlit application:

```bash
streamlit run app.py
```

2. Open your web browser and navigate to the provided local URL (typically http://localhost:8501)
3. Upload your document through the web interface
4. Review and approve image descriptions
5. Download the processed text document

## Data Schema

The application uses the following main data models:

- **Document**: Represents the uploaded document with metadata and processing status
- **Image**: Represents images extracted from the document with OCR text and AI descriptions
- **ProcessingJob**: Tracks the status of document processing tasks

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
