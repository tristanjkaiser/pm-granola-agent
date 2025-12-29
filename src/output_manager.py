"""
Output manager for saving processed meeting results to files.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class OutputManager:
    """Manages saving and organizing processed meeting outputs."""

    def __init__(self, output_dir: str = "./outputs"):
        """
        Initialize output manager.

        Args:
            output_dir: Base directory for saving outputs
        """
        self.output_dir = Path(output_dir)
        self.pm_tasks_dir = self.output_dir / "pm_tasks"
        self.dev_tickets_dir = self.output_dir / "dev_tickets"
        self.summaries_dir = self.output_dir / "summaries"

        # Create directories if they don't exist
        self.pm_tasks_dir.mkdir(parents=True, exist_ok=True)
        self.dev_tickets_dir.mkdir(parents=True, exist_ok=True)
        self.summaries_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, text: str, max_length: int = 100) -> str:
        """
        Sanitize text for use in filename.

        Args:
            text: Text to sanitize
            max_length: Maximum filename length

        Returns:
            Sanitized filename string
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            text = text.replace(char, '_')

        # Replace spaces with underscores
        text = text.replace(' ', '_')

        # Remove multiple consecutive underscores
        while '__' in text:
            text = text.replace('__', '_')

        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]

        return text.strip('_')

    def _generate_filename(
        self,
        meeting_title: Optional[str] = None,
        meeting_date: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> str:
        """
        Generate a filename for the output.

        Args:
            meeting_title: Title of the meeting
            meeting_date: Date of the meeting (ISO format)
            document_id: Document ID from Granola

        Returns:
            Sanitized filename without extension
        """
        parts = []

        # Add date
        if meeting_date:
            try:
                # Parse ISO date and format as YYYY-MM-DD
                dt = datetime.fromisoformat(meeting_date.replace('Z', '+00:00'))
                parts.append(dt.strftime('%Y-%m-%d'))
            except (ValueError, AttributeError):
                parts.append(meeting_date[:10])  # Take first 10 chars
        else:
            parts.append(datetime.now().strftime('%Y-%m-%d'))

        # Add title
        if meeting_title:
            sanitized_title = self._sanitize_filename(meeting_title, max_length=50)
            parts.append(sanitized_title)

        # Add document ID if no title
        if not meeting_title and document_id:
            parts.append(document_id[:12])

        # Add timestamp to ensure uniqueness
        parts.append(datetime.now().strftime('%H%M%S'))

        return '_'.join(parts)

    def save_pm_tasks(
        self,
        pm_tasks: List[Dict],
        meeting_title: Optional[str] = None,
        meeting_date: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> Path:
        """
        Save PM tasks to JSON file.

        Args:
            pm_tasks: List of PM action items
            meeting_title: Title of the meeting
            meeting_date: Date of the meeting
            document_id: Document ID from Granola

        Returns:
            Path to saved file
        """
        filename = self._generate_filename(meeting_title, meeting_date, document_id)
        filepath = self.pm_tasks_dir / f"{filename}.json"

        output_data = {
            "meeting_title": meeting_title,
            "meeting_date": meeting_date,
            "document_id": document_id,
            "generated_at": datetime.now().isoformat(),
            "tasks": pm_tasks
        }

        with open(filepath, 'w') as f:
            json.dump(output_data, f, indent=2)

        return filepath

    def save_dev_tickets(
        self,
        dev_tickets: List[Dict],
        meeting_title: Optional[str] = None,
        meeting_date: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> Path:
        """
        Save development tickets to JSON file.

        Args:
            dev_tickets: List of development tickets
            meeting_title: Title of the meeting
            meeting_date: Date of the meeting
            document_id: Document ID from Granola

        Returns:
            Path to saved file
        """
        filename = self._generate_filename(meeting_title, meeting_date, document_id)
        filepath = self.dev_tickets_dir / f"{filename}.json"

        output_data = {
            "meeting_title": meeting_title,
            "meeting_date": meeting_date,
            "document_id": document_id,
            "generated_at": datetime.now().isoformat(),
            "tickets": dev_tickets
        }

        with open(filepath, 'w') as f:
            json.dump(output_data, f, indent=2)

        return filepath

    def save_summary(
        self,
        summary_text: str,
        meeting_title: Optional[str] = None,
        meeting_date: Optional[str] = None,
        document_id: Optional[str] = None,
        include_metadata: bool = True
    ) -> Path:
        """
        Save meeting summary to Markdown file.

        Args:
            summary_text: Formatted summary text
            meeting_title: Title of the meeting
            meeting_date: Date of the meeting
            document_id: Document ID from Granola
            include_metadata: Whether to include metadata header

        Returns:
            Path to saved file
        """
        filename = self._generate_filename(meeting_title, meeting_date, document_id)
        filepath = self.summaries_dir / f"{filename}.md"

        content_parts = []

        if include_metadata:
            # Add metadata header
            content_parts.append("---")
            if meeting_title:
                content_parts.append(f"Meeting: {meeting_title}")
            if meeting_date:
                content_parts.append(f"Date: {meeting_date}")
            if document_id:
                content_parts.append(f"Document ID: {document_id}")
            content_parts.append(f"Generated: {datetime.now().isoformat()}")
            content_parts.append("---")
            content_parts.append("")

        content_parts.append(summary_text)

        with open(filepath, 'w') as f:
            f.write('\n'.join(content_parts))

        return filepath

    def save_all(
        self,
        result: Dict,
        meeting_title: Optional[str] = None,
        meeting_date: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> Dict[str, Path]:
        """
        Save all outputs from a processed meeting.

        Args:
            result: Complete result dictionary from MeetingProcessor
            meeting_title: Title of the meeting
            meeting_date: Date of the meeting
            document_id: Document ID from Granola

        Returns:
            Dictionary mapping output type to file path
        """
        from .agent import MeetingProcessor

        paths = {}

        # Save PM tasks
        if result.get('pm_action_items'):
            paths['pm_tasks'] = self.save_pm_tasks(
                result['pm_action_items'],
                meeting_title,
                meeting_date,
                document_id
            )

        # Save dev tickets
        if result.get('dev_tickets'):
            paths['dev_tickets'] = self.save_dev_tickets(
                result['dev_tickets'],
                meeting_title,
                meeting_date,
                document_id
            )

        # Generate and save summary
        if result.get('summary'):
            processor = MeetingProcessor()
            summary_text = processor.format_for_slack(
                result['summary'],
                result.get('pm_action_items', []),
                result.get('dev_tickets', [])
            )
            paths['summary'] = self.save_summary(
                summary_text,
                meeting_title,
                meeting_date,
                document_id
            )

        return paths


class ProcessedMeetingsTracker:
    """Tracks which meetings have been processed to avoid duplicates."""

    def __init__(self, data_dir: str = "./data"):
        """
        Initialize tracker.

        Args:
            data_dir: Directory to store tracking data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.tracking_file = self.data_dir / "processed_meetings.json"

        self.processed_ids = self._load_processed_ids()

    def _load_processed_ids(self) -> set:
        """Load set of processed document IDs."""
        if self.tracking_file.exists():
            with open(self.tracking_file, 'r') as f:
                data = json.load(f)
                return set(data.get('processed_document_ids', []))
        return set()

    def _save_processed_ids(self):
        """Save set of processed document IDs."""
        data = {
            'processed_document_ids': list(self.processed_ids),
            'last_updated': datetime.now().isoformat()
        }
        with open(self.tracking_file, 'w') as f:
            json.dump(data, f, indent=2)

    def is_processed(self, document_id: str) -> bool:
        """Check if a document has been processed."""
        return document_id in self.processed_ids

    def mark_processed(self, document_id: str):
        """Mark a document as processed."""
        self.processed_ids.add(document_id)
        self._save_processed_ids()

    def get_processed_count(self) -> int:
        """Get count of processed documents."""
        return len(self.processed_ids)
