from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from PIL import Image
import os, re, json
from dotenv import load_dotenv
from typing import Tuple

load_dotenv()
app = Flask(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found")
genai.configure(api_key=API_KEY)

_JSON_RE = re.compile(r'```(?:json)?\s*([\s\S]*?)\s*```', re.I)

def extract_json(text: str) -> dict:
    """
    Pull the first {...} block out of `text`, strip any markdown fence,
    and return it as a Python dict. If no JSON is found, return a default error dictionary.
    """
    
    m = _JSON_RE.search(text)
    candidate = m.group(1) if m else text       
   
    brace = re.search(r'\{[\s\S]*\}', candidate)
    if not brace:
        app.logger.error(f"No JSON object found in model response. Raw text: {text}")
        return {"error": "No nutritional data found. Please try another image or check the API response.", "original_response": text}
    return json.loads(brace.group(0))            


def analyze_food(image: Image.Image) -> dict:
    """Call Gemini, make sure we come back with a dict, not a string."""
    prompt = (
        "Analyze this food image and return JSON only:\n"
        "{"
        '"items":[{'
           '"name":"...", "calories":..., "carbs":..., '
           '"protein":..., "fat":..., "portion_size":"..."'
        "}],"
        '"total_calories":...,'
        '"health_rating":...,'
        '"micronutrients":{"vitamins":[...],"minerals":[...]}' 
        "}"
    )

    model   = genai.GenerativeModel('gemini-1.5-flash')
    result  = model.generate_content([prompt, image])
    return extract_json(result.text)             

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze() -> Tuple[dict, int]:
    if 'file' not in request.files:
        return jsonify(error="No file uploaded"), 400

    file = request.files['file']
    if not file.filename:
        return jsonify(error="Invalid file"), 400

    try:
        with Image.open(file.stream) as img:
            data = analyze_food(img)              
            return jsonify(data)                  
    except Exception as e:
        app.logger.exception("Analysis failed")
        return jsonify(error=f"Analysis failed: {e}"), 500

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "True")
