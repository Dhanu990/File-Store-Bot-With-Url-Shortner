# Import necessary modules and configurations
import os
import asyncio
import traceback
from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant, QueryIdInvalid, FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from configs import Config
from handlers.database import db
from handlers.add_user_to_db import add_user_to_database
from handlers.send_file import send_media_and_reply
from handlers.helpers import b64_to_str, str_to_b64
from handlers.check_user_status import handle_user_status
from handlers.force_sub_handler import handle_force_sub, get_invite_link
from handlers.broadcast_handlers import main_broadcast_handler
from handlers.save_media import save_media_in_channel, save_batch_media_in_channel

MediaList = {}

Bot = Client(
    name=Config.BOT_USERNAME,
    in_memory=True,
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH
)

# Handle user status when they send a private message
@Bot.on_message(filters.private)
async def handle_user(bot: Client, cmd: Message):
    await handle_user_status(bot, cmd)

# Handle the /start command in private messages
@Bot.on_message(filters.command("start") & filters.private)
async def start(bot: Client, cmd: Message):
    if cmd.from_user.id in Config.BANNED_USERS:
        await cmd.reply_text("Sorry, You are banned.")
        return
    if Config.UPDATES_CHANNEL is not None:
        back = await handle_force_sub(bot, cmd)
        if back == 400:
            return
    
    usr_cmd = cmd.text.split("_", 1)[-1]
    if usr_cmd == "/start":
        await add_user_to_database(bot, cmd)
        await cmd.reply_text(
            Config.HOME_TEXT.format(cmd.from_user.first_name, cmd.from_user.id),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Movie Group", url="https://t.me/filmyspot0")
                    ],
                    [
                        InlineKeyboardButton("About Bot", callback_data="aboutbot"),
                        InlineKeyboardButton("About Dev", callback_data="aboutdevs"),
                        InlineKeyboardButton("Close 🚪", callback_data="closeMessage")
                    ],
                    [
                        InlineKeyboardButton("Support Group", url="https://t.me/filmyspotupdate"),
                        InlineKeyboardButton("Movie Group", url="https://t.me/filmyspotmovies1")
                    ]
                ]
            )
        )
    else:
        try:
            try:
                file_id = int(b64_to_str(usr_cmd).split("_")[-1])
            except (Error, UnicodeDecodeError):
                file_id = int(usr_cmd.split("_")[-1])
            GetMessage = await bot.get_messages(chat_id=Config.DB_CHANNEL, message_ids=file_id)
            message_ids = []
            if GetMessage.text:
                message_ids = GetMessage.text.split(" ")
                _response_msg = await cmd.reply_text(
                    text=f"**Total Files:** `{len(message_ids)}`",
                    quote=True,
                    disable_web_page_preview=True
                )
            else:
                message_ids.append(int(GetMessage.id))
            for i in range(len(message_ids)):
                await send_media_and_reply(bot, user_id=cmd.from_user.id, file_id=int(message_ids[i]))
        except Exception as err:
            await cmd.reply_text(f"Something went wrong!\n\n**Error:** `{err}`")

# Handle media messages
@Bot.on_message((filters.document | filters.video | filters.audio | filters.photo) & ~filters.chat(Config.DB_CHANNEL))
async def handle_media(bot: Client, message: Message):
    if message.is_private:
        await add_user_to_database(bot, message)
        if Config.UPDATES_CHANNEL is not None:
            back = await handle_force_sub(bot, message)
            if back == 400:
                return
        if message.from_user.id in Config.BANNED_USERS:
            await message.reply_text("Sorry, You are banned!\n\nContact [𝙎𝙪𝙥𝙝𝙤𝙫𝙚 𝙂𝙧𝙤𝙪𝙥](https://t.me/filmyspotupdate)",
                         disable_web_page_preview=True)
            return
        if Config.OTHER_USERS_CAN_SAVE_FILE is False:
            return
        await message.reply_text(
            text="**Choose an option from below:**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Save in Batch", callback_data="addToBatchTrue")],
                [InlineKeyboardButton("Get Sharable Link", callback_data="addToBatchFalse")]
            ]),
            quote=True,
            disable_web_page_preview=True
        )
    elif message.chat.type == filters.ChatType.CHANNEL:
        # Handle messages in channels if needed
        pass

# Handle broadcasting messages
@Bot.on_message(filters.private & filters.command("broadcast") & filters.user(Config.BOT_OWNER) & filters.reply)
async def handle_broadcast(bot: Client, message: Message):
    await main_broadcast_handler(message, db)

# Handle status command to get total users
@Bot.on_message(filters.private & filters.command("status") & filters.user(Config.BOT_OWNER))
async def handle_status(bot: Client, message: Message):
    total_users = await db.total_users_count()
    await message.reply_text(
        text=f"**Total Users in DB:** `{total_users}`",
        quote=True
    )

# Handle banning and unbanning users
@Bot.on_message(filters.private & filters.command("ban_user") & filters.user(Config.BOT_OWNER))
async def handle_ban_user(bot: Client, message: Message):
    # Handle user banning logic
    pass

@Bot.on_message(filters.private & filters.command("unban_user") & filters.user(Config.BOT_OWNER))
async def handle_unban_user(bot: Client, message: Message):
    # Handle user unbanning logic
    pass

# Handle listing banned users
@Bot.on_message(filters.private & filters.command("banned_users") & filters.user(Config.BOT_OWNER))
async def handle_banned_users(bot: Client, message: Message):
    # Handle listing banned users
    pass

# Handle clearing user batch
@Bot.on_message(filters.private & filters.command("clear_batch"))
async def handle_clear_user_batch(bot: Client, message: Message):
    MediaList[f"{str(message.from_user.id)}"] = []
    await message.reply_text("Cleared your batch files successfully!")

# Handle callback queries for buttons
@Bot.on_callback_query()
async def handle_button(bot: Client, cmd: CallbackQuery):
    # Handle callback query logic for buttons
    pass

# Run the bot
Bot.run()
