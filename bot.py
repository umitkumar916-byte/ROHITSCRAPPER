# Credit: @goku_bhai001

import asyncio
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
from TechVJ.start import process_queue

class Bot(Client):

    def __init__(self):
        super().__init__(
            "techvj login",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="TechVJ"),
            workers=50,
            sleep_threshold=10
        )

      
    async def start(self):
            
        await super().start()
        asyncio.create_task(process_queue())
        print('Bot Started Powered By @goku_bhai001')

    async def stop(self, *args):

        await super().stop()
        print('Bot Stopped Bye')

Bot().run()

# Credit: @goku_bhai001
