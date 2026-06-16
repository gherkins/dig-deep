# Lane: youtube — watch via transcript

`digdeep youtube` fetches a video's metadata and transcript with `yt-dlp` (no API
key, no IP-blocking issues), so an agent can "watch" a video by reading it.

## Command

```
digdeep youtube "<url-or-id>" [--want both|metadata|transcript] [--lang en,en-US,…]
```

Returns `{video: {video_id, title, channel, upload_date, duration_s, description, url},
segments: [{ts, seconds, text}], language, segment_count}` (fields depend on `--want`).

## How to use it

1. Show the **video header** (title, channel, date, duration) first — confirms
   you've got the right video.
2. **Answer the question from the transcript**, don't just summarize. Cite
   `[mm:ss]` timestamps so the user can jump to the moment.
3. For long videos (>1h), scan timestamps and focus on the relevant sections, or
   summarize in chronological chunks.

## Tips

- Manual subtitles beat auto-generated; the lane prefers a manual English track
  when one exists. Auto-subs may contain `[Music]`, `[Applause]`, or rough
  punctuation — note that when it matters.
- Non-English videos: the lane works with whatever track is available; flag the
  language and that auto-translation may be lower quality.
- Pairs naturally with the **playlist** lane — hand back the videos you cited as
  a clickable playlist.
