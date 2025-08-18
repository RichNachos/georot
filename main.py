import uvicorn
import os
from pathlib import Path
from datetime import datetime
from typing import List

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

from google import genai
from google.genai import types
import wave 

class TextInput(BaseModel):
    inputText: str

class HistoryItem(BaseModel):
    filename: str
    url: str
    date: str

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ---- TEXT TO SPEACH API ---------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

OUTPUT_DIR = Path("static/to_speech")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

client = genai.Client(api_key=GOOGLE_API_KEY)

def get_next_filename() -> Path:
    """Return next incrementing filename in OUTPUT_DIR as X.wav"""
    existing = [int(f.stem) for f in OUTPUT_DIR.glob("*.wav") if f.stem.isdigit()]
    next_id = max(existing, default=0) + 1
    return OUTPUT_DIR / f"{next_id}.wav"

def wave_file(filename: Path, pcm: bytes, channels=1, rate=24000, sample_width=2):
    """Write PCM data to a .wav file"""
    with wave.open(str(filename), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

def generate_speach(input_text:str) -> Path:
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=f"Say in Georgian : {input_text}",
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Kore',
                    )
                )
            ),
        )
    )

    pcm_data = response.candidates[0].content.parts[0].inline_data.data
    file_path = get_next_filename()
    wave_file(file_path, pcm_data)
    return file_path


# --- Transformation Logic Functions ---

def apply_voicing_rules(input_text: str) -> str:
    """
    Applies the first set of transformation rules based on the image.
    This function maps certain voiceless consonants to their voiced counterparts.
    """
    voicing_map = {
        "თ": "დ", "ტ": "დ", "პ": "ბ", "ფ": "ბ", "კ": "გ", "ქ": "გ",
        "ყ": "ღ", "ხ": "ღ", "ჩ": "ჯ", "ჭ": "ჯ", "ს": "ზ", "შ": "ჟ",
        "ც": "ძ", "წ": "ძ",
    }
    translation_table = str.maketrans(voicing_map)
    return input_text.translate(translation_table)


def apply_n_prepending_rules(input_text: str) -> str:
    """
    Applies the second transformation rule based on the image.
    This function prepends the letter 'ნ' to a specific set of consonants.
    """
    target_chars = {"ბ", "გ", "დ", "ზ", "ჟ", "ც", "ძ", "ჯ", "ვ"}
    result = []
    for i, char in enumerate(input_text):
        if char not in target_chars:
            result.append(char)
            continue
        if (i > 0 and input_text[i - 1] == " ") or (i == 0):
            result.append(char)
            continue
        result.append("ნ")
        result.append(char)
    return "".join(result)


def transform_georgian_text(input_text: str):
    voiced_text = apply_voicing_rules(input_text)
    final_text = apply_n_prepending_rules(voiced_text)
    file_path = generate_speach(input_text=final_text)
    return final_text, file_path

# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Serves the main HTML page of the application.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/transform")
async def transform_text(text_input: TextInput):
    transformed_text, file_path = transform_georgian_text(text_input.inputText)
    return JSONResponse(content={
        "transformed_text": transformed_text,
        "audio_url": f"/{file_path}".replace("\\", "/")
    })


@app.get("/history", response_model=List[HistoryItem])
async def get_history():
    """
    Scans the static/to_speach directory, gets the 5 most recent .wav files,
    and returns them as a JSON list.
    """
    history_dir = Path("static/to_speach")
    if not history_dir.exists():
        return []

    try:
        wav_files = list(history_dir.glob("*.wav"))
    except Exception as e:
        print(f"Error reading directory: {e}")
        return []

    files_with_time = []
    for f in wav_files:
        try:
            mod_time = f.stat().st_mtime
            files_with_time.append((f, mod_time))
        except FileNotFoundError:
            continue

    files_with_time.sort(key=lambda x: x[1], reverse=True)
    recent_files = files_with_time[:5]

    history_list = []
    for file_path, mod_time in recent_files:
        history_list.append(
            HistoryItem(
                filename=file_path.name,
                url=f"/{file_path}".replace("\\", "/"), 
                date=datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
            )
        )
    return history_list


# --- Run the Application ---

if __name__ == "__main__":
    os.makedirs("static/to_speach", exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)