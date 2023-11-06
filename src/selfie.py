import automatic1111 as webui
import timedata # retrofitting perposes

def should_take_selfie(msg):
    s = msg # retrofitting
    return bool(sum([k + " " in s.lower() for k in "take|post|paint|generate|make|draw|create|show|give|snap|capture|send|display|share|shoot|see|provide".split("|")])) and bool(sum([k in s.lower() for k in "image|picture|screenshot|screenie|painting|pic|photo|photograph|portrait|selfie|your".split("|")]))

def img_prompt(user, ai, ppt): # retrofitting
    date, time = timedata.current_time()

    prompt = ""

    # Character
    # character_prompt_image = "A 25 year old anime woman smiling black hair, hazel eyes (medium bust:1.2)"
    character_prompt_image = ppt

    user = user.lower()

    selfieterms = "selfie|person|you as|yourself as|you cosplaying|yourself cosplaying| of you | of you with | at you| in you| for you| by you| and you|holding"

    su = sum([t in user for t in selfieterms.split("|")])
    selfie = bool(su)

    # Selfie?
    if selfie:
        prompt += character_prompt_image

    # Formatting

    format_string = ""

    # Special terms
    if "selfie" in user:
        format_string += ", looking into the camera, "
    if " of you with " in user:
        format_string += "she is with"
    if "holding" in user:
        format_string += ", holding"
    
    prompt += format_string

    if len(ai) > 0:
        prompt += f" (({ai}))"

    prompt += f", ({time.lower()}:2)"
    
    prompt = prompt.strip()

    return prompt, selfie

async def take_selfie(msg, ai, ppt, bngp, ngp, ckpt):
    prompt, selfie = img_prompt(msg, ai, ppt)
    
    neg = ""
    if len(bngp) > 0: neg += bngp + ", "
    if selfie: neg += ngp

    return await webui.txt2img(prompt, neg, ckpt)