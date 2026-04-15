class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    OWNER_ID = "8441236350"
    sudo_users = "7553434931", "8725331299"
    GROUP_ID = -1003992204811
    TOKEN = "8264339422:AAEDnkBcUgK_ul-Ivjq32i_lkrkPZE_pPlU"
    mongo_url = "mongodb+srv://rj5706603:O95nvJYxapyDHfkw@cluster0.fzmckei.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    PHOTO_URL = ["https://files.catbox.moe/aw6zui.jpg"]
    SUPPORT_CHAT = "https://t.me/+dv_rcq5uIXhmMWM1"
    UPDATE_CHAT = "https://t.me/+Imyf3M9TO5k1ODRl"
    BOT_USERNAME = "@WAIFU_SLAVE_OP_bot"
    CHARA_CHANNEL_ID = "abrakatabragiligilichu"
    api_id = 35411328
    api_hash = "4c8d3c8f5d3483296f5fb530ea2cfcc6"

    
class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
