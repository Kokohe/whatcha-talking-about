# Radio Chunk Listener + Transcriber

Terminal-based pipeline that records 30-second audio clips from Radio Garden stations, detects language, transcribes in that source language, writes raw transcription, writes English translation, and deletes processed wav clips.

start by station URL copied from browser

```Example Bash
./listen.sh --station-url <URL> --station <Local Folder Name> --model <Model Size>
```

```Example Bash
./listen.sh --station-url "https://radio.garden/listen/bbc-world-service/FXyhz9Xk" --station "BBC World Service" --model small
```

Stop all active listeners:

```bash
./stop.sh
```