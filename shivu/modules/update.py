from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from shivu import application, collection, CHARA_CHANNEL_ID

# ======================= ALLOWED IDS =======================

ALLOWED_IDS = {
    "1741022717",
    "6842275110",
    "8189669345",
    "7553434931",  # Owner
}

# ======================= RARITY MAP =======================

RARITY_MAP = {
    1: "⛩ Normal",
    2: "🏮 Standard",
    3: "🍀 Regular",
    4: "🔮 Mystic",
    5: "🎐 Eternal",
    6: "👑 Royal",
    7: "🔥 Infernal",
    8: "🎊 Astral",
    9: "🏮 Classic",
    10: "🎭 Mythic",
    11: "🧧 Continental",
    12: "🎈 Chunbiyo"
}

# ======================= DELETE COMMAND =======================

async def delete(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)

    # ---- Allowed IDs Check ----
    if user_id not in ALLOWED_IDS:
        return await update.message.reply_text("❌ You don't have permission to use /delete.")

    args = context.args
    if len(args) != 1:
        return await update.message.reply_text("Use: /delete <id>")

    char_id = args[0].strip()

    # Check if character exists
    char = await collection.find_one({"id": char_id})

    if not char:
        return await update.message.reply_text("❌ Character not found in DB.")

    # Mark as EMPTY SLOT (Reusable)
    await collection.update_one(
        {"id": char_id},
        {
            "$set": {
                "deleted": True,
                "name": "",
                "anime": "",
                "rarity": "",
                "rarity_number": None,
                "img_url": None,
                "vid_url": None,
                "message_id": None  # Remove old channel message ref
            }
        }
    )

    # Delete message from channel if exists
    try:
        if char.get("message_id"):
            await context.bot.delete_message(
                chat_id=CHARA_CHANNEL_ID,
                message_id=char["message_id"]
            )
    except:
        pass

    await update.message.reply_text(
        f"✔️ Deleted Successfully\n"
        f"🆔 ID `{char_id}` is now EMPTY & will be reused on next upload."
    )

# ======================= UPDATE COMMAND =======================

async def update_character(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)

    # ---- Allowed IDs Check ----
    if user_id not in ALLOWED_IDS:
        return await update.message.reply_text("❌ You don't have permission to use /update.")

    args = context.args
    if len(args) != 3:
        return await update.message.reply_text("Use:\n/update id field new_value")

    char_id = args[0]
    field = args[1]
    value = args[2]

    valid_fields = ["img_url", "name", "anime", "rarity"]

    if field not in valid_fields:
        return await update.message.reply_text("Invalid field name.")

    char = await collection.find_one({"id": char_id})
    if not char:
        return await update.message.reply_text("Character not found.")

    # transform values
    if field in ["name", "anime"]:
        value = value.replace("-", " ").title()

    if field == "rarity":
        try:
            value = RARITY_MAP[int(value)]
        except:
            return await update.message.reply_text("Invalid rarity number.")

    # update DB
    await collection.update_one({"id": char_id}, {"$set": {field: value}})

    # update channel post caption
    try:
        await context.bot.edit_message_caption(
            chat_id=CHARA_CHANNEL_ID,
            message_id=char["message_id"],
            caption=(
                f"<b>Character Name:</b> {char['name'] if field!='name' else value}\n"
                f"<b>Anime Name:</b> {char['anime'] if field!='anime' else value}\n"
                f"<b>Rarity:</b> {char['rarity'] if field!='rarity' else value}\n"
                f"<b>ID:</b> {char['id']}\n"
                f"Updated by <a href='tg://user?id={update.effective_user.id}'>{update.effective_user.first_name}</a>"
            ),
            parse_mode="HTML"
        )
    except:
        pass

    await update.message.reply_text("✔️ Updated Successfully")

# ======================= REGISTER HANDLERS =======================

application.add_handler(CommandHandler("delete", delete))
application.add_handler(CommandHandler("update", update_character))
  
