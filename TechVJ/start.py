# Credit: @goku_bhai001
# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import base64
import re
import asyncio 
import pyrogram
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message 
from config import API_ID, API_HASH, BYPASS_BOT_USERNAME, BYPASS, FILE_CHANNEL, FILE_BOT_USERNAME, SESSION, HOW_TO_WATCH_LINK
from database.db import db, links_collection

# task queue
task_queue = []

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string

async def decode(base64_string):
    base64_string = base64_string.strip("=") # links generated before this commit will be having = sign, hence striping them to handle padding errors.
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes) 
    string = string_bytes.decode("ascii")
    return string

async def downstatus(client, statusfile, message, chat):
    while True:
        if os.path.exists(statusfile):
            break

        await asyncio.sleep(5)
      
    while os.path.exists(statusfile):
        with open(statusfile, "r") as downread:
            txt = downread.read()
        try:
            await client.edit_message_text(chat, message.id, f"**Downloaded:** **{txt}**")
            await asyncio.sleep(15)
        except:
            await asyncio.sleep(8)


# upload status
async def upstatus(client, statusfile, message, chat):
    while True:
        if os.path.exists(statusfile):
            break

        await asyncio.sleep(5)      
    while os.path.exists(statusfile):
        with open(statusfile, "r") as upread:
            txt = upread.read()
        try:
            await client.edit_message_text(chat, message.id, f"**Uploaded:** **{txt}**")
            await asyncio.sleep(15)
        except:
            await asyncio.sleep(8)


# progress writer
def progress(current, total, message, type):
    with open(f'{message.id}{type}status.txt', "w") as fileup:
        fileup.write(f"{current * 100 / total:.1f}%")

# on & off command 
@Client.on_message(filters.private & filters.command(["on"]))
async def send_on(client: Client, message: Message):
    links_collection.update_one({'id': message.chat.id}, {'$set': {'bypass': True}})
    await message.reply("✅ Bypass Mode Enabled\n\nNow the bot will try to bypass restricted content automatically.")

@Client.on_message(filters.private & filters.command(["off"]))
async def send_off(client: Client, message: Message):
    links_collection.update_one({'id': message.chat.id}, {'$set': {'bypass': False}})
    await message.reply("❌ Bypass Mode Disabled\n\nThe bot will now process links normally.")

# start command
@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
    try:
        links_collection.insert_one({"id": message.chat.id, "bypass": False})
    except:
        pass
    buttons = [[
        InlineKeyboardButton("❣️ Developer", url = "https://t.me/goku_bhai001")
    ],[
        InlineKeyboardButton('🔍 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/goku_bhai001'),
        InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/goku_bhai001')
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await client.send_message(
        chat_id=message.chat.id, 
        text=f"<b>👋 Hi {message.from_user.mention}, I am File Scrapper By @goku_bhai001, For Session Use - /login Send Me link to see magic ✨</b>", 
        reply_markup=reply_markup, 
        reply_to_message_id=message.id
    )
    return

# new code

async def process_queue():
    while True:
        if task_queue:
            # Get the next task from the queue
            current_task = task_queue.pop(0)
            await asyncio.sleep(10)
            await handle_download(current_task)
        else:
            await asyncio.sleep(10)  # Sleep to prevent busy waiting

async def handle_download(task):
    client, message, bot_username, parameter = task
    
    
    try:
        acc = Client("saverestricted", session_string=SESSION, api_hash=API_HASH, api_id=API_ID)
        await acc.connect()
    except:
        return await message.reply("Your Login Session Expired. So Add New String Session.")

    try:
        encode_parameter = parameter.replace("start ", "")
        string = await decode(encode_parameter)
        argument = string.split("-")
        if len(argument) == 3:
            batch = True
            limit = 54
        else:
            batch = False
            limit = 4
        
        sent_message = await acc.send_message(bot_username, f"/{parameter}")
        await asyncio.sleep(5)  # Adjust sleep time as necessary
        
        async for msg in acc.get_chat_history(bot_username, limit=limit):
            if msg.id >= sent_message.id:
                if msg.document or msg.video or msg.photo:
                    if not links_collection.find_one({"parameter": parameter}):
                        links_collection.insert_one({"parameter": parameter, "processed": False, "bot_username": bot_username, "f_msg_id": None, "l_msg_id": None})
                    await handle_private(client, acc, message, bot_username, msg.id, parameter, batch)

        if batch == False:
            data = links_collection.find_one({"parameter": parameter})
            base_string = await encode(f"get-{data['f_msg_id'] * abs(FILE_CHANNEL)}")
            link = f"https://t.me/{FILE_BOT_USERNAME}?start={base_string}"
            await message.reply(f"🔗 Here is your link 🔗\n\n\u200b{link}\n\n👀 How To Watch Video 👀\n{HOW_TO_WATCH_LINK}", disable_web_page_preview=True)
            if links_collection.find_one({"parameter": parameter}):
                links_collection.delete_one({"parameter": parameter})
        else:
            data = links_collection.find_one({"parameter": parameter})
            if not data:
                return await message.reply("❌ No files found. Please check the link and try again.")
            base_string = await encode(f"get-{data['f_msg_id'] * abs(FILE_CHANNEL)}-{data['l_msg_id'] * abs(FILE_CHANNEL)}")
            link = f"https://t.me/{FILE_BOT_USERNAME}?start={base_string}"
            await message.reply(f"🔗 Here is your link 🔗\n\n\u200b{link}\n\n👀 How To Watch Video 👀\n{HOW_TO_WATCH_LINK}", disable_web_page_preview=True)
            if links_collection.find_one({"parameter": parameter}):
                links_collection.delete_one({"parameter": parameter})
            
    except Exception as e:
        print(f"An error occurred: {e}")

@Client.on_message(filters.text & filters.private & ~filters.command(["start", "login", "logout", "cancel", "restart", "on", "off"]))
async def handle_message(client, message):
    # Check if the message contains a bot link
    if "t.me" in message.text:
        try:
            by = links_collection.find_one({"id": message.chat.id})
            if by["bypass"] == True:
                kk = await message.reply("Wait Bypassing Your Link 🖇️")
                bot_username = message.text.split('/')[-1].split('?')[0]
                parameter = message.text.split('?')[-1].replace("=", " ")

                try:
                    acc = Client("saverestricted", session_string=SESSION, api_hash=API_HASH, api_id=API_ID)
                    await acc.connect()
                except:
                    await kk.delete()
                    return await message.reply("Your Login Session Expired. So Add New String Session.")
        
                sent = await acc.send_message(bot_username, f"/{parameter}")
                await asyncio.sleep(5)
                async for msg in acc.get_chat_history(bot_username, limit=4):
                    if msg.text and msg.reply_markup and msg.id >= sent.id:
                        for row in msg.reply_markup.inline_keyboard:
                           for button in row:
                               if button.url:
                                   sent_msg = await acc.send_message(BYPASS_BOT_USERNAME, f"{button.url}") 
                                   await asyncio.sleep(30)
                                   async for msgg in acc.get_chat_history(BYPASS_BOT_USERNAME, limit=4):
                                       if msgg.text and msgg.id >= sent_msg.id:
                                           try:
                                               url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                                               links = re.findall(url_pattern, msgg.text)
                                               for link in links:
                                                   bot_username_sec = link.split('/')[-1].split('?')[0]
                                                   parameter_sec = link.split('?')[-1].replace("=", " ")
                                                   await acc.send_message(bot_username_sec, f"/{parameter_sec}")
                                                   task_queue.append((client, message, bot_username, parameter))
                                               #    if not links_collection.find_one({"parameter": parameter}):
                                                #       links_collection.insert_one({"parameter": parameter, "processed": False, "bot_username": bot_username, "parameter": parameter})
                                                   await kk.delete()
                                                   return 
                                               
                                           except Exception as e:
                                               await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
                    else:
                        if msg.video or msg.document or msg.photo:
                            await kk.delete()
                            bot_username = message.text.split('/')[-1].split('?')[0]
                            parameter = message.text.split('?')[-1].replace("=", " ")
                            task_queue.append((client, message, bot_username, parameter))
                        #    if not links_collection.find_one({"link": message.text}):
                        #        links_collection.insert_one({"link": message.text, "processed": False, "bot_username": bot_username, "parameter": parameter})
                            break
                return 
        except Exception as e:
            return await message.reply(f"Error parsing link: {e}")
        try:
            bot_username = message.text.split('/')[-1].split('?')[0]
            parameter = message.text.split('?')[-1].replace("=", " ")
        except Exception as e:
            return await message.reply(f"Error parsing link: {e}")

        try:
            task_queue.append((client, message, bot_username, parameter))
        except Exception as e:
            return await message.reply(f"Error parsing link: {e}")
        
      #  if not links_collection.find_one({"link": message.text}):
      #      links_collection.insert_one({"link": message.text, "processed": False, "bot_username": bot_username, "parameter": parameter})

@Client.on_message(filters.private & filters.command(["restart"]))
async def load_pending_tasks(client, message):
    kk = await message.reply("Adding All Pending Task To Queue.")
    pending_tasks = links_collection.find({"processed": False})
    for task in pending_tasks:
        try:
            task_queue.append((client, message, task['bot_username'], task['parameter']))
           # links_collection.delete_one({"parameter": task['parameter'])
        except:
            pass
    await kk.edit("Added Successfully")

# handle private
async def handle_private(client: Client, acc, message: Message, chatid: int, msgid: int, parameter, batch):
    msg: Message = await acc.get_messages(chatid, msgid)
    if msg.empty: return 
    msg_type = get_message_type(msg)
    if not msg_type: return 
    chat = message.chat.id
    
    smsg = await client.send_message(message.chat.id, '**Downloading**', reply_to_message_id=message.id)
    asyncio.create_task(downstatus(client, f'{message.id}downstatus.txt', smsg, chat))
    try:
        file = await acc.download_media(msg, progress=progress, progress_args=[message,"down"])
        os.remove(f'{message.id}downstatus.txt')
    except Exception as e:
        await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML) 
        return await smsg.delete()
    asyncio.create_task(upstatus(client, f'{message.id}upstatus.txt', smsg, chat))

    if msg.caption:
        caption = msg.caption
    else:
        caption = None
                
    if "Document" == msg_type:
        try:
            ph_path = await acc.download_media(msg.document.thumbs[0].file_id)
        except:
            ph_path = None
        
        try:
            k = await client.send_document(FILE_CHANNEL, file, thumb=ph_path, caption=caption, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message,"up"])
            if batch == False:
                links_collection.update_one({'parameter': parameter}, {'$set': {'f_msg_id': k.id}})
            else:
                data = links_collection.find_one({"parameter": parameter})
                if data["f_msg_id"] == None:
                    links_collection.update_one({'parameter': parameter}, {'$set': {'f_msg_id': k.id}})
                else:
                    links_collection.update_one({'parameter': parameter}, {'$set': {'l_msg_id': k.id}})
        except Exception as e:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        if ph_path != None: os.remove(ph_path)
        

    elif "Video" == msg_type:
        try:
            ph_path = await acc.download_media(msg.video.thumbs[0].file_id)
        except:
            ph_path = None
        
        try:
            k = await client.send_video(FILE_CHANNEL, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=ph_path, caption=caption, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message,"up"])
            if batch == False:
                links_collection.update_one({'parameter': parameter}, {'$set': {'f_msg_id': k.id}})
            else:
                data = links_collection.find_one({"parameter": parameter})
                if data["f_msg_id"] == None:
                    links_collection.update_one({'parameter': parameter}, {'$set': {'f_msg_id': k.id}})
                else:
                    links_collection.update_one({'parameter': parameter}, {'$set': {'l_msg_id': k.id}})
        except Exception as e:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        if ph_path != None: os.remove(ph_path)

    elif "Photo" == msg_type:
        try:
            k = await client.send_photo(FILE_CHANNEL, file, caption=caption, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
            if batch == False:
                links_collection.update_one({'parameter': parameter}, {'$set': {'f_msg_id': k.id}})
            else:
                data = links_collection.find_one({"parameter": parameter})
                if data["f_msg_id"] == None:
                    links_collection.update_one({'parameter': parameter}, {'$set': {'f_msg_id': k.id}})
                else:
                    links_collection.update_one({'parameter': parameter}, {'$set': {'l_msg_id': k.id}})
        except:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
    

    if os.path.exists(f'{message.id}upstatus.txt'): 
        os.remove(f'{message.id}upstatus.txt')
        os.remove(file)
    await client.delete_messages(message.chat.id,[smsg.id])


# get the type of message
def get_message_type(msg: pyrogram.types.messages_and_media.message.Message):
    try:
        msg.document.file_id
        return "Document"
    except:
        pass

    try:
        msg.video.file_id
        return "Video"
    except:
        pass

    try:
        msg.photo.file_id
        return "Photo"
    except:
        pass

@Client.on_message(filters.command(["help"]))
async def help_command(client: Client, message: Message):
    help_text = """
🤖 *File Scrapper Bot Help*

*Available Commands:*
• /start - Start the bot
• /help - Show this help message
• /login - Login with your Telegram account
• /logout - Logout from your account
• /on - Enable bypass mode
• /off - Disable bypass mode
• /restart - Restart pending tasks

*How to use:*
1. Send any Telegram file link to the bot
2. The bot will process it and give you a new link
3. Use the new link to access the file

*Note:* For restricted content, enable bypass mode using /on command.

For support, contact @goku_bhai001
"""
    await message.reply(help_text, parse_mode=enums.ParseMode.MARKDOWN)
