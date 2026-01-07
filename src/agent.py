"""
AI agent for processing meeting notes and extracting action items.
"""
import os
from typing import Dict, List, Optional
import json
from anthropic import Anthropic
from openai import OpenAI
from .config import get_config


class MeetingProcessor:
    """AI agent for extracting structured information from meeting notes."""

    def __init__(self, provider: str = "anthropic", api_key: Optional[str] = None, config=None):
        """
        Initialize the meeting processor.

        Args:
            provider: AI provider to use ("anthropic" or "openai")
            api_key: API key for the provider. If None, will read from env var.
            config: Config instance. If None, will load from get_config()
        """
        self.provider = provider.lower()
        self.config = config or get_config()

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
        # Use configured prompts
        system_prompt = self.config.system_prompt
        extraction_prompt = self.config.extraction_prompt.format(meeting_notes=meeting_notes)

        if self.provider == "anthropic":
            model = model or self.config.ai_model or "claude-3-5-sonnet-20241022"
            message = self.client.messages.create(
                model=model,
                max_tokens=self.config.max_tokens,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": extraction_prompt
                    }
                ]
            )
            response_text = message.content[0].text

        elif self.provider == "openai":
            model = model or self.config.ai_model or "gpt-4o"

            # Build API call parameters
            api_params = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": extraction_prompt
                    }
                ],
                "max_completion_tokens": self.config.max_tokens,
            }

            # Some models don't support temperature or system messages
            # O1 models and certain experimental models only support temperature=1
            models_without_temperature = ["o1", "gpt-5"]
            supports_temperature = not any(model.startswith(prefix) for prefix in models_without_temperature)

            if supports_temperature:
                api_params["temperature"] = self.config.ai_temperature
            else:
                # Models without temperature support may also need combined messages
                # O1 models require developer messages instead of system
                api_params["messages"] = [
                    {
                        "role": "user",
                        "content": f"{system_prompt}\n\n{extraction_prompt}"
                    }
                ]

            try:
                completion = self.client.chat.completions.create(**api_params)
                response_text = completion.choices[0].message.content
            except Exception as e:
                raise ValueError(f"OpenAI API error: {e}")

            # Check for empty response
            if not response_text or not response_text.strip():
                raise ValueError(
                    f"AI returned empty response. This may indicate the model '{model}' "
                    f"doesn't exist or isn't compatible with this task. "
                    f"Try using 'gpt-4o' or 'gpt-4o-mini' instead."
                )

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
            raise ValueError(
                f"Failed to parse AI response as JSON: {e}\n\n"
                f"Response preview: {response_text[:500]}...\n\n"
                f"This may indicate the model '{model}' doesn't follow JSON output format. "
                f"Try using 'gpt-4o' or 'gpt-4o-mini' instead."
            )

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
                    # Try to convert name to Slack handle
                    slack_handle = self.config.get_slack_handle(item["assignee"])
                    display_name = slack_handle if slack_handle else item["assignee"]
                    message_parts.append(f"• [{display_name}] {item['text']}")
                else:
                    message_parts.append(f"• {item['text']}")
            message_parts.append("")

        # Next Steps
        if summary.get("next_steps"):
            message_parts.append("*Next Steps*")
            for step in summary["next_steps"]:
                message_parts.append(f"• {step}")

        return "\n".join(message_parts)
