import os
import json
import fitz  # PyMuPDF
from datetime import datetime
from sentence_transformers import SentenceTransformer, util

# Load sentence transformer model once
model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_sections(pdf_path, query, threshold=0.4):
    doc = fitz.open(pdf_path)
    sections = []
    subsections = []

    query_embedding = model.encode(query, convert_to_tensor=True)

    for i, page in enumerate(doc):
        text = page.get_text().strip()
        if not text:
            continue

        page_embedding = model.encode(text, convert_to_tensor=True)
        similarity = util.pytorch_cos_sim(query_embedding, page_embedding).item()

        if similarity > threshold:
            title = text.split('\n')[0][:100]
            sections.append({
                "document": os.path.basename(pdf_path),
                "section_title": title,
                "importance_rank": similarity,  # Will sort later
                "page_number": i + 1
            })
            subsections.append({
                "document": os.path.basename(pdf_path),
                "refined_text": text[:2000],
                "page_number": i + 1
            })

    return sections, subsections

def process_collection(collection_path):
    input_path = os.path.join(collection_path, "challenge1b_input.json")
    output_path = os.path.join(collection_path, "challenge1b_output.json")
    pdf_dir = os.path.join(collection_path, "PDFs")

    with open(input_path, 'r') as f:
        input_data = json.load(f)

    persona = input_data["persona"]["role"]
    task = input_data["job_to_be_done"]["task"]
    query = f"{persona} - {task}"

    extracted_sections = []
    subsection_analysis = []

    for doc in input_data["documents"]:
        pdf_path = os.path.join(pdf_dir, doc["filename"])
        sections, subs = extract_sections(pdf_path, query)
        extracted_sections.extend(sections)
        subsection_analysis.extend(subs)

    # Sort sections by semantic score descending, and re-rank
    extracted_sections.sort(key=lambda x: -x["importance_rank"])
    for rank, sec in enumerate(extracted_sections, 1):
        sec["importance_rank"] = rank

    output_data = {
        "metadata": {
            "input_documents": [doc["filename"] for doc in input_data["documents"]],
            "persona": persona,
            "job_to_be_done": task,
            "processing_timestamp": datetime.utcnow().isoformat()
        },
        "extracted_sections": extracted_sections,
        "subsection_analysis": subsection_analysis
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=4)

    print(f"✅ Processed: {collection_path}")

# 🔁 Run across all collections
base_path = "/Users/medhansh/Desktop/PROJECTS/ADOBE 2/Adobe-Hackathon-Round1B/Collections"
for collection in os.listdir(base_path):
    if "Collection" in collection:
        process_collection(os.path.join(base_path, collection))