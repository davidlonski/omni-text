import streamlit as st
import chromadb
from sentence_transformers import SentenceTransformer
import uuid
import random
import json

@st.cache_resource
def get_embedding_model():
    """Loads and caches the sentence-transformer model."""
    return SentenceTransformer('all-MiniLM-L6-v2')

class RAGCore:
    """Handles the core Retrieval-Augmented Generation pipeline."""
    
    def __init__(self, extracted_data):
        """
        Initializes the RAGCore with extracted data.

        Args:
            extracted_data (list[dict]): The parsed content from the PowerPoint.
        """
        self.extracted_data = extracted_data
        self.embedding_model = get_embedding_model()
        self.chroma_client = chromadb.Client() # In-memory client
        self.collection = None

    def build(self):
        """
        Builds the vector database from the text content and image descriptions.

        This method extracts text, creates embeddings, and populates the
        ChromaDB collection.

        Returns:
            bool: True if the build was successful, False otherwise.
        """
        all_texts = []
        all_ids = []
        all_metadatas = []
        
        # Process text items
        for item in self.extracted_data:
            if item['type'] == 'text':
                all_texts.append(item['content'])
                all_ids.append(item['id'])
                all_metadatas.append({
                    "slide_number": item['slide_number'], 
                    "source": item['source']
                })
            elif item['type'] == 'image' and 'description' in item:
                # Include image descriptions as text content
                all_texts.append(f"Image on slide {item['slide_number']}: {item['description']}")
                all_ids.append(f"img_desc_{item['id']}")
                all_metadatas.append({
                    "slide_number": item['slide_number'], 
                    "source": "image_description"
                })
        
        if not all_texts:
            st.error("No text content available to build the knowledge base.")
            return False

        # Create embeddings
        embeddings = self.embedding_model.encode(all_texts, show_progress_bar=True)
        
        # Create and populate ChromaDB collection
        collection_name = f"ppt_rag_{uuid.uuid4().hex}"
        self.collection = self.chroma_client.create_collection(name=collection_name)
        
        self.collection.add(
            embeddings=embeddings,
            documents=all_texts,
            metadatas=all_metadatas,
            ids=all_ids
        )
        return True

    def get_random_context(self):
        """
        Retrieves a random document (context) from the vector store.

        Returns:
            str or None: A piece of text from the document, or None if the
                         collection is empty.
        """
        if self.collection and self.collection.count() > 0:
            
            # Get all documents and select randomly
            all_docs = self.collection.get()['documents']
            
            if all_docs:
                random_content = random.choice(all_docs)
                print("--------------------------------")
                print("This is all the context to choose from: ", all_docs)
                print("--------------------------------")
                print("This is the random content: ", random_content)
                print("--------------------------------")
                return random_content
        return None
