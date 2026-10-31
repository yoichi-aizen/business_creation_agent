"""
Crustdata API Quickstart Script
Run this script to verify your API key and inspect your account balance.

Usage:
    export CRUSTDATA_API_KEY="your_actual_key_here"
    python examples/quickstart.py
"""

import os
import sys

# Ensure parent directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crustdata_client import CrustdataClient, CrustdataError

def main():
    api_key = os.environ.get("CRUSTDATA_API_KEY")
    if not api_key:
        print("[!] CRUSTDATA_API_KEY environment variable not set.")
        print("    Please run: export CRUSTDATA_API_KEY='your_api_key_here'")
        print("    Or pass it into CrustdataClient(api_key='...')")
        return

    client = CrustdataClient(api_key=api_key)
    print("=== Step 1: Checking Credit Balance ===")
    try:
        credits_info = client.get_credits()
        print(f"Credit Balance: {credits_info.get('credit_balance')} credits remaining")
        grant = credits_info.get("recurring_credit_grant", {})
        print(f"Grant: {grant.get('grant_size')} ({grant.get('frequency')}), next renewal: {grant.get('next_refresh_date')}")
    except CrustdataError as e:
        print(f"Error checking credits: {e}")
        return

    print("\n=== Step 2: Testing Free Entity Identification ===")
    try:
        # Resolving OpenAI (Free endpoint, 0 credits)
        res = client.identify_company(domains=["openai.com"], exact_match=True)
        if res and len(res) > 0 and res[0].get("matches"):
            match = res[0]["matches"][0]
            print(f"Resolved company: {match.get('company_data', {}).get('basic_info', {}).get('name')}")
            print(f"Crustdata ID: {match.get('company_data', {}).get('crustdata_company_id')}")
        else:
            print("No match found.")
    except CrustdataError as e:
        print(f"Error in identify: {e}")

    print("\n=== Step 3: Testing Autocomplete for Technologies ===")
    try:
        suggestions = client.autocomplete_company(field="technology", query="pyt")
        print("Suggestions for 'pyt':")
        for s in suggestions[:5]:
            print(f" - {s.get('value')} ({s.get('count')} documents)")
    except CrustdataError as e:
        print(f"Error in autocomplete: {e}")

    print(f"\nTotal credits consumed during quickstart: {client.total_credits_used}")

if __name__ == "__main__":
    main()

