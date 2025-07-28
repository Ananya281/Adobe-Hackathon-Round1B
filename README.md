# Challenge 1B – Intelligent Document Analyzer

## 🐳 Docker Setup

### Step 1: Build the Docker Image
`docker build -t challenge1b .`

## Input Format
Place your PDFs in:
/sample_dataset/input/collection

# Provide your persona query inside:
/sample_dataset/input/input.json (Filename must be input.json)

## Step 2: Run the Container

`docker run -v $(pwd):/app challenge1b`
