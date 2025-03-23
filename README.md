# Multi-Agent Workers

A powerful multi-agent system built with AutoGen for document search and log analysis.

## Features

- Document search and analysis across multiple formats:
  - Confluence pages
  - PDF documents
  - Word documents
- Intelligent log analysis:
  - Error pattern detection
  - Nested log tracing
  - Solution suggestions
- Multi-agent architecture:
  - Prompt Engineer Agent: Query interpretation
  - Triage Agent: Task distribution
  - Researcher Agent: Document search
  - Debug Agent: Log analysis

## Installation

1. Clone the repository:
```bash
git clone [your-repo-url]
cd multi-agent-workers
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configurations
```

## Project Structure

```
├── agents/              # Agent implementations
│   ├── prompt_agent.py  # Query interpretation
│   ├── triage_agent.py  # Task distribution
│   ├── research_agent.py# Document search
│   └── debug_agent.py   # Log analysis
├── processors/          # Document and log processors
│   ├── confluence.py    # Confluence integration
│   ├── pdf_processor.py # PDF handling
│   ├── docx_processor.py# Word doc handling
│   └── log_analyzer.py  # Log analysis
├── utils/              # Utility functions
└── config/             # Configuration files
```

## Usage

```python
from agents.prompt_agent import PromptAgent
from agents.triage_agent import TriageAgent

# Initialize agents
prompt_agent = PromptAgent()
triage_agent = TriageAgent()

# Process a query
response = prompt_agent.process_query("Find error logs from last week")
```

## Environment Variables

Create a `.env` file with:

```env
CONFLUENCE_URL=your_confluence_url
CONFLUENCE_USERNAME=your_username
CONFLUENCE_API_TOKEN=your_api_token
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

MIT License