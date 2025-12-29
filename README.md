# PM Agent

AI agent that processes Granola meeting notes to extract:
- PM action items
- Development tickets (backend/frontend/design)
- Meeting summaries

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API key
```

3. Run:
```bash
python main.py
```

## Usage

### Basic Commands

Process latest meeting:
```bash
python main.py
```

Process all unprocessed meetings:
```bash
python main.py --all
```

Force reprocess latest meeting:
```bash
python main.py --force
```

### AI Provider Options

Use OpenAI instead of Anthropic:
```bash
python main.py --provider openai
```

Use a specific model:
```bash
python main.py --provider openai --model gpt-4o-mini
python main.py --provider anthropic --model claude-3-5-sonnet-20241022
```

### All Options

```
--all              Process all unprocessed meetings
--limit N          Process at most N meetings
--force            Reprocess even if already processed
--provider NAME    Use 'anthropic' or 'openai' (default: from .env)
--model NAME       Specific model to use
--output-dir PATH  Custom output directory
```

## Output

Results are saved to:
- `outputs/pm_tasks/` - PM action items (JSON)
- `outputs/dev_tickets/` - Development tickets (JSON)
- `outputs/summaries/` - Meeting summaries (Markdown)
