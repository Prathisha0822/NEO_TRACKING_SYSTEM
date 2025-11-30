**Project: "NASA NEO Tracking System"**

setup_steps:
  -  "Create Virtual Environment"

  -  "Install Requirements"
     (command: "pip install -r requirements.txt")

  -  "Get API Key" - (Create a .env file enter the API key)

  -  "Set Database Structure"
    command: "python db_setup.py"
    description: "Creates the SQLite DB file (NEO.db) and required tables."

  -  "Fetch NEO Data from NASA API"
    commands:
      - "Ensure .env contains: API=your_nasa_api_key"
      - "python get_data.py"

  -  "Run Streamlit App"
    command: "streamlit run app.py --server.port 8502"

  - : "Login to Application"
    description: "Login to access Analysis, Queries, and the NEO Tracking Dashboard."


