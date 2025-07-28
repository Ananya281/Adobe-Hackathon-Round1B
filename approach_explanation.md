# Challenge 1B – Approach Explanation

## 🔍 Objective
This challenge requires developing a system that takes multiple PDF documents as input, extracts their structural headings, analyzes their content, and ranks them based on semantic relevance to a user-provided persona query.

---

## 🧠 Methodology

### 1. **PDF Parsing & Structure Extraction**
We first extract all potential headings from each PDF using `pdfminer.six`. However, instead of relying on font size heuristics alone (which are inconsistent across documents), we use an ML-enhanced classifier based on text features, position, and formatting cues to identify real headings.

### 2. **Semantic Embedding using SBERT**
Each heading is passed through the **`sentence-transformers`** model (`all-MiniLM-L6-v2`) to convert the heading into a 384-dimensional dense vector. Similarly, the **persona query** is encoded into the same vector space.

### 3. **Relevance Scoring**
We compute the cosine similarity between each heading’s embedding and the persona query embedding using `util.cos_sim()`. This helps us quantify the semantic relevance of each heading to the persona.

### 4. **Output Format**
The final output is a sorted JSON
---

## ⚙️ Technologies Used
- Python 3.11
- `sentence-transformers` 5.0.0
- `transformers` 4.41.2
- `pdfminer.six`
- Dockerized environment for portability

---

## ✅ Advantages
- **Highly accurate semantic similarity using SBERT**
- **Very Fast**
- Fully offline and self-contained (except downloading model once)
- Scalable to a large number of PDFs

## 🔚 Conclusion
This system smartly extracts document insights based on meaning, not keywords or formatting, making it powerful for intelligent summarization and persona-based content navigation.
