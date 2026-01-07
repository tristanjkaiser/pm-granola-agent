"""
Configuration loader for PM Agent.

Loads configuration from environment variables with sensible defaults.
"""
import os
import json
from pathlib import Path
from typing import Dict, Optional


class Config:
    """Centralized configuration management."""

    # Default prompts
    DEFAULT_SYSTEM_PROMPT = """You are an AI assistant that analyzes meeting notes and extracts structured information.

Your task is to analyze meeting notes and extract:
1. Action items specifically for the PM (Product Manager)
2. Development tickets that need to be created (categorized as backend, frontend, or design)
3. A concise meeting summary plus any additional action items not captured in categories 1 or 2
4. Action items for anyone else. Use specific names to identify action item owners.

Be specific and actionable. For development tickets, include enough context that an engineer could understand what needs to be built."""

    DEFAULT_EXTRACTION_PROMPT = """Analyze the following meeting notes and extract information in the specified JSON format.

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

    def __init__(self):
        """Initialize configuration from environment variables."""
        # AI Configuration
        self.ai_provider = os.getenv('AI_PROVIDER', 'anthropic').lower()
        self.ai_model = os.getenv('AI_MODEL')
        self.ai_temperature = float(os.getenv('AI_TEMPERATURE', '0.7'))
        self.max_tokens = int(os.getenv('MAX_TOKENS', '4096'))

        # Prompts
        self.company_context = os.getenv('COMPANY_CONTEXT', '')
        self.pm_role_description = os.getenv('PM_ROLE_DESCRIPTION', '')
        self.system_prompt = self._load_system_prompt()
        self.extraction_prompt = self._load_extraction_prompt()

        # Slack Configuration
        self.slack_handles = self._load_slack_handles()
        self.slack_channel_default = os.getenv('SLACK_CHANNEL_DEFAULT', '')

        # Output Configuration
        self.include_timestamps = os.getenv('INCLUDE_TIMESTAMPS', 'true').lower() == 'true'
        self.include_document_id = os.getenv('INCLUDE_DOCUMENT_ID', 'true').lower() == 'true'
        self.summary_style = os.getenv('SUMMARY_STYLE', 'slack')

        # Processing Preferences
        self.min_meeting_length = int(os.getenv('MIN_MEETING_LENGTH', '100'))
        self.skip_keywords = self._parse_csv(os.getenv('SKIP_RECURRING_KEYWORDS', ''))
        self.priority_keywords = self._parse_csv(os.getenv('PRIORITY_KEYWORDS', 'urgent,blocker,asap'))

        # Ticket Configuration
        self.dev_ticket_types = self._parse_csv(
            os.getenv('DEV_TICKET_TYPES', 'backend,frontend,design')
        )
        self.default_ticket_labels = self._parse_csv(
            os.getenv('DEFAULT_TICKET_LABELS', '')
        )

    def _load_system_prompt(self) -> str:
        """Load system prompt with optional customization."""
        # Check for complete override
        override = os.getenv('SYSTEM_PROMPT_OVERRIDE')
        if override:
            return override

        # Use default with optional context injection
        prompt = self.DEFAULT_SYSTEM_PROMPT

        if self.company_context:
            prompt += f"\n\nCompany Context: {self.company_context}"

        if self.pm_role_description:
            prompt += f"\n\nPM Role: {self.pm_role_description}"

        return prompt

    def _load_extraction_prompt(self) -> str:
        """Load extraction prompt with optional customization."""
        override = os.getenv('EXTRACTION_PROMPT_OVERRIDE')
        if override:
            return override

        return self.DEFAULT_EXTRACTION_PROMPT

    def _load_slack_handles(self) -> Dict[str, str]:
        """
        Load Slack handle mappings from env var or JSON file.

        Returns:
            Dictionary mapping real names to Slack handles
        """
        # Try JSON file first
        handles_file = os.getenv('SLACK_HANDLES_FILE')
        if handles_file and Path(handles_file).exists():
            try:
                with open(handles_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse {handles_file}, using env var instead")

        # Try env var format: "Name:@handle, Name2:@handle2"
        handles_str = os.getenv('SLACK_HANDLES', '')
        if not handles_str:
            return {}

        handles = {}
        for pair in handles_str.split(','):
            pair = pair.strip()
            if ':' in pair:
                name, handle = pair.split(':', 1)
                handles[name.strip()] = handle.strip()

        return handles

    def _parse_csv(self, value: str) -> list:
        """Parse comma-separated values into a list."""
        if not value:
            return []
        return [item.strip() for item in value.split(',') if item.strip()]

    def should_skip_meeting(self, title: str) -> bool:
        """
        Check if meeting should be skipped based on keywords.

        Args:
            title: Meeting title

        Returns:
            True if meeting should be skipped
        """
        if not self.skip_keywords:
            return False

        title_lower = title.lower()
        return any(keyword.lower() in title_lower for keyword in self.skip_keywords)

    def is_high_priority(self, text: str) -> bool:
        """
        Check if text contains high-priority keywords.

        Args:
            text: Text to check

        Returns:
            True if high-priority keywords found
        """
        if not self.priority_keywords:
            return False

        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in self.priority_keywords)

    def get_slack_handle(self, name: str) -> Optional[str]:
        """
        Get Slack handle for a person's name.

        Args:
            name: Person's real name

        Returns:
            Slack handle (e.g., "@tristan") or None if not found
        """
        # Try exact match first
        if name in self.slack_handles:
            handle = self.slack_handles[name]
            # Ensure handle starts with @
            return handle if handle.startswith('@') else f'@{handle}'

        # Try case-insensitive match
        name_lower = name.lower()
        for real_name, handle in self.slack_handles.items():
            if real_name.lower() == name_lower:
                return handle if handle.startswith('@') else f'@{handle}'

        # Try first name match
        first_name = name.split()[0] if ' ' in name else name
        for real_name, handle in self.slack_handles.items():
            if real_name.lower().startswith(first_name.lower()):
                return handle if handle.startswith('@') else f'@{handle}'

        return None


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config():
    """Reload configuration from environment."""
    global _config
    _config = Config()
