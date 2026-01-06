# PM Agent

AI agent that processes **Granola** meeting notes to extract:
- PM action items
- Development tickets (backend/frontend/design)
- Meeting summaries

## Features

- 🎙️ **Full Transcript Access**: Fetches complete meeting transcripts with speaker labels
- 📝 **Comprehensive Context**: Combines transcript + enhanced notes + manual notes
- 🤖 **Multi-AI Provider**: Works with OpenAI (GPT-4) or Anthropic (Claude)
- 📊 **Structured Extraction**: Automatically categorizes action items and tickets
- 🔄 **Smart Tracking**: Avoids reprocessing the same meetings
- 💾 **Multiple Output Formats**: JSON for integration, Markdown for Slack

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. **Setup:**
- Granola must be installed and you must be logged in
- No additional configuration needed - uses Granola's local credentials
- **Automatically fetches full transcripts** for meetings with transcription
- Combines: Transcript + Enhanced Notes + Manual Notes for complete context

4. **Run:**
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

Process specific number of meetings:
```bash
python main.py --limit 5
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
--debug            Show API request/response details
--verbose          Show parsing details
```

### Troubleshooting

If meetings appear empty or too short:
```bash
python main.py --verbose
```

To see API details and parsing:
```bash
python main.py --debug --verbose
```

## What Gets Analyzed

The AI receives comprehensive meeting context:
1. **📜 Transcript** - Full meeting transcript with speaker labels (if available)
2. **✨ Enhanced Notes** - Granola's AI-enhanced notes
3. **📝 Manual Notes** - Your manually typed notes

All three sources are automatically combined for maximum context.

## Output

Results are saved to:
- `outputs/pm_tasks/` - PM action items (JSON)
- `outputs/dev_tickets/` - Development tickets (JSON)
- `outputs/summaries/` - Meeting summaries (Markdown)

## Automation

To automatically process new meetings, set up a scheduled job:

**macOS/Linux (cron):**
```bash
# Edit crontab
crontab -e

# Add this line to run every 10 minutes
*/10 * * * * cd /path/to/pm-agent && source venv/bin/activate && python main.py --all >> /tmp/pm-agent.log 2>&1
```

**macOS (launchd) - More Reliable:**

Create `~/Library/LaunchAgents/com.pm-agent.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pm-agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/pm-agent/venv/bin/python</string>
        <string>/path/to/pm-agent/main.py</string>
        <string>--all</string>
    </array>
    <key>StartInterval</key>
    <integer>600</integer> <!-- Run every 10 minutes -->
    <key>StandardOutPath</key>
    <string>/tmp/pm-agent.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/pm-agent-error.log</string>
</dict>
</plist>
```

Then load it:
```bash
launchctl load ~/Library/LaunchAgents/com.pm-agent.plist
```

**Workflow:**
1. Finish your meeting in Granola
2. Granola automatically processes and enhances notes
3. Automated script picks up new meetings within 10 minutes
4. PM tasks and dev tickets automatically generated
5. Check `outputs/` folder for results
