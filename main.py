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


class TextInput(BaseModel):
    inputText: str

class HistoryItem(BaseModel):
    filename: str
    url: str
    date: str

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


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


def transform_georgian_text(input_text: str) -> str:
    """
    Combines all transformation rules into a single function.
    """
    voiced_text = apply_voicing_rules(input_text)
    final_text = apply_n_prepending_rules(voiced_text)
    return final_text


# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Serves the main HTML page of the application.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/transform")
async def transform_text(text_input: TextInput):
    """
    Receives JSON with input text, transforms it, and returns the result.
    """
    transformed_text = transform_georgian_text(text_input.inputText)
    return JSONResponse(content={"transformed_text": transformed_text})


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