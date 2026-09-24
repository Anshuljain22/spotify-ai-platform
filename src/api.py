from fastapi import FastAPI
from src.agent_tools import (
    query_listening_summary,
    query_recent_listening,
    query_artist_analytics,
    query_track_analytics,
    query_listening_profile,
    query_artist_concentration,
    query_completion_behavior,
    query_saved_vs_listened,
    get_currently_playing,
)
from src.langgraph_agent import agent

app = FastAPI(
    title="Spotify Intelligence API",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "service": "Spotify Intelligence API",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/analytics/summary")
def analytics_summary():
    return query_listening_summary()


@app.get("/analytics/recent")
def analytics_recent():
    return query_recent_listening()


@app.get("/analytics/profile")
def analytics_profile():
    return query_listening_profile()


@app.get("/analytics/concentration")
def analytics_concentration():
    return query_artist_concentration()


@app.get("/analytics/completion")
def analytics_completion():
    return query_completion_behavior()


@app.get("/analytics/saved-vs-listened")
def analytics_saved_vs_listened(days: int = 7):
    return query_saved_vs_listened(days)


@app.get("/currently-playing")
def currently_playing():
    return get_currently_playing()


@app.get("/analytics/artist/{artist_name}")
def artist_analytics(artist_name: str):
    return query_artist_analytics(artist_name)


@app.get("/analytics/track/{track_name}")
def track_analytics(track_name: str):
    return query_track_analytics(track_name)


@app.get("/agent")
def run_agent(question: str):
    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config={
            "configurable": {
                "thread_id": "spotify-api",
            }
        },
    )

    messages = result.get("messages", [])

    if not messages:
        return {"answer": "No response generated."}

    return {
        "question": question,
        "answer": messages[-1].content,
    }