# setup.py
from setuptools import setup, find_packages

setup(
    name="pptx_rag_quizzer",
    version="0.1.0",
    packages=find_packages(),
    author="Your Name",
    author_email="your.email@example.com",
    description="A Streamlit app to create an interactive RAG quiz from PowerPoint files.",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=open('requirements.txt').read().splitlines(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: Streamlit",
    ],
)
