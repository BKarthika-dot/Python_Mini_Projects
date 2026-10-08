#!/usr/bin/env python3
"""
Quick command-line entry point: give the pipeline a job posting URL (the
primary input path) or pasted text, and see the classification result
immediately, without starting the API server.

Usage:
    python test_cli.py https://example.com/job/123        # URL, positional (primary flow)
    python test_cli.py --url "https://example.com/job/123"
    python test_cli.py --text "Urgent hiring! Pay $50 registration fee..."
"""
import argparse
import json
import sys

from app.pipeline import ClassificationPipeline


def main():
    parser = argparse.ArgumentParser(description="Classify a job posting as Safe / Suspicious / Unsafe.")
    parser.add_argument("url_positional", nargs="?", help="Job posting URL (shorthand for --url)")
    parser.add_argument("--url", help="Job posting URL to fetch and analyze")
    parser.add_argument("--text", help="Pasted job posting text")
    parser.add_argument("--company-domain", default=None, help="Optional known official employer domain")
    args = parser.parse_args()

    url = args.url or args.url_positional
    if not url and not args.text:
        parser.error("Provide a URL (positional or --url) or --text.")
    if url and args.text:
        parser.error("Provide either a URL or --text, not both.")

    pipeline = ClassificationPipeline()

    try:
        if url:
            print(f"Fetching and analyzing: {url}", file=sys.stderr)
            result = pipeline.classify("url", url, company_domain=args.company_domain)
        else:
            result = pipeline.classify("text", args.text, company_domain=args.company_domain)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
