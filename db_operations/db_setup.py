import sqlite3
import os

def setup_neo_sqlite(db_path="NEO.db"):
    # -------- CONNECT / CREATE SQLITE DB --------
    creating_db = not os.path.exists(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    if creating_db:
        print(f"Database '{db_path}' created.")
    else:
        print(f"Database '{db_path}' already exists.")

    # -------- HELPER: CHECK IF TABLE EXISTS --------
    def table_exists(table_name: str) -> bool:
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name = ?;",
            (table_name,),
        )
        return cur.fetchone() is not None

    # -------- CREATE ASTEROIDS TABLE --------
    if table_exists("asteroids"):
        print("Table 'asteroids' already exists.")
    else:
        cur.execute("""
            CREATE TABLE asteroids (
                id INT,
                name TEXT,
                absolute_magnitude_h REAL,
                estimated_diameter_min_km REAL,
                estimated_diameter_max_km REAL,
                is_potentially_hazardous_asteroid INTEGER
            );
        """)
        print("Table 'asteroids' created successfully.")

    # -------- CREATE CLOSE_APPROACH TABLE --------
    if table_exists("close_approach"):
        print("Table 'close_approach' already exists.")
    else:
        cur.execute("""
            CREATE TABLE close_approach (
                neo_reference_id INT,
                close_approach_date TEXT,  -- store as ISO date string 'YYYY-MM-DD'
                relative_velocity_kmph REAL,
                astronomical REAL,
                miss_distance_km REAL,
                miss_distance_lunar REAL,
                orbiting_body TEXT
            );
        """)
        print("Table 'close_approach' created successfully.")

    # -------- SAVE & CLOSE --------
    conn.commit()
    cur.close()
    conn.close()
    print("SQLite database setup completed.")


if __name__ == "__main__":
    setup_neo_sqlite()
