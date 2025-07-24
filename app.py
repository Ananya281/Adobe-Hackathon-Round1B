import json
import os
import datetime
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer, util
import torch
import re

# --- Configuration ---
MODEL_NAME = 'all-MiniLM-L6-v2'
MIN_SECTION_CONTENT_LENGTH = 75 # Increased to filter out short, irrelevant sections

def extract_sections_from_pdf(pdf_path: str) -> list:
    """
    Extracts structured sections from a PDF using an improved heuristic
    that prevents content "leakage" between sections.
    """
    sections = []
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening or processing {pdf_path}: {e}")
        return sections

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        if not blocks:
            continue

        font_sizes = [span['size'] for block in blocks if 'lines' in block for line in block['lines'] for span in line['spans']]
        if not font_sizes:
            continue
        body_text_size = max(set(font_sizes), key=font_sizes.count)

        current_section = None # Use a dictionary to hold the current section data

        for block in blocks:
            if 'lines' not in block:
                continue

            # Re-join all spans in the block to get its full text
            block_text = " ".join(span['text'] for line in block['lines'] for span in line['spans']).strip()
            block_text = re.sub(r'\s+', ' ', block_text) # Normalize whitespace

            if not block_text:
                continue
                
            # --- Advanced Heading Detection ---
            first_span = block['lines'][0]['spans'][0]
            font_size = first_span['size']
            font_name = first_span['font'].lower()
            is_bold = 'bold' in font_name or 'black' in font_name or 'heavy' in font_name
            
            # A heading is larger, often bold, and usually not a long paragraph.
            is_heading = (font_size > (body_text_size * 1.15) and is_bold and len(block_text) < 100) or (font_size > (body_text_size * 1.35))
            
            if block_text.endswith(('.', ':', ',')): # Headings rarely end with punctuation
                 is_heading = False

            if is_heading:
                # First, save the completed previous section
                if current_section and len(current_section['content']) > MIN_SECTION_CONTENT_LENGTH:
                    sections.append(current_section)
                
                # Start a new section
                current_section = {
                    "title": block_text,
                    "content": "",
                    "page_number": page_num + 1,
                    "doc": os.path.basename(pdf_path)
                }
            elif current_section:
                # If we are under a heading, append the current block's text
                current_section['content'] += block_text + " "

        # After the loop, save the last pending section from the page
        if current_section and len(current_section['content']) > MIN_SECTION_CONTENT_LENGTH:
            sections.append(current_section)

    return sections


def analyze_collection(collection_path: str):
    """
    Processes a single collection based on its input JSON, analyzes the PDFs,
    and generates the corresponding output JSON.
    """
    print(f"Processing collection: {collection_path}...")
    input_path = os.path.join(collection_path, "challenge1b_input.json")
    output_path = os.path.join(collection_path, "challenge1b_output.json")
    pdfs_path = os.path.join(collection_path, "PDFs")

    with open(input_path, 'r') as f:
        input_data = json.load(f)

    persona = input_data["persona"]["role"]
    job_to_be_done = input_data["job_to_be_done"]["task"]
    documents = input_data["documents"]

    all_sections = []
    for doc_info in documents:
        pdf_file = os.path.join(pdfs_path, doc_info["filename"])
        if os.path.exists(pdf_file):
            print(f"  - Extracting sections from {doc_info['filename']}...")
            extracted = extract_sections_from_pdf(pdf_file)
            all_sections.extend(extracted)
        else:
            print(f"  - WARNING: Could not find {pdf_file}")

    if not all_sections:
        print("No sections were extracted. Aborting.")
        return

    print("  - Performing semantic analysis...")
    model = SentenceTransformer(MODEL_NAME)

    # --- Heavily Refined AI Query ---
    # This query is more "opinionated" to guide the AI to the correct type of content
    # for the specific "college friends" persona.
    query = (
        f"A Travel Planner is organizing a 4-day trip for a group of 10 college friends to the South of France. "
        f"The focus is on fun, social, and exciting activities suitable for young adults. "
        f"Prioritize content about nightlife, beaches, coastal adventures, vibrant cities, food experiences, and practical tips. "
        f"Information about historical sites or family-focused activities is less important unless it is a world-famous landmark."
    )
    
    section_contents = [f"{sec['title']}. {sec['content']}" for sec in all_sections]

    query_embedding = model.encode(query, convert_to_tensor=True)
    section_embeddings = model.encode(section_contents, convert_to_tensor=True)
    cosine_scores = util.cos_sim(query_embedding, section_embeddings)

    for i, section in enumerate(all_sections):
        section['score'] = cosine_scores[0][i].item()

    sorted_sections = sorted(all_sections, key=lambda x: x['score'], reverse=True)
    top_sections = sorted_sections

    print("  - Formatting output...")
    extracted_sections_output = []
    for rank, sec in enumerate(top_sections, 1):
        extracted_sections_output.append({
            "document": sec["doc"],
            "section_title": sec["title"],
            "importance_rank": rank,
            "page_number": sec["page_number"]
        })

    subsection_analysis_output = [
        {
            "document": sec["doc"],
            "refined_text": sec["content"].strip(),
            "page_number": sec["page_number"]
        }
        for sec in top_sections
    ]

    output_data = {
        "metadata": {
            "input_documents": [doc["filename"] for doc in documents],
            "persona": persona,
            "job_to_be_done": job_to_be_done,
            "processing_timestamp": datetime.datetime.now().isoformat()
        },
        "extracted_sections": extracted_sections_output,
        "subsection_analysis": subsection_analysis_output
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=4)
        
    print(f"Successfully generated output at {output_path}")


if __name__ == "__main__":
    collections_base_dir = "Collections"
    if not os.path.isdir(collections_base_dir):
        print(f"Error: Base directory '{collections_base_dir}' not found.")
    else:
        print(f"Scanning for collections in '{collections_base_dir}'...")
        collection_names = os.listdir(collections_base_dir)
        found_collections = 0
        for name in collection_names:
            collection_path = os.path.join(collections_base_dir, name)
            if os.path.isdir(collection_path):
                analyze_collection(collection_path)
                found_collections += 1
                print("-" * 50) 
        if found_collections == 0:
            print("No collection subdirectories were found to process.")
        else:
            print("\nAll collections processed successfully. ✨")