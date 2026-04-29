# Radio Chunk Listener + Transcriber

Terminal-based pipeline that records 30-second audio clips from Radio Garden stations, detects language, transcribes in that source language, writes raw transcription, writes English translation, and deletes processed wav clips.

The channels contain example transcribed channels. Results vary on language and size of model. Recommended to use higher sized models for languages other than english.

Add station URL copied from browser into the --station-url flag, add the local folder name in --station flag, and the model size in --model flag.

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