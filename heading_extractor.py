import os
import re
import json
import numpy as np
from difflib import SequenceMatcher
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar
from sklearn.cluster import KMeans

# ----------- Title Extraction -----------

def extract_title(pdf_path):
    title_candidates = []

    for page_layout in extract_pages(pdf_path):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    line_text = text_line.get_text().strip()
                    if not line_text or len(line_text) < 3:
                        continue

                    font_sizes = []
                    font_names = []

                    for char in text_line:
                        if isinstance(char, LTChar):
                            font_sizes.append(char.size)
                            font_names.append(char.fontname)

                    if not font_sizes:
                        continue

                    avg_size = sum(font_sizes) / len(font_sizes)
                    is_bold = any("Bold" in fn or "bold" in fn for fn in font_names)

                    if text_line.y1 > page_layout.height * 0.75 and avg_size > 10:
                        score = avg_size + (5 if is_bold else 0)
                        title_candidates.append({
                            "text": line_text,
                            "score": score,
                            "font_size": avg_size,
                            "y_pos": text_line.y1
                        })
        break  # only first page

    if not title_candidates:
        return None, None

    title_candidates.sort(key=lambda x: (-x['score'], -x['y_pos']))
    best = title_candidates[0]
    best_title = re.sub(r'\s+', ' ', best['text']).strip()
    return best_title, 1

# ----------- Heading Extraction -----------

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def is_heading_candidate(text):
    if len(text) < 3 or len(text) > 100:
        return False
    if text[-1] in ".!?":
        return False
    if text.lower() in ['the', 'a', 'an', 'and', 'for', 'we', 'our', 'in this']:
        return False
    if len(text.split()) > 12:
        return False
    return True

def is_similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > 0.85

def remove_duplicates(headings, title_text=None, title_page=None):
    seen = set()
    filtered = []
    for h in headings:
        if title_text and title_page:
            if h['page'] == title_page and is_similar(h['text'], title_text):
                continue

        key = (h['text'].lower(), h['level'])
        if key not in seen:
            filtered.append(h)
            seen.add(key)
    return filtered

def extract_headings_accurate(pdf_path, title_text=None, title_page=None):
    line_items = []
    font_sizes = []

    for page_num, layout in enumerate(extract_pages(pdf_path)):
        for element in layout:
            if not isinstance(element, LTTextContainer):
                continue
            for line in element:
                if not hasattr(line, 'get_text'):
                    continue

                text = clean_text(line.get_text())
                if not is_heading_candidate(text):
                    continue

                chars = [c for c in line if isinstance(c, LTChar)]
                if not chars:
                    continue

                avg_size = sum(c.size for c in chars) / len(chars)
                font_sizes.append(avg_size)

                bold = any('Bold' in c.fontname or 'bold' in c.fontname for c in chars)
                caps_ratio = sum(1 for ch in text if ch.isupper()) / len(text)
                position_y = line.y1

                line_items.append({
                    'text': text,
                    'size': avg_size,
                    'bold': bold,
                    'caps_ratio': caps_ratio,
                    'y': position_y,
                    'page': page_num + 1
                })

    if not font_sizes or not line_items:
        return []

    font_sizes_arr = np.array(font_sizes).reshape(-1, 1)
    cluster_count = min(3, len(set(font_sizes)))
    kmeans = KMeans(n_clusters=cluster_count, n_init=10)
    kmeans.fit(font_sizes_arr)

    font_to_cluster = {}
    for size, label in zip(font_sizes, kmeans.labels_):
        font_to_cluster[size] = label

    cluster_centers = kmeans.cluster_centers_.flatten()
    sorted_clusters = np.argsort(cluster_centers)[::-1]
    cluster_to_level = {cluster: f"H{i+1}" for i, cluster in enumerate(sorted_clusters)}

    results = []
    for item in line_items:
        cluster = font_to_cluster.get(item['size'])
        if cluster is None:
            continue
        level = cluster_to_level.get(cluster, "H3")

        score = 0
        if item['bold']:
            score += 1
        if item['caps_ratio'] > 0.5:
            score += 1
        if item['y'] > 400:
            score += 1
        if len(item['text']) < 60:
            score += 1

        if score >= 3:
            results.append({
                "level": level,
                "text": item['text'],
                "page": item['page']
            })

    return remove_duplicates(results, title_text, title_page)

# ----------- Main Pipeline -----------

def analyze_pdf(pdf_path):
    title_text, title_page = extract_title(pdf_path)
    headings = extract_headings_accurate(pdf_path, title_text, title_page)
    return {
        "title": title_text,
        "outline": headings
    }

def process_all_pdfs(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_folder, filename)
            print(f"Processing: {filename}")
            result = analyze_pdf(pdf_path)
            output_path = os.path.join(output_folder, filename.replace(".pdf", ".json"))
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Saved: {output_path}")

# ----------- Entry Point -----------

if __name__ == "__main__":
    process_all_pdfs("sample_dataset/pdfs", "sample_dataset/output")
