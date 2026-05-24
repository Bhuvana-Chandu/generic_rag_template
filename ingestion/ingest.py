"""
Property & Home Insurance AI Copilot - Knowledge Base Ingestion
Loads Markdown and CSVs, chunks them, and persists to FAISS.
"""
import sys
import os
import glob
import time
import shutil
import pandas as pd
from rich.console import Console

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, CSVLoader, PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()
console = Console()

DOCUMENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
FAISS_PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db", "faiss_index")

def load_and_chunk_documents():
    docs = []
    
    md_files = glob.glob(os.path.join(DOCUMENTS_DIR, "*.md"))
    csv_files = glob.glob(os.path.join(DOCUMENTS_DIR, "*.csv"))
    pdf_files = glob.glob(os.path.join(DOCUMENTS_DIR, "*.pdf"))

    console.print(f"Loading {len(md_files)} Markdown files, {len(csv_files)} CSV files, and {len(pdf_files)} PDF files...")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    for f in md_files:
        filename = os.path.basename(f)
        try:
            loader = TextLoader(f, encoding='utf-8')
            loaded = loader.load()
            for doc in loaded:
                doc.metadata["source_file"] = filename
            docs.extend(text_splitter.split_documents(loaded))
        except Exception as e:
            console.print(f"Skipping {filename}: {e}")

    for f in csv_files:
        filename = os.path.basename(f)
        try:
            loader = CSVLoader(f, encoding='utf-8')
            loaded = loader.load()
            for doc in loaded:
                doc.metadata["source_file"] = filename
            docs.extend(loaded)
        except Exception as e:
            console.print(f"Skipping {filename}: {e}")
            
    for f in pdf_files:
        filename = os.path.basename(f)
        try:
            loader = PyPDFLoader(f)
            loaded = loader.load()
            for doc in loaded:
                doc.metadata["source_file"] = filename
            docs.extend(text_splitter.split_documents(loaded))
        except Exception as e:
            console.print(f"Skipping {filename}: {e}")
            
    console.print(f"Created {len(docs)} chunks.")
    return docs

def build_vector_store(chunks):
    if not chunks:
        console.print("No chunks to embed.")
        return None

    if os.path.exists(FAISS_PERSIST_DIR):
        shutil.rmtree(FAISS_PERSIST_DIR)
        console.print("Cleared previous database")
        
    console.print(f"Embedding {len(chunks)} chunks into FAISS at {FAISS_PERSIST_DIR}...")
    
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(FAISS_PERSIST_DIR)
    
    console.print("FAISS persisted successfully!")
    return vectorstore

def main():
    console.print("===================================================")
    console.print("   Insurance Copilot Knowledge Base -- Ingestion")
    console.print("===================================================")

    if not os.path.exists(DOCUMENTS_DIR):
        os.makedirs(DOCUMENTS_DIR)

    chunks = load_and_chunk_documents()
    build_vector_store(chunks)
    console.print("===================================================")
    console.print("Ingestion Pipeline Complete.")

if __name__ == "__main__":
    main()
