"""
Granola API client for fetching meeting notes.
Uses reverse-engineered API endpoint.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import requests


class GranolaClient:
    """Client for accessing Granola meeting notes via their API."""

    API_BASE_URL = "https://api.granola.ai/v2"
    USER_AGENT = "Granola/5.354.0"
    CLIENT_VERSION = "5.354.0"

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Granola client.

        Args:
            credentials_path: Path to supabase.json credentials file.
                            Defaults to ~/Library/Application Support/Granola/supabase.json
        """
        if credentials_path is None:
            credentials_path = os.path.expanduser(
                "~/Library/Application Support/Granola/supabase.json"
            )

        self.credentials_path = Path(credentials_path)
        self.access_token = self._load_access_token()

    def _load_access_token(self) -> str:
        """Load access token from Granola credentials file."""
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"Granola credentials not found at {self.credentials_path}. "
                "Make sure Granola is installed and you're logged in."
            )

        with open(self.credentials_path, 'r') as f:
            creds = json.load(f)

        # The access token is nested inside the workos_tokens field (which is a JSON string)
        workos_tokens_str = creds.get('workos_tokens')
        if not workos_tokens_str:
            # Fallback: try to get access_token at top level (older format)
            access_token = creds.get('access_token')
            if access_token:
                return access_token
            raise ValueError(
                "No workos_tokens or access_token found in Granola credentials. "
                "Make sure you're logged in to Granola."
            )

        # Parse the workos_tokens JSON string
        try:
            workos_tokens = json.loads(workos_tokens_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse workos_tokens: {e}")

        # Extract access token from the parsed object
        access_token = workos_tokens.get('access_token')
        if not access_token:
            raise ValueError("No access_token found in workos_tokens")

        return access_token

    def _make_request(self, endpoint: str, data: Dict, debug: bool = False) -> Dict:
        """Make authenticated request to Granola API."""
        url = f"{self.API_BASE_URL}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "User-Agent": self.USER_AGENT,
            "X-Client-Version": self.CLIENT_VERSION,
        }

        if debug:
            print(f"\n🔍 DEBUG: Making request to {url}")
            print(f"   Payload: {data}")

        response = requests.post(url, json=data, headers=headers)

        if debug:
            print(f"   Status: {response.status_code}")
            print(f"   Response preview: {str(response.text)[:500]}...")

        response.raise_for_status()
        return response.json()

    def get_documents(self, limit: int = 10, offset: int = 0, debug: bool = False) -> List[Dict]:
        """
        Fetch meeting documents from Granola.

        Args:
            limit: Number of documents to fetch
            offset: Offset for pagination
            debug: Enable debug output

        Returns:
            List of document dictionaries
        """
        data = {
            "limit": limit,
            "offset": offset
        }

        result = self._make_request("get-documents", data, debug=debug)

        # API returns 'docs' not 'documents'
        docs = result.get('docs', result.get('documents', []))

        if debug:
            print(f"   Result keys: {result.keys()}")
            print(f"   Documents found: {len(docs)}")

        return docs

    def get_latest_document(self) -> Optional[Dict]:
        """Get the most recent meeting document."""
        docs = self.get_documents(limit=1)
        return docs[0] if docs else None

    def prosemirror_to_markdown(self, prosemirror_json: Dict) -> str:
        """
        Convert ProseMirror JSON to Markdown.

        This is a simplified converter. For production use, consider
        using a proper ProseMirror to Markdown library.
        """
        def process_node(node: Dict) -> str:
            node_type = node.get('type', '')
            content = node.get('content', [])
            text = node.get('text', '')

            # Process text nodes
            if text:
                marks = node.get('marks', [])
                for mark in marks:
                    mark_type = mark.get('type', '')
                    if mark_type == 'bold':
                        text = f"**{text}**"
                    elif mark_type == 'italic':
                        text = f"*{text}*"
                    elif mark_type == 'code':
                        text = f"`{text}`"
                return text

            # Process block nodes
            result = []
            for child in content:
                result.append(process_node(child))

            text_content = ''.join(result)

            if node_type == 'paragraph':
                return text_content + '\n\n'
            elif node_type == 'heading':
                level = node.get('attrs', {}).get('level', 1)
                return f"{'#' * level} {text_content}\n\n"
            elif node_type == 'bulletList':
                return text_content
            elif node_type == 'listItem':
                return f"- {text_content}"
            elif node_type == 'codeBlock':
                return f"```\n{text_content}\n```\n\n"
            else:
                return text_content

        if isinstance(prosemirror_json, dict):
            return process_node(prosemirror_json).strip()
        return str(prosemirror_json)

    def get_document_as_markdown(self, document: Dict) -> str:
        """
        Extract and convert document content to Markdown.

        Args:
            document: Document dictionary from API

        Returns:
            Markdown string
        """
        # Try to get content from various possible fields
        # Current API returns 'notes' field with ProseMirror content
        content = (
            document.get('notes') or
            document.get('content') or
            document.get('prosemirror_content')
        )

        if isinstance(content, dict):
            return self.prosemirror_to_markdown(content)
        elif isinstance(content, str):
            # If content is already a string, try to parse as JSON
            try:
                content_dict = json.loads(content)
                return self.prosemirror_to_markdown(content_dict)
            except json.JSONDecodeError:
                return content

        # Fallback: return any text field we can find
        return document.get('text', '') or str(document)
