"use client";

import { useEffect, useState, type ReactNode } from "react";

const API = "http://127.0.0.1:8000";

type AnyData = Record<string, any>;

type Activity = {
  date: string;
  play_events: number;
  unique_tracks: number;
};

type AgentInsight = {
  title: string;
  description: string;
};

type AgentMetric = {
  label: string;
  value: string;
};

type AgentData = {
  question: string;
  answer: string;
  insights: AgentInsight[];
  metrics: AgentMetric[];
};

function Metric({
  label,
  value,
  sub,
}: {
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
      <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
        {label}
      </p>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
      {sub && <p className="mt-1 text-xs text-zinc-500">{sub}</p>}
    </div>
  );
}

function Panel({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.035] p-5 shadow-2xl shadow-black/10">
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-white">{title}</h2>
        {subtitle && (
          <p className="mt-1 text-sm text-zinc-500">{subtitle}</p>
        )}
      </div>
      {children}
    </section>
  );
}

function ProgressBar({
  value,
  label,
}: {
  value: number;
  label?: string;
}) {
  const safe = Math.max(0, Math.min(100, Number(value) || 0));

  return (
    <div>
      {label && (
        <div className="mb-1 flex justify-between text-xs text-zinc-500">
          <span>{label}</span>
          <span>{safe.toFixed(1)}%</span>
        </div>
      )}

      <div className="h-2 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-white transition-all"
          style={{ width: `${safe}%` }}
        />
      </div>
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-white/10 p-6 text-center text-sm text-zinc-600">
      {text}
    </div>
  );
}

function ActivityChart({ data }: { data: Activity[] }) {
  if (!data.length) {
    return <Empty text="No listening activity available yet." />;
  }

  const maxEvents = Math.max(
    ...data.map((item) => Number(item.play_events) || 0),
    1
  );

  return (
    <div className="space-y-4">
      <div className="flex h-56 items-end gap-3">
        {data.map((item) => {
          const events = Number(item.play_events) || 0;
          const height = Math.max((events / maxEvents) * 100, 6);

          const formattedDate = new Date(
            `${item.date}T00:00:00`
          ).toLocaleDateString(undefined, {
            month: "short",
            day: "numeric",
          });

          return (
            <div
              key={item.date}
              className="flex h-full flex-1 flex-col items-center justify-end gap-2"
            >
              <span className="text-xs font-medium text-zinc-400">
                {events}
              </span>

              <div
                className="group relative w-full max-w-16 rounded-t-xl bg-green-400/70 transition-all duration-300 hover:bg-green-400"
                style={{ height: `${height}%` }}
                title={`${events} play events · ${item.unique_tracks} unique tracks`}
              >
                <div className="pointer-events-none absolute bottom-full left-1/2 mb-2 hidden -translate-x-1/2 whitespace-nowrap rounded-lg border border-white/10 bg-zinc-900 px-3 py-2 text-xs text-zinc-300 shadow-xl group-hover:block">
                  <div>{events} play events</div>
                  <div className="text-zinc-500">
                    {item.unique_tracks} unique tracks
                  </div>
                </div>
              </div>

              <span className="text-xs text-zinc-500">
                {formattedDate}
              </span>
            </div>
          );
        })}
      </div>

      <div className="flex items-center justify-between border-t border-white/5 pt-3 text-xs text-zinc-600">
        <span>Captured listening events</span>
        <span>Unique tracks shown on hover</span>
      </div>
    </div>
  );
}

export default function Home() {
  const [summary, setSummary] = useState<AnyData>({});
  const [profile, setProfile] = useState<AnyData>({});
  const [patterns, setPatterns] = useState<AnyData>({});
  const [concentration, setConcentration] = useState<AnyData>({});
  const [saved, setSaved] = useState<AnyData>({});
  const [current, setCurrent] = useState<AnyData>({});
  const [recent, setRecent] = useState<AnyData[]>([]);
  const [completion, setCompletion] = useState<AnyData>({});
  const [activity, setActivity] = useState<Activity[]>([]);

  const [question, setQuestion] = useState("");
  const [agentData, setAgentData] = useState<AgentData | null>(null);
  const [asking, setAsking] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function fetchJson(path: string) {
    const response = await fetch(`${API}${path}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`${path} returned ${response.status}`);
    }

    return response.json();
  }

  async function loadDashboard() {
    try {
      setError("");

      const [
        summaryData,
        profileData,
        patternsData,
        concentrationData,
        savedData,
        currentData,
        recentData,
        completionData,
        activityData,
      ] = await Promise.all([
        fetchJson("/analytics/summary"),
        fetchJson("/analytics/profile"),
        fetchJson("/analytics/patterns"),
        fetchJson("/analytics/concentration"),
        fetchJson("/analytics/saved-vs-listened?days=7"),
        fetchJson("/currently-playing"),
        fetchJson("/analytics/recent"),
        fetchJson("/analytics/completion"),
        fetchJson("/analytics/activity"),
      ]);

      setSummary(summaryData);
      setProfile(profileData);
      setPatterns(patternsData);
      setConcentration(concentrationData);
      setSaved(savedData);
      setCurrent(currentData);

      setRecent(
        Array.isArray(recentData)
          ? recentData
          : recentData.items || []
      );

      setCompletion(completionData);
      setActivity(
        Array.isArray(activityData) ? activityData : []
      );
    } catch (err) {
      console.error(err);
      setError("Unable to load analytics from the FastAPI backend.");
    } finally {
      setLoading(false);
    }
  }

  async function refreshCurrent() {
    try {
      const data = await fetchJson("/currently-playing");
      setCurrent(data);
    } catch (err) {
      console.error(err);
    }
  }

  async function askAgent() {
    if (!question.trim() || asking) return;

    try {
      setAsking(true);

      const response = await fetch(
        `${API}/agent?question=${encodeURIComponent(
          question.trim()
        )}`,
        {
          cache: "no-store",
        }
      );

      if (!response.ok) {
        throw new Error(`Agent returned ${response.status}`);
      }

      const data = await response.json();

      setAgentData({
        question: data.question ?? question,
        answer: data.answer ?? "No response generated.",
        insights: Array.isArray(data.insights)
          ? data.insights
          : [],
        metrics: Array.isArray(data.metrics)
          ? data.metrics
          : [],
      });
    } catch (err) {
      console.error(err);

      setAgentData({
        question,
        answer: "The AI Analyst could not process that question.",
        insights: [],
        metrics: [],
      });
    } finally {
      setAsking(false);
    }
  }

  useEffect(() => {
    loadDashboard();

    const interval = setInterval(refreshCurrent, 10000);

    return () => clearInterval(interval);
  }, []);

  const currentProgress =
    current?.duration_ms > 0
      ? (current.progress_ms / current.duration_ms) * 100
      : 0;

  const topArtists = patterns?.top_artists || [];
  const topTracks = patterns?.top_tracks || [];

  const maxArtistEvents = Math.max(
    1,
    ...topArtists.map(
      (item: AnyData) => Number(item.play_events) || 0
    )
  );

  const maxTrackEvents = Math.max(
    1,
    ...topTracks.map(
      (item: AnyData) => Number(item.play_events) || 0
    )
  );

  const formatTime = (ms: number) => {
    if (!ms || ms < 0) return "0:00";

    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remaining = seconds % 60;

    return `${minutes}:${remaining
      .toString()
      .padStart(2, "0")}`;
  };

  const associationShare = Number(
    agentData?.metrics
      ?.find(
        (metric) => metric.label === "Association share"
      )
      ?.value.replace("%", "") || 0
  );

  return (
    <main className="min-h-screen bg-[#09090b] text-white">
      <div className="mx-auto max-w-7xl px-5 py-8 md:px-8 lg:px-10">

        {/* Header */}
        <header className="mb-8 flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="mb-3 flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-green-400 shadow-[0_0_12px_rgba(74,222,128,0.7)]" />

              <span className="text-xs font-medium uppercase tracking-[0.2em] text-zinc-500">
                Spotify Intelligence
              </span>
            </div>

            <h1 className="text-3xl font-bold tracking-tight md:text-4xl">
              Listening Analytics
            </h1>

            <p className="mt-2 max-w-2xl text-sm text-zinc-500">
              Your personal music data lakehouse, streaming analytics, and AI
              analyst in one place.
            </p>
          </div>

          <button
            type="button"
            onClick={loadDashboard}
            className="rounded-xl border border-white/10 bg-white/[0.05] px-4 py-2.5 text-sm font-medium text-zinc-300 transition hover:bg-white/[0.09] hover:text-white"
          >
            Refresh analytics
          </button>
        </header>

        {error && (
          <div className="mb-6 rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex min-h-[50vh] items-center justify-center">
            <div className="text-sm text-zinc-500">
              Loading your listening data...
            </div>
          </div>
        ) : (
          <div className="space-y-6">

            {/* Current Playback */}
            <section className="overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.08] to-white/[0.025] p-6">
              <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
                <div className="flex min-w-0 items-center gap-5">
                  <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl bg-white/[0.08] text-3xl">
                    🎧
                  </div>

                  <div className="min-w-0">
                    <div className="mb-1 flex items-center gap-2">
                      <span className="text-xs font-medium uppercase tracking-wider text-green-400">
                        {current?.is_playing
                          ? "Now playing"
                          : "Playback inactive"}
                      </span>

                      {current?.is_playing && (
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-green-400" />
                      )}
                    </div>

                    {current?.is_playing ? (
                      <>
                        <h2 className="truncate text-2xl font-semibold text-white">
                          {current.track_name}
                        </h2>

                        <p className="truncate text-sm text-zinc-400">
                          {current.artists?.join(", ")} ·{" "}
                          {current.album_name}
                        </p>
                      </>
                    ) : (
                      <>
                        <h2 className="text-2xl font-semibold text-white">
                          Nothing is playing
                        </h2>

                        <p className="text-sm text-zinc-500">
                          The live listener is still monitoring playback.
                        </p>
                      </>
                    )}
                  </div>
                </div>

                {current?.is_playing && (
                  <div className="w-full md:w-72">
                    <ProgressBar value={currentProgress} />

                    <div className="mt-2 flex justify-between text-xs text-zinc-600">
                      <span>{formatTime(current.progress_ms)}</span>
                      <span>{formatTime(current.duration_ms)}</span>
                    </div>
                  </div>
                )}
              </div>
            </section>

            {/* Overview */}
            <div>
              <div className="mb-4">
                <h2 className="text-lg font-semibold">
                  Overview
                </h2>

                <p className="text-sm text-zinc-500">
                  Captured listening activity from your lakehouse.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                <Metric
                  label="Play events"
                  value={summary.play_events ?? 0}
                  sub="Last 7 days"
                />

                <Metric
                  label="Unique tracks"
                  value={summary.unique_tracks ?? 0}
                  sub="Observed"
                />

                <Metric
                  label="Unique artists"
                  value={profile.unique_artists ?? 0}
                  sub="Observed"
                />

                <Metric
                  label="Avg completion"
                  value={`${Number(
                    summary.avg_completion_pct ?? 0
                  ).toFixed(1)}%`}
                  sub="Observed playback"
                />
              </div>
            </div>

            {/* Listening Activity */}
            <Panel
              title="Listening activity"
              subtitle="Captured playback events by day"
            >
              <ActivityChart data={activity} />
            </Panel>

            {/* Artists + Tracks */}
            <div className="grid gap-6 lg:grid-cols-2">
              <Panel
                title="Top artists"
                subtitle="Based on captured listening events"
              >
                {topArtists.length === 0 ? (
                  <Empty text="No artist data available." />
                ) : (
                  <div className="space-y-4">
                    {topArtists.slice(0, 7).map(
                      (artist: AnyData, index: number) => {
                        const count =
                          Number(artist.play_events) || 0;

                        return (
                          <div
                            key={`${artist.artist}-${index}`}
                          >
                            <div className="mb-1.5 flex items-center justify-between">
                              <div className="flex min-w-0 items-center gap-3">
                                <span className="w-5 text-xs text-zinc-600">
                                  {String(index + 1).padStart(2, "0")}
                                </span>

                                <span className="truncate text-sm text-zinc-200">
                                  {artist.artist}
                                </span>
                              </div>

                              <span className="ml-3 text-xs text-zinc-500">
                                {count}
                              </span>
                            </div>

                            <div className="ml-8 h-1.5 overflow-hidden rounded-full bg-white/10">
                              <div
                                className="h-full rounded-full bg-zinc-300"
                                style={{
                                  width: `${
                                    (count / maxArtistEvents) *
                                    100
                                  }%`,
                                }}
                              />
                            </div>
                          </div>
                        );
                      }
                    )}
                  </div>
                )}
              </Panel>

              <Panel
                title="Top tracks"
                subtitle="Most frequently captured tracks"
              >
                {topTracks.length === 0 ? (
                  <Empty text="No track data available." />
                ) : (
                  <div className="space-y-4">
                    {topTracks.slice(0, 7).map(
                      (track: AnyData, index: number) => {
                        const count =
                          Number(track.play_events) || 0;

                        return (
                          <div
                            key={`${track.track_name}-${index}`}
                          >
                            <div className="mb-1.5 flex items-center justify-between">
                              <div className="flex min-w-0 items-center gap-3">
                                <span className="w-5 text-xs text-zinc-600">
                                  {String(index + 1).padStart(2, "0")}
                                </span>

                                <span className="truncate text-sm text-zinc-200">
                                  {track.track_name}
                                </span>
                              </div>

                              <span className="ml-3 text-xs text-zinc-500">
                                {count}
                              </span>
                            </div>

                            <div className="ml-8 h-1.5 overflow-hidden rounded-full bg-white/10">
                              <div
                                className="h-full rounded-full bg-zinc-300"
                                style={{
                                  width: `${
                                    (count / maxTrackEvents) *
                                    100
                                  }%`,
                                }}
                              />
                            </div>
                          </div>
                        );
                      }
                    )}
                  </div>
                )}
              </Panel>
            </div>

            {/* Profile / Concentration / Saved */}
            <div className="grid gap-6 md:grid-cols-3">
              <Panel title="Listening profile">
                <div className="grid grid-cols-2 gap-3">
                  <Metric
                    label="Days"
                    value={profile.days ?? 0}
                  />

                  <Metric
                    label="Events"
                    value={profile.total_events ?? 0}
                  />

                  <Metric
                    label="Tracks"
                    value={profile.unique_tracks ?? 0}
                  />

                  <Metric
                    label="Artists"
                    value={profile.unique_artists ?? 0}
                  />
                </div>
              </Panel>

              <Panel
                title="Artist concentration"
                subtitle="Artist-event associations"
              >
                <div className="space-y-5">
                  <div>
                    <p className="text-xs uppercase tracking-wider text-zinc-600">
                      Top artist
                    </p>

                    <p className="mt-1 text-xl font-semibold text-white">
                      {concentration.top_artist || "—"}
                    </p>

                    <p className="mt-1 text-sm text-zinc-500">
                      {Number(
                        concentration.top_artist_association_share_pct ??
                          0
                      ).toFixed(2)}
                      % of associations
                    </p>
                  </div>

                  <ProgressBar
                    value={
                      Number(
                        concentration.top_artist_association_share_pct
                      ) || 0
                    }
                    label="Top artist share"
                  />

                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-xl bg-white/[0.04] p-3">
                      <p className="text-xs text-zinc-600">
                        Top 3
                      </p>

                      <p className="mt-1 text-lg font-semibold">
                        {Number(
                          concentration.top_3_artist_association_share_pct ??
                            0
                        ).toFixed(1)}
                        %
                      </p>
                    </div>

                    <div className="rounded-xl bg-white/[0.04] p-3">
                      <p className="text-xs text-zinc-600">
                        Top 5
                      </p>

                      <p className="mt-1 text-lg font-semibold">
                        {Number(
                          concentration.top_5_artist_association_share_pct ??
                            0
                        ).toFixed(1)}
                        %
                      </p>
                    </div>
                  </div>
                </div>
              </Panel>

              <Panel
                title="Saved vs listened"
                subtitle="Last 7 days"
              >
                <div className="space-y-5">
                  <Metric
                    label="Saved tracks"
                    value={saved.saved_tracks ?? 0}
                  />

                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-xl bg-white/[0.04] p-3">
                      <p className="text-xs text-zinc-600">
                        Recently listened
                      </p>

                      <p className="mt-1 text-xl font-semibold">
                        {saved.recently_listened_unique_tracks ?? 0}
                      </p>
                    </div>

                    <div className="rounded-xl bg-white/[0.04] p-3">
                      <p className="text-xs text-zinc-600">
                        Saved + listened
                      </p>

                      <p className="mt-1 text-xl font-semibold">
                        {saved.saved_and_listened_tracks ?? 0}
                      </p>
                    </div>
                  </div>
                </div>
              </Panel>
            </div>

            {/* Completion */}
            <Panel
              title="Completion behavior"
              subtitle="Observed playback completion from captured events"
            >
              <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
                <Metric
                  label="Events"
                  value={completion.total_events ?? 0}
                />

                <Metric
                  label="Average"
                  value={`${Number(
                    completion.average_completion_pct ?? 0
                  ).toFixed(1)}%`}
                />

                <Metric
                  label="High completion"
                  value={completion.high_completion_events ?? 0}
                />

                <Metric
                  label="Low completion"
                  value={completion.low_completion_events ?? 0}
                />
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                <div>
                  <p className="mb-3 text-sm font-medium text-zinc-300">
                    Most completed
                  </p>

                  <div className="space-y-3">
                    {(completion.top_completed_tracks || [])
                      .slice(0, 5)
                      .map(
                        (
                          track: AnyData,
                          index: number
                        ) => (
                          <div
                            key={`${track.track_name}-${index}`}
                            className="rounded-xl bg-white/[0.035] p-3"
                          >
                            <div className="mb-2 flex justify-between gap-3">
                              <span className="truncate text-sm text-zinc-300">
                                {track.track_name}
                              </span>

                              <span className="shrink-0 text-xs text-zinc-500">
                                {Number(
                                  track.avg_completion_pct ?? 0
                                ).toFixed(1)}
                                %
                              </span>
                            </div>

                            <ProgressBar
                              value={
                                Number(
                                  track.avg_completion_pct
                                ) || 0
                              }
                            />
                          </div>
                        )
                      )}
                  </div>
                </div>

                <div>
                  <p className="mb-3 text-sm font-medium text-zinc-300">
                    Lowest observed completion
                  </p>

                  <div className="space-y-3">
                    {(completion.low_completion_tracks || [])
                      .slice(0, 5)
                      .map(
                        (
                          track: AnyData,
                          index: number
                        ) => (
                          <div
                            key={`${track.track_name}-${index}`}
                            className="rounded-xl bg-white/[0.035] p-3"
                          >
                            <div className="mb-2 flex justify-between gap-3">
                              <span className="truncate text-sm text-zinc-300">
                                {track.track_name}
                              </span>

                              <span className="shrink-0 text-xs text-zinc-500">
                                {Number(
                                  track.avg_completion_pct ?? 0
                                ).toFixed(1)}
                                %
                              </span>
                            </div>

                            <ProgressBar
                              value={
                                Number(
                                  track.avg_completion_pct
                                ) || 0
                              }
                            />
                          </div>
                        )
                      )}
                  </div>
                </div>
              </div>
            </Panel>

            {/* Recent listening */}
            <Panel
              title="Recent listening"
              subtitle="Latest captured playback observations"
            >
              {recent.length === 0 ? (
                <Empty text="No recent listening events." />
              ) : (
                <div className="divide-y divide-white/5">
                  {recent.slice(0, 10).map(
                    (
                      item: AnyData,
                      index: number
                    ) => (
                      <div
                        key={`${item.track_name}-${index}`}
                        className="flex items-center gap-4 py-4 first:pt-0 last:pb-0"
                      >
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/[0.05] text-sm text-zinc-500">
                          {String(index + 1).padStart(2, "0")}
                        </div>

                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-zinc-200">
                            {item.track_name}
                          </p>

                          <p className="mt-0.5 truncate text-xs text-zinc-600">
                            {item.artists?.join(", ") ||
                              "Unknown artist"}
                            {item.album_name
                              ? ` · ${item.album_name}`
                              : ""}
                          </p>
                        </div>

                        <div className="w-24 shrink-0">
                          <ProgressBar
                            value={
                              Number(item.progress_pct) || 0
                            }
                          />
                        </div>

                        <span className="w-12 shrink-0 text-right text-xs text-zinc-500">
                          {Number(
                            item.progress_pct || 0
                          ).toFixed(0)}
                          %
                        </span>
                      </div>
                    )
                  )}
                </div>
              )}
            </Panel>

            {/* AI Analyst */}
            <section className="overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.07] to-white/[0.025]">
              <div className="border-b border-white/10 px-6 py-5">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.08] text-lg">
                    ✦
                  </div>

                  <div>
                    <h2 className="font-semibold text-white">
                      AI Analyst
                    </h2>

                    <p className="text-xs text-zinc-500">
                      Ask questions about your Spotify listening data
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-6">
                {/* Suggested questions */}
                <div className="mb-4 flex flex-wrap gap-2">
                  {[
                    "What artist do I listen to most?",
                    "What percentage of my listening is concentrated in my top 3 artists?",
                    "What music have I listened to recently?",
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      onClick={() => setQuestion(suggestion)}
                      className="rounded-full border border-white/10 bg-white/[0.035] px-3 py-2 text-xs text-zinc-400 transition hover:bg-white/[0.08] hover:text-white"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>

                {/* Question input */}
                <div className="flex flex-col gap-3 md:flex-row">
                  <input
                    value={question}
                    onChange={(event) =>
                      setQuestion(event.target.value)
                    }
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        askAgent();
                      }
                    }}
                    placeholder="Ask something about your listening..."
                    className="min-w-0 flex-1 rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none placeholder:text-zinc-700 focus:border-white/20"
                  />

                  <button
                    type="button"
                    onClick={askAgent}
                    disabled={
                      asking || !question.trim()
                    }
                    className="rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {asking ? "Analyzing..." : "Ask Analyst"}
                  </button>
                </div>

                {/* Analyst result */}
                {agentData && (
                  <div className="mt-5 space-y-5">

                    {/* Answer */}
                    <div className="rounded-2xl border border-white/10 bg-black/20 p-5">
                      <div className="mb-3 flex items-center gap-2">
                        <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-white/[0.08] text-xs">
                          ✦
                        </div>

                        <div className="text-xs font-medium uppercase tracking-wider text-zinc-600">
                          Analyst
                        </div>
                      </div>

                      <div className="text-sm leading-7 text-zinc-300">
                        {agentData.answer}
                      </div>
                    </div>

                    {/* Metrics */}
                    {agentData.metrics.length > 0 && (
                      <div>
                        <div className="mb-3 text-xs font-medium uppercase tracking-wider text-zinc-600">
                          Key metrics
                        </div>

                        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                          {agentData.metrics.map(
                            (metric, index) => (
                              <div
                                key={`${metric.label}-${index}`}
                                className="rounded-2xl border border-white/10 bg-white/[0.035] p-4"
                              >
                                <div className="text-xs text-zinc-600">
                                  {metric.label}
                                </div>

                                <div className="mt-2 truncate text-lg font-semibold text-white">
                                  {metric.value}
                                </div>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    )}

                    {/* Insights */}
                    {agentData.insights.length > 0 && (
                      <div>
                        <div className="mb-3 text-xs font-medium uppercase tracking-wider text-zinc-600">
                          Key insights
                        </div>

                        <div className="grid gap-3 md:grid-cols-2">
                          {agentData.insights.map(
                            (insight, index) => (
                              <div
                                key={`${insight.title}-${index}`}
                                className="rounded-2xl border border-white/10 bg-white/[0.035] p-4"
                              >
                                <div className="flex items-start gap-3">
                                  <div className="mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-white/[0.06] text-xs text-zinc-400">
                                    ✦
                                  </div>

                                  <div className="min-w-0">
                                    <div className="text-sm font-medium text-white">
                                      {insight.title}
                                    </div>

                                    <div className="mt-1 text-sm leading-6 text-zinc-500">
                                      {insight.description}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    )}

                    {/* Artist concentration */}
                    {agentData.metrics.some(
                      (metric) =>
                        metric.label === "Association share"
                    ) && (
                      <div>
                        <div className="mb-3 text-xs font-medium uppercase tracking-wider text-zinc-600">
                          Artist concentration
                        </div>

                        <div className="rounded-2xl border border-white/10 bg-black/20 p-5">
                          <div className="mb-3 flex items-center justify-between gap-4">
                            <span className="text-sm text-zinc-500">
                              Top artist share
                            </span>

                            <span className="text-sm font-semibold text-white">
                              {associationShare.toFixed(2)}%
                            </span>
                          </div>

                          <div className="h-2.5 overflow-hidden rounded-full bg-white/[0.06]">
                            <div
                              className="h-full rounded-full bg-white transition-all duration-700"
                              style={{
                                width: `${Math.min(
                                  100,
                                  associationShare
                                )}%`,
                              }}
                            />
                          </div>

                          <div className="mt-2 flex justify-between text-[11px] text-zinc-700">
                            <span>0%</span>
                            <span>100%</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </section>

            {/* Footer */}
            <footer className="border-t border-white/5 pt-6 text-center text-xs text-zinc-700">
              Spotify Intelligence Platform · Batch analytics + Kafka
              near-real-time events + Spark + Iceberg + LangGraph
            </footer>
          </div>
        )}
      </div>
    </main>
  );
}