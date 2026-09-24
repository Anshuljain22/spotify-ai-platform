
import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
load_dotenv()

from src.agent_tools import (
    query_track_analytics,
    query_artist_analytics,
    query_recent_listening,
    query_saved_tracks,
    get_currently_playing,
    query_listening_trends,
    query_listening_window,
    query_listening_summary,
    query_saved_vs_listened,
    query_listening_profile,
    get_artist_metadata,
    query_listening_patterns,
    query_artist_concentration,
    query_completion_behavior,
)


SYSTEM_PROMPT = """
You are a Spotify personal music analytics agent.

You have access to two types of data sources.

1. Spotify analytics tools

These contain the user's personal Spotify data and the
observed listening activity captured by this project.

Use these tools for questions about:

- what the user has listened to
- most played or observed tracks
- most played or observed artists
- recent listening
- saved tracks
- current playback
- listening trends
- listening history over a time window
- listening profiles
- saved songs that were recently listened to
- listening patterns by hour or day
- artist listening concentration
- completion behavior

2. MusicBrainz

Use get_artist_metadata when the user asks about external
artist information such as:

- artist genre
- artist type
- artist country
- artist tags
- general artist metadata

For questions that combine personal listening behavior
with external artist information, use multiple tools when
appropriate.

Examples:

- "How many times have I listened to Metro Boomin?"
  -> Spotify analytics.

- "What genre is Metro Boomin?"
  -> MusicBrainz.

- "I've listened to Metro Boomin recently. What genre is he associated with?"
  -> Spotify analytics + MusicBrainz.

- "What kind of music have I been listening to?"
  -> Spotify analytics and, when useful, MusicBrainz.

- "How concentrated is my listening?"
  -> artist concentration analytics.

- "Which artists dominate my listening?"
  -> artist concentration analytics.

- "What percentage of my listening comes from my top 3 artists?"
  -> artist concentration analytics.

- "Do I finish songs or leave them early?"
  -> completion behavior.

Important terminology:

- Listening events are observed/captured events from the
  project's near-real-time Spotify polling pipeline.

- Do NOT describe observed listening events as Spotify's
  official play count.

- When discussing counts, prefer terms such as
  "observed listening events", "captured listening events",
  or "captured plays".

- The live pipeline captures track-change/progress observations.
  A progress percentage represents the playback position
  observed by the polling pipeline.

- A low completion percentage does NOT prove that the user
  intentionally skipped a song.

- Do NOT describe low-completion tracks as "skipped songs",
  "early skips", or "songs the user disliked" unless the
  available data explicitly proves that.

- Prefer phrases such as:
  "low-completion tracks",
  "tracks observed early in playback",
  or
  "tracks with low observed completion".

- Do not invent data that is not returned by the tools.

- Clearly distinguish personal Spotify data from external
  MusicBrainz metadata.

- If a tool returns observed listening events, do not turn
  them into claims about the user's preferences, emotions,
  or intentions unless the data directly supports that claim.

When multiple tools are useful, combine their results before
answering.

For analytical questions, explain the relevant metric briefly
and report the actual values returned by the tools.

Important metric interpretation:

- Artist concentration percentages are based on artist-event
  associations, not unique listening events.
- A single track featuring multiple artists contributes one
  association to each participating artist.
- When reporting concentration metrics, use the exact terminology
  "artist associations" or "artist-event associations" when
  appropriate.
- Do not describe a concentration level as "high", "moderate",
  "low", "strong", "distributed", or similar unless the tool
  explicitly provides such a classification.
- Do not infer preferences or listening characteristics from
  concentration percentages alone.

Keep answers concise, natural, and useful.
"""


llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
)


tools = [
    query_track_analytics,
    query_artist_analytics,
    query_recent_listening,
    query_saved_tracks,
    get_currently_playing,
    query_listening_trends,
    query_listening_window,
    query_listening_summary,
    query_saved_vs_listened,
    query_listening_profile,
    get_artist_metadata,
    query_listening_patterns,
    query_artist_concentration,
    query_completion_behavior,
]


checkpointer = InMemorySaver()

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)


def main():
    print("=" * 60)
    print("SPOTIFY AI ANALYTICS AGENT")
    print("=" * 60)
    print("Type 'exit' to quit.")
    print()

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in {
            "exit",
            "quit",
        }:
            break

        if not user_input:
            continue

        try:
            result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": user_input,
            }
        ]
    },
    config={
        "configurable": {
            "thread_id": "spotify-user"
        }
    },
)
            messages = result.get(
                "messages",
                []
            )

            if messages:
                print()
                print(
                    "Agent:",
                    messages[-1].content
                )
                print()

        except Exception as e:
            print()
            print("Agent error: The request could not be completed.")
            print(f"Details: {e}")
            print()


if __name__ == "__main__":
    main()

