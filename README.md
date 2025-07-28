# Adobe Hackathon Round 1B – Intelligent Document Analyzer

A smart, Dockerized Python solution that mimics an intelligent document analyst. This tool extracts persona-driven insights from a collection of documents based on a specific job role and job-to-be-done query, enabling content filtering, summarization, and persona alignment.

---

## ✨ Features

- 🧠 Understands the persona and intent (job-to-be-done)
- 📄 Processes multiple PDFs at once
- 🔍 Performs semantic filtering, clustering, and highlighting of relevant sections
- 📦 Generates clean and structured JSON output
- 🐳 Docker-ready, no setup hassle
- 🔒 Fully offline — No internet or GPU required

---

## 🛠️ Tech Stack

| 🔧 Component     | 🚀 Technology         |
|------------------|------------------------|
| Language         | Python 3.10            |
| PDF Processing     | `pdfminer.six`, `PyMuPDF`         |
| NLP & AI       | `spaCy`, `transformers`, `scikit-learn`|
| Numerical Ops    | `Pandas`,`NumPy`                |
| Containerization | Docker                 |
| Architecture     | `linux/amd64 (x86_64)` |

---

## 📁 Project Structure

```
Adobe-Hackathon-Round1B/
├── Dockerfile                # Docker configuration
├── main.py                   # Main processing script
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
└── sample_dataset/
    ├── input/
    │   ├── collection/       # Place all input PDFs here
    │   └── input.json        # Persona query file (must be named exactly this)
    └── output/
        └── output.json       # Auto-generated output file
```

---

## 🚀 How to Run with Docker

Make sure Docker is installed and running.

#### ▶️ Step 1: Build the Docker Image

```
docker build --platform linux/amd64 -t adobe-hackathon-round1b .
```


#### ▶️ Step 2: Run the Container

```
docker run -v "$(pwd):/app" adobe-hackathon-round1b
```

Note:- for Windows users (Git Bash):
If you're running the Docker command on Windows using Git Bash or MSYS2, please add `winpty` before `docker run` to avoid TTY-related issues.

- 📥 Input PDFs: `sample_dataset/input/collection/`

- 🧑‍💼 Persona Query File: `sample_dataset/input/input.json` (must be named `input.json`)

- 📤 Output: `sample_dataset/output/result.json`

- 🔒 Network: Fully disabled (offline and secure)

## 📄 Input Format

🎯 Persona Input (input.json)

```
{
  "persona": "Academic Researcher",
  "job_to_be_done": "Research on latest methods for citation-based ranking"
}
```

- `"persona"`: Describes the role/user type (e.g., "Student", "Analyst", "Professor")

- `"job_to_be_done"`: Describes what they hope to accomplish using the document

## ✅ Output Format

```
The system produces a structured JSON with:

{
  "metadata": { ... },
  "matched_documents": [
    {
      "title": "Document Title",
      "relevance_score": 0.91,
      "summary": "This document discusses...",
      "highlights": ["Key sentence 1", "Key sentence 2"]
    },
    ...
  ],
  "extracted_topics": ["topic1", "topic2"]
}
```

Output file is saved at:

```
sample_dataset/output/result.json
```

---

## 📬 Deliverables

- 🧾 result.json (final output)

- 📝 approach_explanation.md (500–600 words) explaining:

    - Persona mapping logic
    - Clustering/filtering approach
    - Model or rule-based strategy used

- ⚙️ Execution instructions (this README)

---

## 🚫 Constraints

- Max: 10 documents

- Execution time: ⏱️ <5 mins

- No internet access during container execution

---

## 🧪 Sample Input for Testing

You can refer to the provided PDF and persona samples in the `sample_dataset/input/collection/` directory and test with a variety of roles like:

- 👩‍🏫 Academic Researcher

- 📊 Business Analyst

- 👨‍🎓 Undergraduate Student
