"""
Script to test feed parsers.

This script fetches an RSS feed and runs the specified (or all) parsers on each entry,
displaying a detailed breakdown of the parsing process and the extracted content.
This helps in debugging and choosing the best parser for a given feed.
"""

import feedparser
import requests
import typer
import sys
import importlib
from pathlib import Path
from typing import List
import inspect

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.components.feed_parsers.base_parser import BaseParser

app = typer.Typer()

def get_all_parser_classes() -> List[type]:
    """Dynamically discovers and loads all parser classes."""
    parser_classes = []
    parser_dir = Path(__file__).parent
    for f in parser_dir.glob('*_parser.py'):
        if f.name == '__init__.py' or f.name == 'test_parser.py':
            continue
        module_name = f'src.components.feed_parsers.{f.stem}'
        try:
            module = importlib.import_module(module_name)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BaseParser) and attr is not BaseParser:
                    parser_classes.append(attr)
        except ImportError as e:
            print(f"Error importing {module_name}: {e}")
    return parser_classes

@app.command()
def test_feed(
    feed_urls: List[str] = typer.Argument(..., help="The URL(s) of the RSS feed(s) to test."),
    parser_name: str = typer.Option(None, "--parser", "-p", help="Specific parser to test (e.g., DefaultParser). If not provided, all parsers will be tested."),
):
    """
    Fetches RSS feeds and shows the output of the specified (or all) parsers for each entry.
    """
    parser_classes_to_test = []
    all_parser_classes = get_all_parser_classes()

    if parser_name:
        found_parser = next((p for p in all_parser_classes if p.__name__ == parser_name), None)
        if found_parser:
            parser_classes_to_test.append(found_parser)
        else:
            print(f"Error: Parser '{parser_name}' not found.")
            raise typer.Exit(1)
    else:
        parser_classes_to_test = all_parser_classes

    for feed_url in feed_urls:
        print(f"Fetching feed: {feed_url}\n")
        try:
            response = requests.get(feed_url, timeout=15)
            response.raise_for_status()
            feed_data = feedparser.parse(response.content)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching feed: {e}")
            continue

        if feed_data.bozo:
            print(f"Warning: Feed may be malformed. Bozo exception: {feed_data.bozo_exception}\n")

        if not feed_data.entries:
            print("No entries found in the feed.")
            continue

        print(f"Found {len(feed_data.entries)} entries. Testing first entry with {len(parser_classes_to_test)} parser(s).\n")

        entry = feed_data.entries[0]

        print("=" * 80)
        print(f"Entry Title: {entry.get('title', 'N/A')}")
        print(f"Entry URL:   {entry.get('link', 'N/A')}")
        print("=" * 80)
        
        print("\n--- Raw Entry Data ---")
        for key, value in entry.items():
            if isinstance(value, str) and len(value) > 150:
                print(f"  - {key}: {value[:350]}...")
            else:
                print(f"  - {key}: {value}")
        print("----------------------\n")


        for parser_class in parser_classes_to_test:
            parser_instance = parser_class()
            parser_doc = inspect.getdoc(parser_instance.parse)

            print("*" * 50)
            print(f"Testing with Parser: {parser_class.__name__}")
            print("*" * 50)
            
            if parser_doc:
                print("\n--- Parser Logic ---")
                print(parser_doc)
                print("--------------------\n")

            try:
                content_parts = parser_instance.parse(entry)
                
                print("--- Extracted Content ---")
                if content_parts:
                    for part in content_parts:
                        print(f"  - Type: {part.type}")
                        print(f"    Text: {part.text[:300]}{'...' if len(part.text) > 300 else ''}\n")
                else:
                    print("No content extracted.")
                print("-------------------------\n")

            except Exception as e:
                print(f"An error occurred while running {parser_class.__name__}: {e}\n")


if __name__ == "__main__":
    app()
