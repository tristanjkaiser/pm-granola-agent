#!/usr/bin/env python3
"""
PM Agent - AI agent for processing Granola meeting notes

Extracts PM action items, development tickets, and meeting summaries.
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from src.granola_client import GranolaClient
from src.agent import MeetingProcessor
from src.output_manager import OutputManager, ProcessedMeetingsTracker


def setup_environment():
    """Load environment variables from .env file."""
    load_dotenv()

    # Get provider
    provider = os.getenv('AI_PROVIDER', 'anthropic').lower()

    # Check for required API key based on provider
    if provider == 'anthropic' and not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ Error: ANTHROPIC_API_KEY not found in environment")
        print("\nPlease:")
        print("1. Copy .env.example to .env")
        print("2. Add your Anthropic API key to .env")
        sys.exit(1)
    elif provider == 'openai' and not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY not found in environment")
        print("\nPlease:")
        print("1. Copy .env.example to .env")
        print("2. Add your OpenAI API key to .env")
        sys.exit(1)

    return provider


def process_meeting(
    document: dict,
    granola_client: GranolaClient,
    processor: MeetingProcessor,
    output_manager: OutputManager,
    model: Optional[str] = None
) -> dict:
    """
    Process a single meeting document.

    Args:
        document: Document dictionary from Granola
        granola_client: Granola API client
        processor: Meeting processor instance
        output_manager: Output manager instance

    Returns:
        Dictionary with paths to saved files
    """
    # Extract document metadata
    doc_id = document.get('id') or document.get('document_id', 'unknown')
    title = document.get('title', 'Untitled Meeting')
    created_at = document.get('created_at') or document.get('createdAt')

    print(f"\n📋 Processing: {title}")
    print(f"   Document ID: {doc_id}")

    # Convert to markdown
    try:
        markdown_notes = granola_client.get_document_as_markdown(document)
    except Exception as e:
        print(f"❌ Error converting document to markdown: {e}")
        return {}

    if not markdown_notes or len(markdown_notes.strip()) < 10:
        print("⚠️  Document appears to be empty or too short, skipping...")
        return {}

    print(f"   Notes length: {len(markdown_notes)} characters")

    # Process with AI
    print("   🤖 Processing with AI...")
    try:
        result = processor.process_meeting_notes(markdown_notes, model=model)
    except Exception as e:
        print(f"❌ Error processing with AI: {e}")
        return {}

    # Save outputs
    print("   💾 Saving results...")
    try:
        saved_paths = output_manager.save_all(
            result,
            meeting_title=title,
            meeting_date=created_at,
            document_id=doc_id
        )
    except Exception as e:
        print(f"❌ Error saving results: {e}")
        return {}

    # Print summary
    pm_count = len(result.get('pm_action_items', []))
    dev_count = len(result.get('dev_tickets', []))

    print(f"\n✅ Processed successfully!")
    print(f"   📌 PM Tasks: {pm_count}")
    print(f"   🔧 Dev Tickets: {dev_count}")

    if saved_paths:
        print(f"\n   📁 Saved to:")
        for output_type, path in saved_paths.items():
            print(f"      {output_type}: {path}")

    return saved_paths


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Process Granola meeting notes with AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process latest meeting
  python main.py

  # Process all unprocessed meetings
  python main.py --all

  # Process latest 5 meetings
  python main.py --limit 5

  # Force reprocess latest meeting
  python main.py --force
        """
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all unprocessed meetings (default: latest only)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of meetings to process'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Reprocess meetings even if already processed'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory (default: ./outputs)'
    )

    parser.add_argument(
        '--provider',
        type=str,
        choices=['anthropic', 'openai'],
        default=None,
        help='AI provider to use (default: from .env or anthropic)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Specific model to use (default: provider default)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output for API requests'
    )

    args = parser.parse_args()

    # Setup
    provider = setup_environment()

    # Override provider if specified via CLI
    if args.provider:
        provider = args.provider

    print("🚀 PM Agent - Meeting Notes Processor")
    print("=" * 50)
    print(f"   AI Provider: {provider}")

    # Initialize components
    try:
        granola_client = GranolaClient()
        processor = MeetingProcessor(provider=provider)
        output_manager = OutputManager(
            output_dir=args.output_dir or os.getenv('OUTPUT_DIR', './outputs')
        )
        tracker = ProcessedMeetingsTracker()
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        print("\nMake sure Granola is installed and you're logged in.")
        sys.exit(1)
    except ValueError as e:
        print(f"\n❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Initialization error: {e}")
        sys.exit(1)

    # Fetch documents
    try:
        if args.all:
            # Fetch more documents if processing all
            limit = args.limit or 50
            print(f"\n📥 Fetching up to {limit} recent meetings...")
        else:
            # Just fetch the latest
            limit = args.limit or 1
            print(f"\n📥 Fetching latest meeting...")

        documents = granola_client.get_documents(limit=limit, debug=args.debug)

        if not documents:
            print("❌ No documents found")
            if not args.debug:
                print("   Try running with --debug to see API response details")
            sys.exit(1)

        print(f"   Found {len(documents)} meeting(s)")

    except Exception as e:
        print(f"❌ Error fetching documents: {e}")
        sys.exit(1)

    # Process documents
    processed_count = 0
    skipped_count = 0

    for i, doc in enumerate(documents, 1):
        doc_id = doc.get('id') or doc.get('document_id', f'unknown_{i}')

        # Check if already processed
        if not args.force and tracker.is_processed(doc_id):
            skipped_count += 1
            if not args.all:
                print(f"\n⏭️  Latest meeting already processed (ID: {doc_id})")
                print("   Use --force to reprocess")
            continue

        # Process the meeting
        saved_paths = process_meeting(
            doc,
            granola_client,
            processor,
            output_manager,
            model=args.model
        )

        if saved_paths:
            # Mark as processed
            tracker.mark_processed(doc_id)
            processed_count += 1

        # Stop if we're only processing one and we got it
        if not args.all and processed_count > 0:
            break

    # Final summary
    print("\n" + "=" * 50)
    print(f"✨ Complete!")
    print(f"   Processed: {processed_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Total tracked: {tracker.get_processed_count()}")


if __name__ == '__main__':
    main()
