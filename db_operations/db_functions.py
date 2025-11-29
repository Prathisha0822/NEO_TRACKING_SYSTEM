import sqlite3

# Connect to SQLite instead of MySQL
sql_connection = sqlite3.connect("NEO.db")
cursor = sql_connection.cursor()


def get_record_count(table_name="asteroids"):
    """Get total record count from a table."""
    try:
        query = f"SELECT COUNT(*) FROM {table_name}"
        cursor.execute(query)
        count = cursor.fetchone()[0]
        return count
    except sqlite3.Error as err:
        print(f"Error getting record count: {err}")
        return 0


def insert_asteroid_batch(asteroid_list):
    insert_asteroids = """
        INSERT INTO asteroids (
            id,
            name,
            absolute_magnitude_h,
            estimated_diameter_min_km,
            estimated_diameter_max_km,
            is_potentially_hazardous_asteroid
        ) VALUES (?, ?, ?, ?, ?, ?)
    """

    insert_close_approach = """
        INSERT INTO close_approach (
            neo_reference_id,
            close_approach_date,
            relative_velocity_kmph,
            astronomical,
            miss_distance_km,
            miss_distance_lunar,
            orbiting_body
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    try:
        asteroid_data = [
            (
                asteroid.get("id"),
                asteroid.get("name"),
                asteroid.get("absolute_magnitude_h"),
                asteroid.get("estimated_diameter_min_km"),
                asteroid.get("estimated_diameter_max_km"),
                asteroid.get("is_potentially_hazardous_asteroid"),
            )
            for asteroid in asteroid_list
        ]

        approach_data = [
            (
                asteroid.get("neo_reference_id"),
                asteroid.get("close_approach_date"),  # expect 'YYYY-MM-DD' string
                asteroid.get("relative_velocity_kmph"),
                asteroid.get("astronomical"),
                asteroid.get("miss_distance_km"),
                asteroid.get("miss_distance_lunar"),
                asteroid.get("orbiting_body"),
            )
            for asteroid in asteroid_list
        ]

        cursor.executemany(insert_asteroids, asteroid_data)
        cursor.executemany(insert_close_approach, approach_data)
        sql_connection.commit()

        print(f"✓ Batch inserted successfully: {len(asteroid_list)} records")
        return len(asteroid_list)

    except sqlite3.Error as err:
        print(f"✗ Error inserting batch: {err}")
        sql_connection.rollback()
        return 0


def close_connection():
    """Close database connection"""
    cursor.close()
    sql_connection.close()
    print("Database connection closed")


def _rows_to_dicts(rows):
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, r)) for r in rows]


def get_earth_approach_counts(limit=None):
    query = """
        SELECT a.id, a.name, COUNT(*) AS approach_count
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        WHERE c.orbiting_body = 'Earth'
        GROUP BY a.id, a.name
        ORDER BY approach_count DESC
    """
    if limit:
        query += f" LIMIT {int(limit)}"
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        return _rows_to_dicts(rows)
    except sqlite3.Error as err:
        print(f"Error executing query: {err}")
        return []


def get_avg_velocity_per_asteroid(limit=None):
    query = """
        SELECT 
            a.id, 
            a.name, 
            AVG(c.relative_velocity_kmph) AS avg_velocity_kmph 
        FROM asteroids a 
        JOIN close_approach c 
            ON a.id = c.neo_reference_id 
        WHERE c.orbiting_body = 'Earth' 
        GROUP BY a.id, a.name 
        ORDER BY avg_velocity_kmph DESC
    """
    if limit:
        query += f" LIMIT {int(limit)}"
    try:
        cursor.execute(query)
        return _rows_to_dicts(cursor.fetchall())
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return []


def get_top_n_fastest_asteroids(n=10):
    query = f"""
        SELECT 
            a.id, 
            a.name, 
            MAX(c.relative_velocity_kmph) AS max_velocity_kmph 
        FROM asteroids a 
        JOIN close_approach c 
            ON a.id = c.neo_reference_id 
        WHERE c.orbiting_body = 'Earth' 
        GROUP BY a.id, a.name 
        ORDER BY max_velocity_kmph DESC 
        LIMIT {int(n)}
    """
    try:
        cursor.execute(query)
        return _rows_to_dicts(cursor.fetchall())
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return []


def get_hazardous_asteroids_more_than(times=3):
    query = f"""
        SELECT 
            a.id, 
            a.name, 
            COUNT(*) AS approach_count 
        FROM asteroids a 
        JOIN close_approach c 
            ON a.id = c.neo_reference_id 
        WHERE  
            c.orbiting_body = 'Earth' 
            AND a.is_potentially_hazardous_asteroid = 1 
        GROUP BY a.id, a.name 
        HAVING COUNT(*) > {int(times)}
        ORDER BY approach_count DESC
    """
    try:
        cursor.execute(query)
        return _rows_to_dicts(cursor.fetchall())
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return []


def get_month_with_most_approaches():
    # DATE_FORMAT -> strftime in SQLite
    query = """
        SELECT  
            strftime('%Y-%m', close_approach_date) AS year_month, 
            COUNT(*) AS approaches 
        FROM close_approach 
        WHERE orbiting_body = 'Earth' 
        GROUP BY year_month 
        ORDER BY approaches DESC 
        LIMIT 1
    """
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        return _rows_to_dicts(rows)[0] if rows else None
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return None


def get_fastest_ever_approach():
    query = """
        SELECT  
            a.id, 
            a.name, 
            c.close_approach_date, 
            c.relative_velocity_kmph 
        FROM close_approach c 
        JOIN asteroids a 
            ON a.id = c.neo_reference_id 
        WHERE c.orbiting_body = 'Earth' 
        ORDER BY c.relative_velocity_kmph DESC 
        LIMIT 1
    """
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        return _rows_to_dicts(rows)[0] if rows else None
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return None


def get_asteroids_sorted_by_max_diameter(limit=None):
    query = """
        SELECT 
            id, 
            name, 
            estimated_diameter_max_km 
        FROM asteroids 
        ORDER BY estimated_diameter_max_km DESC
    """
    if limit:
        query += f" LIMIT {int(limit)}"
    try:
        cursor.execute(query)
        return _rows_to_dicts(cursor.fetchall())
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return []


def get_approach_closer_over_time():
    query = """
        SELECT 
            a.id, 
            a.name, 
            first_approach.miss_distance_km AS first_distance_km, 
            last_approach.miss_distance_km AS last_distance_km 
        FROM asteroids a 
        JOIN ( 
            SELECT  
                neo_reference_id, 
                MIN(close_approach_date) AS first_date 
            FROM close_approach 
            WHERE orbiting_body = 'Earth' 
            GROUP BY neo_reference_id 
        ) f ON a.id = f.neo_reference_id 
        JOIN close_approach first_approach 
            ON first_approach.neo_reference_id = f.neo_reference_id 
           AND first_approach.close_approach_date = f.first_date 
        JOIN ( 
            SELECT  
                neo_reference_id, 
                MAX(close_approach_date) AS last_date 
            FROM close_approach 
            WHERE orbiting_body = 'Earth' 
            GROUP BY neo_reference_id 
        ) l ON a.id = l.neo_reference_id 
        JOIN close_approach last_approach 
            ON last_approach.neo_reference_id = l.neo_reference_id 
           AND last_approach.close_approach_date = l.last_date 
        WHERE last_approach.miss_distance_km < first_approach.miss_distance_km
    """
    try:
        cursor.execute(query)
        return _rows_to_dicts(cursor.fetchall())
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return []


def get_closest_approach_per_asteroid(limit=None):
    query = """
        SELECT  
            a.id, 
            a.name, 
            c.close_approach_date, 
            c.miss_distance_km 
        FROM asteroids a 
        JOIN close_approach c 
            ON a.id = c.neo_reference_id 
        JOIN ( 
            SELECT  
                neo_reference_id, 
                MIN(miss_distance_km) AS min_distance_km 
            FROM close_approach 
            WHERE orbiting_body = 'Earth' 
            GROUP BY neo_reference_id 
        ) m ON m.neo_reference_id = c.neo_reference_id 
           AND m.min_distance_km = c.miss_distance_km 
        WHERE c.orbiting_body = 'Earth' 
        ORDER BY c.miss_distance_km ASC
    """
    if limit:
        query += f" LIMIT {int(limit)}"
    try:
        cursor.execute(query)
        return _rows_to_dicts(cursor.fetchall())
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return []


def get_asteroids_velocity_above(threshold=50000):
    query = f"""
        SELECT DISTINCT 
            a.id, 
            a.name 
        FROM asteroids a 
        JOIN close_approach c 
            ON a.id = c.neo_reference_id 
        WHERE  
            c.orbiting_body = 'Earth' 
            AND c.relative_velocity_kmph > {float(threshold)}
        ORDER BY c.relative_velocity_kmph DESC
    """
    try:
        cursor.execute(query)
        return _rows_to_dicts(cursor.fetchall())
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return []


def get_approaches_per_month():
    query = """
        SELECT 
            strftime('%Y-%m', close_approach_date) AS year_month, 
            COUNT(*) AS approach_count 
        FROM close_approach 
        WHERE orbiting_body = 'Earth' 
        GROUP BY year_month 
        ORDER BY year_month
    """
    try:
        cursor.execute(query)
        return _rows_to_dicts(cursor.fetchall())
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return []


def get_brightest_asteroid():
    query = """
        SELECT 
            id, 
            name, 
            absolute_magnitude_h 
        FROM asteroids 
        ORDER BY absolute_magnitude_h ASC
        LIMIT 1
    """
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        return _rows_to_dicts(rows)[0] if rows else None
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return None


def get_hazardous_vs_nonhazardous():
    query = """
        SELECT 
            CASE  
                WHEN is_potentially_hazardous_asteroid = 1 THEN 'Hazardous' 
                ELSE 'Non-hazardous' 
            END AS hazard_type, 
            COUNT(*) AS asteroid_count 
        FROM asteroids 
        GROUP BY hazard_type
    """
    try:
        cursor.execute(query)
        return _rows_to_dicts(cursor.fetchall())
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return []


def get_passed_closer_than_moon():
    query = """
        SELECT 
            a.id, 
            a.name, 
            c.close_approach_date, 
            c.miss_distance_lunar 
        FROM asteroids a 
        JOIN close_approach c 
            ON a.id = c.neo_reference_id 
        WHERE  
            c.orbiting_body = 'Earth' 
            AND c.miss_distance_lunar < 1 
        ORDER BY c.miss_distance_lunar ASC
    """
    try:
        cursor.execute(query)
        return _rows_to_dicts(cursor.fetchall())
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return []


def get_within_au(limit_au=0.05):
    query = f"""
        SELECT 
            a.id, 
            a.name, 
            c.close_approach_date, 
            c.astronomical AS distance_au 
        FROM asteroids a 
        JOIN close_approach c 
            ON a.id = c.neo_reference_id 
        WHERE  
            c.orbiting_body = 'Earth' 
            AND c.astronomical < {float(limit_au)}
        ORDER BY c.astronomical ASC
    """
    try:
        cursor.execute(query)
        return _rows_to_dicts(cursor.fetchall())
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return []


if __name__ == "__main__":
    results = get_within_au(limit_au=0.02)
    print(f"Fetched {len(results)} rows")
    for row in results[:5]:
        print(row)
