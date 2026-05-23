from flask import Flask, request, jsonify
import json, os
from io import BytesIO
from main import *
import base64

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app = Flask(__name__)

@app.route('/')
def home():
  return "This is the home page"

@app.route('/get_filters', methods=['POST'])
@app.route('/get_filter', methods=['POST'])
def get_filter():
  # recieve the image and get the json filters and send them back to the user
  if 'image' not in request.files:
    return jsonify({"error": "there is no file in packet"}), 400
  file = request.files['image'] # grabbed the image
  image_path = os.path.join(UPLOAD_FOLDER, file.filename) # create image path
  file.save(image_path) # save the image on the server

  try:
    model = config_gemini()
    result = request_gemini(model, image_path)
    return jsonify(result)
  except Exception as error:
    return jsonify({"error": str(error)}), 502
  finally:
    if os.path.exists(image_path):
      os.remove(image_path)

@app.route('/get_image', methods=['POST'])
def get_image():
  # send the image and filters and receive the modified image
  
  if 'image' not in request.files:
    return jsonify({"error": "there is no file in packet"}), 400
  file = request.files['image'] # grabbed the image
  
  filters_json = request.form.get('filters')    # grab the json filters data
  if filters_json is None:
    return jsonify({'error': 'there is no filter'}), 400

  try:
    filters = json.loads(filters_json)
  except Exception as error:
    return jsonify({'error': str(error)}), 400

  image_path = os.path.join(UPLOAD_FOLDER, file.filename)
  file.save(image_path)

  try:
    filter_changes = filters['filters'] if isinstance(filters, dict) else filters
    edited_image = apply_filter(filter_changes, image_path)
  except Exception as error:
    if os.path.exists(image_path):
      os.remove(image_path)
    return jsonify({'error': str(error)}), 400

  buffer = BytesIO()
  if edited_image.mode != 'RGB':
    edited_image = edited_image.convert('RGB')
  edited_image.save(buffer, format="JPEG")

  image_bytes = buffer.getvalue()

  encoded_image = base64.b64encode(image_bytes).decode('utf-8')

  if os.path.exists(image_path):
    os.remove(image_path)

  response = {"image" : encoded_image}
  return jsonify(response)

if __name__ == "__main__":
  app.run(host='0.0.0.0', port=5000)
