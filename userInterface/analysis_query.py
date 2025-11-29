ANALYSI_QUERIES = [
    {
        "id": "q1",
        "title": "1. Last Approached Asteroid",
        "question": "Which asteroid had the most recent close approach to Earth?",
        "sql": """
            SELECT a.id, a.name, c.close_approach_date, c.miss_distance_km
            FROM asteroids a
            JOIN close_approach c ON a.id = c.neo_reference_id
            WHERE c.orbiting_body = 'Earth'
            ORDER BY c.close_approach_date DESC
            LIMIT 1;
        """,
    },
    {
        "id": "q2",
        "title": "2. Largest Asteroid Approached Earth",
        "question": "Which is the largest asteroid that has approached Earth?",
        "sql": """
            SELECT 
                a.id, 
                a.name,
                a.estimated_diameter_max_km AS max_diameter_km,
                c.close_approach_date,
                c.miss_distance_km
            FROM asteroids a
            JOIN close_approach c ON a.id = c.neo_reference_id
            WHERE c.orbiting_body = 'Earth'
            ORDER BY a.estimated_diameter_max_km DESC
            LIMIT 1;
        """,
    },
    {
        "id": "q3",
        "title": "3. Smallest Asteroid Approached Earth",
        "question": "Which is the smallest asteroid that has approached Earth?",
        "sql": """
            SELECT 
                a.id, 
                a.name, 
                a.estimated_diameter_min_km AS min_diameter_km,
                c.close_approach_date, 
                c.miss_distance_km
            FROM asteroids a
            JOIN close_approach c ON a.id = c.neo_reference_id
            WHERE c.orbiting_body = 'Earth'
            ORDER BY a.estimated_diameter_min_km ASC
            LIMIT 1;
        """,
    },
    {
        "id": "q4",
        "title": "4. Asteroids That Approached Earth Only Once",
        "question": "Which asteroids have approached Earth exactly one time?",
        "sql": """
            SELECT 
                a.id, 
                a.name, 
                c.close_approach_date, 
                c.miss_distance_km
            FROM asteroids a
            JOIN close_approach c ON a.id = c.neo_reference_id
            JOIN (
                SELECT neo_reference_id
                FROM close_approach
                WHERE orbiting_body = 'Earth'
                GROUP BY neo_reference_id
                HAVING COUNT(*) = 1
            ) single ON a.id = single.neo_reference_id
            WHERE c.orbiting_body = 'Earth';
        """,
    },
    {
        "id": "q5",
        "title": "5. Maximum Distances Labeled as Sun and Moon",
        "question": "Get the highest astronomical distance labeled as Sun and the highest lunar distance labeled as Moon from asteroid approaches to Earth.",
        "sql": """
            SELECT 'Sun' AS body, MAX(astronomical) AS distance
            FROM close_approach
            UNION ALL
            SELECT 'Moon' AS body, MAX(miss_distance_lunar) AS distance
            FROM close_approach;
        """,
    },
    {
        "id": "q6",
        "title": "6. Yearly Asteroid Approaches and Hazardous Count",
        "question": "For each year, show the total number of asteroid approaches to Earth and how many of them were potentially hazardous.",
        "sql": """
            SELECT 
                strftime('%Y', c.close_approach_date) AS year,
                COUNT(*) AS total_approaches,
                SUM(
                    CASE 
                        WHEN a.is_potentially_hazardous_asteroid = 1 THEN 1 
                        ELSE 0 
                    END
                ) AS hazardous_count
            FROM close_approach c
            JOIN asteroids a ON c.neo_reference_id = a.id
            WHERE c.orbiting_body = 'Earth'
            GROUP BY strftime('%Y', c.close_approach_date)
            ORDER BY year;
        """,
    },
    {
        "id": "q7",
        "title": "7. Weekly Asteroid Approaches",
        "question": "For each week, show the total number of asteroid approaches to Earth.",
        "sql": """
            SELECT 
                strftime('%Y', c.close_approach_date) AS year,
                strftime('%W', c.close_approach_date) AS week_number,
                MIN(c.close_approach_date) AS week_start,
                MAX(c.close_approach_date) AS week_end,
                COUNT(*) AS total_approaches
            FROM close_approach c
            WHERE c.orbiting_body = 'Earth'
            GROUP BY 
                strftime('%Y', c.close_approach_date),
                strftime('%W', c.close_approach_date)
            ORDER BY year, week_number;
        """,
    },
    {
        "id": "q8",
        "title": "8. Week with Maximum Asteroid Approaches",
        "question": "Find the week in which the highest number of asteroids approached Earth.",
        "sql": """
            SELECT 
                strftime('%Y', c.close_approach_date) AS year,
                strftime('%W', c.close_approach_date) AS week_number,
                MIN(c.close_approach_date) AS week_start,
                MAX(c.close_approach_date) AS week_end,
                COUNT(*) AS total_approaches
            FROM close_approach c
            WHERE c.orbiting_body = 'Earth'
            GROUP BY 
                strftime('%Y', c.close_approach_date),
                strftime('%W', c.close_approach_date)
            ORDER BY total_approaches DESC
            LIMIT 1;
        """,
    },
]