
import asyncio
import random
import os
import sys
import json
import subprocess
from dataclasses import dataclass
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import io
import tempfile
# Patch for Pillow 10+ compatibility with moviepy 1.0.3
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

from edge_tts import Communicate
import whisper_timestamped as whisper
from moviepy.editor import VideoFileClip, AudioFileClip
from moviepy.config import change_settings

# --- CAPTION STYLES (from ai-video-captions) ---

@dataclass
class CaptionStyle:
    """Caption style configuration with animation"""
    name: str
    font_name: str
    font_size: int
    primary_color: tuple  # RGB tuple
    highlight_color: tuple  # RGB tuple
    outline_color: tuple  # RGB tuple
    shadow_color: tuple  # RGB tuple
    outline_size: float
    shadow_depth: float
    bold: bool
    italic: bool
    animation_type: str  # "highlight", "karaoke", "bounce", "scale"
    letter_spacing: int

CAPTION_STYLES = {
    "mrbeast": CaptionStyle(
        name="MrBeast",
        font_name="Bebas Neue",
        font_size=100,
        primary_color=(255, 255, 0),  # Yellow
        highlight_color=(255, 165, 0),  # Orange
        outline_color=(0, 0, 0),  # Black
        shadow_color=(0, 0, 0),
        outline_size=2.0,
        shadow_depth=2.0,
        bold=True,
        italic=False,
        animation_type="highlight",
        letter_spacing=100
    ),
    "bounce": CaptionStyle(
        name="Bounce",
        font_name="Arial Black",
        font_size=95,
        primary_color=(0, 255, 0),  # Green
        highlight_color=(255, 0, 255),  # Magenta
        outline_color=(0, 0, 0),
        shadow_color=(0, 0, 0),
        outline_size=1.5,
        shadow_depth=1.5,
        bold=True,
        italic=False,
        animation_type="bounce",
        letter_spacing=100
    ),
    "hormozi": CaptionStyle(
        name="Hormozi",
        font_name="Montserrat",
        font_size=90,
        primary_color=(255, 255, 255),  # White
        highlight_color=(0, 255, 255),  # Cyan
        outline_color=(0, 0, 0),
        shadow_color=(0, 0, 0),
        outline_size=2.0,
        shadow_depth=2.0,
        bold=False,
        italic=False,
        animation_type="highlight",
        letter_spacing=100
    ),
    "karaoke": CaptionStyle(
        name="Karaoke",
        font_name="Arial",
        font_size=85,
        primary_color=(255, 255, 255),  # White
        highlight_color=(0, 0, 255),  # Blue
        outline_color=(0, 0, 0),
        shadow_color=(0, 0, 0),
        outline_size=2.0,
        shadow_depth=2.0,
        bold=False,
        italic=False,
        animation_type="karaoke",
        letter_spacing=100
    ),
    "classic": CaptionStyle(
        name="Classic",
        font_name="Arial Black",
        font_size=100,
        primary_color=(255, 255, 255),  # White
        highlight_color=(255, 255, 0),  # Yellow
        outline_color=(0, 0, 0),
        shadow_color=(0, 0, 0),
        outline_size=2.5,
        shadow_depth=3.0,
        bold=True,
        italic=False,
        animation_type="highlight",
        letter_spacing=100
    ),
}

# --- HELPER FUNCTIONS FOR ASS SUBTITLE GENERATION ---

def rgb_to_ass(r: int, g: int, b: int, alpha: int = 0) -> str:
    """Convert RGB to ASS color format (&HAABBGGRR&)"""
    # ASS uses BGR order, not RGB!
    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}&"

def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def escape_ass_text(text: str) -> str:
    """Escape special ASS characters"""
    text = text.replace("\\", "\\\\")
    text = text.replace("{", "\\{")
    text = text.replace("}", "\\}")
    return text

def generate_ass_subtitles(
    transcription: dict,
    output_path: str,
    caption_style: str = "mrbeast",
    caption_position: int = 10,
    video_width: int = 1920,
    video_height: int = 1080
) -> bool:
    """
    Generate ASS subtitle file with word-level animations
    from Whisper transcription data.
    
    Args:
        transcription: Output from whisper.transcribe()
        output_path: Path to write ASS file
        caption_style: Style name from CAPTION_STYLES
        caption_position: Position from bottom (1-50)
        video_width, video_height: Video dimensions
    """
    style = CAPTION_STYLES.get(caption_style, CAPTION_STYLES["mrbeast"])
    
    # Calculate Y position (percentage from bottom)
    y_pos = int(video_height * (1 - caption_position / 100))
    
    # ASS color codes
    primary_color = rgb_to_ass(*style.primary_color)
    highlight_color = rgb_to_ass(*style.highlight_color)
    outline_color = rgb_to_ass(*style.outline_color)
    shadow_color = rgb_to_ass(*style.shadow_color)
    
    # Build ASS file
    ass_content = []
    ass_content.append("[Script Info]")
    ass_content.append("Title: Auto-generated Captions")
    ass_content.append("ScriptType: v4.00+")
    ass_content.append(f"PlayResX: {video_width}")
    ass_content.append(f"PlayResY: {video_height}")
    ass_content.append("")
    
    # Style section
    ass_content.append("[V4+ Styles]")
    ass_content.append("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding")
    
    bold_val = "-1" if style.bold else "0"
    italic_val = "-1" if style.italic else "0"
    
    ass_content.append(
        f"Style: Default,{style.font_name},100,{primary_color},{highlight_color},{outline_color},&H00000000,{bold_val},{italic_val},0,0,100,100,0,0,1,{style.outline_size},{style.shadow_depth},2,10,10,10,1"
    )
    ass_content.append("")
    
    # Events section
    ass_content.append("[Events]")
    ass_content.append("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text")
    
    # Extract words with timing
    words_data = []
    for segment in transcription.get("segments", []):
        for word_obj in segment.get("words", []):
            words_data.append({
                "word": word_obj.get("word", "").strip(),
                "start": word_obj.get("start", 0),
                "end": word_obj.get("end", 0)
            })
    
    # Generate per-word events with animations
    for i, word_data in enumerate(words_data):
        word = escape_ass_text(word_data["word"])
        start_cs = int(word_data["start"] * 100)  # Convert to centiseconds
        end_cs = int(word_data["end"] * 100)
        
        # Format times as HH:MM:SS.CC
        def format_time(cs):
            total_seconds = cs / 100
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            centiseconds = cs % 100
            return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"
        
        start_time = format_time(start_cs)
        end_time = format_time(end_cs)
        
        # Build animation based on style
        if style.animation_type == "karaoke":
            # Color wipe effect
            duration_cs = end_cs - start_cs
            text = f"{{\\kf{duration_cs}\\c{highlight_color}}}{word}"
        elif style.animation_type == "bounce":
            # Scale effect with color
            text = f"{{\\kf50\\fscx120\\fscy120\\c{highlight_color}}}{word}"
        elif style.animation_type == "scale":
            # Subtle scale
            text = f"{{\\kf30\\fscx110\\fscy110\\c{highlight_color}}}{word}"
        else:  # "highlight" (default)
            # Simple color change
            text = f"{{\\c{highlight_color}}}{word}"
        
        # Add event
        event_line = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}"
        ass_content.append(event_line)
    
    # Write ASS file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(ass_content))
        return True
    except Exception as e:
        print(f"Error writing ASS file: {e}")
        return False

def burn_subtitles_ffmpeg(video_path: str, ass_path: str, output_path: str) -> bool:
    """
    Burn ASS subtitles into video using FFmpeg.
    Uses the exact approach from ai-video-captions repository.
    
    Args:
        video_path: Input video file
        ass_path: ASS subtitle file
        output_path: Output video file
    
    Returns:
        True on success, False on failure
    """
    try:
        # Exact FFmpeg command from ai-video-captions repo
        # Key: -c:a copy preserves original audio without re-encoding
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file
            '-i', video_path,
            '-vf', f"ass={ass_path}",  # Apply ASS subtitle filter
            '-c:v', 'libx264',  # H.264 video codec
            '-preset', 'veryfast',  # Fast encoding
            '-crf', '18',  # High quality (lower = higher quality, 18 is excellent)
            '-c:a', 'copy',  # CRITICAL: Copy audio stream without re-encoding
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            return True
        else:
            print(f"FFmpeg error: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error burning subtitles: {e}")
        return False

# --- CONFIGURATION ---

# Reddit content
REDDIT_TITLE = "AITA for building a castle in my friend's farm?"
REDDIT_STORY = "So I spent 10 hours building this massive stone castle. My friend says it ruined his wheat production, but I think it looks majestic. Now he wants me to tear it down or he will ban me."

# Video files
BACKGROUND_FILE = "minecraft_bg.mp4"
OUTPUT_NAME = "videos/final_reddit_edit.mp4"
TEMP_DIR = "videos/temp"

# Caption settings
CAPTION_STYLE = "mrbeast"  # Options: mrbeast, bounce, hormozi, karaoke, classic
CAPTION_POSITION = 10  # Distance from bottom (1-50)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080


# --- HELPER FUNCTIONS ---



def get_truetype_font(fontname, size):
    """Try to load TrueType font, with fallback"""
    candidates = []
    # Prefer the requested font, then a set of aesthetic fallbacks
    if sys.platform == "win32":
        candidates = [
            f"C:\\Windows\\Fonts\\{fontname}.ttf",
            "C:\\Windows\\Fonts\\Poppins-Bold.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf",
            "C:\\Windows\\Fonts\\ARIALBD.TTF",
            "C:\\Windows\\Fonts\\impact.ttf",
            "C:\\Windows\\Fonts\\segoeui.ttf",
        ]
    else:
        candidates = [
            f"/usr/share/fonts/truetype/{fontname}.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]

    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    return ImageFont.load_default()


def whisper_to_srt(transcription):
    """
    Convert Whisper transcription output to SRT format.
    
    Args:
        transcription: Output from whisper.transcribe()
    
    Returns:
        SRT content as string
    """
    srt_lines = []
    counter = 1
    
    for segment in transcription["segments"]:
        for word in segment["words"]:
            start = word["start"]
            end = word["end"]
            text = word["text"].strip()
            
            if not text:
                continue
            
            # Convert seconds to SRT time format (HH:MM:SS,mmm)
            def format_time(seconds):
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                millis = int((seconds % 1) * 1000)
                return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
            
            srt_lines.append(str(counter))
            srt_lines.append(f"{format_time(start)} --> {format_time(end)}")
            srt_lines.append(text)
            srt_lines.append("")
            counter += 1
    
    return "\n".join(srt_lines)



def make_caption_frame(word_text, progress, caption_config, max_width=None):
    """
    DEPRECATED: This function is kept for backward compatibility.
    Use beautiful-captions instead for better results.
    """
    pass


def create_word_caption_clip(word_text, start_time, end_time, caption_config):
    """
    DEPRECATED: This function is kept for backward compatibility.
    Use beautiful-captions instead for better results.
    """
    pass


def create_word_container(word_data, target_w, caption_config):
    """
    DEPRECATED: This function is kept for backward compatibility.
    Use beautiful-captions instead for better results.
    """
    pass


async def generate_assets():
    print("Step 1: Generating AI Voiceover...")
    full_text = f"{REDDIT_TITLE}. {REDDIT_STORY}"
    communicate = Communicate(full_text, "en-US-AriaNeural")
    await communicate.save("audio.mp3")

    print("Step 2: Transcribing for word-level timestamps...")
    audio = whisper.load_audio("audio.mp3")
    model = whisper.load_model("tiny")
    result = whisper.transcribe(model, audio, language="en")
    return result


def create_edit(transcription):
    """
    Create the final video edit using ASS subtitles with professional animations.
    Uses the ai-video-captions approach with direct FFmpeg subtitle burning.
    
    Args:
        transcription: Output from whisper.transcribe()
    """
    print("Step 3: Processing Video...")
    audio = AudioFileClip("audio.mp3")
    
    # Load and Randomize Background
    bg_video = VideoFileClip(BACKGROUND_FILE)
    start_time = random.uniform(0, max(0, bg_video.duration - audio.duration - 1))
    bg_video = bg_video.subclip(start_time, start_time + audio.duration)
    
    # Vertical Crop (9:16)
    w, h = bg_video.size
    target_w = h * (9/16)
    bg_video = bg_video.crop(x_center=w/2, width=target_w).resize(height=VIDEO_HEIGHT)

    print("Step 4: Generating animated ASS subtitles...")
    
    # Create temp directory for intermediate files
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Generate ASS subtitle file
    ass_path = os.path.join(TEMP_DIR, "captions.ass")
    if not generate_ass_subtitles(
        transcription,
        ass_path,
        caption_style=CAPTION_STYLE,
        caption_position=CAPTION_POSITION,
        video_width=VIDEO_WIDTH,
        video_height=VIDEO_HEIGHT
    ):
        print("⚠ Warning: Failed to generate ASS subtitles")
        return False
    
    print("Step 5: Composing video with audio...")
    
    # Composite video without audio first
    from moviepy.editor import CompositeVideoClip
    final = CompositeVideoClip([bg_video.resize((VIDEO_WIDTH, VIDEO_HEIGHT))])
    final = final.set_duration(audio.duration)
    final = final.set_audio(audio)
    
    # Write composite video with audio to temp file
    temp_video_path = os.path.join(TEMP_DIR, "temp_video_with_audio.mp4")
    print("   Encoding intermediate video with audio...")
    final.write_videofile(
        temp_video_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        audio_bitrate="192k",
        verbose=False,
        logger=None
    )
    
    print("Step 6: Burning animated captions with FFmpeg...")
    if not burn_subtitles_ffmpeg(temp_video_path, ass_path, OUTPUT_NAME):
        print("⚠ Warning: FFmpeg subtitle burning failed")
        return False
    
    print(f"✓ Done! Video saved as {OUTPUT_NAME}")
    
    # Cleanup temp files
    try:
        os.remove(temp_video_path)
        os.remove(ass_path)
    except:
        pass


if __name__ == "__main__":
    if not os.path.exists(BACKGROUND_FILE):
        print(f"Error: {BACKGROUND_FILE} not found! Place your Minecraft video in this folder.")
    else:
        data = asyncio.run(generate_assets())
        create_edit(data)