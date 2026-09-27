
# Spotify AI Platform

An end-to-end Spotify data engineering and AI analytics platform that combines batch data pipelines, real-time streaming, analytics, and a LangGraph-powered AI Analyst into a single dashboard.

## Overview

Spotify AI Platform collects personal Spotify listening data through the Spotify Web API and processes it through a modern data pipeline.

The platform supports both:

- **Batch analytics** for saved tracks, artists, albums, playlists, and listening history
- **Real-time listening events** using Kafka and Spark Structured Streaming
- **Analytical storage** using PostgreSQL and Apache Iceberg
- **AI-powered analysis** using LangGraph and Gemini
- **Artist metadata enrichment** using MusicBrainz
- **Interactive dashboard** built with Next.js

The goal is to provide both structured listening analytics and natural-language insights over the user's Spotify data.

---

## Architecture

```text
                         Spotify Web API
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
            Batch Pipeline              Live Playback
                 │                           │
                 ▼                           ▼
        Bronze → Silver → Gold            Kafka
                 │                           │
                 ▼                           ▼
            PostgreSQL              Spark Structured Streaming
                                             │
                                             ▼
                                      Apache Iceberg
                                             │
                 ┌───────────────────────────┘
                 │
                 ▼
          FastAPI Analytics API
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
   Next.js Dashboard   LangGraph Agent
                           │
                           ▼
                         Gemini
                           │
                           ▼
                    Analytics Tools
                           │
                           ▼
                     MusicBrainz
```



## Key Features

### Spotify Data Pipeline

* Spotify Web API ingestion
* Saved tracks and music metadata
* Playlist data
* Followed artists
* Recently played tracks
* Top artists and tracks
* Daily listening analytics
* Bronze, Silver, and Gold data layers

### Data Engineering

* PostgreSQL analytical storage
* Apache Kafka event streaming
* Spark Structured Streaming
* Apache Iceberg table storage
* Incremental listening-event processing
* Analytics aggregation pipelines

### Real-Time Pipeline

The live listening pipeline monitors the currently playing Spotify track and publishes track-change events to Kafka.

```text
Spotify Playback
      ↓
Live Poller
      ↓
Kafka: spotify-listening
      ↓
Spark Structured Streaming
      ↓
Apache Iceberg
```

Only track changes are emitted as listening events, avoiding duplicate events while a track continues playing.

### Analytics

The platform provides analytics for:

* Listening activity
* Recent listening
* Top artists
* Top tracks
* Listening profiles
* Artist concentration
* Saved vs. listened tracks
* Completion behavior
* Listening patterns
* Listening windows and trends

### AI Analyst

The platform includes a LangGraph-based AI Analyst powered by Gemini.

The agent can use analytics tools to answer natural-language questions about the user's listening data.

Example:

```text
Who is my top artist?
```

The agent retrieves the relevant analytics and produces a natural-language response along with structured insights and metrics.

The agent is designed to distinguish between:

* Personal Spotify listening data
* Captured listening events
* External artist metadata from MusicBrainz

Captured listening events are treated as observations from this pipeline rather than official Spotify play counts.

### MusicBrainz Enrichment

Artist information can be enriched using MusicBrainz, including metadata such as:

* Artist country
* Genres
* Additional artist information

This allows the AI Analyst to combine personal listening analytics with external artist metadata.

### Dashboard

The Next.js dashboard provides:

* Current playback
* Overview metrics
* Listening activity
* Top artists
* Top tracks
* Listening profile
* Artist concentration
* Saved vs. listened analysis
* Completion behavior
* Recent listening
* AI Analyst

---

## Tech Stack

### Backend & Data Engineering

* Python
* FastAPI
* PostgreSQL
* Apache Kafka
* Apache Spark
* Apache Iceberg
* Pandas
* PySpark

### AI & LLM

* LangGraph
* LangChain
* Google Gemini
* MusicBrainz API

### Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS

### Infrastructure

* Docker
* Docker Compose
* Git / GitHub

---

## Project Structure

```text
spotify-ai-platform/
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── package.json
│   └── tsconfig.json
│
├── src/
│   ├── analytics/
│   │   ├── build_artist_listening.py
│   │   ├── build_daily_listening.py
│   │   ├── build_listening_analytics.py
│   │   └── build_listening_concentration.py
│   │
│   ├── streaming/
│   │   ├── spotify_live.py
│   │   └── spark_to_iceberg.py
│   │
│   ├── agent_tools.py
│   ├── api.py
│   ├── langgraph_agent.py
│   └── spark_config.py
│
├── start.ps1
├── .gitignore
└── README.md
```

---

## Setup

### 1. Clone the repository

```powershell
git clone https://github.com/Anshuljain22/spotify-ai-platform.git
cd spotify-ai-platform
```

### 2. Create the Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root containing the required Spotify and Gemini credentials.

Example structure:

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=your_redirect_uri
GEMINI_API_KEY=your_gemini_api_key
```

Do not commit `.env` or any API credentials to GitHub.

### 5. Install frontend dependencies

```powershell
cd frontend
npm install
cd ..
```

---

## Running the Platform

The project includes `start.ps1` to simplify starting the local services.

From the project root:

```powershell
.\start.ps1
```

The individual services can also be started separately.

### FastAPI

```powershell
uvicorn src.api:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

### Next.js Dashboard

```powershell
cd frontend
npm run dev
```

Dashboard:

```text
http://localhost:3000
```

### Spotify Live Poller

```powershell
python -m src.streaming.spotify_live
```

### Spark Streaming

```powershell
python -m src.streaming.spark_to_iceberg
```

---

## Real-Time Streaming

The real-time pipeline uses Kafka and Spark Structured Streaming.

Kafka topic:

```text
spotify-listening
```

The Spotify live poller checks the current playback state and publishes an event when the currently playing track changes.

Spark consumes these events and writes them into the Iceberg listening-events table.

This creates a streaming path from Spotify playback to analytical storage:

```text
Spotify
   ↓
Python Poller
   ↓
Kafka
   ↓
Spark Structured Streaming
   ↓
Apache Iceberg
```

---

## AI Analyst

The AI Analyst uses LangGraph to orchestrate an LLM with custom Spotify analytics tools.

Available analytical capabilities include:

* Track analytics
* Artist analytics
* Recent listening
* Saved tracks
* Current playback
* Listening trends
* Listening windows
* Listening summaries
* Saved vs. listened analysis
* Listening profiles
* Listening patterns
* Artist concentration
* Completion behavior
* Listening activity
* Artist metadata enrichment

Example questions:

```text
Who is my top artist?

What are my recent listening patterns?

Which artists dominate my listening?

How does my saved music compare with what I actually listen to?

What are my listening trends?
```

---

## Data Storage

The platform uses multiple storage layers for different workloads.

### PostgreSQL

Used for structured analytical data and API queries.

### Apache Iceberg

Used for streaming listening events and analytical table storage.

### Bronze / Silver / Gold

The batch pipeline separates raw ingestion from cleaned and aggregated analytical datasets.

```text
Bronze
  ↓
Raw Spotify data

Silver
  ↓
Cleaned and normalized data

Gold
  ↓
Analytics-ready datasets
```

---

## Windows Development

The project was developed and tested locally on Windows.

The Spark configuration includes Windows-specific environment setup for PySpark and Hadoop dependencies.

The project also reuses a local Kafka Docker container for streaming workloads.

---

## Future Improvements

Potential future improvements include:

* More advanced AI Analyst visualizations
* More listening trend analytics
* Improved natural-language insight generation
* Additional MusicBrainz enrichment
* Automated scheduled ingestion
* Production cloud deployment
* More robust streaming monitoring
* Authentication and multi-user support

---

## Author

**Anshul Jain**

B.Tech Computer Science & Engineering

GitHub: [https://github.com/Anshuljain22](https://github.com/Anshuljain22)

```
```
