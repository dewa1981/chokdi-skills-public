---
name: youtube-content
description: "YouTube transcripts to summaries, threads, blogs."
version: 1.0.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [YouTube, Video, Transcripts, Media]
    related_skills: []
---

# YouTube Content Tool

## When to use

Use when the user shares a YouTube URL or video link, asks to summarize a video, requests a transcript, or wants to extract and reformat content from any YouTube video. Transforms transcripts into structured content (chapters, summaries, threads, blog posts).

Extract transcripts from YouTube videos and convert them into useful formats.

## Setup

Use `uv` so the dependency is installed into the same Hermes-managed environment
that runs the helper script:

```bash
uv pip install youtube-transcript-api
```

## Helper Script

`SKILL_DIR` is the directory containing this SKILL.md file. The script accepts any standard YouTube URL format, short links (youtu.be), shorts, embeds, live links, or a raw 11-character video ID.

```bash
# JSON output with metadata
uv run python SKILL_DIR/scripts/fetch_transcript.py "https://youtube.com/watch?v=VIDEO_ID"

# Plain text (good for piping into further processing)
uv run python SKILL_DIR/scripts/fetch_transcript.py "URL" --text-only

# With timestamps
uv run python SKILL_DIR/scripts/fetch_transcript.py "URL" --timestamps

# Specific language with fallback chain
uv run python SKILL_DIR/scripts/fetch_transcript.py "URL" --language tr,en
```

## Output Formats

After fetching the transcript, format it based on what the user asks for:

- **Chapters**: Group by topic shifts, output timestamped chapter list
- **Summary**: Concise 5-10 sentence overview of the entire video
- **Chapter summaries**: Chapters with a short paragraph summary for each
- **Thread**: Twitter/X thread format — numbered posts, each under 280 chars
- **Blog post**: Full article with title, sections, and key takeaways
- **Quotes**: Notable quotes with timestamps

### Example — Chapters Output

```
00:00 Introduction — host opens with the problem statement
03:45 Background — prior work and why existing solutions fall short
12:20 Core method — walkthrough of the proposed approach
24:10 Results — benchmark comparisons and key takeaways
31:55 Q&A — audience questions on scalability and next steps
```

## Workflow

1. **Fetch** the transcript using the helper script with `--text-only --timestamps` via `uv run python`.
2. **Validate**: confirm the output is non-empty and in the expected language. If empty, retry without `--language` to get any available transcript. If STILL empty, do not stop and do not tell the user it is impossible — Shorts and many recent uploads ship no caption track at all. Switch to the audio→STT fallback below and summarize from that.
3. **Chunk if needed**: if the transcript exceeds ~50K characters, split into overlapping chunks (~40K with 2K overlap) and summarize each chunk before merging.
4. **Transform** into the requested output format. If the user did not specify a format, default to a summary.
5. **Verify**: re-read the transformed output to check for coherence, correct timestamps, and completeness before presenting.

## Fallback when there are no captions (Shorts, captions off)

`{"error": "No transcript found"}` is the NORMAL result for YouTube Shorts — go straight to audio + STT instead of reporting failure:

```bash
mkdir -p /opt/data/cache/scratch/yt && cd /opt/data/cache/scratch/yt
/opt/hermes-v0204/.venv/bin/yt-dlp --no-warnings --retries 3 --socket-timeout 60 \
  -f 'bestaudio/best' -x --audio-format mp3 -o 'short_%(id)s.%(ext)s' "<URL>"
ls -la *.mp3        # must exist before you call STT
# then POST the mp3 to ElevenLabs Scribe (model_id=scribe_v2) — see skill voice-tts-elevenlabs
```

- **Run the download ALONE, never chained with `--print`.** One invocation that prints `TITLE=`/`UPLOADER=` metadata can exit successfully while writing no audio file; metadata prints and the download step succeed/fail independently. Take metadata first, download in a separate call, then confirm the file with `ls`.
- **`Unable to download API page: Read timed out`** is transient throttling, not a dead URL — rerun with `--socket-timeout 60 --retries 3` (a plain rerun usually clears it). Do not conclude the video is unavailable from the first timeout.
- **Check the artifact, not the exit code.** yt-dlp can return 0 with no file — confirm the `.mp3` exists (search_files with target='files', or the shell's own `ls` inside the same command block) before you call STT.
- A 2–3 minute Shorts is ~3 MB of mp3 — one Scribe call, no chunking. Chunking is only for the 50K-char transcript problem, not for Shorts.
- **State the basis** of the summary to the user (auto-captions vs audio transcribed with STT, plus the detected language probability). A machine transcription can mis-hear names and numbers; saying so keeps the summary honest.

## Error Handling

- **Transcript disabled**: on Shorts/music uploads assume this and use the audio→STT fallback above; only report it as a blocker if the audio download itself fails too.
- **Private/unavailable video**: relay the error and ask the user to verify the URL.
- **No matching language**: retry without `--language` to fetch any available transcript, then note the actual language to the user.
- **Dependency missing**: run `uv pip install youtube-transcript-api` and retry.
