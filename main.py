import os
import json
from datetime import datetime
from tqdm import tqdm
from sentence_transformers import SentenceTransformer, util
from pdfminer.high_level import extract_text
from heading_extractor import extract_title, extract_headings_accurate

# Load model (offline, CPU)
MODEL_PATH = "model/all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_PATH, device='cpu')

def extract_snippet(pdf_path, heading_text, max_chars=800):
    try:
        full_text = extract_text(pdf_path)
        idx = full_text.lower().find(heading_text.lower())
        if idx == -1:
            return ""
        snippet = full_text[idx:idx + max_chars]
        return ' '.join(snippet.split())
    except:
        return ""

def get_best_heading(pdf_path, persona, job, doc_name):
    title, title_page = extract_title(pdf_path)
    headings = extract_headings_accurate(pdf_path, title, title_page)

    if not headings:
        return None

    query = f"{persona}. {job}"
    query_embedding = model.encode(query, convert_to_tensor=True)

    heading_texts = [f"{h['level']} {h['text']}" for h in headings]
    heading_embeddings = model.encode(heading_texts, convert_to_tensor=True)

    similarities = util.cos_sim(query_embedding, heading_embeddings)[0]
    top_idx = int(similarities.argmax())

    top_heading = headings[top_idx]
    score = float(similarities[top_idx])

    return {
        "document": doc_name,
        "section_title": top_heading["text"],
        "page_number": top_heading["page"],
        "score": score,
        "refined_text": extract_snippet(pdf_path, top_heading["text"])
    }

def process_all(input_json_path, pdf_folder, output_path):
    with open(input_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    documents = data["documents"]
    persona = data["persona"]["role"]
    job = data["job_to_be_done"]["task"]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    all_best = []

    for doc in tqdm(documents, desc="Processing PDFs"):
        filename = doc["filename"]
        pdf_path = os.path.join(pdf_folder, filename)

        if not os.path.exists(pdf_path):
            print(f"⚠️ Skipping missing PDF: {filename}")
            continue

        best = get_best_heading(pdf_path, persona, job, filename)
        if best:
            all_best.append(best)

    # Sort by relevance score
    all_best.sort(key=lambda x: -x["score"])

    extracted_sections = []
    subsection_analysis = []

    for rank, item in enumerate(all_best, start=1):
        extracted_sections.append({
            "document": item["document"],
            "section_title": item["section_title"],
            "importance_rank": rank,
            "page_number": item["page_number"]
        })
        subsection_analysis.append({
            "document": item["document"],
            "refined_text": item["refined_text"],
            "page_number": item["page_number"]
        })

    final_output = {
        "metadata": {
            "input_documents": [d["filename"] for d in documents],
            "persona": persona,
            "job_to_be_done": job,
            "processing_timestamp": datetime.utcnow().isoformat()
        },
        "extracted_sections": extracted_sections,
        "subsection_analysis": subsection_analysis
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Output saved to: {output_path}")

if __name__ == "__main__":
    process_all(
        input_json_path="sample_dataset/input/input.json",
        pdf_folder="sample_dataset/input/collection",
        output_path="sample_dataset/output/output.json"
    )