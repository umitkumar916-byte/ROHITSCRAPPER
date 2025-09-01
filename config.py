import os

# Bot token @Botfather
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7713330273:AAHGTZMO6PnrJx0XheVNKYe98KRKTWYze5Y")

# Your API ID from my.telegram.org
API_ID = int(os.environ.get("API_ID", "25649636"))

# Your API Hash from my.telegram.org
API_HASH = os.environ.get("API_HASH", "43af470d1c625e603733268b3c2f7b8f")

# String Session (still left blank as per previous setup)
SESSION = os.environ.get("SESSION", "BQFziNcAgyeaP3wrd-tgMN_DsRL8Gd08dYoH9_IEkn-eFctJpM6nvFEDq52jbB1HM6Cj7NCGtPuxEQT5oKxQKM-DwRCxFHw_ehk3-7HrAbT4SQmFm3i-1sqjiT2trxz23IySldyBVF5yIO7k1APc9pjXXHqB5fAnH6f3eZ3DbBMJjYMgq-uo8E8SsaXNLNph57uFl0_CLPdKyY8Xu6uzVB__aoCKJpwuPUo0U7yGy1QMm_utkE1CwyKjQ6RKxAJIGVicYdYtmK6Qt1dLq0e25rVfsxcU9YkAF2CV2glxuaSXXQUFVICig8VK2D0P9ik-PNB-tKm3uclzDGCqwgcEr3ywOiDbgQAAAAHR0wr8AA")

# Your Owner / Admin Id For Broadcast 
ADMINS = int(os.environ.get("ADMINS", "7815236348"))

# Your Mongodb Database Url
# Warning - Give Db uri in deploy server environment variable, don't give in repo.
DB_URI = os.environ.get(
    "DB_URI", 
    "mongodb+srv://Goku_bhai001:iS5sYySFKS2xZZpc@cluster0.voj0eyt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
DB_NAME = os.environ.get("DB_NAME", "scrapper1")

FILE_CHANNEL = int(os.environ.get("FILE_CHANNEL", "-1002016298313"))
FILE_BOT_USERNAME = os.environ.get("FILE_BOT_USERNAME", "Gori_madam1bot")

BYPASS = bool(os.environ.get("BYPASS", False))
BYPASS_BOT_USERNAME = os.environ.get("BYPASS_BOT_USERNAME", "Nick_Bypass_Bot")

# How to watch video guide link
HOW_TO_WATCH_LINK = os.environ.get("HOW_TO_WATCH_LINK", "https://t.me/how_bot_work/15")
