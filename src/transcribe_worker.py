#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import re
import ssl
import sys
import time
from pathlib import Path


def append_line(file_path: Path, text: str) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("a", encoding="utf-8") as handle:
        handle.write(text.strip() + "\n")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def collapse_repeated_phrases(text: str) -> str:
    parts = [p.strip() for p in re.split(r"([.!?])", text) if p.strip()]
    rebuilt: list[str] = []
    i = 0
    while i < len(parts):
        if i + 1 < len(parts) and parts[i + 1] in ".!?":
            sentence = f"{parts[i]}{parts[i + 1]}"
            i += 2
        else:
            sentence = parts[i]
            i += 1
        if rebuilt and normalize_text(rebuilt[-1]) == normalize_text(sentence):
            continue
        rebuilt.append(sentence)
    return " ".join(rebuilt).strip()


def translate_to_english(translator, text: str) -> str:
    try:
        return translator.translate(text)
    except Exception:
        return text


def detect_chunk_language(whisper_module, model, wav_file: Path) -> tuple[str | None, float]:
    try:
        audio = whisper_module.load_audio(str(wav_file))
        audio = whisper_module.pad_or_trim(audio)
        mel = whisper_module.log_mel_spectrogram(audio).to(model.device)
        _, probs = model.detect_language(mel)
        if not probs:
            return None, 0.0
        lang, score = max(probs.items(), key=lambda item: item[1])
        return lang, float(score)
    except Exception:
        return None, 0.0


def is_file_stable(wav_file: Path, min_age_seconds: float = 1.5) -> bool:
    try:
        stat = wav_file.stat()
    except FileNotFoundError:
        return False
    age = time.time() - stat.st_mtime
    return age >= min_age_seconds and stat.st_size > 0


def run(channel_dir: Path, model_name: str, poll_seconds: float) -> None:
    raw_transcript_file = channel_dir / "raw-transcription.txt"
    translation_file = channel_dir / "translation.txt"
    raw_transcript_file.touch(exist_ok=True)
    translation_file.touch(exist_ok=True)
    # Some environments have broken cert chains; this allows model download to proceed.
    ssl._create_default_https_context = ssl._create_unverified_context

    try:
        whisper = importlib.import_module("whisper")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency 'openai-whisper'. Create a venv and install requirements."
        ) from exc
    try:
        deep_translator = importlib.import_module("deep_translator")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency 'deep-translator'. Install requirements in your venv."
        ) from exc

    model = whisper.load_model(model_name)
    translator = deep_translator.GoogleTranslator(source="auto", target="en")
    while True:
        wav_files = sorted(channel_dir.glob("*.wav"))
        ready_files = [wav for wav in wav_files if is_file_stable(wav)]
        for wav_file in ready_files:
            try:
                result = model.transcribe(
                    str(wav_file),
                    task="transcribe",
                    fp16=False,
                    condition_on_previous_text=False,
                    temperature=0.0,
                    no_speech_threshold=0.6,
                    compression_ratio_threshold=2.2,
                    language=None,
                )
                detected_lang, lang_conf = detect_chunk_language(whisper, model, wav_file)
                if detected_lang and lang_conf >= 0.45:
                    result = model.transcribe(
                        str(wav_file),
                        task="transcribe",
                        fp16=False,
                        condition_on_previous_text=False,
                        temperature=0.0,
                        no_speech_threshold=0.6,
                        compression_ratio_threshold=2.2,
                        language=detected_lang,
                    )
                source_text = re.sub(r"\s+", " ", str(result.get("text", "")).strip())
                if not source_text:
                    wav_file.unlink(missing_ok=True)
                    continue
                source_text = collapse_repeated_phrases(source_text)

                language_tag = detected_lang if detected_lang else "unknown"
                append_line(raw_transcript_file, f"[{language_tag}] {source_text}")

                english_text = translate_to_english(translator, source_text)
                english_text = collapse_repeated_phrases(re.sub(r"\s+", " ", english_text).strip())
                if english_text:
                    append_line(translation_file, english_text)
                wav_file.unlink(missing_ok=True)
            except FileNotFoundError:
                # ffmpeg rotated/deleted file between scan and processing.
                continue
            except Exception as exc:
                # Keep wav for retry, but don't pollute transcript with internal errors.
                print(f"[worker-error] {wav_file.name}: {exc}", file=sys.stderr, flush=True)
        time.sleep(poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Translate wav clips to English text.")
    parser.add_argument("--channel-dir", required=True, help="Path to station folder")
    parser.add_argument(
        "--model",
        default="small",
        help="Whisper model (tiny, base, small, medium, large)",
    )
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    args = parser.parse_args()

    run(
        channel_dir=Path(args.channel_dir),
        model_name=args.model,
        poll_seconds=args.poll_seconds,
    )


if __name__ == "__main__":
    main()

