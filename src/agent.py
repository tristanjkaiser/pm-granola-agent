"""
AI agent for processing meeting notes and extracting action items.
"""
import os
from typing import Dict, List, Optional
import json
from anthropic import Anthropic
from openai import OpenAI


class MeetingProcessor:
    """AI agent for extracting structured information from meeting notes."""

    SYSTEM_PROMPT = """You are an AI assistant that analyzes meeting notes and extracts structured information.

Your task is to analyze meeting notes and extract:
1. Action items specifically for the PM (Product Manager)
2. Development tickets that need to be created (categorized as backend, frontend, or design)
3. A concise meeting summary plus any additional action items not captured in categories 1 or 2
4. Action items for anyone else. Use specific names to identify action item owners.

Be specific and actionable. For development tickets, include enough context that an engineer could understand what needs to be built."""

    EXTRACTION_PROMPT = """Analyze the following meeting notes and extract information in the specified JSON format.

Meeting Notes:
{meeting_notes}

Return a JSON object with this exact structure:
{{
  "pm_action_items": [
    {{
      "title": "Brief action item title",
      "description": "Detailed description of what needs to be done",
      "priority": "high|medium|low",
      "deadline": "any mentioned deadline or null"
    }}
  ],
  "dev_tickets": [
    {{
      "title": "Ticket title",
      "description": "Detailed technical description",
      "type": "backend|frontend|design",
      "priority": "high|medium|low",
      "acceptance_criteria": ["criterion 1", "criterion 2"]
    }}
  ],
  "summary": {{
    "overview": "2-3 sentence meeting summary",
    "key_decisions": ["decision 1", "decision 2"],
    "additional_action_items": [
      {{
        "assignee": "person name or 'unassigned'",
        "task": "what needs to be done"
      }}
    ],
    "next_steps": ["next step 1", "next step 2"]
  }}
}}

Only include items that are explicitly mentioned or clearly implied in the notes. If a section has no items, use an empty array."""

    def __init__(self, provider: str = "anthropic", api_key: Optional[str] = None):
        """
        Initialize the meeting processor.

        Args:
            provider: AI provider to use ("anthropic" or "openai")
            api_key: API key for the provider. If None, will read from env var.
        """
        self.provider = provider.lower()

        if self.provider == "anthropic":
            self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
            if not self.api_key:
                raise ValueError(
                    "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                    "or pass api_key parameter."
                )
            self.client = Anthropic(api_key=self.api_key)

        elif self.provider == "openai":
            self.api_key = api_key or os.getenv('OPENAI_API_KEY')
            if not self.api_key:
                raise ValueError(
                    "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                    "or pass api_key parameter."
                )
            self.client = OpenAI(api_key=self.api_key)

        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'anthropic' or 'openai'.")

    def process_meeting_notes(
        self,
        meeting_notes: str,
        model: Optional[str] = None
    ) -> Dict:
        """
        Process meeting notes and extract structured information.

        Args:
            meeting_notes: The meeting notes text
            model: Model to use. If None, uses default for provider.

        Returns:
            Dictionary with extracted information
        """
        prompt = self.EXTRACTION_PROMPT.format(meeting_notes=meeting_notes)

        if self.provider == "anthropic":
            model = model or "claude-3-5-sonnet-20241022"
            message = self.client.messages.create(
                model=model,
                max_tokens=4096,
                system=self.SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            response_text = message.content[0].text

        elif self.provider == "openai":
            model = model or "gpt-4o"

            # Build API call parameters
            api_params = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": self.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_completion_tokens": 4096,
            }

            # Some models don't support temperature or system messages
            # O1 models and certain experimental models only support temperature=1
            models_without_temperature = ["o1", "gpt-5"]
            supports_temperature = not any(model.startswith(prefix) for prefix in models_without_temperature)

            if supports_temperature:
                api_params["temperature"] = 0.7
            else:
                # Models without temperature support may also need combined messages
                # O1 models require developer messages instead of system
                api_params["messages"] = [
                    {
                        "role": "user",
                        "content": f"{self.SYSTEM_PROMPT}\n\n{prompt}"
                    }
                ]

            completion = self.client.chat.completions.create(**api_params)
            response_text = completion.choices[0].message.content

        # Parse JSON response
        try:
            # Try to extract JSON from markdown code blocks if present
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            result = json.loads(response_text)
            return result

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {e}\n\nResponse: {response_text}")

    def format_for_notion(self, pm_action_items: List[Dict]) -> List[Dict]:
        """
        Format PM action items for Notion database import.

        Args:
            pm_action_items: List of action items

        Returns:
            List formatted for Notion API
        """
        # Placeholder for future Notion integration
        return [
            {
                "Name": item["title"],
                "Description": item["description"],
                "Priority": item["priority"].capitalize(),
                "Deadline": item.get("deadline") or "No deadline",
                "Status": "To Do"
            }
            for item in pm_action_items
        ]

    def format_for_linear(self, dev_tickets: List[Dict]) -> List[Dict]:
        """
        Format dev tickets for Linear import.

        Args:
            dev_tickets: List of development tickets

        Returns:
            List formatted for Linear API
        """
        # Placeholder for future Linear integration
        return [
            {
                "title": ticket["title"],
                "description": ticket["description"],
                "priority": ticket["priority"],
                "labels": [ticket["type"]],
                "acceptance_criteria": ticket.get("acceptance_criteria", [])
            }
            for ticket in dev_tickets
        ]

    def format_for_slack(self, summary: Dict, pm_items: List[Dict], dev_tickets: List[Dict]) -> str:
        """
        Format meeting summary for Slack message.

        Args:
            summary: Meeting summary dictionary
            pm_items: PM action items
            dev_tickets: Development tickets

        Returns:
            Formatted Slack message (markdown)
        """
        message_parts = []

        # Meeting Overview
        message_parts.append("*Meeting Summary*")
        message_parts.append(summary["overview"])
        message_parts.append("")

        # Key Decisions
        if summary.get("key_decisions"):
            message_parts.append("*Key Decisions*")
            for decision in summary["key_decisions"]:
                message_parts.append(f"• {decision}")
            message_parts.append("")

        # Dev Tickets
        if dev_tickets:
            message_parts.append(f"*Development Tickets ({len(dev_tickets)})*")
            for ticket in dev_tickets:
                message_parts.append(f"• [{ticket['type'].upper()}] {ticket['title']}")
            message_parts.append("")

        # Combined Action Items (PM items + other action items)
        all_action_items = []

        # Add PM action items
        for item in pm_items:
            all_action_items.append({
                "text": item['title'],
                "assignee": None
            })

        # Add additional action items with assignees
        for item in summary.get("additional_action_items", []):
            assignee = item.get("assignee", "Unassigned")
            all_action_items.append({
                "text": item['task'],
                "assignee": assignee if assignee.lower() != "unassigned" else None
            })

        if all_action_items:
            message_parts.append(f"*Action Items ({len(all_action_items)})*")
            for item in all_action_items:
                if item["assignee"]:
                    message_parts.append(f"• [{item['assignee']}] {item['text']}")
                else:
                    message_parts.append(f"• {item['text']}")
            message_parts.append("")

        # Next Steps
        if summary.get("next_steps"):
            message_parts.append("*Next Steps*")
            for step in summary["next_steps"]:
                message_parts.append(f"• {step}")

        return "\n".join(message_parts)
