import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


# Pydantic model to define the structure of the incoming request body
class TextInput(BaseModel):
    inputText: str


# Initialize the FastAPI application
app = FastAPI()

# Mount the 'static' directory to serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2Templates to render HTML
templates = Jinja2Templates(directory="templates")


def apply_voicing_rules(input_text: str) -> str:
    """
    Applies the first set of transformation rules based on the image.
    This function maps certain voiceless consonants to their voiced counterparts.
    """
    voicing_map = {
        # Original (From) : Replacement (To)
        "თ": "დ",
        "ტ": "დ",
        "პ": "ბ",
        "ფ": "ბ",
        "კ": "გ",
        "ქ": "გ",
        "ყ": "ღ",
        "ხ": "ღ",
        "ჩ": "ჯ",
        "ჭ": "ჯ",
        "ს": "ზ",
        "შ": "ჟ",
        "ც": "ძ",
        "წ": "ძ",
    }
    # Create a translation table from the mapping dictionary
    translation_table = str.maketrans(voicing_map)
    # Apply the translation to the input text
    return input_text.translate(translation_table)


def apply_n_prepending_rules(input_text: str) -> str:
    """
    Applies the second transformation rule based on the image.
    This function prepends the letter 'ნ' to a specific set of consonants.
    """
    # The set of characters to which 'ნ' should be prepended
    target_chars = {"ბ", "გ", "დ", "ზ", "ჟ", "ც", "ძ", "ჯ", "ვ"}

    result = []
    for i, char in enumerate(input_text):
        if char not in target_chars:
            # If the character is not in our target set, keep it as is
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
    The process is sequential: first apply voicing, then apply 'ნ' prepending.
    """
    # Step 1: Apply the voicing rules
    voiced_text = apply_voicing_rules(input_text)

    # Step 2: Apply the 'ნ' prepending rule to the result of the first step
    final_text = apply_n_prepending_rules(voiced_text)

    return final_text


# --- API Endpoints ---


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    This endpoint serves the main HTML page of the application.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/transform")
async def transform_text(text_input: TextInput):
    """
    This endpoint receives JSON with the input text, transforms it,
    and returns the result in a JSON response.
    """
    transformed_text = transform_georgian_text(text_input.inputText)
    return JSONResponse(content={"transformed_text": transformed_text})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
