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
