import logging
import time
import os
from typing import Any

import timedata

from discord.flags import Intents
from discord.utils import remove_markdown, escape_markdown, escape_mentions
from selfie import should_take_selfie, take_selfie

import yamlfile, personality

import discord
import llama_cpp as llama

import asyncio as aio
from functools import partial

__cached_personalities = {}

current_personality = None

STOP = [ "\n", "\n[", "\n>", "]:", "\n#", "\n##", "\n###", "##", "###", "</s>", "000000000000", "1111111111", "0.0.0.0.", "1.1.1.1.", "2.2.2.2.", "3.3.3.3.", "4.4.4.4.", "5.5.5.5.", "6.6.6.6.", "7.7.7.7.", "8.8.8.8.", "9.9.9.9.", "22222222222222", "33333333333333", "4444444444444444", "5555555555555", "66666666666666", "77777777777777", "888888888888888", "999999999999999999", "01010101", "0123456789", "<noinput>", "<nooutput>" ]

personality_path = None

class LLM(llama.Llama):
    def __init__(self, personality) -> None:
        mdl = get_config("model")
        if not mdl:
            for name in os.listdir("./data/models/lang"):
                if name.endswith("gguf"):
                    mdl = os.path.join("./data/models/lang", name)
        super().__init__(mdl, n_gpu_layers=100, n_ctx=2048)
        
        self.chat_history = []
        self.load_personality(personality)
    
    def load_personality(self, personality_obj):
        # maybe some housekeeping here?
        self.personality: personality.Personality = personality_obj

    def _chat2text(self):
        # Turns chat to text
        formatted = ""
        for msg in self.chat_history:
            formatted += f"[{msg[0]}]: {msg[1]}\n"
        
        return formatted.strip()
    
    def chat2text(self, trim_if_needed=True):
        if trim_if_needed:
            ctxlength = self.n_ctx()
            while len(self._chat2text()) > ctxlength:
                self.chat_history = self.chat_history[1:]
        
        return self._chat2text()
    
    async def chat(self, message, author):
        # Use the LLM to generate a chatbot message
        self.chat_history.append([author, message])
        prompt = f"{timedata.time_summary()}\n\n{self.personality.ctx}\n{self.chat2text()}\n[{self.personality.name}]:"
        results = await aio.get_event_loop().run_in_executor(None, partial(self.__call__, prompt, top_p=0.1, max_tokens=128, stop=STOP, temperature=0.8, repeat_penalty=1.25))
        text = results["choices"][0]["text"].strip()
        logging.info(f"[{self.personality.name}]: {text}")
        self.chat_history.append([self.personality.name, text])
        return text # For use by the bot

class Bot(discord.Client):
    def __init__(self, **options) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents, **options)

    async def on_ready(self):
        logging.info(f"Bot is online.")

        self.server = self.get_guild(1167982423410217073)
        self.nickname = self.server.get_member(self.user.id).nick

        self.ainfo = await self.application_info()

        logging.info("Booting up LLaMA...")
        self.llama = LLM(current_personality)

    async def on_message(self, msg: discord.Message):
        swapcmd = "$personality:"
        if msg.author.id == self.ainfo.owner.id:
            if msg.content.startswith(swapcmd):
                np = msg.content[len(swapcmd):]
                self.llama.load_personality(load_personality(np))
                await msg.reply(f"Successfully changed personality to **{np}**")
                logging.info(f"Successfully changed personality to {np}")
                return
            if msg.content == "$reload":
                self.llama.load_personality(load_personality(personality_path))
                await msg.reply(f"Reloaded Personality")
                logging.info(f"Reloaded Personality")
                return
            if msg.content == "$reset":
                self.llama.chat_history = []
                await msg.reply(f"Deleted Chat History")
                logging.info(f"Deleted Chat History")
                return
        
        # If replied or mentioned
        if msg.reference and msg.reference.message_id:
            referredmessage: discord.Message = await (self.get_channel(msg.reference.channel_id).fetch_message(msg.reference.message_id))
            if referredmessage.author.id != self.user.id:
                return

        if not self.user.mentioned_in(msg):
            return

        # if banned
        if msg.author.id in get_config("banned-users"):
            await msg.reply("no.")
            return
        
        cleaned_message = remove_markdown(msg.clean_content.replace(f"@{self.nickname}", "")).strip() # remove mentions and markdown

        logging.info(f"[{msg.author.name}]: {cleaned_message}")

        chat = await self.llama.chat(cleaned_message, msg.author.name)

        await msg.reply(chat)

        should_selfie = should_take_selfie(msg.content)

        if should_selfie:
            s = msg.content # retrofitting
            askdesc = f"### Maintain accuracy to the user's prompt. Do not alter the user request. You may use semantic tags to describe the image. Try to not be sexual unless requested.\n### User Request: {s}\n### Description of the requested image:"
#             askdesc = f"""
# ### SD isn't in english, so you must generate in Danbooru-style semantic tags. Do not reply with Danbooru or Imgur links.
# ### Do not say "the user is asking" or "the user is requesting", instead say danbooru tags
# ### Turn a message asking for a selfie into a SD prompt.
# ### BE AS DETAILED AS POSSIBLE, DESCRIBE AS MUCH AS POSSIBLE

# Message: {s}
# Danbooru Tags:"""
            tags = (await aio.get_event_loop().run_in_executor(None, partial(self.llama.__call__, askdesc, top_p=0.1, max_tokens=128, stop=STOP, temperature=0.8, repeat_penalty=1.5)))["choices"][0]["text"].strip()
            logging.info(f"AI Prompt: {tags}")
            summary = (await aio.get_event_loop().run_in_executor(None, partial(self.llama.__call__, f"### Summarise the following prompt into semantic tags. Do NOT use hashtags. Be detailed.\n### Prompt: {tags}\n### Summarised tags:", top_p=0.1, max_tokens=128, stop=STOP + ["()"], temperature=0.8, repeat_penalty=1.5)))["choices"][0]["text"].strip()
            summary = summary.replace("\"", "").replace("#", "")
            logging.info(f"Summary: {summary}")
            file = discord.File(await take_selfie(msg.content, tags, self.llama.personality.character_prompt, get_config("base-negative"), self.llama.personality.character_negative_prompt, get_config("sd-ckpt"), 1.21), "stable_diffusion.png")
            self.llama.chat_history.append([self.llama.personality.name, f"Photo: {summary}"])

            await msg.channel.send(file=file)

def setup_logger():
    if not os.path.exists("logs"): os.mkdir("logs") # Just in case

    # do the basic config stuff, so emojis dont get sent to hell by this horrible logging tool
    logging.basicConfig(
        level=logging.INFO,
        format=u"%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(time.strftime('logs/%Y_%m_%d_%H_%M.log'), "w", "utf-8"),
            logging.StreamHandler()
        ],
        encoding="utf-8"
    )

def get_config(attr):
    return yamlfile.get_attr("data/config/config.yaml", attr)

def load_personality(path):
    global personality_path
    global current_personality
    personality_path = path
    hashed_path = hash(path)

    current_personality = personality.Personality(path)
    return current_personality

async def main():
    logging.info("Booting up...")

    # Load Personality
    load_personality(get_config("personality"))
    logging.info(f"Loaded personality \"{current_personality.name}\"")

    client = Bot()
    await client.start(get_config("bot-token"))

if __name__ == "__main__":
    import sys
    sys.path.append("src/")

    setup_logger() # Set up logger

    aio.run(main())