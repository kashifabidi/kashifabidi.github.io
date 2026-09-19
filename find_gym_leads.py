#!/usr/bin/env python3
"""Find gym leads via the Google Places API and write them to a CSV file.

Usage:
    export GOOGLE_PLACES_API_KEY="your-key-here"
    python3 find_gym_leads.py                       # searches the default location
    python3 find_gym_leads.py "Mumbai, India"        # override the search location
    python3 find_gym_leads.py --max-results 40 --output leads.csv
"""

import argparse
import csv
import os
import sys
import time

import requests

DEFAULT_LOCATION = "Delhi, India"
DEFAULT_OUTPUT = "gym_leads.csv"
TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.websiteUri",
    "places.rating",
    "places.googleMapsUri",
    "nextPageToken",
])


def search_gyms(api_key, location, max_results):
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    body = {"textQuery": f"gyms in {location}"}
    places = []

    while True:
        response = requests.post(TEXT_SEARCH_URL, headers=headers, json=body, timeout=10)
        if response.status_code != 200:
            raise RuntimeError(f"Places API error: {response.status_code} - {response.text}")
        data = response.json()

        places.extend(data.get("places", []))

        next_page_token = data.get("nextPageToken")
        if not next_page_token or len(places) >= max_results:
            break

        # The pageToken needs a short delay before it becomes valid.
        time.sleep(2)
        body = {"textQuery": f"gyms in {location}", "pageToken": next_page_token}

    return places[:max_results]


def build_leads(places):
    leads = []
    for place in places:
        leads.append({
            "name": place.get("displayName", {}).get("text", ""),
            "address": place.get("formattedAddress", ""),
            "phone": place.get("nationalPhoneNumber", ""),
            "website": place.get("websiteUri", ""),
            "rating": place.get("rating", ""),
            "maps_link": place.get("googleMapsUri", ""),
        })
    return leads


def write_csv(leads, output_path):
    fieldnames = ["name", "address", "phone", "website", "rating", "maps_link"]
    with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(leads)


def parse_args():
    parser = argparse.ArgumentParser(description="Find gym leads via the Google Places API.")
    parser.add_argument("location", nargs="?", default=DEFAULT_LOCATION,
                         help=f"City/region to search (default: {DEFAULT_LOCATION!r})")
    parser.add_argument("--max-results", type=int, default=60,
                         help="Maximum number of gyms to fetch (default: 60)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT,
                         help=f"CSV output path (default: {DEFAULT_OUTPUT!r})")
    return parser.parse_args()


def main():
    args = parse_args()

    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        sys.exit("Error: set the GOOGLE_PLACES_API_KEY environment variable before running this script.")

    print(f"Searching for gyms in: {args.location}")
    places = search_gyms(api_key, args.location, args.max_results)
    print(f"Found {len(places)} gyms")

    leads = build_leads(places)
    write_csv(leads, args.output)

    print(f"Wrote {len(leads)} leads to {args.output}")


if __name__ == "__main__":
    main()
