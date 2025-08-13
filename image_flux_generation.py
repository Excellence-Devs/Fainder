import requests
import random
import time
import base64
import json

with open("config.json", "r") as f:
    config = json.load(f)
    api_keys = config["api_keys"]["flux"]
    
def image_to_base64(image_path):
    with open(image_path, 'rb') as img:
        return base64.b64encode(img.read()).decode('utf-8')

models_generation = ["flux-kontext-pro", "flux-kontext-max", "flux-pro-1.1", "flux-pro", "flux-dev", "flux-pro-1.1-ultra"]

class AscpectRatio:
    SQUARE = "1:1"
    PORTRAIT = "9:16"
    LANDSCAPE = "16:9"
    WIDE = "21:9"
    ULTRA_WIDE = "9:21"



def show_image_with_url(url: str):
    import webbrowser
    webbrowser.open(url)

class FLUX:
    pooling_errors = ["Task not found", "Request Moderated", "Content Moderated","Error"]
    def __init__(self, api_keys: list, api_url: str = "https://api.bfl.ai/v1") -> None:
        self.api_keys = api_keys
        self.api_url = api_url
        self.blocked_keys = []

    def pooling(self, url):
        while True:
            response = requests.get(url).json()
            if response["status"] in self.pooling_errors:
                raise Exception(response["status"])

            elif response["status"] == "Ready":
                return response["result"]["sample"]
            time.sleep(1)

    def _acpect(self, aspect_ratio: str) -> str:
        if aspect_ratio == AscpectRatio.SQUARE:
            return {"height": 1024, "width": 1024}
        elif aspect_ratio == AscpectRatio.PORTRAIT:
            return {"height": 1152, "width": 640}
        elif aspect_ratio == AscpectRatio.LANDSCAPE:
            return {"height": 640, "width": 1152}
        elif aspect_ratio == AscpectRatio.WIDE:
            return {"height": 544, "width": 1280}
        elif aspect_ratio == AscpectRatio.ULTRA_WIDE:
            return {"height": 1280, "width": 544}
        else:
            raise ValueError("aspect_ratio must be a value from AscpectRatio")


    def _get_api_key(self) -> str:
        for i in range(len(self.api_keys)):
            api_key = random.choice(self.api_keys)
            if api_key not in self.blocked_keys:
                return api_key
        raise Exception("All api keys are blocked")



    def _flux_kontext(self, model, prompt: str, images: list = None, seed: int = None, aspect_ratio: str = AscpectRatio.SQUARE, promt_upscaling: bool = False) -> str:
        """
        images: list of images in base64 format (max 4 images)

        > return url for pulling image
        """
        api_key = self._get_api_key()
        headers = {
            "x-key": api_key,
            "Content-Type": "application/json"
        }


        if seed is None:
            # Генерация сида от 0 до 99999999999
            seed = random.randint(0, 99999999999)

        url = f"{self.api_url}/flux-kontext-{model}"


        payload = {
        "prompt": prompt,
        "input_image": None,
        "input_image_2": None,
        "input_image_3": None,
        "input_image_4": None,
        "seed": seed,
        "aspect_ratio": aspect_ratio,
        "output_format": "png",
        "prompt_upsampling": promt_upscaling,
        "safety_tolerance": 6
    }
        if images is None:
                images = []
        if len(images) > 4:
            raise ValueError("images must be a list of 4 images")
        if len(images) > 0:
            payload["input_image"] = images[0]
            if len(images) > 1:
                payload["input_image_2"] = images[1]
            if len(images) > 2:
                payload["input_image_3"] = images[2]
            if len(images) > 3:
                payload["input_image_4"] = images[3]

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(response.json())
        else:
            return response.json()["polling_url"]

    def kontext_max(self, prompt: str, images: list = None, seed: int = None, aspect_ratio: str = AscpectRatio.SQUARE, promt_upscaling: bool = False) -> str:
        return self._flux_kontext("max", prompt, images, seed, aspect_ratio, promt_upscaling)
    
    def kontext_pro(self, prompt: str, images: list = None, seed: int = None, aspect_ratio: str = AscpectRatio.SQUARE, promt_upscaling: bool = False) -> str:
        return self._flux_kontext("pro", prompt, images, seed, aspect_ratio, promt_upscaling)

    def x1_1_pro(self, prompt: str, image = None, seed: int = None, aspect_ratio: str = AscpectRatio.SQUARE, promt_upscaling: bool = False) -> str:
        
        api_key = self._get_api_key()
        headers = {
            "x-key": api_key,
            "Content-Type": "application/json"
        }


        if seed is None:
            # Генерация сида от 0 до 99999999999
            seed = random.randint(0, 99999999999)

        url = f"{self.api_url}/flux-pro-1.1"
        aspect_ratio_need = self._acpect(aspect_ratio)

        payload = {
            "prompt": prompt,
            "image_prompt": image,
            "width": aspect_ratio_need["width"],
            "height": aspect_ratio_need["height"],
            "prompt_upsampling": promt_upscaling,
            "seed": seed,
            "safety_tolerance": 6,
            "output_format": "png"
        }
        

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(response.json())
        else:
            return response.json()["polling_url"]



# flux = FLUX(["048790b8-7e38-4a2a-af7f-c886ffb1ede5"])
# # image = image_to_base64("assets/photo.jpg")

# # # p_url = flux.flux_kontext_pro("Remove the white frames, please", aspect_ratio=AscpectRatio.SQUARE, images=[image])
# p_url = flux.x1_1_pro("Gwen Stacy, 19 years old, striking a casual, confident pose on a New York City rooftop at sunset. She's wearing a slightly oversized band t-shirt, ripped skinny jeans, and high-top sneakers. Her platinum blonde hair with pink tips is styled in a messy, effortless way. Her expressive blue eyes are visible, and she has a subtle, knowing smirk. In the background, a highly detailed cityscape of New York at dusk with sharp buildings and vibrant colors, no blur, realistic lighting. Full body shot, natural light, realistic photo, taken with a 35mm lens.", aspect_ratio=AscpectRatio.PORTRAIT)

# image_url = flux.pooling(p_url)
# show_image_with_url(image_url)
