import requests
from dotenv import load_dotenv
import os
import json
import time

from db_operations.db_functions import (
    insert_asteroid_batch,
    close_connection,
    get_record_count,
)

# Load the .env file
load_dotenv()

# Access variables
API_KEY = os.getenv("API")  # ensure .env has API=<your_key>


def save_to_json_file(asteroid_dict, filename="asteroids_output.json"):
    with open(filename, "a") as f:
        json.dump(asteroid_dict, f, indent=4)
        f.write("\n")


def get_data_from_api():
    """Simple one-shot fetch + dump (debug helper)."""
    url = (
        f"https://api.nasa.gov/neo/rest/v1/feed"
        f"?start_date=2024-01-01&end_date=2024-01-07&api_key={API_KEY}"
    )
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    data = response.json()
    next_url = data.get("links", {}).get("next")
    print(f"Next URL: {next_url}")
    with open("data.json", "w") as f:
        f.write(response.text)


def get_required_data(limit, batch_size):
    """
    Fetch NEO data from NASA API until `limit` rows are in DB,
    inserting in batches of `batch_size`.
    """
    url = (
        f"https://api.nasa.gov/neo/rest/v1/feed"
        f"?start_date=2024-01-01&end_date=2024-01-07&api_key={API_KEY}"
    )
    asteroid_data = []
    batch_count = 0
    visited_urls = set()

    while url:
        # Avoid infinite loops if NASA gives same URL again
        norm_url = url.rstrip("/")
        if norm_url in visited_urls:
            print(f"Already visited URL, stopping: {url}")
            break
        visited_urls.add(norm_url)

        current_count = get_record_count()
        if current_count >= limit :
            print(f"\n{'=' * 60}")
            print(f"✓ DATABASE LIMIT REACHED: {current_count} records")
            print("Terminating API calls...")
            print(f"{'=' * 60}")
            break

        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()
            details = data.get("near_earth_objects", {})

            if not details:
                print("No data found in API response")
                break

            for date_str, asteroid_list in details.items():
                for asteroid in asteroid_list:
                    if get_record_count() >= limit :
                        break

                    try:
                        # Convert numeric fields to proper types for SQLite
                        absolute_magnitude_h = float(
                            asteroid["absolute_magnitude_h"]
                        )
                        est_diam_min = float(
                            asteroid["estimated_diameter"]["kilometers"][
                                "estimated_diameter_min"
                            ]
                        )
                        est_diam_max = float(
                            asteroid["estimated_diameter"]["kilometers"][
                                "estimated_diameter_max"
                            ]
                        )

                        ca_data = asteroid["close_approach_data"][0]
                        rel_vel_kmph = float(
                            ca_data["relative_velocity"]["kilometers_per_hour"]
                        )
                        astronomical = float(
                            ca_data["miss_distance"]["astronomical"]
                        )
                        miss_km = float(ca_data["miss_distance"]["kilometers"])
                        miss_lunar = float(ca_data["miss_distance"]["lunar"])

                        asteroid_dict = dict(
                            id=asteroid["id"],
                            neo_reference_id=asteroid["neo_reference_id"],
                            name=asteroid["name"],
                            absolute_magnitude_h=absolute_magnitude_h,
                            is_potentially_hazardous_asteroid=int(
                                bool(
                                    asteroid[
                                        "is_potentially_hazardous_asteroid"
                                    ]
                                )
                            ),
                            estimated_diameter_min_km=est_diam_min,
                            estimated_diameter_max_km=est_diam_max,
                            close_approach_date=ca_data["close_approach_date"],
                            relative_velocity_kmph=rel_vel_kmph,
                            astronomical=astronomical,
                            miss_distance_km=miss_km,
                            miss_distance_lunar=miss_lunar,
                            orbiting_body=ca_data["orbiting_body"],
                        )

                        save_to_json_file(asteroid_dict)
                        asteroid_data.append(asteroid_dict)

                    except (KeyError, IndexError, ValueError) as err:
                        print(f"Skipping asteroid due to parse error: {err}")
                        continue

                    # Insert batch when enough collected
                    if len(asteroid_data) >= batch_size:
                        batch_count += 1
                        print(
                            f"\n--- Inserting Batch {batch_count} ({len(asteroid_data)} records) ---"
                        )
                        inserted = insert_asteroid_batch(asteroid_data)
                        current_count = get_record_count()
                        print(
                            f"Total records in database: {current_count}/{limit }"
                        )
                        asteroid_data = []
                        time.sleep(1)

                        if current_count >= limit :
                            break

                if get_record_count() >= limit :
                    break

            if get_record_count() >= limit :
                break

            next_url = data.get("links", {}).get("next")
            if not next_url:
                print("No next page. Stopping.")
                break

            url = next_url
            print(f"\nFetching next page: {url}")

        except requests.exceptions.RequestException as err:
            print(f"API Error: {err}")
            break
        except (KeyError, IndexError) as err:
            print(f"Data parsing error: {err}")
            break

    # Insert any remaining items
    current_count = get_record_count()
    if asteroid_data and current_count < limit :
        batch_count += 1
        print(
            f"\n--- Inserting Final Batch {batch_count} ({len(asteroid_data)} records) ---"
        )
        insert_asteroid_batch(asteroid_data)
        current_count = get_record_count()

    print(f"\nTotal batches inserted: {batch_count}")
    print(f"Final record count: {current_count}")

    # Now safe to close
    close_connection()


if __name__ == "__main__":
    get_required_data(limit=10000, batch_size=100)
    # get_data_from_api()