
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/analytics/patterns")
def analytics_patterns():
    from src.agent_tools import query_listening_patterns
    return query_listening_patterns()

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

@app.get("/analytics/activity")
def analytics_activity():
    from src.agent_tools import query_listening_activity
    return query_listening_activity()


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
        return {
            "question": question,
            "answer": "No response generated.",
            "insights": [],
            "metrics": [],
        }

    content = messages[-1].content

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(text)
            elif isinstance(item, str):
                parts.append(item)

        content = "\n".join(parts)

    insights = []
    metrics = []

    question_lower = question.lower()

    try:
        if "top artist" in question_lower:
            concentration = query_artist_concentration()

            top_artist = concentration["top_artist"]
            top_artist_events = concentration["top_artist_associations"]
            top_artist_share = concentration["top_artist_association_share_pct"]
            total_events = concentration["total_artist_associations"]

            insights = [
                {
                    "title": "Top artist",
                    "description": (
                        f"{top_artist} has the highest number of "
                        f"captured artist-event associations."
                    ),
                },
                {
                    "title": "Listening share",
                    "description": (
                        f"{top_artist} represents "
                        f"{top_artist_share:.2f}% of your captured "
                        f"artist associations."
                    ),
                },
            ]

            metrics = [
                {
                    "label": "Top artist",
                    "value": top_artist,
                },
                {
                    "label": "Artist associations",
                    "value": str(top_artist_events),
                },
                {
                    "label": "Association share",
                    "value": f"{top_artist_share:.2f}%",
                },
                {
                    "label": "Total associations",
                    "value": str(total_events),
                },
            ]

    except Exception as e:
        print(f"Structured analytics error: {e}")

    return {
        "question": question,
        "answer": content,
        "insights": insights,
        "metrics": metrics,
    }