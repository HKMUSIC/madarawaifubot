import re
from html import escape
from cachetools import TTLCache
from telegram import (
    Update, 
    InlineQueryResultPhoto, 
    InlineQueryResultVideo
)
from telegram.constants import ParseMode
from telegram.ext import InlineQueryHandler, CallbackContext

from shivu import application, db
from shivu.modules.zyro_inline import get_user_collection, search_characters, get_all_characters, refresh_character_caches

# Cache instances
all_characters_cache = TTLCache(maxsize=10000, ttl=300)
user_collection_cache = TTLCache(maxsize=10000, ttl=30)

# ==============================================================
#                     INLINE QUERY HANDLER
# ==============================================================

async def inlinequery(update: Update, context: CallbackContext):
    query = update.inline_query.query.strip()
    offset = int(update.inline_query.offset or 0)

    force_refresh = False
    if "!refresh" in query:
        force_refresh = True
        query = query.replace("!refresh", "").strip()
        await refresh_character_caches()

    # --- Extract AMV flag early ---
    is_amv = False
    if ".AMV" in query:
        is_amv = True
        query = query.replace(".AMV", "").strip()

    user = None
    characters = []

    # ================= COLLECTION MODE =================
    if query.startswith("collection."):
        parts = query.split(" ", 1)
        target_user_id = parts[0].replace("collection.", "").strip()
        search = parts[1] if len(parts) > 1 else ""

        if target_user_id.isdigit():
            user = await get_user_collection(target_user_id)
            if user:
                unique = {}
                for c in user.get("characters", []):
                    if c and isinstance(c, dict) and "id" in c:
                        unique[c["id"]] = c
                characters = list(unique.values())

                if search:
                    rgx = re.compile(search, re.I)
                    characters = [
                        c for c in characters
                        if rgx.search(str(c.get("name", "")))
                        or rgx.search(str(c.get("anime", "")))
                        or rgx.search(" ".join(c.get("aliases", [])))
                    ]

    # ================= GLOBAL SEARCH =================
    else:
        if query:
            characters = await search_characters(query, force_refresh)
        else:
            characters = await get_all_characters(force_refresh)

    # ================= MEDIA FILTER =================
    if is_amv:
        characters = [c for c in characters if c.get("vid_url") or c.get("video_url")]
    else:
        characters = [c for c in characters if c.get("img_url")]

    # ================= PAGINATION =================
    page = characters[offset: offset + 50]
    next_offset = str(offset + 50) if len(page) == 50 else None

    results = []

    for c in page:
        cid = str(c.get("id", "0"))
        
        # --- SAFE STRINGS FOR ESCAPE() ---
        c_name = str(c.get('name') or 'Unknown')
        c_anime = str(c.get('anime') or 'Unknown')
        c_rarity = str(c.get('rarity') or 'Unknown')
        
        # Format list description (Sub-text under the Name)
        list_description = f"Rarity: {c_rarity}\nID: {cid}"

        # --- DYNAMIC CAPTION LOGIC ---
        if user:
            u_name = str(user.get('first_name') or 'User')
            count = sum(1 for x in user.get("characters", []) if x.get("id") == c.get("id"))
            
            caption = (
                f"<b>👤 {escape(u_name)}'s collection</b>\n\n"
                f"<b>📛 {escape(c_name)} ×{count}</b>\n"
                f"<b>🌈 {escape(c_anime)}</b>\n"
                f"<b>✨ rarity: {c_rarity}</b>\n"
                f"<b>🆔 <code>{cid}</code></b>"
            )
        else:
            caption = (
                f"<b>📛 {escape(c_name)}</b>\n"
                f"<b>🌈 {escape(c_anime)}</b>\n"
                f"<b>✨ rarity: {c_rarity}</b>\n"
                f"<b>🆔 <code>{cid}</code></b>"
            )

        # --- MEDIA RESULT ---
        vid_url = c.get("vid_url") or c.get("video_url")
        
        if vid_url:
            # AMVs always show in List View natively
            thumb = c.get("thum_url") or c.get("img_url")
            if not thumb or not str(thumb).startswith("http"):
                thumb = "https://files.catbox.moe/0v2p69.jpg" 

            results.append(
                InlineQueryResultVideo(
                    id=f"v_{cid}_{offset}",
                    video_url=vid_url,
                    mime_type="video/mp4",
                    thumbnail_url=thumb,
                    title=c_name, 
                    description=list_description, 
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            )
        else:
            img_url = c.get("img_url") or "https://files.catbox.moe/0v2p69.jpg"
            
            # Standard Grid View for Images
            results.append(
                InlineQueryResultPhoto(
                    id=f"p_{cid}_{offset}",
                    photo_url=img_url,
                    thumbnail_url=img_url,
                    title=c_name, 
                    description=list_description, 
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            )

    try:
        await update.inline_query.answer(
            results,
            next_offset=next_offset,
            cache_time=2 
        )
    except Exception as e:
        print(f"Inline Query Error for User {update.inline_query.from_user.id}: {e}")

# Register Handlers
application.add_handler(InlineQueryHandler(inlinequery, block=False))
    
