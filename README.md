# Slop Combiner (AI Generated)

A Python script that automatically generates short-form videos with AI voiceovers and animated captions.

## Features

- **Text-to-Speech** — Convert any script to natural-sounding audio using Microsoft Edge TTS
- **Video Composition** — Automatically selects random clips from a source video that match the audio duration
- **Automated Captions** — Generates word-level animated subtitles with professional styling
- **Centered Positioning** — Captions are positioned in the center of the video for optimal viewing
- **Multiple Caption Styles** — Choose from Hormozi, MrBeast, Karaoke, Minimal, Bounce, or Classic styles

## Requirements

- Python 3.11+
- FFmpeg (for video processing)
- ffprobe (included with FFmpeg)
- faster-whisper (for transcription)

### Python Dependencies

```
edge-tts
whisper-timestamped
moviepy
pillow
pysubs2
faster-whisper
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/MrPlankton611/Slop-Combiner.git
cd Slop-Combiner
```

2. Create a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install FFmpeg:
   - **Windows**: `choco install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

## Usage

1. Place your background video as `minecraft_bg.mp4` in the script directory.

2. Edit the script configuration in `test.py`:
```python
REDDIT_TITLE = "Your Title Here"
REDDIT_STORY = "Your script text here"
CAPTION_STYLE = "mrbeast"  # hormozi, bounce, karaoke, minimal, classic
CAPTION_POSITION = 50  # 1-50 (50 = center)
```

3. Run the script:
```bash
python test.py
```

4. Output video will be saved as `videos/final_reddit_edit.mp4`

## Configuration

Edit these variables in `test.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `REDDIT_TITLE` | — | Video title/headline |
| `REDDIT_STORY` | — | Main script text |
| `CAPTION_STYLE` | `"mrbeast"` | Caption style: hormozi, mrbeast, karaoke, minimal, bounce, classic |
| `CAPTION_POSITION` | `50` | Vertical position (1-50, where 50 = center) |
| `VIDEO_WIDTH` | `1920` | Output video width in pixels |
| `VIDEO_HEIGHT` | `1080` | Output video height in pixels |

## Credits

This project uses [ai-video-captions](https://github.com/nicolaigaina/ai-video-captions) by [@nicolaigaina](https://github.com/nicolaigaina) for subtitle generation and caption styling.

**ai-video-captions** is licensed under the [MIT License](LICENSE).

### Third-Party Libraries

- **edge-tts** — Microsoft Edge text-to-speech API wrapper
- **whisper-timestamped** — OpenAI Whisper with word-level timestamps
- **moviepy** — Video composition and editing
- **faster-whisper** — Optimized Whisper transcription
- **pysubs2** — Subtitle file handling

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## Disclaimer

This tool is designed for creating short-form content. Ensure you have the rights to use any background videos and comply with platform policies when uploading generated content.
