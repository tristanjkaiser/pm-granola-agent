# PM Agent Customization Guide

This guide explains how to customize PM Agent for your team and share it with other PMs.

## For Individual PMs

### Quick Customization

Edit your `.env` file with these essentials:

```bash
# 1. Add your API key
OPENAI_API_KEY=your_key_here

# 2. Add team Slack handles (for @mentions)
SLACK_HANDLES=Your Name:@yourhandle, Teammate:@teammate

# 3. Add company context (helps AI understand your workflow)
COMPANY_CONTEXT=We build SaaS products for enterprise clients. Tech: React, Node.js, AWS.
```

That's it! These three settings make a huge difference.

## For Team Leads: Sharing with Other PMs

### Option 1: Create a Team Template

1. **Create `.env.template` for your team:**

```bash
# ============================================================================
# ACME CORP PM AGENT CONFIGURATION
# ============================================================================

# AI Configuration
AI_PROVIDER=openai
OPENAI_API_KEY=YOUR_KEY_HERE  # ← Each PM adds their own key

# Company Context (pre-filled for your team)
COMPANY_CONTEXT=Acme builds B2B SaaS products for financial services. Tech stack: React, Node.js, PostgreSQL, AWS. PMs work with distributed teams across 3 time zones.
PM_ROLE_DESCRIPTION=PMs at Acme own product roadmaps, coordinate with engineering and design, and manage client relationships.

# Team Slack Handles (pre-filled)
SLACK_HANDLES=Sarah Chen:@sarah, Mike Johnson:@mike, Priya Patel:@priya, Alex Kim:@alex

# Meeting Preferences (pre-configured)
SKIP_RECURRING_KEYWORDS=Daily Standup,Team Sync,1-on-1
PRIORITY_KEYWORDS=urgent,blocker,p0,critical

# Granola Configuration
GRANOLA_CREDENTIALS_PATH=~/Library/Application Support/Granola/supabase.json
OUTPUT_DIR=./outputs
```

2. **Share with your team:**

```bash
# Send them:
1. The repo link
2. The .env.template file
3. Instructions: "Copy .env.template to .env, add your OpenAI key on line 5, done!"
```

### Option 2: Use JSON for Team Handles

For larger teams, use `config/team-handles.json`:

```json
{
  "Sarah Chen": "@sarah",
  "Mike Johnson": "@mike",
  "Priya Patel": "@priya",
  "Alex Kim": "@alex",
  "Jordan Lee": "@jordan",
  "Taylor Brown": "@taylor"
}
```

Then in `.env`:
```bash
SLACK_HANDLES_FILE=./config/team-handles.json
```

## Advanced Customizations

### Custom AI Prompts

If your team has specific needs (e.g., Agile ceremonies, OKR tracking), customize the prompts:

```bash
# Add context to default prompts
COMPANY_CONTEXT=We follow Shape Up methodology. Work in 6-week cycles. No estimates, use appetite instead.

# OR completely override (advanced)
SYSTEM_PROMPT_OVERRIDE=You are analyzing Shape Up cycle planning meetings. Extract bets, appetites, and cool-down tasks. Format for Basecamp Hill Charts...
```

### Skip Specific Meeting Types

```bash
# Don't process these meetings
SKIP_RECURRING_KEYWORDS=Daily Standup,Sprint Planning,Retro,1-on-1,Coffee Chat,Team Lunch
```

### Auto-Priority Detection

```bash
# Keywords that mark items as high-priority
PRIORITY_KEYWORDS=urgent,blocker,p0,critical,asap,emergency,breaking
```

### Customize Ticket Types

```bash
# If your team tracks QA and DevOps work
DEV_TICKET_TYPES=backend,frontend,design,qa,devops,infrastructure

# Default labels for all generated tickets
DEFAULT_TICKET_LABELS=pm-agent,auto-generated,needs-review
```

## Configuration Reference

See [`.env.example`](.env.example) for all available options with detailed comments.

### Most Important Settings

| Setting | Purpose | Example |
|---------|---------|---------|
| `COMPANY_CONTEXT` | Help AI understand your business | `SaaS for healthcare` |
| `SLACK_HANDLES` | Auto-tag team members | `Name:@handle` |
| `SKIP_RECURRING_KEYWORDS` | Skip daily meetings | `Standup,1-on-1` |
| `PRIORITY_KEYWORDS` | Auto-detect urgent items | `urgent,blocker,asap` |
| `AI_MODEL` | Control cost/quality | `gpt-4o-mini` (cheaper) |

## Sharing Best Practices

### For Agencies/Consulting Firms

Pre-configure for client work:

```bash
COMPANY_CONTEXT=Digital agency. We build MVPs for startups in 8-12 week sprints. Most clients are non-technical founders.
PM_ROLE_DESCRIPTION=PMs translate business requirements into technical specs, manage scope, and ensure on-time delivery.
PRIORITY_KEYWORDS=client-request,urgent,blocker,launch-critical
```

### For Product Companies

Focus on product development:

```bash
COMPANY_CONTEXT=B2B SaaS company. We ship weekly. Product-led growth model. Engineering team of 15.
PM_ROLE_DESCRIPTION=PMs own roadmaps, gather user feedback, and coordinate cross-functional teams.
SKIP_RECURRING_KEYWORDS=Daily Standup,Weekly All-Hands,Team Retro
```

### For Distributed Teams

Emphasize async communication:

```bash
COMPANY_CONTEXT=Fully remote team across US, EU, and APAC time zones. Async-first culture.
PM_ROLE_DESCRIPTION=PMs coordinate asynchronously, document decisions clearly, and ensure all time zones stay informed.
```

## Testing Your Configuration

```bash
# Test that config loads correctly
python -c "from dotenv import load_dotenv; load_dotenv(); from src.config import get_config; c = get_config(); print(f'Context: {c.company_context}'); print(f'Handles: {c.slack_handles}')"

# Process a test meeting
python main.py --limit 1

# Check if Slack handles appear in output
cat outputs/summaries/*.md | grep "@"
```

## Troubleshooting

**Slack handles not working?**
- Check format: `Full Name:@handle` (with @ symbol)
- Names must match exactly as they appear in meeting notes
- First name matching works: "Tristan Kaiser" matches "Tristan"

**AI not understanding your company?**
- Add more specific context to `COMPANY_CONTEXT`
- Include your tech stack, industry, and workflow
- Keep it under 200 characters for best results

**Want to reset to defaults?**
- Delete or comment out custom settings in `.env`
- Restart the app to use built-in defaults

## Examples from Real Teams

### Example 1: Small Agency
```bash
COMPANY_CONTEXT=Boutique agency, 8 people, building mobile apps for local businesses
SLACK_HANDLES=Tom:@tom, Lisa:@lisa, Jay:@jay
SKIP_RECURRING_KEYWORDS=Standup,Check-in
```

### Example 2: Enterprise PM Team
```bash
COMPANY_CONTEXT=Fortune 500 fintech. Waterfall + Agile hybrid. Heavy compliance requirements. 6-month release cycles.
PM_ROLE_DESCRIPTION=PMs manage stakeholder alignment, write PRDs, and ensure regulatory compliance.
SKIP_RECURRING_KEYWORDS=Sprint Planning,Daily Scrum,Retrospective,Backlog Grooming
PRIORITY_KEYWORDS=sev-1,critical,regulatory,audit-finding
```

### Example 3: Startup
```bash
COMPANY_CONTEXT=Early-stage YC startup. Moving fast. Weekly deploys. Team of 5.
PM_ROLE_DESCRIPTION=PM wears many hats: product, customer success, and operations.
PRIORITY_KEYWORDS=urgent,launch-blocker,investor-demo,fundraising
AI_MODEL=gpt-4o-mini  # Save costs
```

## Support

Questions? Check:
1. [.env.example](.env.example) - Full configuration reference
2. [README.md](README.md) - Usage guide
3. [GitHub Issues](https://github.com/your-repo/issues) - Report bugs

---

**Pro Tip:** Start with just `COMPANY_CONTEXT` and `SLACK_HANDLES`. Add more customization as needed. You don't need to configure everything upfront!
