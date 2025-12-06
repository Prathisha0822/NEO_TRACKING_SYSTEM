import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime  # 👈 added datetime

from userInterface.query_definitions import PREDEFINED_QUERIES
from userInterface.analysis_query import ANALYSI_QUERIES


# ---------- HELPERS ----------

def to_date(val):
    """Convert SQLite date/text value to a Python date object."""
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        try:
            return datetime.strptime(val, "%Y-%m-%d").date()
        except ValueError:
            return date.today()
    return date.today()


# ---------- DB HELPERS ----------

@st.cache_resource
def get_connection():
    """Create a cached SQLite connection to NEO.db (thread-safe for Streamlit)."""
    conn = sqlite3.connect(
        "NEO.db",
        check_same_thread=False 
    )
    return conn


@st.cache_data
def get_filter_bounds():
    """Read min/max values from DB for sliders."""
    conn = get_connection()
    cur = conn.cursor()

    def one_value(query: str):
        cur.execute(query)
        return cur.fetchone()

    mag_min, mag_max = one_value(
        "SELECT MIN(absolute_magnitude_h), MAX(absolute_magnitude_h) FROM asteroids"
    )

    dmin_min, dmin_max = one_value(
        "SELECT MIN(estimated_diameter_min_km), "
        "MAX(estimated_diameter_min_km) FROM asteroids"
    )
    dmax_min, dmax_max = one_value(
        "SELECT MIN(estimated_diameter_max_km), "
        "MAX(estimated_diameter_max_km) FROM asteroids"
    )

    vel_min, vel_max = one_value(
        "SELECT MIN(relative_velocity_kmph), "
        "MAX(relative_velocity_kmph) FROM close_approach"
    )
    au_min, au_max = one_value(
        "SELECT MIN(astronomical), MAX(astronomical) FROM close_approach"
    )
    date_min, date_max = one_value(
        "SELECT MIN(close_approach_date), MAX(close_approach_date) FROM close_approach"
    )

    cur.close()
    return {
        "mag": (float(mag_min), float(mag_max)),
        "dmin": (float(dmin_min), float(dmin_max)),
        "dmax": (float(dmax_min), float(dmax_max)),
        "vel": (float(vel_min), float(vel_max)),
        "au": (float(au_min), float(au_max)),
        "date": (date_min, date_max),  # still raw; we convert later
    }


def run_filter_query(
    mag_range,
    dmin_range,
    dmax_range,
    vel_range,
    au_range,
    start_date,
    end_date,
    hazard_flag,
) -> pd.DataFrame:
    """Run SELECT with all filter criteria and return a DataFrame."""
    sql = """
        SELECT
            a.id,
            a.name,
            a.absolute_magnitude_h,
            a.estimated_diameter_min_km,
            a.estimated_diameter_max_km,
            a.is_potentially_hazardous_asteroid,
            c.close_approach_date,
            c.relative_velocity_kmph,
            c.astronomical,
            c.miss_distance_km,
            c.miss_distance_lunar
        FROM asteroids a
        JOIN close_approach c
            ON a.id = c.neo_reference_id
        WHERE
            c.orbiting_body = 'Earth'
            AND a.absolute_magnitude_h BETWEEN ? AND ?
            AND a.estimated_diameter_min_km BETWEEN ? AND ?
            AND a.estimated_diameter_max_km BETWEEN ? AND ?
            AND c.relative_velocity_kmph BETWEEN ? AND ?
            AND c.astronomical BETWEEN ? AND ?
            AND c.close_approach_date BETWEEN ? AND ?
            AND (? = 0 OR a.is_potentially_hazardous_asteroid = 1)
        ORDER BY c.close_approach_date;
    """

    params = (
        mag_range[0],
        mag_range[1],
        dmin_range[0],
        dmin_range[1],
        dmax_range[0],
        dmax_range[1],
        vel_range[0],
        vel_range[1],
        au_range[0],
        au_range[1],
        # ensure dates are strings 'YYYY-MM-DD' for SQLite
        start_date.isoformat() if hasattr(start_date, "isoformat") else str(start_date),
        end_date.isoformat() if hasattr(end_date, "isoformat") else str(end_date),
        int(hazard_flag),
    )

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()

    return pd.DataFrame(rows, columns=cols)


def run_custom_sql(sql: str) -> pd.DataFrame:
    """Run a custom SELECT SQL query and return a DataFrame."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    return pd.DataFrame(rows, columns=cols)


# ---------- MAIN UI PAGE ----------

def asteroid_app_page():
    """Render the main NASA Asteroid Tracker UI."""

    # Sidebar
    st.sidebar.markdown("## 🪐 Asteroid")

    mode = st.sidebar.radio(
        "View",
        ["Filter", "Queries", "Analytics"],
        help="Switch between filter view and analytics/queries",
    )

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # --- Global styles (dark-theme friendly pills) ---
    st.markdown(
        """
        <style>
        .pill-metric {
            display: inline-flex;
            flex-direction: column;
            gap: 2px;
            padding: 0.45rem 0.8rem;
            border-radius: 999px;
            background: #020617;   /* dark pill */
            color: #f9fafb;
            font-size: 0.78rem;
            margin-right: 0.5rem;
            margin-bottom: 0.25rem;
        }
        .pill-label {
            opacity: 0.72;
            font-weight: 500;
        }
        .pill-value {
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Header
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:1.2rem;">
            <span style="font-size:2.0rem;">🚀</span>
            <div>
                <div style="font-size:2.0rem;font-weight:800;margin-bottom:-4px;">
                    NASA Asteroid Tracker
                </div>
                <div style="color:#666;font-size:0.9rem;">
                    A focused console to explore near-Earth asteroid approaches from the NASA NEO dataset
                </div>
            </div>
        </div>
        <hr style="margin-top:0.4rem;margin-bottom:1.2rem;" />
        """,
        unsafe_allow_html=True,
    )

    # ========== FILTER VIEW ==========
    if mode == "Filter":
        bounds = get_filter_bounds()

        mag_min, mag_max = bounds["mag"]
        dmax_min, dmax_max = bounds["dmax"]
        vel_min, vel_max = bounds["vel"]

        # convert raw date bounds (string from SQLite) to Python date
        raw_date_min, raw_date_max = bounds["date"]
        date_min = to_date(raw_date_min) if raw_date_min else date(2000, 1, 1)
        date_max = to_date(raw_date_max) if raw_date_max else date.today()

        # Top summary pills – dashboard feel
        with st.container():
            st.markdown(
                f"""
                <div style="margin-bottom:0.6rem;font-size:0.9rem;color:#9ca3af;">
                    Data range currently loaded from the database:
                </div>
                <div>
                    <span class="pill-metric">
                        <span class="pill-label">Brightness (mag)</span>
                        <span class="pill-value">{mag_min:.1f} – {mag_max:.1f}</span>
                    </span>
                    <span class="pill-metric">
                        <span class="pill-label">Max diameter (km)</span>
                        <span class="pill-value">{dmax_min:.2f} – {dmax_max:.2f}</span>
                    </span>
                    <span class="pill-metric">
                        <span class="pill-label">Velocity (km/h)</span>
                        <span class="pill-value">{vel_min:,.0f} – {vel_max:,.0f}</span>
                    </span>
                    <span class="pill-metric">
                        <span class="pill-label">Approach dates</span>
                        <span class="pill-value">{date_min} → {date_max}</span>
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("")

        # Three logical groups of filters
        col_left, col_middle, col_right = st.columns([1.1, 1.1, 0.9])

        with col_left:
            st.markdown("### Brightness & Size")

            mag_range = st.slider(
                "Absolute Magnitude (H)",
                min_value=round(bounds["mag"][0], 2),
                max_value=round(bounds["mag"][1], 2),
                value=(round(bounds["mag"][0], 2), round(bounds["mag"][1], 2)),
                help="Lower magnitude = brighter asteroid",
            )

            dmin_range = st.slider(
                "Min Estimated Diameter (km)",
                min_value=float(f"{bounds['dmin'][0]:.2f}"),
                max_value=float(f"{bounds['dmin'][1]:.2f}"),
                value=(
                    float(f"{bounds['dmin'][0]:.2f}"),
                    float(f"{bounds['dmin'][1]:.2f}"),
                ),
                help="Minimum possible diameter based on NASA estimates",
            )

            dmax_range = st.slider(
                "Max Estimated Diameter (km)",
                min_value=float(f"{bounds['dmax'][0]:.2f}"),
                max_value=float(f"{bounds['dmax'][1]:.2f}"),
                value=(
                    float(f"{bounds['dmax'][0]:.2f}"),
                    float(f"{bounds['dmax'][1]:.2f}"),
                ),
                help="Maximum possible diameter based on NASA estimates",
            )

        with col_middle:
            st.markdown("### Motion & Orbit")

            vel_range = st.slider(
                "Relative Velocity (km/h)",
                min_value=float(f"{bounds['vel'][0]:.2f}"),
                max_value=float(f"{bounds['vel'][1]:.2f}"),
                value=(
                    float(f"{bounds['vel'][0]:.2f}"),
                    float(f"{bounds['vel'][1]:.2f}"),
                ),
                help="Velocity of the asteroid relative to Earth",
            )

            au_range = st.slider(
                "Distance (AU)",
                min_value=float(f"{bounds['au'][0]:.4f}"),
                max_value=float(f"{bounds['au'][1]:.4f}"),
                value=(
                    float(f"{bounds['au'][0]:.4f}"),
                    float(f"{bounds['au'][1]:.4f}"),
                ),
                help="Miss distance in astronomical units (AU)",
            )

        with col_right:
            st.markdown("### Date & Risk")

            start_date = st.date_input(
                "Start Date",
                value=date_min or date(2024, 1, 1),
                min_value=date_min or date(2000, 1, 1),
                max_value=date_max or date.today(),  
            )

            end_date = st.date_input(
                "End Date",
                value=date_max or date.today(),
                min_value=date_min or date(2000, 1, 1),
                max_value=date_max or date.today(),
            )

            hazard_option = st.selectbox(
                "Potentially Hazardous?",
                ["All asteroids", "Only hazardous"],
                help="Filter using NASA's potentially hazardous asteroid flag",
            )
            hazard_flag = hazard_option == "Only hazardous"

        # Centered Apply button
        st.markdown("")
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            filter_clicked = st.button("Execute Query 🌐", use_container_width=True)
            # reset_operration = st.button("Reset Filters ", use_container_width=True)

        st.markdown("### Filtered Asteroids")

        if filter_clicked:
            with st.spinner("Loading data from database..."):
                df = run_filter_query(
                    mag_range,
                    dmin_range,
                    dmax_range,
                    vel_range,
                    au_range,
                    start_date,
                    end_date,
                    hazard_flag,
                )

            if df.empty:
                st.info("No asteroids matched your filter criteria.")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)
        # elif reset_operration:
        #     print("Resetting filters...")

    # ========== QUERIES VIEW ==========
    elif mode == "Queries":
        st.subheader("Analytics & Predefined Queries")

        st.markdown(
            """
            Select a predefined question on the left, then click **Run Query**  
            to see the results rendered below in a clean table.
            """
        )

        col_left, col_right = st.columns([1, 2])

        with col_left:
            titles = [q["title"] for q in PREDEFINED_QUERIES]
            selected_title = st.radio("Choose a question", titles)

        with col_right:
            if selected_title != "Custom SQL":
                query = next(
                    q for q in PREDEFINED_QUERIES if q["title"] == selected_title
                )

                st.markdown(f"### {query['title']}")
                st.markdown(f"**Question:** {query['question']}")
                # st.markdown("**SQL:**")
                # st.code(query["sql"], language="sql")

                run_btn = st.button("Run Query", key=f"run_{query['id']}")

                if run_btn:
                    try:
                        with st.spinner("Running query..."):
                            df = run_custom_sql(query["sql"])
                        st.markdown("#### Results")
                        if df.empty:
                            st.info(
                                "Query executed successfully, but returned no rows."
                            )
                        else:
                            st.dataframe(df, use_container_width=True, hide_index=True)
                    except Exception as e:
                        st.error(f"Error running query: {e}")
            else:
                st.markdown("### Custom SQL")
                st.markdown(
                    "You are in **Custom SQL** mode. Only `SELECT` statements are allowed."
                )

                default_sql = """
                    SELECT
                        a.id,
                        a.name,
                        a.absolute_magnitude_h,
                        c.close_approach_date,
                        c.relative_velocity_kmph,
                        c.astronomical
                    FROM asteroids a
                    JOIN close_approach c
                        ON a.id = c.neo_reference_id
                    WHERE c.orbiting_body = 'Earth'
                    LIMIT 100;
                """

                sql = st.text_area(
                    "SQL (SELECT only):",
                    value=default_sql,
                    height=220,
                )

                run_query = st.button("Run Custom Query", key="run_custom")

                if run_query:
                    if not sql.strip():
                        st.warning("Please enter a SQL query.")
                    elif not sql.strip().lower().startswith("select"):
                        st.error("Only SELECT queries are allowed in this panel.")
                    else:
                        try:
                            with st.spinner("Running query..."):
                                df = run_custom_sql(sql)
                            st.markdown("#### Results")
                            if df.empty:
                                st.info(
                                    "Query executed successfully, but returned no rows."
                                )
                            else:
                                st.dataframe(df, use_container_width=True, hide_index=True)
                        except Exception as e:
                            st.error(f"Error running query: {e}")

    # ========== ANALYTICS VIEW ==========
    elif mode == "Analytics":
        st.subheader("Analytics & Insights")

        st.markdown(
            """
            Select an insight on the left, then click **Run Query**
            """
        )

        col_left, col_right = st.columns([1, 2])

        with col_left:
            titles = [q["title"] for q in ANALYSI_QUERIES]
            selected_title = st.radio("Choose a question", titles)

        with col_right:
            if selected_title != "Custom SQL":
                query = next(
                    q for q in ANALYSI_QUERIES if q["title"] == selected_title
                )

                st.markdown(f"### {query['title']}")
                st.markdown(f"**Question:** {query['question']}")
                # st.markdown("**SQL:**")
                # st.code(query["sql"], language="sql")

                run_btn = st.button("Run Query", key=f"run_{query['id']}")

                if run_btn:
                    try:
                        with st.spinner("Running query..."):
                            df = run_custom_sql(query["sql"])
                        st.markdown("#### Results")
                        if df.empty:
                            st.info(
                                "Query executed successfully, but returned no rows."
                            )
                        else:
                            st.dataframe(df, use_container_width=True, hide_index=True)
                    except Exception as e:
                        st.error(f"Error running query: {e}")
            else:
                st.markdown("### Custom SQL")
                st.markdown(
                    "You are in **Custom SQL** mode. Only `SELECT` statements are allowed."
                )

                default_sql = """
                    SELECT
                        a.id,
                        a.name,
                        a.absolute_magnitude_h,
                        c.close_approach_date,
                        c.relative_velocity_kmph,
                        c.astronomical
                    FROM asteroids a
                    JOIN close_approach c
                        ON a.id = c.neo_reference_id
                    WHERE c.orbiting_body = 'Earth'
                    LIMIT 100;
                """

                sql = st.text_area(
                    "SQL (SELECT only):",
                    value=default_sql,
                    height=220,
                )

                run_query = st.button("Run Custom Query", key="run_custom")

                if run_query:
                    if not sql.strip():
                        st.warning("Please enter a SQL query.")
                    elif not sql.strip().lower().startswith("select"):
                        st.error("Only SELECT queries are allowed in this panel.")
                    else:
                        try:
                            with st.spinner("Running query..."):
                                df = run_custom_sql(sql)
                            st.markdown("#### Results")
                            if df.empty:
                                st.info(
                                    "Query executed successfully, but returned no rows."
                                )
                            else:
                                st.dataframe(df, use_container_width=True, hide_index=True)
                        except Exception as e:
                            st.error(f"Error running query: {e}")
