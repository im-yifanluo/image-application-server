# turns out we needed to use 'pip install -q -U google-generativeai'

# chatgpt api: https://platform.openai.com/docs/guides/images/introduction

import google.generativeai as genai
from PIL import Image, ImageEnhance
import os, json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API key not found. Please ensure it is set in the .env file.")

genai.configure(api_key=API_KEY)

# define a function to upload an image to gemini
def upload_img(image_path, mime_type=None):

    # upload file to gemini
    file = genai.upload_file(image_path, mime_type=None)
    return file  # directory location in the gemini chat


def config_gemini():
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json"
    }

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config,
    )

    return model


def request_gemini(model, image_path):

    # upload file to gemini, returns the location of the image in the gemini chat
    file = upload_img(image_path, mime_type="image/jpeg")

    chat_session = model.start_chat(history=[{
        "role":
        "user",
        "parts": [
            file,
            "You are a professional photographer and image editor, this is an unedited image. "
            "Significantly enhance this image with larger and more noticeable adjustments"
            "I'm open to editing this image, here is the json structure of how you should give editing feedback"
            'MAKE SURE YOUR OUTPUT IS EXCLUSIVELY JSON DATA THAT CAN BE DECODED AND YOU ONLY CHANGE values AND NOT key!'
            '{"filters": [{"filter_type": "brightness", "factor": 1.05},{"filter_type": "contrast", "factor": 1.1}, {"filter_type": "color", "factor": 1.05 }, {"filter_type": "sharpness", "factor": 1.05}],"suggestion": "A brief description of the filter\'s effect and how the image improves using the filter" }'
        ]
    }])

    response = chat_session.send_message(
        "Please generate 5 filter suggestions to enhance the image. Please ensure your response is only in json format."
    )
    response = response.text.replace("```JSON",
                                     "").replace("```json",
                                                 "").replace("```", "").strip()
    response = json.loads(response)
    if isinstance(response, list):
        response = {f"Filter {index + 1}": value for index, value in enumerate(response)}
    if isinstance(response, dict) and "filters" in response:
        response = {"Filter 1": response}
    if not isinstance(response, dict):
        raise ValueError("Gemini response must be a JSON object or list")

    for filter_name, filter_data in response.items():
        if not isinstance(filter_data, dict):
            raise ValueError(f"{filter_name} must be an object")
        break_down_filter(filter_data)

    print()
    print(response)
    print()
    return response


# function to apply the filter
def apply_filter(filters, image_path, save=False, output_path=None):
    image = Image.open(image_path)

    # [{"filter_type": "brightness", "factor": 1.05},{"filter_type": "contrast", "factor": 1.1}, {"filter_type": "color", "factor": 1.05 }{"filter_type": "sharpness", "factor": 1.05}]
    for filter in filters:
        filter_type = filter["filter_type"]
        factor = filter["factor"]
        if filter_type == "brightness":
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(factor)
        elif filter_type == "contrast":
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(factor)
        elif filter_type == "color":
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(factor)
        elif filter_type == "sharpness":
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(factor)

    if save:
        image.save(output_path)
    return image


def break_down_filter(result):
    #{"Filter Changes":
    #{"filters": [{"filter_type": "brightness", "factor": 1.05},{"filter_type": "contrast", "factor": 1.1}, {"filter_type": "color", "factor": 1.05 }{"filter_type": "sharpness", "factor": 1.05}],"enhancement":"what value to increase or decrease in percent based on the factor that you suggest","suggestion": "A brief description of the filter\'s effect and how the image improves using the filter" },}
    if not isinstance(result, dict):
        raise ValueError("filter data must be a JSON object")
    filter_changes = result['filters']
    suggestion_description = result['suggestion']

    if not isinstance(filter_changes, list):
        raise ValueError("filters must be a list")

    return filter_changes, suggestion_description


if __name__ == "__main__":

    img = "DSC_2742.JPG"
    img_path = "DSC_2742.JPG"

    model = config_gemini()
    result = request_gemini(model, img_path)

    filter_changes, suggestion_description = break_down_filter(result)

    apply_filter(filter_changes,
                 img_path,
                 save=True,
                 output_path="edited_image.jpg")
