# AI Resume Analyzer

This project analyzes resumes (TXT/PDF/DOCX), scores them for ATS-friendliness, highlights keywords, and generates suggestions and a short AI summary.

Quick start

1. Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

2. Run the Streamlit app:

```powershell
python -m streamlit run app.py
```

Project layout

- `app.py` - Streamlit UI
- `utils/` - analyzer, parser, converter modules
- `tests/` - unit tests
- `samples/` - sample resumes for testing

Development

- Run tests: `python -m pytest -q`
- Formatting: `black .`
- Lint: `ruff .`

OpenAI / Deployment

- To enable AI features, install `openai` and set `OPENAI_API_KEY` in your environment.
- Example (PowerShell):

```powershell
$env:OPENAI_API_KEY = 'sk-...'
```

- For Streamlit Community Cloud deployment, add `OPENAI_API_KEY` as a secret in the app settings.
