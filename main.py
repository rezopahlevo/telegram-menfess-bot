import os
import random
from datetime import datetime, timedelta, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ENV
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # contoh: @channelkamu
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

# Data
KUOTA_AWAL = 5
user_kuota = {}
premium_user = {}          # user_id: expired_date
emoji_koleksi_user = {}    # user_id: list of emoji
emoji_user_aktif = {}      # user_id: emoji
emoji_gacha_used = set()   # user_id: sudah gacha atau belum
last_reset_date = None
is_paused = False

# Tier Emoji
emoji_tier = {
    "common": ["😇", "😎", "😁", "🐣", "🌻"],
    "rare": ["💎", "🔥", "🧠", "🌈", "🦄"],
    "legendary": ["👑", "💀", "🌟", "😈", "⚡"]
}
emoji_chance = {
    "common": 60,
    "rare": 30,
    "legendary": 10
}

# Reset kuota harian
def reset_kuota_harian():
    global last_reset_date, user_kuota
    now_utc = datetime.utcnow()
    now_wib = now_utc + timedelta(hours=7)
    if (now_wib.time() >= time(6, 0)) and (last_reset_date != now_wib.date()):
        for user_id in user_kuota:
            user_kuota[user_id] = KUOTA_AWAL
        last_reset_date = now_wib.date()

# Cek premium
def is_user_premium(user_id):
    return user_id in premium_user and datetime.utcnow() < premium_user[user_id]

# Gacha emoji
def gacha_emoji():
    roll = random.randint(1, 100)
    if roll <= emoji_chance["common"]:
        return random.choice(emoji_tier["common"])
    elif roll <= emoji_chance["common"] + emoji_chance["rare"]:
        return random.choice(emoji_tier["rare"])
    else:
        return random.choice(emoji_tier["legendary"])

# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Selamat datang!\n\n"
        "Kirim menfess pakai:\n"
        "`#menfess isi pesanmu`\n"
        "atau kirim foto + caption pakai `#menfess`\n\n"
        "📊 Kuota harian: 5x (reset jam 06.00 WIB)\n"
        "💎 Member Premium dapat emoji eksklusif\n"
        "🎰 /gachaemoji | 🎒 /koleksiemoji | ✅ /pakaiemoji 😇\n"
        "🔑 Upgrade premium ke admin: @cszepestorybot",
        parse_mode="Markdown"
    )

# Kuota
async def cek_kuota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_kuota_harian()
    user_id = update.effective_user.id
    kuota = user_kuota.get(user_id, KUOTA_AWAL)
    await update.message.reply_text(f"📊 Kuota kamu hari ini: {kuota}")

# Pause/Resume
async def pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_paused
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Kamu bukan admin.")
    is_paused = True
    await update.message.reply_text("⏸️ Bot sekarang dalam mode PAUSE.")

async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_paused
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Kamu bukan admin.")
    is_paused = False
    await update.message.reply_text("▶️ Bot sudah aktif kembali.")

# Tambah kuota
async def tambah_kuota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Kamu bukan admin.")
    try:
        user_id = int(context.args[0])
        jumlah = int(context.args[1])
        user_kuota[user_id] = user_kuota.get(user_id, KUOTA_AWAL) + jumlah
        await update.message.reply_text(f"✅ Kuota user {user_id} ditambah {jumlah}.")
    except:
        await update.message.reply_text("❌ Format: /tambahkuota user_id jumlah")

# Premium
async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Kamu bukan admin.")
    try:
        user_id = int(context.args[0])
        hari = int(context.args[1])
        premium_user[user_id] = datetime.utcnow() + timedelta(days=hari)
        emoji_gacha_used.discard(user_id)
        await update.message.reply_text(f"✅ User {user_id} jadi premium selama {hari} hari. Gacha diaktifkan kembali.")
    except:
        await update.message.reply_text("❌ Format: /premium user_id hari")

# Gacha emoji
async def gachaemoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_user_premium(user_id):
        return await update.message.reply_text("❌ Hanya member premium yang bisa gacha.")
    if user_id in emoji_gacha_used:
        return await update.message.reply_text("🚫 Kamu sudah melakukan gacha pada periode premium ini.")

    emoji = gacha_emoji()
    emoji_gacha_used.add(user_id)
    emoji_koleksi_user.setdefault(user_id, [])
    if emoji not in emoji_koleksi_user[user_id]:
        emoji_koleksi_user[user_id].append(emoji)
    emoji_user_aktif[user_id] = emoji

    await update.message.reply_text(f"🎰 Selamat! Kamu mendapat emoji premium: {emoji} (aktif sekarang)")

# Koleksi emoji
async def koleksiemoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_user_premium(user_id):
        return await update.message.reply_text("❌ Fitur ini hanya untuk member premium.")

    koleksi = emoji_koleksi_user.get(user_id, [])
    if not koleksi:
        return await update.message.reply_text("🚫 Kamu belum punya emoji premium.")

    aktif = emoji_user_aktif.get(user_id, "❌ Belum dipilih")
    await update.message.reply_text(f"🎒 Koleksi emoji kamu:\n{' '.join(koleksi)}\n\n✅ Aktif: {aktif}")

# Pakai emoji
async def pakaiemoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_user_premium(user_id):
        return await update.message.reply_text("❌ Hanya member premium yang bisa pakai emoji.")

    if not context.args:
        return await update.message.reply_text("❌ Format: /pakaiemoji 😇")

    emoji = context.args[0]
    if emoji not in emoji_koleksi_user.get(user_id, []):
        return await update.message.reply_text("❌ Kamu belum memiliki emoji itu.")

    emoji_user_aktif[user_id] = emoji
    await update.message.reply_text(f"✅ Emoji aktif kamu sekarang: {emoji}")

# Handle #menfess
async def handle_menfess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_kuota_harian()
    user_id = update.effective_user.id
    kuota = user_kuota.get(user_id, KUOTA_AWAL)

    if is_paused:
        return await update.message.reply_text("🚫 Bot sedang pause.")
    if kuota <= 0:
        return await update.message.reply_text("❌ Kuota kamu habis. Coba lagi besok jam 06.00 WIB.")

    msg_text = update.message.text or update.message.caption or ""
    if not msg_text.lower().startswith("#menfess"):
        return

    isi = msg_text[len("#menfess"):].strip()
    prefix = ""

    if is_user_premium(user_id):
        emoji = emoji_user_aktif.get(user_id)
        if emoji:
            prefix = f"{emoji} "

    message = None
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        message = await context.bot.send_photo(chat_id=CHANNEL_ID, photo=file_id, caption=prefix + isi)
    else:
        message = await context.bot.send_message(chat_id=CHANNEL_ID, text=prefix + isi)

    user_kuota[user_id] = kuota - 1
    sisa = user_kuota[user_id]

    if CHANNEL_ID.startswith("@"):
        username = CHANNEL_ID[1:]
        post_link = f"https://t.me/{username}/{message.message_id}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Lihat Postingan", url=post_link)]
        ])
        await update.message.reply_text(f"✅ Menfess dikirim!\n📊 Sisa kuota: {sisa}", reply_markup=keyboard)
    else:
        await update.message.reply_text(f"✅ Menfess dikirim!\n📊 Sisa kuota: {sisa}")

# Setup
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("kuota", cek_kuota))
app.add_handler(CommandHandler("pause", pause))
app.add_handler(CommandHandler("resume", resume))
app.add_handler(CommandHandler("tambahkuota", tambah_kuota))
app.add_handler(CommandHandler("premium", premium))
app.add_handler(CommandHandler("gachaemoji", gachaemoji))
app.add_handler(CommandHandler("koleksiemoji", koleksiemoji))
app.add_handler(CommandHandler("pakaiemoji", pakaiemoji))
app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_menfess))
app.run_polling()
