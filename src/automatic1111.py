from aiohttp import ClientSession
import base64
import io
import re
import time

emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags=re.UNICODE)

async def txt2img(prompt: str, negative_prompt, ckpt, seed=-1, sampler="DPM++ 2M Karras", steps=20, landscape = False):
    prompt = emoji_pattern.sub(r"", prompt)
    async with ClientSession() as cs:
        async with cs.post("http://127.0.0.1:7860/sdapi/v1/txt2img", json={
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "seed": seed,
            "sampler_index": sampler,
            "steps": steps,
            "width": 512 if landscape else 288,
            "height": 288 if landscape else 512,
            "override_settings": {"sd_model_checkpoint": ckpt}, # AOM3A1B_orangemixs.safetensors
            "override_settings_restore_afterwards": False,
        }) as resp:
            response = await resp.json()
            file = base64.b64decode(response["images"][0])
            stamp = int(time.time())
            with open(f"data/ugc/generated_images/{stamp}.png", "wb") as fobj:
                fobj.write(file)
            f = io.BytesIO(file)
            return f