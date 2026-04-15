import random
import string
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from telegram.constants import ParseMode
from shivu import application, user_collection, collection

OWNER = 7553434931   # <-- Change if needed


# ==============================================================
#               Helper - Generate Random Code
# ==============================================================

def generate_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))


# ==============================================================
#                    ADMIN: /gen  (Money Code)
# ==============================================================

async def gen_command(update: Update, context: CallbackContext):
    user = update.message.from_user

    if user.id != OWNER:
        return await update.message.reply_text("❌ Only my Owner can use /gen")

    try:
        amount = float(context.args[0])
        quantity = int(context.args[1])
    except:
        return await update.message.reply_text("Usage:\n/gen <amount> <quantity>")

    code = generate_code()

    await user_collection.update_one(
        {"_id": f"money_{code}"},
        {
            "$set": {
                "_id": f"money_{code}",
                "code": code,
                "amount": amount,
                "quantity": quantity,
                "claimed_by": []
            }
        },
        upsert=True
    )

    amt = f"{amount:,.0f}"

    await update.message.reply_html(
        f"🔑 <b>Money Code Generated!</b>\n"
        f"Code: <code>{code}</code>\n"
        f"💰 Amount: <b>{amt}</b>\n"
        f"♻ Quantity: <b>{quantity}</b>"
    )


# ==============================================================
#                USER: /redeem  (Money Claim)
# ==============================================================

async def redeem_command(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        return await update.message.reply_text("Usage: /redeem <code>")

    code = context.args[0]
    user_id = update.message.from_user.id

    code_data = await user_collection.find_one({"_id": f"money_{code}"})
    if not code_data:
        return await update.message.reply_text("❌ Invalid Code.")

    if user_id in code_data.get("claimed_by", []):
        return await update.message.reply_text("❌ You already claimed this code.")

    if len(code_data.get("claimed_by", [])) >= code_data["quantity"]:
        return await update.message.reply_text("❌ This code is fully claimed.")

    # Add balance
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"balance": float(code_data['amount'])}},
        upsert=True
    )

    # Add claim entry
    await user_collection.update_one(
        {"_id": f"money_{code}"},
        {"$push": {"claimed_by": user_id}}
    )

    amt = f"{code_data['amount']:,.0f}"

    await update.message.reply_html(
        f"✅ <b>Redeemed Successfully!</b>\n"
        f"💸 Added <b>{amt}</b> to your wallet."
    )


# ==============================================================
#                ADMIN: /sgen (Waifu Code Generate)
# ==============================================================

async def sgen_command(update: Update, context: CallbackContext):
    user = update.message.from_user

    if user.id != OWNER:
        return await update.message.reply_text("❌ Only my Owner can use /sgen")

    try:
        char_id = context.args[0]
        quantity = int(context.args[1])
    except:
        return await update.message.reply_text("Usage:\n/sgen <char_id> <quantity>")

    waifu = await collection.find_one({"id": char_id})
    if not waifu:
        return await update.message.reply_text("❌ Invalid Character ID.")

    code = generate_code()

    await user_collection.update_one(
        {"_id": f"waifu_{code}"},
        {
            "$set": {
                "_id": f"waifu_{code}",
                "code": code,
                "waifu": waifu,
                "quantity": quantity,
                "claimed_by": [] # Fixed: Used array to prevent double-claiming
            }
        },
        upsert=True
    )

    await update.message.reply_html(
        f"🎀 <b>Waifu Code Generated!</b>\n"
        f"🔑 Code: <code>{code}</code>\n"
        f"👧 Name: <b>{waifu['name']}</b>\n"
        f"💎 Rarity: <b>{waifu['rarity']}</b>\n"
        f"♻ Quantity: <b>{quantity}</b>"
    )


# ==============================================================
#                USER: /sredeem (Waifu Claim)
# ==============================================================

async def sreedeem_command(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        return await update.message.reply_text("Usage: /sredeem <code>")

    code = context.args[0]
    user_id = update.message.from_user.id
    mention = update.message.from_user.mention_html()

    code_data = await user_collection.find_one({"_id": f"waifu_{code}"})
    if not code_data:
        return await update.message.reply_text("❌ Invalid Code.")

    # Prevent a single user from claiming the same waifu code multiple times
    if user_id in code_data.get("claimed_by", []):
        return await update.message.reply_text("❌ You already claimed this code.")

    if len(code_data.get("claimed_by", [])) >= code_data["quantity"]:
        return await update.message.reply_text("❌ This code is fully used.")

    waifu = code_data["waifu"]

    # Add waifu to user
    await user_collection.update_one(
        {"id": user_id},
        {"$push": {"characters": waifu}},
        upsert=True
    )

    # Add user to claimed_by list
    await user_collection.update_one(
        {"_id": f"waifu_{code}"},
        {"$push": {"claimed_by": user_id}}
    )

    caption = (
        f"🎉 <b>Congratulations {mention}!</b>\n"
        f"You received a new character!\n\n"
        f"👧 Name: <b>{waifu['name']}</b>\n"
        f"💎 Rarity: <b>{waifu['rarity']}</b>\n"
        f"📺 Anime: <b>{waifu['anime']}</b>"
    )

    # --- MEDIA SUPPORT LOGIC ---
    if waifu.get("vid_url"):
        # Sends video if vid_url exists
        await update.message.reply_video(
            video=waifu["vid_url"],
            caption=caption,
            parse_mode=ParseMode.HTML
        )
    else:
        # Defaults to photo
        await update.message.reply_photo(
            photo=waifu.get("img_url"),
            caption=caption,
            parse_mode=ParseMode.HTML
        )


# ==============================================================
#             REGISTER COMMAND HANDLERS (PTB STYLE)
# ==============================================================

application.add_handler(CommandHandler("gen", gen_command))
application.add_handler(CommandHandler("redeem", redeem_command))
application.add_handler(CommandHandler("sgen", sgen_command))
application.add_handler(CommandHandler("sredeem", sreedeem_command))
