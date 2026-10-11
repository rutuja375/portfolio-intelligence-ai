# Portfolio Intelligence AI

An AI-assisted financial investigation system that detects
unusual stock movements, analyzes portfolio impact, retrieves
relevant financial evidence, and generates grounded explanations.

## Project Goals

- Analyze historical and intraday market data
- Detect statistically significant stock movements
- Calculate portfolio returns and stock contributions
- Retrieve and rank relevant financial news
- Apply financial NLP and sentiment analysis
- Generate evidence-grounded AI explanations with citations
- Evaluate AI outputs for accuracy and reliability
- Deploy a production-style AI application

## Planned Technology Stack

- Python, Pandas, NumPy, scikit-learn
- PyTorch, Hugging Face Transformers, FinBERT
- LangChain, LangGraph, vector search
- FastAPI, PostgreSQL, React
- Docker, GitHub Actions, cloud deployment

## Development Status

Milestone 0: Project initialization and testing setup.

## Getting Started

Requires Python 3.12.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest -v
python -m ruff check backend