PREDEFINED_QUERIES = [
    {
        "id": "q1",
        "title": "1. Count how many times each asteroid has approached Earth",
        "question": "How many times has each asteroid approached Earth?",
        "sql": """
            SELECT 
                a.id,
                a.name,
                COUNT(*) AS approach_count
            FROM asteroids a
            JOIN close_approach c ON a.id = c.neo_reference_id
            WHERE c.orbiting_body = 'Earth'
            GROUP BY a.id, a.name
            ORDER BY approach_count DESC;
        """,
    },
    {
        "id": "q2",
        "title": "2. Average velocity of each asteroid over multiple approaches",
        "question": "What is the average approach velocity of each asteroid (towards Earth)?",
        "sql": """
            SELECT
                a.id,
                a.name,
                AVG(c.relative_velocity_kmph) AS avg_velocity_kmph
            FROM asteroids a
            JOIN close_approach c ON a.id = c.neo_reference_id
            WHERE c.orbiting_body = 'Earth'
            GROUP BY a.id, a.name
            ORDER BY avg_velocity_kmph DESC;
        """,
    },
    {
        "id": "q3",
        "title": "3. Top 10 fastest asteroids (by max approach speed)",
        "question": "Which asteroids have had the highest recorded approach speeds towards Earth?",
        "sql": """
            SELECT
                a.id,
                a.name,
                MAX(c.relative_velocity_kmph) AS max_velocity_kmph
            FROM asteroids a
            JOIN close_approach c ON a.id = c.neo_reference_id
            WHERE c.orbiting_body = 'Earth'
            GROUP BY a.id, a.name
            ORDER BY max_velocity_kmph DESC
            LIMIT 10;
        """,
    },
    {
        "id": "q4",
        "title": "4. Hazardous asteroids with > 3 Earth approaches",
        "question": "Which potentially hazardous asteroids have approached Earth more than 3 times?",
        "sql": """
            SELECT
                a.id,
                a.name,
                COUNT(*) AS approach_count
            FROM asteroids a
            JOIN close_approach c ON a.id = c.neo_reference_id
            WHERE 
                c.orbiting_body = 'Earth'
                AND a.is_potentially_hazardous_asteroid = 1
            GROUP BY a.id, a.name
            HAVING COUNT(*) > 3
            ORDER BY approach_count DESC;
        """,
    },
    {
        "id": "q5",
        "title": "5. Month with the most asteroid approaches",
        "question": "Which month (year-month) had the highest number of approaches to Earth?",
        "sql": """
            SELECT 
                strftime('%Y', close_approach_date) AS year,
                strftime('%m', close_approach_date) AS month,
                COUNT(*) AS approaches
            FROM close_approach
            WHERE orbiting_body = 'Earth'
            GROUP BY strftime('%Y', close_approach_date),
                     strftime('%m', close_approach_date)
            ORDER BY approaches DESC
            LIMIT 3;
        """,
    },
    {
        "id": "q6",
        "title": "6. Fastest ever Earth approach (single pass)",
        "question": "What is the fastest single approach speed recorded for any asteroid approaching Earth?",
        "sql": """
            SELECT 
                a.id,
                a.name,
                c.close_approach_date,
                c.relative_velocity_kmph
            FROM close_approach c
            JOIN asteroids a ON a.id = c.neo_reference_id
            WHERE c.orbiting_body = 'Earth'
            ORDER BY c.relative_velocity_kmph DESC
            LIMIT 1;
        """,
    },
    {
        "id": "q7",
        "title": "7. Sort asteroids by maximum estimated diameter (desc)",
        "question": "Which asteroids are the largest by maximum estimated diameter?",
        "sql": """
            SELECT
                id,
                name,
                estimated_diameter_max_km
            FROM asteroids
            ORDER BY estimated_diameter_max_km DESC;
        """,
    },
    {
        "id": "q8",
        "title": "8. Asteroids whose latest approach is closer than the first",
        "question": "Which asteroids are getting closer to Earth over time (latest approach closer than the first)?",
        "sql": """
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
            WHERE last_approach.miss_distance_km < first_approach.miss_distance_km;
        """,
    },
    {
        "id": "q9",
        "title": "9. Closest approach (date & distance) for each asteroid",
        "question": "For each asteroid, what is the date and distance of its closest approach to Earth?",
        "sql": """
            SELECT 
                a.id,
                a.name,
                c.close_approach_date,
                c.miss_distance_km
            FROM asteroids a
            JOIN close_approach c ON a.id = c.neo_reference_id
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
            ORDER BY c.miss_distance_km ASC;
        """,
    },
    {
        "id": "q10",
        "title": "10. Asteroids with velocity > 50,000 km/h",
        "question": "Which asteroids have ever approached Earth with velocity > 50,000 km/h?",
        "sql": """
            SELECT DISTINCT
                a.id,
                a.name,
                c.relative_velocity_kmph
            FROM asteroids a
            JOIN close_approach c ON a.id = c.neo_reference_id
            WHERE 
                c.orbiting_body = 'Earth'
                AND c.relative_velocity_kmph > 50000
            ORDER BY c.relative_velocity_kmph DESC;
        """,
    },
    {
        "id": "q11",
        "title": "11. Count how many approaches happened per month",
        "question": "How many approaches to Earth occurred in each year-month?",
        "sql": """
            SELECT 
                strftime('%Y', close_approach_date) AS year,
                strftime('%m', close_approach_date) AS month,
                COUNT(*) AS approach_count
            FROM close_approach
            WHERE orbiting_body = 'Earth'
            GROUP BY strftime('%Y', close_approach_date),
                     strftime('%m', close_approach_date)
            ORDER BY year, month;
        """,
    },
    {
        "id": "q12",
        "title": "12. Asteroid with highest brightness (lowest magnitude)",
        "question": "Which asteroid is brightest (lowest absolute magnitude)?",
        "sql": """
            SELECT
                id,
                name,
                absolute_magnitude_h
            FROM asteroids
            ORDER BY absolute_magnitude_h ASC
            LIMIT 1;
        """,
    },
    {
        "id": "q13",
        "title": "13. Number of hazardous vs non-hazardous asteroids",
        "question": "How many asteroids are hazardous vs non-hazardous?",
        "sql": """
            SELECT
                CASE 
                    WHEN is_potentially_hazardous_asteroid = 1 THEN 'Hazardous'
                    ELSE 'Non-hazardous'
                END AS hazard_type,
                COUNT(*) AS asteroid_count
            FROM asteroids
            GROUP BY hazard_type;
        """,
    },
    {
        "id": "q14",
        "title": "14. Asteroids that passed closer than the Moon (< 1 LD)",
        "question": "Which asteroids passed closer than the Moon (< 1 lunar distance)?",
        "sql": """
            SELECT
                a.id,
                a.name,
                c.close_approach_date,
                c.miss_distance_lunar
            FROM asteroids a
            JOIN close_approach c ON a.id = c.neo_reference_id
            WHERE 
                c.orbiting_body = 'Earth'
                AND c.miss_distance_lunar < 1
            ORDER BY c.miss_distance_lunar ASC;
        """,
    },
    {
        "id": "q15",
        "title": "15. Asteroids that came within 0.05 AU",
        "question": "Which asteroids came within 0.05 AU of Earth?",
        "sql": """
            SELECT
                a.id,
                a.name,
                c.close_approach_date,
                c.astronomical AS distance_au
            FROM asteroids a
            JOIN close_approach c ON a.id = c.neo_reference_id
            WHERE 
                c.orbiting_body = 'Earth'
                AND c.astronomical < 0.05
            ORDER BY c.astronomical ASC;
        """,
    },
]
