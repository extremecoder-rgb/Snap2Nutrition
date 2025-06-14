from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from PIL import Image
import os, re, json
from dotenv import load_dotenv
from typing import Tuple
import io
import logging
import traceback


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
app = Flask(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found")
genai.configure(api_key=API_KEY)

_JSON_RE = re.compile(r'```(?:json)?\s*([\s\S]*?)\s*```', re.I)

def optimize_image(image: Image.Image, max_size: int = 1024) -> Image.Image:
    """Optimize image size while maintaining aspect ratio"""
    try:
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        return image
    except Exception as e:
        logger.error(f"Error optimizing image: {str(e)}")
        raise

def extract_json(text: str) -> dict:
    """
    Pull the first {...} block out of `text`, strip any markdown fence,
    and return it as a Python dict. If no JSON is found, return a default error dictionary.
    """
    try:
        m = _JSON_RE.search(text)
        candidate = m.group(1) if m else text       
       
        brace = re.search(r'\{[\s\S]*\}', candidate)
        if not brace:
            logger.error(f"No JSON object found in model response. Raw text: {text}")
            return {"error": "No nutritional data found. Please try another image or check the API response.", "original_response": text}
        return json.loads(brace.group(0))
    except Exception as e:
        logger.error(f"Error extracting JSON: {str(e)}")
        return {"error": f"Error processing response: {str(e)}", "original_response": text}

def analyze_food(image: Image.Image) -> dict:
    """Call Gemini, make sure we come back with a dict, not a string."""
    try:
       
        image = optimize_image(image)
        
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

        logger.info("Sending request to Gemini API")
        model = genai.GenerativeModel('gemini-1.5-flash')
        result = model.generate_content([prompt, image])
        logger.info("Received response from Gemini API")
        
        return extract_json(result.text)
    except Exception as e:
        logger.error(f"Error in analyze_food: {str(e)}\n{traceback.format_exc()}")
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze() -> Tuple[dict, int]:
    try:
        if 'file' not in request.files:
            logger.error("No file in request")
            return jsonify(error="No file uploaded"), 400

        file = request.files['file']
        if not file.filename:
            logger.error("Empty filename")
            return jsonify(error="Invalid file"), 400

        logger.info(f"Processing file: {file.filename}")
        
       
        image_data = file.read()
        if not image_data:
            logger.error("Empty file data")
            return jsonify(error="Empty file"), 400

        with Image.open(io.BytesIO(image_data)) as img:
            data = analyze_food(img)              
            return jsonify(data)
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {str(e)}\n{traceback.format_exc()}")
        return jsonify(error=f"Analysis failed: {str(e)}"), 500

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "True")
