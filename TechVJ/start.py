# Credit: @goku_bhai001
# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os, sys, subprocess, html
import base64
import re
import asyncio 
import pyrogram
#from bot import Bot
from pyrogram import Client, filters, enums
from pyrogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument
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


@Client.on_message(filters.command("update"))
async def update_bot(client, message):
    msg = await message.reply_text("🔄 Pulling updates from GitHub...")
    try:
        pull = subprocess.run(["git", "pull"], capture_output=True, text=True)
        if pull.returncode == 0:
            await msg.edit(f"✅ Updated:\n<pre>{pull.stdout}</pre>")
        else:
            await msg.edit(f"❌ Git error:\n<pre>{pull.stderr}</pre>")
            return

        await asyncio.sleep(2)
        await msg.edit("♻️ Rᴇsᴛᴀʀᴛɪɴɢ ʙᴏᴛ...")

        # ✅ Delete after 5s
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except:
            pass

        os.execl(sys.executable, sys.executable, *sys.argv)

    except Exception as e:
        await msg.edit(f"⚠️ Error: {e}")

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


# New function: handle media groups

async def handle_media_group(client, message, bot_username, parameter):
    chat_id = message.chat.id
    media_group_id = message.media_group_id

    acc = Client("saverestricted", session_string=SESSION, api_hash=API_HASH, api_id=API_ID)
    await acc.start()

    # Fetch all messages in that media group
    messages = []
    async for msg in acc.get_chat_history(chat_id, limit=20):
        if msg.media_group_id == media_group_id:
            messages.append(msg)

    messages = sorted(messages, key=lambda m: m.id)  # keep original order
    batch = True if len(messages) > 1 else False

    # Create temp placeholders
    results = []
    for msg in messages:
        task_queue.append((client, msg, bot_username, parameter))
        results.append(msg)

    # Fetch link data from DB
    data = links_collection.find_one({"parameter": parameter})
    if not data:
        await acc.stop()
        return await client.send_message(chat_id, "❌ No files found. Please check the link and try again.")

    # Try getting f_msg_id and l_msg_id safely
    f_msg_id = data.get("f_msg_id") or (messages[0].id if messages else None)
    l_msg_id = data.get("l_msg_id") or (messages[-1].id if messages else None)

    if not f_msg_id or not l_msg_id:
        await acc.stop()
        return await client.send_message(
            chat_id,
            "❌ File message IDs are missing or invalid. Please regenerate the link."
        )

    base_string = await encode(f"get-{f_msg_id * abs(FILE_CHANNEL)}-{l_msg_id * abs(FILE_CHANNEL)}")
    link = f"https://t.me/{FILE_BOT_USERNAME}?start={base_string}"

    # Build the same media group response but with updated caption containing link
    media = []
    for i, msg in enumerate(results):
        cap = msg.caption or ""
        if i == 0:  # only first one has caption with link
            cap += f"\n\n🔗 Updated Link: {link}"

        if msg.photo:
            media.append(InputMediaPhoto(msg.photo.file_id, caption=cap))
        elif msg.video:
            media.append(InputMediaVideo(msg.video.file_id, caption=cap))
        elif msg.document:
            media.append(InputMediaDocument(msg.document.file_id, caption=cap))

    if media:
        await client.send_media_group(chat_id, media)

    await acc.stop()

# handle_download stays same, but works per message
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
        await asyncio.sleep(5)

        async for msg in acc.get_chat_history(bot_username, limit=limit):
            if msg.id >= sent_message.id:
                if msg.document or msg.video or msg.photo:
                    if not links_collection.find_one({"parameter": parameter}):
                        links_collection.insert_one(
                            {"parameter": parameter, "processed": False, "bot_username": bot_username, "f_msg_id": None, "l_msg_id": None}
                        )
                    await handle_private(client, acc, message, msg.chat.id, msg.id, parameter, batch)

        # Only reply if single file
        if batch is False:
            data = links_collection.find_one({"parameter": parameter})
            base_string = await encode(f"get-{data['f_msg_id'] * abs(FILE_CHANNEL)}")
            link = f"https://t.me/{FILE_BOT_USERNAME}?start={base_string}"
            await message.reply(f"🔗 Here is your link 🔗\n\n\u200b{link}\n\n👀 How To Watch Video 👀\n{HOW_TO_WATCH_LINK}", disable_web_page_preview=True)
            links_collection.delete_one({"parameter": parameter})

    except Exception as e:
        print(f"An error occurred: {e}")

@Client.on_message((filters.text | filters.caption | filters.photo | filters.video) & filters.private & ~filters.command(["start", "login", "logout", "cancel", "restart", "on", "off", "help", "update"]))
async def handle_message(client, message):
    text = message.text or ""
    caption = message.caption or ""
    full_text = f"{text} {caption}".strip()

    # Extract bot link from text or caption
    link = None
    if "https://t.me/" in full_text or "https://telegram.me/" in full_text:
        link = next(
            (word for word in full_text.split() if ("https://t.me/" in word or "https://telegram.me/" in word) and "?start=" in word),
            None
        )

    if not link:
        return  # no valid link found

    bot_username = link.split('/')[-1].split('?')[0]
    parameter = link.split('?')[-1].replace("=", " ")

    # If this is a media group -> handle as group
    if message.media_group_id:
        await handle_media_group(client, message, bot_username, parameter)
    else:
        task_queue.append((client, message, bot_username, parameter))

# handle private
async def handle_private(
    client: Client,
    acc: Client,
    message: Message,
    bot_username: str,
    chatid: int,
    msgid: int,
    parameter: str,
    batch: bool
):
    msg: Message = await acc.get_messages(chatid, msgid)
    if msg.empty:
        return
    msg_type = get_message_type(msg)
    if not msg_type:
        return
    chat = message.chat.id

    smsg = await client.send_message(chat, '**Downloading**', reply_to_message_id=message.id)
    asyncio.create_task(downstatus(client, f'{message.id}downstatus.txt', smsg, chat))

    try:
        file = await acc.download_media(
            msg, progress=progress, progress_args=[message, "down"]
        )
        os.remove(f'{message.id}downstatus.txt')
    except Exception as e:
        await client.send_message(
            chat, f"Error: {e}",
            reply_to_message_id=message.id,
            parse_mode=enums.ParseMode.HTML
        )
        return await smsg.delete()

    asyncio.create_task(upstatus(client, f'{message.id}upstatus.txt', smsg, chat))

    # escape caption safely
    caption = html.escape(msg.caption) if msg.caption else None

    if msg_type == "Document":
        try:
            ph_path = None
            if msg.document.thumbs:
                ph_path = await acc.download_media(msg.document.thumbs[0].file_id)

            k = await client.send_document(
                FILE_CHANNEL,
                file,
                thumb=ph_path,
                caption=caption,
                parse_mode=enums.ParseMode.HTML,
                progress=progress,
                progress_args=[message, "up"]
            )
            if not batch:
                links_collection.update_one({'parameter': parameter}, {'$set': {'f_msg_id': k.id}})
            else:
                data = links_collection.find_one({"parameter": parameter})
                if data["f_msg_id"] is None:
                    links_collection.update_one({'parameter': parameter}, {'$set': {'f_msg_id': k.id}})
                else:
                    links_collection.update_one({'parameter': parameter}, {'$set': {'l_msg_id': k.id}})
        except Exception as e:
            await client.send_message(chat, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        if ph_path:
            os.remove(ph_path)

    elif msg_type == "Video":
        try:
            ph_path = None
            if msg.video.thumbs:
                ph_path = await acc.download_media(msg.video.thumbs[0].file_id)

            k = await client.send_video(
                FILE_CHANNEL,
                file,
                duration=msg.video.duration,
                width=msg.video.width,
                height=msg.video.height,
                thumb=ph_path,
                caption=caption,
                parse_mode=enums.ParseMode.HTML,
                progress=progress,
                progress_args=[message, "up"]
            )
            if not batch:
                links_collection.update_one({'parameter': parameter}, {'$set': {'f_msg_id': k.id}})
            else:
                data = links_collection.find_one({"parameter": parameter})
                if data["f_msg_id"] is None:
                    links_collection.update_one({'parameter': parameter}, {'$set': {'f_msg_id': k.id}})
                else:
                    links_collection.update_one({'parameter': parameter}, {'$set': {'l_msg_id': k.id}})
        except Exception as e:
            await client.send_message(chat, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        if ph_path:
            os.remove(ph_path)

    elif msg_type == "Photo":
        try:
            k = await client.send_photo(
                FILE_CHANNEL,
                file,
                caption=caption,
                parse_mode=enums.ParseMode.HTML
            )
            if not batch:
                links_collection.update_one({'parameter': parameter}, {'$set': {'f_msg_id': k.id}})
            else:
                data = links_collection.find_one({"parameter": parameter})
                if data["f_msg_id"] is None:
                    links_collection.update_one({'parameter': parameter}, {'$set': {'f_msg_id': k.id}})
                else:
                    links_collection.update_one({'parameter': parameter}, {'$set': {'l_msg_id': k.id}})
        except Exception as e:
            await client.send_message(chat, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)

    if os.path.exists(f'{message.id}upstatus.txt'):
        os.remove(f'{message.id}upstatus.txt')
        os.remove(file)
    await client.delete_messages(chat, [smsg.id])


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

