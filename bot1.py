import json

import requests
from module1 import send_welcome, handle_start_button
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
from telebot.apihelper import ApiException

from psycopg2 import Error
from dotenv import load_dotenv
import os

import time
import logging

load_dotenv()
API_key = os.getenv("API_KOD1")
bot_username = os.getenv("BOT_USERNAME1")

bot = telebot.TeleBot(API_key)

from psycopg2 import pool

DATABASE_URL = os.getenv("DATABASE_URL")

logging.basicConfig(
    level=logging.INFO,  # Can be DEBUG, INFO, WARNING, ERROR, or CRITICAL
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)

logger = logging.getLogger(__name__)

db_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=5,  # Adjust this based on your needs
    dbname="neondb",
    user="neondb_owner",
    password="npg_tICD3d7ogBGq",
    host="ep-winter-union-a2jhss06-pooler.eu-central-1.aws.neon.tech",
    port="5432",  # Default PostgreSQL port
    sslmode="require"
)


def get_connection():
    return db_pool.getconn()


def release_connection(conn):
    db_pool.putconn(conn)


bmd = "CAACAgIAAxkBAAIBlmdxZi6sK42VCA3-ogaIn30MXGrmAAJnIAACKVtpSNxijIXcPOrMNgQ"

holatbot = True

# url = urlparse(DATABASE_URL)
# from flask import Flask
import threading

# app = Flask(__name__)


# @app.route('/')
# def home():
#     return "I'm alive!"


# def run_flask():
#     app.run(host='0.0.0.0', port=5000)


# # Run Flask in a separate thread so it doesn't block your bot
# threading.Thread(target=run_flask, daemon=True).start()


def keep_connection_alive():
    while True:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1;")  # Simple query to keep DB alive
        except Exception as e:
            print(f"Keep-alive error: {e}")
        finally:
            cursor.close()
            release_connection(conn)
            time.sleep(50)  # Run every 5 minutes


# Run keep-alive in a background thread
threading.Thread(target=keep_connection_alive, daemon=True).start()


def create_all_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS followers (
                        id SERIAL PRIMARY KEY,
                        channel_name TEXT,
                        channel_url TEXT,
                        num_follower INTEGER,
                        now_follower INTEGER

                    );
                ''')
    conn.commit()

    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS blockers (
                        id SERIAL PRIMARY KEY,
                        number_blok INTEGER
                    );
                ''')
    conn.commit()

    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS files (
                        id SERIAL PRIMARY KEY,
                        file_kod INTEGER,
                        file_id TEXT,
                        file_name TEXT,
                        file_type TEXT,
                        timestamp REAL

                    );
                ''')
    conn.commit()

    cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT
                );
                """)
    conn.commit()

    cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT
                );
                """)
    conn.commit()
    cursor.close()
    release_connection(conn)


create_all_database()

def create_konkurs_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS konkurs (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT UNIQUE NOT NULL,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        referrer_user_id BIGINT UNIQUE NOT NULL,
                        referrer_username TEXT,
                        referrer_first_name TEXT,
                        referrer_last_name TEXT
                    );
                    """)
    cursor.close()
    release_connection(conn)

create_konkurs_database()


def save_file(file_kod, file_id, file_name, file_type):
    conn = get_connection()
    cursor = conn.cursor()
    try:

        cursor.execute('''
                INSERT INTO files (file_kod, file_id, file_name, file_type,timestamp)
                VALUES (%s,%s ,%s ,%s, %s)
            ''', (file_kod, file_id, file_name, file_type, time.time()))
        conn.commit()

    except Exception as e:
        logger.info(f"[anipower] Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)


# Get file metadata from the database
def get_file(file_kod):
    file = 0
    conn = get_connection()

    cursor = conn.cursor()
    try:

        cursor.execute('SELECT  file_id, file_name, file_type FROM files WHERE file_kod = %s', (file_kod,))
        file = cursor.fetchall()

    except Exception as e:
        logger.info(f"[anipower] Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)
    return file


def get_ani_kod(name):
    conn = get_connection()

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT  id,file_kod,file_name  FROM files;')
        fil = cursor.fetchall()
    except Exception as e:
        logger.info(f"[anipower] Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)

    l_a = []
    k = []
    for x in fil:
        word = x[2].split("\n")[1]
        ans = word.split(":")[1]
        if name in ans.lower() and x[1] not in k:
            l_a.append(x)
            k.append(x[1])

    return l_a


def get_last_kod():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT  file_kod  FROM files;')
        kod = max(cursor.fetchall())
    except Exception as e:
        logger.info(f"[anipower] Database connection error: {e}")
        kod = [0]
    finally:
        cursor.close()
        release_connection(conn)
    return kod


def show_anime_list():
    conn = get_connection()
    cursor = conn.cursor()
    names = ""
    try:
        cursor.execute('SELECT  file_kod, file_name  FROM files;')
        names = cursor.fetchall()
    except Exception as e:
        logger.info(f"[anipower] Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)
    ls = ["List of animes"]
    lr = []
    for x in names:
        if x not in lr:
            lr.append(x)
            try:
                word = x[1].split("\n")[1]
                ans = word.split(":")[1]
                ls.append(f"{x[0]}:  {ans}\n")
            except Exception as e:
                ls.append(f"{x[0]}: Nomda xatolik {e}")

    return ls


def log_admin(user_id, username, first_name, last_name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
                            INSERT INTO admins (user_id, username, first_name, last_name)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (user_id) DO UPDATE
                            SET username = EXCLUDED.username,
                                first_name = EXCLUDED.first_name,
                                last_name = EXCLUDED.last_name;
                        ''', (user_id, username, first_name, last_name))
        conn.commit()
    except Exception as e:
        logger.info(f"[anipower]Admin_log Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)


# Count total users
def count_users():
    conn = get_connection()
    cursor = conn.cursor()
    count = 0
    try:
        cursor.execute("SELECT COUNT(*) FROM users;")
        count = cursor.fetchone()[0]
    except Exception as e:
        logger.info(f"[anipower]count_users Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)
    return count


# Keyboards-------------------------

def get_control_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_st = types.KeyboardButton('📊Statistika')
    item_xy = types.KeyboardButton("📨E'lon qilish")
    item_pt = types.KeyboardButton("📬Post tayyorlash")
    item_tx = types.KeyboardButton("📥Text post")
    item_as = types.KeyboardButton("⚙️Anime sozlash")
    item_kl = types.KeyboardButton("📢Kanallar")
    item_ad = types.KeyboardButton("📋Adminlar")
    item_bh = types.KeyboardButton("🤖Bot holati")
    item_bc = types.KeyboardButton("◀️Orqaga")

    markup.row(item_st, item_xy)
    markup.row(item_pt, item_tx, item_kl)
    markup.row(item_as, item_ad)
    markup.row(item_bh, item_bc)
    return markup


def main_keyboard(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_al = types.KeyboardButton('🫀 Animes')
    markup.row(item_al)
    if is_admin(message.chat.id):
        item_bh = types.KeyboardButton(text="🛂Boshqaruv")
        markup.row(item_bh)
    return markup


def search_keyboard():
    tip_board = InlineKeyboardMarkup()
    butname = InlineKeyboardButton(text="📛Search by name", switch_inline_query_current_chat="")
    butkod = InlineKeyboardButton(text="🔢Search by kod", callback_data="search_kod")
    butlate = InlineKeyboardButton(text="🆕New animes", callback_data="search_lates")
    tip_board.add(butname, butkod)
    tip_board.add(butlate)

    return tip_board


# @bot.message_handler(content_types= ["photo"])
# def show_id(message):
#     print(message.photo[-1].file_id)

def is_admin(user_id):
    user_id = str(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    ids_of_admin = ()
    try:
        cursor.execute("SELECT user_id FROM admins;")
        ids_of_admin = cursor.fetchall()
    except Exception as e:
        logger.info(f"[anipower]is_admin Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)
    for x in ids_of_admin:
        if user_id == str(x[0]) or user_id == "6945876603":
            return True
    return False


# checking Inchannel----------------------------
channel_id = "@telegrabotkrito"


def check_user_in_channel(message):
    conn = get_connection()
    cursor = conn.cursor()
    ll: tuple = ()
    try:
        cursor.execute("SELECT channel_name,channel_url FROM followers;")
        ll = cursor.fetchall()
    except Exception as e:
        logger.info(f"[anipower]check_user_in_channel Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)
    bo = len(ll)
    keyboard = InlineKeyboardMarkup()
    for c in ll:
        s: str = c[1]
        url1: str = f"@{s[13:]}"
        member = bot.get_chat_member(chat_id=url1, user_id=message.chat.id)
        if member.status not in ['member', 'administrator', 'creator']:
            keyboard.add(InlineKeyboardButton(text=c[0], url=c[1]))
        else:
            bo -= 1

    if bo > 0:
        start_button = InlineKeyboardButton("✅Check", callback_data="send_start")
        keyboard.add(start_button)

        bot.send_message(message.chat.id,
                         f"Please follow this channels !",
                         reply_markup=keyboard)
        bot.send_sticker(message.chat.id, sticker=bmd)
        return False
    else:
        return True


@bot.message_handler(func=lambda message: message.text == "🫀 Animes")
def anime_main(message):
    if check_user_in_channel(message):
        bot.send_photo(message.chat.id,
                       "AgACAgIAAxkBAAMMaEZ7SpJNnYzLFeBr7wKQaVwpsT4AAs_2MRuZUzBKhM2uOA7JLB8BAAMCAAN4AAM2BA",
                       caption=". .  ── •✧⛩✧• ──  . .• Animelarni biz bilan tomosha qilish yanada osonroq  o((≧ω≦ ))o",
                       reply_markup=search_keyboard())


# Starts bot--------------------------------------------------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("send_start:"))
def a2(call):
    knlar = call.data.split(":")[1]
    knlar = knlar.split(",")
    knlar = [int(element) for element in knlar]
    print(knlar)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    handle_start_button(call, knlar)
    send_welcome(call.message)


@bot.message_handler(commands=['start'])
def a1(message):
    send_welcome(message)


@bot.message_handler(commands=['mylink'])
def link(message):
    bot.send_message(message.chat.id,
                     f"🎁 MOBILE LEGENDS KONKURSI! 🎁\nYangi Mobile Legends olmoslari bo‘yicha konkurs boshlanganini mamnuniyat bilan e’lon qilaman!\n📅 Konkurs 2025-yil 19-iyuldan 21-iyulgacha davom etadi.\n\n✨ Bitta omadli ishtirokchi tasodifiy tarzda tanlanadi.\n✨ Bu safar faqat g‘olib emas, balki uni taklif qilgan odam ham 56 olmosga ega bo‘ladi! 💎\n📢 Bor-yo‘g‘i 3 kun — imkoniyatni qo‘ldan boy bermang!\n\n📥 Ishtirok etish uchun havola: https://t.me/{bot_username}?start={message.chat.id}")
    bot.send_message(message.chat.id,
                     f"🎁 MOBILE LEGENDS GIVEAWAY! 🎁\nI'm excited to announce the launch of a brand new Mobile Legends diamond giveaway!\n📅 The giveaway will run from July 19 to July 21, 2025.\n\n✨ One lucky participant will be selected randomly.\n✨ This time, not only the winner but also the person who invited them will receive 56 diamonds each! 💎\n📢 Only 3 days — don’t miss your chance!\n\n📥 Join here: https://t.me/{bot_username}?start={message.chat.id}")


# Anime Izlash ko'di--------------------------------------------------------


@bot.callback_query_handler(func=lambda call: call.data == "search_kod" and check_user_in_channel(call.message))
def handle_kod_button(call):
    keyboard_kod = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_bk = types.KeyboardButton('Bekor qilish')
    keyboard_kod.row(item_bk)
    bot.send_message(call.message.chat.id, "🔎Iltimos qidirmoqchi bo'lgan Anime kodini kiriting:",
                     reply_markup=keyboard_kod)


@bot.callback_query_handler(func=lambda call: call.data == "search_lates")
def handle_xit_button(call):
    bot.answer_callback_query(call.id, "Sending /Anime list...")
    tip_board = InlineKeyboardMarkup()

    names: tuple = ()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT  file_kod, file_name  FROM files;')
        names = cursor.fetchall()
    except Exception as e:
        logger.info(f"[anipower]handle_xit_button Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)
    lr = []
    k = 0
    for x in names:

        if k == 8:
            break
        if x not in lr:
            k += 1
            lr.append(x)
            word = x[1].split("\n")[1]
            ans = word.split(":")[1]
            butname = InlineKeyboardButton(text=ans, url=f"https://t.me/{bot_username}?start={x[0]}")
            tip_board.add(butname)

    bot.send_message(call.message.chat.id, "---- Anime List ----", reply_markup=tip_board)


@bot.message_handler(func=lambda message: message.text == "🔎Anime izlash" and holatbot)
def relpy_search(message):
    if check_user_in_channel(message):
        bot.send_message(message.chat.id, "🔍Qidiruv tipini tanlang:", reply_markup=search_keyboard())


# Boshqaruv paneli----------------

broadcast_mode = False


@bot.message_handler(func=lambda message: message.text == "🛂Boshqaruv")
def control(message):
    if is_admin(message.chat.id):
        bot.send_message(message.chat.id, "✅Siz admin ekanligingiz tasdiqlandi.", reply_markup=get_control_keyboard())
        bot.send_sticker(message.chat.id, "CAACAgIAAxkBAAICmWd2qLc5grUQzAkIASgXwR4-jW1FAAKfGgAC43BwSQoc1Niaab0fNgQ")
    else:
        bot.send_message(message.chat.id, "❌Siz bu tizimdan foyadalanish huquqiga ega emasiz.")
        bot.send_sticker(message.chat.id, "CAACAgQAAxkBAAICk2d2pwlY_Az7yUl1HN1qkEGGlkLmAAI2EwACGJ3wUKir7ygymVAENgQ")


# statistika tugmasi----------------------------

def blockers_pp():
    s = 0
    conn = get_connection()
    cursor = conn.cursor()
    a = ()
    try:
        cursor.execute("SELECT user_id FROM users;")
        peaple = cursor.fetchall()
        for user_id in peaple:
            try:
                bot.send_message(chat_id=user_id, text="Hello! Just testing 😊")
            except:
                s += 1

        cursor.execute("UPDATE blockers SET number_blok = %s WHERE id = %s", (s, 1))
        conn.commit()
        cursor.execute("SELECT id FROM blockers;")
        a = cursor.fetchall()
        if len(a) < 1:
            a = ()
    except Exception as e:
        logger.info(f"[anipower]count_users Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)
    return len(a)


@bot.callback_query_handler(func=lambda call: call.data == "num_blockers")
def num_b(call):
    son = blockers_pp()
    bot.send_message(call.message.chat.id,
                     f"❇️Faol foydalanuvchilar soni: {count_users() - int(son)}\n⭕️Blocklagan boydalanuvchilar soni: {son} ")


def bl_keybord():
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text="Blocklagan foydalanuvchilar soni", callback_data="num_blockers")
    keyboard.add(button)
    return keyboard


@bot.message_handler(func=lambda message: message.text == "📊Statistika" and is_admin(message.chat.id))
def user_num(message):
    bot.send_message(message.chat.id, f"📋Bot foydalanuvchilar soni: {count_users()}", reply_markup=bl_keybord())


# Broadcast tugmasi-----------------------------

@bot.message_handler(func=lambda message: message.text == "📨E'lon qilish" and is_admin(message.chat.id))
def start_broadcast(message):
    global broadcast_mode
    if is_admin(message.chat.id):
        broadcast_mode = True
        bot.send_message(message.chat.id, text="❇️Yuboriladigan xabarni yozing...")
    else:
        bot.send_message(message.chat.id, "❌Siz bu tizimdan foyadalanish huquqiga ega emasiz.")
        bot.send_sticker(message.chat.id, "CAACAgQAAxkBAAICk2d2pwlY_Az7yUl1HN1qkEGGlkLmAAI2EwACGJ3wUKir7ygymVAENgQ")


# 🎥Anime sozlash--------------------------------------------------------------------------------------------------
get_anime = False
get_anime_nom = False
get_anime_qism = False
get_anime_fasl = False
get_anime_janr = False
get_anime_hol = False
anime_del = False
anime_change = False
anime_kod = get_last_kod()[0]
file_n: str = ""
file_m: str = ""
file_q: str = ""
file_f: str = ""
file_j: str = ""
file_h: str = ""
print(anime_kod)
add_uz_bool = False
file_list = []
get_post_vid_or_photo = False


@bot.message_handler(func=lambda message: message.text == "⚙️Anime sozlash" and is_admin(message.chat.id))
def create_keyboard_of_anime_change(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_st = types.KeyboardButton("❇️Anime qo'shish")
    item_xy = types.KeyboardButton("🗑Anime o'chrish")
    item_rh = types.KeyboardButton("📚Animelar ro'yhati")
    item_pt = types.KeyboardButton("🔱O'zgartirish")
    item_bc = types.KeyboardButton("◀️Orqaga")

    markup.row(item_st, item_xy)
    markup.row(item_rh, item_pt)
    markup.row(item_bc)

    bot.send_message(message.chat.id, "Anime Sozlash bo'limi!", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "📚Animelar ro'yhati")
def handle_list_button(message):
    roy = show_anime_list()
    m = ""
    k = 0
    for i in roy:
        k += 1
        if k >= 50:
            bot.send_message(message.chat.id, m)
            k = 0
            m = ""
        m += ("🆔" + i + "\n")

    m += "Ko'rmoqchi bo'lgan anime kodini kiriting !"
    bot.send_message(message.chat.id, m)


@bot.message_handler(func=lambda message: message.text == "❇️Anime qo'shish" and is_admin(message.chat.id))
def add_anime(message):
    global get_anime_nom
    get_anime_nom = True
    global anime_kod
    anime_kod += 1
    bot.send_message(message.chat.id, "Nomini kiriting")


@bot.message_handler(func=lambda message: get_anime_nom and is_admin(message.chat.id))
def get_file_name(message):
    global file_m, get_anime_nom, get_anime_qism
    file_m = message.text
    get_anime_nom = False
    get_anime_qism = True
    bot.send_message(message.chat.id, "Qismlar sonini kiriting")


@bot.message_handler(func=lambda message: get_anime_qism and is_admin(message.chat.id))
def get_file_name(message):
    global file_q, get_anime_qism, get_anime_janr
    file_q = message.text
    get_anime_janr = True
    get_anime_qism = False
    bot.send_message(message.chat.id, "Anime janrini kiriting !")


# @bot.message_handler(func=lambda message: get_anime_qism and is_admin(message.chat.id))
# def get_file_name(message):
#     global file_h, get_anime_janr, get_anime_hol
#     file_h = message.text
#     get_anime_janr = True
#     get_anime_hol = False
#     bot.send_message(message.chat.id, "Anime janrini kiriting !")


@bot.message_handler(func=lambda message: get_anime_janr and is_admin(message.chat.id))
def get_file_name(message):
    global file_j, get_anime_janr, get_anime, get_post_vid_or_photo
    file_j = message.text
    get_anime = True
    get_anime_janr = False
    get_post_vid_or_photo = True
    bot.send_message(message.chat.id, "🖼 Suratini yoki Videosini tashlang.")


@bot.message_handler(content_types=['photo', 'video', 'document'],
                     func=lambda message: get_anime and is_admin(message.chat.id))
def handle_file_upload(message):
    global file_list, get_anime, get_post_vid_or_photo
    file_id = None
    file_name = "Unknown"

    if message.photo:
        file_id = message.photo[-1].file_id  # Get the largest photo
        file_type = 'photo'
    elif message.video:
        file_id = message.video.file_id
        file_type = 'video'
    elif message.document:
        file = message.document  # Get the uploaded file info
        if file.mime_type == "video/x-matroska":  # Check if it's an MKV file
            file_id = file.file_id
            file_type = "mkv"
        elif file.mime_type == "video/mp4" or file.file_name.endswith(".mp4"):
            file_id = file.file_id
            file_type = "mp4"
        else:
            bot.reply_to(message, "⛔️Unsupported file type.")
            return
    else:
        bot.reply_to(message, "⛔️Unsupported file type.")
        return

    # Save file metadata to database
    if file_id:
        file_list.append({"message_id": message.message_id, "file_id": file_id, "file_type": file_type})
        file_list.sort(key=lambda x: x["message_id"])
    # save_file_eng(anime_kod2, file_id, file_n, file_type)

    bot.reply_to(message, f"✅{file_type.capitalize()} saved successfully! /save")
    if get_post_vid_or_photo:
        get_post_vid_or_photo = False
        bot.send_message(message.chat.id,
                         "🎥Ok, yuklamoqchi bo'lgan anime qismlarini tartib bo'yicha tashlang (1 -> 12)")


@bot.message_handler(func=lambda message: is_admin(message.chat.id), commands=["save"])
def finish_file_upload(message):
    global anime_kod, file_m, file_q, file_h, file_j, file_list, get_anime
    sorted_files = file_list
    get_anime = False
    file_name = f"╭━━━⌈ 𝗔𝗡𝗜𝗠𝗘 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡 ⌋━━━╮\n┃ 🏷 𝗡𝗮𝗺𝗲: {file_m}\n┃ 🎭 𝗚𝗲𝗻𝗿𝗲: {file_j}\n┃ 🎞 𝗘𝗽𝗶𝘀𝗼𝗱𝗲: {file_q}\n┃ 🆔 𝗞𝗼𝗱:{anime_kod} {file_h}\n╰━━━━━━━━━━━━━━━━━━━━━━━╯\n\nInstagram: https://www.instagram.com/anime_kirito_2oo7?igsh=bzVsOHQwZWYzMHJs"
    # file_n = f"‣ {file_m}\n╭──────────────────────\n├‣ Qismlar soni: {file_q}\n├‣ Holati{file_h}\n├‣ Fasl: {file_f}\n├‣ Janr: {file_j}\n╰──────────────────────"

    for file in sorted_files:
        save_file(anime_kod, file["file_id"], file_name, file["file_type"])
    bot.reply_to(message, f"✅{file_name.split("\n")[1]} saved successfully!")
    bot.reply_to(message, f"✅Anime kodi: {anime_kod}")
    file_list = []


@bot.message_handler(func=lambda message: message.text == "🗑Anime o'chrish" and is_admin(message.chat.id))
def del_anime(message):
    global anime_del
    anime_del = True
    roy = show_anime_list()
    m = ""
    k = 0
    for i in roy:
        k += 1
        if k >= 50:
            bot.send_message(message.chat.id, m)
            k = 0
            m = ""
        m += ("🆔" + i + "\n")
    bot.send_message(message.chat.id, m)
    bot.send_message(message.chat.id, "O'chirmoqchi bo'lgan anime kodini kiriting...")


@bot.message_handler(func=lambda message: is_admin(message.chat.id) and anime_del)
def delete_anime_from_anime_list(message):
    global anime_del
    anime_del = False
    conn = get_connection()
    cursor = conn.cursor()
    try:
        kod = int(message.text)
        cursor.execute("DELETE FROM files WHERE file_kod = %s", (kod,))
        conn.commit()

        bot.send_message(message.chat.id, "✅Anime muvaffaqiyatli o'chirildi")
    except Exception as e:
        bot.send_message(message.chat.id, f"⛔️Tizimda xatolik yuz berdi: {e}")
    finally:
        cursor.close()
        release_connection(conn)


add_ep_bool1 = False
add_ep_bool2 = False
ep_num: int = 0
an_name: str = "Unknown"


@bot.callback_query_handler(func=lambda call: call.data == "ep_anime")
def change_anime_ep(call):
    global add_ep_bool1
    roy = show_anime_list()
    m = ""
    k = 0
    for i in roy:
        k += 1
        if k >= 50:
            bot.send_message(call.message.chat.id, m)
            k = 0
            m = ""
        m += ("🆔" + i + "\n")
    bot.send_message(call.message.chat.id, m)
    bot.send_message(call.message.chat.id, "Qism qo'shiladigan anime kodini kiriting...")
    add_ep_bool1 = True


@bot.message_handler(func=lambda message: is_admin(message.chat.id) and add_ep_bool1)
def add_episode(message):
    global ep_num, an_name, add_ep_bool1, add_ep_bool2
    conn = get_connection()
    cursor = conn.cursor()
    eplist = ()
    try:
        cursor.execute("SELECT file_kod, file_name FROM files;")
        eplist = cursor.fetchall()
    except Exception as e:
        logger.info(f"[anipower]add_episode Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)

    for i in eplist:
        if int(i[0]) == int(message.text):
            an_name = i[1]
            break
    if an_name == "Unknown":
        bot.send_message(message.chat.id, "Siz mavjud bo'lmagan kod kiritingiz!")
    else:
        ep_num = int(message.text)
        add_ep_bool2 = True
        bot.send_message(message.chat.id,
                         f"🎥Ok, {an_name} animesiga yuklamoqchi bo'lgan qismni/larni tartib bo'yicha tashlang...")
    add_ep_bool1 = False


@bot.message_handler(content_types=['video', 'document'],
                     func=lambda message: add_ep_bool2 and is_admin(message.chat.id))
def handle_file_upload(message):
    global ep_num, an_name
    file_id = 0
    file_type = 'photo'
    if message.video:
        file_id = message.video.file_id
        file_type = 'video'
    elif message.document:
        file = message.document  # Get the uploaded file info
        if file.mime_type == "video/x-matroska":  # Check if it's an MKV file
            file_id = file.file_id
            file_type = "mkv"
        elif file.mime_type == "video/mp4" or file.file_name.endswith(".mp4"):
            file_id = file.file_id
            file_type = "mp4"
        else:
            bot.reply_to(message, "⛔️Unsupported file type.")
    else:
        bot.reply_to(message, "⛔️Unsupported file type.")
        return

    # Save file metadata to database
    save_file(ep_num, file_id, an_name, file_type)
    bot.reply_to(message, f"✅{file_type.capitalize()} saved successfully!")


@bot.callback_query_handler(func=lambda call: call.data == "name_anime")
def change_anime_name(call):
    global anime_change
    anime_change = True
    # roy = show_anime_list()
    # m = ""
    # k = 0
    # for i in roy:
    #     k += 1
    #     if k >= 50:
    #         bot.send_message(call.message.chat.id, m)
    #         k = 0
    #         m = ""
    #     m += ("🆔" + i + "\n")
    # bot.send_message(call.message.chat.id, m)
    bot.send_message(call.message.chat.id,
                     "O'zgartirmoqchi bo'lgan anime kodi va yangi nomini kiriting Eg. 1, Anime_name. Vergul bo'lishi shart.")


@bot.message_handler(func=lambda message: anime_change and is_admin(message.chat.id))
def change_name(message):
    global anime_change
    conn = get_connection()
    cursor = conn.cursor()
    k = message.text.split(",")
    try:
        cursor.execute("UPDATE files SET file_name = %s WHERE file_kod = %s", (k[1], int(k[0])))
        conn.commit()
        bot.send_message(message.chat.id, "✅Anime muvaffaqiyatli o'zgartirildi.")

    except Exception as e:
        logger.info(f"[anipower]change_name Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)
        anime_change = False


@bot.message_handler(func=lambda message: message.text == "🔱O'zgartirish" and is_admin(message.chat.id))
def change_anime(message):
    keyboard = InlineKeyboardMarkup()
    button_name = InlineKeyboardButton(text="Nomini o'zgartish", callback_data="name_anime")
    button_ep = InlineKeyboardButton(text="Qismini o'zgartirish", callback_data="ep_anime")
    keyboard.add(button_ep, button_name)
    bot.send_message(message.chat.id, "Animeni qanday o'zgartirmoqchisiz ?", reply_markup=keyboard)


# post text--------------------------------------------------------------------------------------------------
anime_kd = 0
take_text = False
take_kd = False


@bot.message_handler(func=lambda message: message.text == "📥Text post" and is_admin(message.chat.id))
def post_kd(message):
    global take_kd
    take_kd = True
    bot.send_message(message.chat.id, "📥Post qilish kerak bo'lgan anime ID-ni kiriting:")


@bot.message_handler(func=lambda message: take_kd and is_admin(message.chat.id))
def post_text(message):
    global take_text, take_kd, anime_kd
    take_text = True
    take_kd = False
    anime_kd = message.text
    bot.send_message(message.chat.id, "✍️Post qilish kerak bo'lgan matnni kiriting:")


@bot.message_handler(func=lambda message: take_text and is_admin(message.chat.id))
def finish_post(message):
    global anime_kd
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton("🔹👉Watch now", url=f"https://t.me/{bot_username}?start={anime_kd}")
    markup.add(button)
    global take_text
    take_text = False
    bot.send_message(CHANNEL_ID, text=message.text, reply_markup=markup)
    bot.send_message(message.chat.id, "✅Xabar muvaffaqiyatli yuborildi.")


# 📬Post tayyorlash----------------------------------------------------------------------------------------------------------------
kd_bool = False
kd = 0
get_post_bool = False
CAPTION: str = "This is a caption for the photo!"
FILE_ID: str = "AgACAgIAAxkBAAIVLGeSgqErwpnTn6rQBDNA0MBLlueRAAJ96jEbetaRSPk5lM895IfOAQADAgADeAADNgQ"
BUTTON = {
    "inline_keyboard": [
        [
            {
                "text": "🔹👉Wacht now",  # Button text
                "url": f"https://t.me/{bot_username}?start={kd}"  # URL the button links to
            }
        ]
    ]
}


@bot.callback_query_handler(func=lambda call: call.data == "send_channel")
def channel_send(call):
    global video_bool
    url7 = f"https://api.telegram.org/bot{API_key}/sendPhoto"
    url8 = f"https://api.telegram.org/bot{API_key}/sendVideo"
    if video_bool:
        response = requests.post(url8, data=get_payload())
    else:
        response = requests.post(url7, data=get_payload())

    if response.status_code == 200:
        bot.send_message(call.message.chat.id, "Post sent successfully")
    else:
        logger.info(f"[anipower] : Failed to send photo: {response.status_code} - {response.text}")


@bot.message_handler(func=lambda message: message.text == "📬Post tayyorlash" and is_admin(message.chat.id))
def create_post(message):
    global kd_bool
    kd_bool = True
    bot.send_message(message.chat.id, "Iltimos, Anime ko'dini kiriting.")


@bot.message_handler(func=lambda message: is_admin(message.chat.id) and kd_bool)
def get_post(message):
    global kd, kd_bool, get_post_bool
    kd_bool = False
    get_post_bool = True
    kd = int(message.text)
    bot.send_message(message.chat.id, "Iltimos, foto va anime postingizni tashlang...")


@bot.message_handler(content_types=["photo", "video"],
                     func=lambda message: is_admin(message.chat.id) and get_post_bool)
def ready_post(message):
    global kd, nm_channel, CAPTION, FILE_ID, get_post_bool, BUTTON, video_bool
    get_post_bool = False

    BUTTON = {
        "inline_keyboard": [
            [
                {
                    "text": "🔹👉Watch now",  # Button text
                    "url": f"https://t.me/{bot_username}?start={kd}"  # URL the button links to
                }
            ]
        ]
    }
    conn = get_connection()
    cursor = conn.cursor()
    file_lost = ()
    try:
        cursor.execute('SELECT  file_name FROM files WHERE file_kod = %s', (kd,))
        file_lost = cursor.fetchone()
    except Exception as e:
        logger.info(f"[anipower]ready_post Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)

    CAPTION = f"{file_lost[0]}"
    link = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text="🔹👉Watch now", url=f"https://t.me/{bot_username}?start={kd}")
    button2 = InlineKeyboardButton(text=nm_channel, callback_data="send_channel")
    link.add(button)
    link.add(button2)
    if message.content_type == "photo":
        bot.send_photo(message.chat.id, message.photo[-1].file_id, caption=CAPTION,
                       reply_markup=link)
        FILE_ID = message.photo[-1].file_id
    elif message.content_type == "video":
        bot.send_video(message.chat.id, message.video.file_id, caption=CAPTION,
                       reply_markup=link)
        FILE_ID = message.video.file_id
        video_bool = True
    else:
        bot.send_message(message.chat.id, "Siz noto'g'ri turdagi xabar yubordiz!")


video_bool = False

# "📢Kanallar"-----------------------------------------
add_channel_bool = False
del_channel_bool = False
hisobot_bool = False
CHANNEL_ID = "@neon_katanas"

nm_channel: str = "Neon ^ katanas"


@bot.callback_query_handler(func=lambda call: call.data == "oth_channel")
def channel_add_to_post(call):
    global hisobot_bool
    hisobot_bool = True
    bot.send_message(call.message.chat.id,
                     "Kanal nomini, silkasisini  vergul bilan ajratib kiriting .\nkanal_nomi,kanal_silkasi")


@bot.callback_query_handler(func=lambda call: call.data == "add_channel")
def channel_add_to_list(call):
    global add_channel_bool
    add_channel_bool = True
    bot.send_message(call.message.chat.id,
                     "Kanal nomini, silkasisini va qo'shiluvchilar soni  vergul bilan ajratib kiriting .\nkanal_nomi,kanal_silkasi,100")


@bot.callback_query_handler(func=lambda call: call.data == "del_channel")
def channel_add_to_list(call):
    global del_channel_bool
    del_channel_bool = True
    bot.send_message(call.message.chat.id, "Kanal kodini kiriting.")


@bot.message_handler(func=lambda message: message.text == "📢Kanallar" and is_admin(message.chat.id))
def channel_list(message):
    keyboard = InlineKeyboardMarkup()
    button_add = InlineKeyboardButton(text="➕Kanal qo'shish", callback_data="add_channel")
    button_oth = InlineKeyboardButton(text="➕Post kanali", callback_data="oth_channel")
    button_del = InlineKeyboardButton(text="➖Kanal o'chrish", callback_data="del_channel")
    keyboard.add(button_oth)
    keyboard.add(button_add)
    keyboard.add(button_del)
    conn = get_connection()
    cursor = conn.cursor()
    ch_list = ()
    try:
        cursor.execute("SELECT * FROM followers;")
        ch_list = cursor.fetchall()
    except Exception as e:
        logger.info(f"[anipower]channel_list Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)
    mm: str = ""
    for c in ch_list:
        mm += f"{c[0]}. {c[1]} , {c[2]} , {c[4]}\n"
    try:
        bot.send_message(message.chat.id, mm, reply_markup=keyboard)
    except:
        bot.send_message(message.chat.id, "Kanal qo'shing!", reply_markup=keyboard)


@bot.message_handler(func=lambda message: is_admin(message.chat.id) and add_channel_bool)
def add_channel(message):
    global add_channel_bool
    conn = get_connection()
    cursor = conn.cursor()

    m = message.text.split(",")
    try:
        cursor.execute("""
        INSERT INTO followers (channel_name,channel_url, num_follower, now_follower)
        VALUES (%s,%s,%s,%s)
        """, (m[0], m[1], m[2], 0))
        conn.commit()
        bot.send_message(message.chat.id, "✅Kanal muvoffaqiyatli qo'shildi.")
    except Error as e:
        logger.info(f"[anipower]add_channel Database connection error: {e}")
    finally:
        add_channel_bool = False
        cursor.close()
        release_connection(conn)


@bot.message_handler(func=lambda message: is_admin(message.chat.id) and del_channel_bool)
def del_channel(message):
    global del_channel_bool
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM followers WHERE id = %s", (int(message.text),))
        conn.commit()

        bot.send_message(message.chat.id, "✅Kanal muvoffaqiyatli o'chirildi")
    except Error as e:
        logger.info(f"[anipower]del_channel Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)
        del_channel_bool = False


@bot.message_handler(func=lambda message: is_admin(message.chat.id) and hisobot_bool)
def qosh_kanal(message):
    global hisobot_bool, nm_channel, CHANNEL_ID
    hisobot_bool = False
    try:
        ll = message.text.split(",")
        CHANNEL_ID = f"@{ll[1][13:]}"
        nm_channel = ll[0]
        bot.send_message(message.chat.id, "✅Kanal muvoffaqiyatli qo'shildi.")
    except:
        bot.send_message(message.chat.id, "⛔️Kanal o'rnamadi, iltimos qayta urining.")


def get_payload():
    global CAPTION, CHANNEL_ID, FILE_ID, BUTTON, video_bool
    if video_bool:
        payload = {
            "chat_id": CHANNEL_ID,
            "video": FILE_ID,
            "caption": CAPTION,
            "reply_markup": json.dumps(BUTTON)  # Inline keyboard markup must be JSON-encoded
        }
        video_bool = False
    else:
        payload = {
            "chat_id": CHANNEL_ID,
            "photo": FILE_ID,
            "caption": CAPTION,
            "reply_markup": json.dumps(BUTTON)  # Inline keyboard markup must be JSON-encoded
        }

    return payload


# Admins tugmasi--------------------------------------
enable_add = False
enable_del = False


@bot.callback_query_handler(func=lambda call: call.data == "add_admin")
def admin_add(call):
    global enable_add, enable_del
    enable_add = True
    enable_del = False
    bot.send_message(call.message.chat.id, "📃Admin qilmoqchi bo'lgan shaxsning 'username'ini  kiriting...")


@bot.callback_query_handler(func=lambda call: call.data == "del_admin")
def admin_del(call):
    global enable_del, enable_add
    enable_del = True
    enable_add = False
    bot.send_message(call.message.chat.id, "🔢Admin raqamini jo'nating...")


@bot.message_handler(func=lambda message: message.text == "📋Adminlar" and is_admin(message.chat.id))
def show_admins(message):
    keyboard = InlineKeyboardMarkup()
    button_add = InlineKeyboardButton(text="➕Admin qo'shish", callback_data="add_admin")
    button_del = InlineKeyboardButton(text="➖Admin o'chrish", callback_data="del_admin")
    keyboard.add(button_add)
    keyboard.add(button_del)
    conn = get_connection()
    cursor = conn.cursor()
    adminlar = ()
    try:
        cursor.execute("SELECT * FROM admins;")
        adminlar = cursor.fetchall()
    except Exception as e:
        logger.info(f"[anipower]show_admins Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)
    mes_to_admin: str = ""
    for person in adminlar:

        mes_to_admin += f"{person[0]}."
        if None != person[2]:
            mes_to_admin += f" {person[2]},"
        if None != person[3]:
            mes_to_admin += f" {person[3]},"
        if None != person[4]:
            mes_to_admin += f" {person[4]},"
        mes_to_admin += "\n"
    try:
        bot.send_message(message.chat.id, mes_to_admin, reply_markup=keyboard)
    except Exception as e:
        bot.send_message(message.chat.id, f"Admin qo'shing !\n{e}", reply_markup=keyboard)


@bot.message_handler(func=lambda message: is_admin(message.chat.id) and enable_add)
def search_admin(message):
    global enable_add
    conn = get_connection()
    cursor = conn.cursor()
    people = ()
    try:
        cursor.execute("SELECT * FROM users;")
        people = cursor.fetchall()
    except Exception as e:
        logger.info(f"[anipower]search_admin Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)
    try:
        num = int(message.text)
        for p in people:
            if p[0] == num:
                log_admin(p[1], p[2], p[3], p[4])
                bot.send_message(message.chat.id, "✅Yangi Admin o'rnatildi")
                enable_add = False
                break


    except ValueError:
        mes_to_admin: str = ""
        for person in people:

            if message.text in person:
                mes_to_admin += f"{person[0]}."
                if None != person[2]:
                    mes_to_admin += f" {person[2]},"
                if None != person[3]:
                    mes_to_admin += f" {person[3]},"
                if None != person[4]:
                    mes_to_admin += f" {person[4]},"
                mes_to_admin += "\n"
        bot.send_message(message.chat.id, f"Natijalar:\n{mes_to_admin}Ism oldidagi raqamni jo'nating")
    except Exception as e:
        bot.send_message(message.chat.id, f"⛔️Tizimda xatolik: {e}")


@bot.message_handler(func=lambda message: is_admin(message.chat.id) and enable_del)
def delete_admin(message):
    global enable_del
    conn = get_connection()
    cursor = conn.cursor()

    try:
        num = int(message.text)
        cursor.execute("DELETE FROM admins WHERE id = %s", (num,))
        conn.commit()

        bot.send_message(message.chat.id, "😎Adim muvoffaqiyatli o'chirildi.")
    except Exception as e:
        logger.info(f"[anipower]delete_admin Database connection error: {e}")

    finally:
        cursor.close()
        release_connection(conn)
        enable_del = False


# bot holati tugmasi----------------------------------
@bot.callback_query_handler(func=lambda call: call.data == "starts")
def starts_bot(call):
    global holatbot
    holatbot = True
    switch(call.message)


def start_bot(message):
    mes_key = InlineKeyboardMarkup()
    but1 = InlineKeyboardButton(text="✅Turn On", callback_data="starts")
    mes_key.add(but1)
    bot.send_message(message.chat.id, "⛔️Bot to'xtatildi.", reply_markup=mes_key)


@bot.callback_query_handler(func=lambda call: call.data == "stop")
def stops(call):
    global holatbot
    holatbot = False
    start_bot(call.message)


@bot.message_handler(func=lambda message: message.text == "🤖Bot holati" and is_admin(message.chat.id))
def switch(message):
    global holatbot
    if is_admin(message.chat.id):
        keyboard = InlineKeyboardMarkup()
        if holatbot:
            hol = "Ishalamoqda"
        else:
            hol = "To'xtatilgan"
        button2 = InlineKeyboardButton(text="🚷Turn off", callback_data="stop")

        keyboard.add(button2)
        bot.send_message(message.chat.id, f"😇Bot holati: {hol}", reply_markup=keyboard)


# Back tugmasi---------------------------------------------
@bot.message_handler(func=lambda message: message.text == "◀️Orqaga" or message.text == "Bekor qilish")
def back(message):
    global get_anime, get_anime_nom, anime_del, anime_change, add_uz_bool, enable_add, enable_del, take_text, take_kd, add_ep_bool2
    take_kd = False
    take_text = False
    enable_add = False
    enable_del = False
    get_anime = False
    get_anime_nom = False
    anime_del = False
    anime_change = False
    add_uz_bool = False
    add_ep_bool2 = False
    bot.send_message(message.chat.id, "📋Bosh menyu", reply_markup=main_keyboard(message))


# Anime Izlash-------------------------------------------------------------------------------------------------------

def get_ani_button(kod, file_id, st):
    ls_anime = InlineKeyboardMarkup()
    file_n_i = get_file(kod)
    k = -1
    a = (len(file_n_i) - 1) // 24
    b = (len(file_n_i) - 1 - a * 24) % 3
    arr = []
    choosen = 0
    bol = True
    for f in file_n_i:

        k += 1

        if k > st * 24:
            if k <= (st + 1) * 24:
                saved_file_id, file_name, file_type = f
                if k != 0:
                    if saved_file_id == file_id:
                        arr.append(InlineKeyboardButton(text=f"📌{k}", callback_data=f"show_ep:{k}:{kod}"))
                        choosen = k
                    else:
                        arr.append(InlineKeyboardButton(text=f"{k}", callback_data=f"show_ep:{k}:{kod}"))
                if k % 3 == 0 and k != 0:
                    ls_anime.add(arr[0], arr[1], arr[2])
                    arr = []
        if k == (st + 1) * 24:
            bol = False
            break

    if bol:
        for i in arr:
            ls_anime.add(i)

    #     k += 1
    #     saved_file_id, file_name, file_type = f
    #     if k != 0:
    #         if saved_file_id == file_id:
    #             arr.append(InlineKeyboardButton(text=f"📌{k}", callback_data=f"show_ep:{k}:{kod}"))
    #             choosen = k
    #         else:
    #             arr.append(InlineKeyboardButton(text=f"{k}", callback_data=f"show_ep:{k}:{kod}"))
    #     if k % 3 == 0 and k != 0:
    #         ls_anime.add(arr[0], arr[1], arr[2])
    #         arr = []
    #     if k >= 24:
    #         bo = False
    #         break

    # if bo:
    #     for i in arr:
    #         ls_anime.add(i)

    if choosen % 24 == 0:
        choosen -= 1
    fw = InlineKeyboardButton(text=f"Forward⏩", callback_data=f"forward:{choosen // 24}:{kod}")
    bc = InlineKeyboardButton(text=f"⏪Back", callback_data=f"back:{choosen // 24}:{kod}")
    ls_anime.add(bc, fw)
    ls_anime.add(InlineKeyboardButton(text=f"📋All episodes", callback_data=f"show_all:{kod}"))

    return ls_anime


@bot.callback_query_handler(func=lambda call: call.data.startswith("back:"))
def back_episode(call):
    try:
        st = int(call.data.split(":")[1])
        kod = call.data.split(":")[2]
        ls_anime = InlineKeyboardMarkup()
        file_n_i = get_file(kod)
        k = -1

        arr = []
        bo = True
        for f in file_n_i:
            k += 1
            if st == 0:
                return 0
            if k > (st - 1) * 24 and k <= st * 24 and st != 0:
                if bo:
                    sv_fl_id, f_n, f_t = f
                    bo = False
                saved_file_id, file_name, file_type = f
                if k != 0:
                    arr.append(InlineKeyboardButton(text=f"{k}", callback_data=f"show_ep:{k}:{kod}"))
                if k % 3 == 0 and k != 0:
                    ls_anime.add(arr[0], arr[1], arr[2])
                    arr = []

        fw = InlineKeyboardButton(text=f"Forward⏩", callback_data=f"forward:{st}:{kod}")
        bc = InlineKeyboardButton(text=f"⏪Back", callback_data=f"back:{st - 1}:{kod}")
        ls_anime.add(bc, fw)

        ls_anime.add(InlineKeyboardButton(text=f"📋All episodes", callback_data=f"show_all:{kod}"))
        bot.send_video(call.message.chat.id, sv_fl_id, caption=f_n,
                       reply_markup=ls_anime, protect_content=True)
    except:
        print("uyog'i yo'q")


@bot.callback_query_handler(func=lambda call: call.data.startswith("forward:"))
def forward_episode(call):
    try:
        st = int(call.data.split(":")[1])
        kod = call.data.split(":")[2]
        ls_anime = InlineKeyboardMarkup()
        file_n_i = get_file(kod)
        k = -1
        a = (len(file_n_i) - 1)
        b = (len(file_n_i) - 1 - st * 24) % 3
        arr = []
        bo = True
        bol = True
        for f in file_n_i:

            k += 1

            if k > (st + 1) * 24 and k <= (st + 2) * 24:
                if bo:
                    sv_fl_id, f_n, f_t = f
                    bo = False
                saved_file_id, file_name, file_type = f
                if k != 0:
                    arr.append(InlineKeyboardButton(text=f"{k}", callback_data=f"show_ep:{k}:{kod}"))

                if k % 3 == 0 and k != 0:
                    ls_anime.add(arr[0], arr[1], arr[2])
                    arr = []
            if k == (st + 2) * 24:
                bol = False
                break

        if bol:
            for i in arr:
                ls_anime.add(i)
        fw = InlineKeyboardButton(text=f"Forward⏩", callback_data=f"forward:{st + 1}:{kod}")
        bc = InlineKeyboardButton(text=f"⏪Back", callback_data=f"back:{st + 1}:{kod}")
        ls_anime.add(bc, fw)
        ls_anime.add(InlineKeyboardButton(text=f"📋All episodes", callback_data=f"show_all:{kod}"))
        bot.send_video(call.message.chat.id, sv_fl_id, caption=f_n,
                       reply_markup=ls_anime, protect_content=True)
    except Exception as e:
        logger.info(f"[anipower]  Error: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("show_all:"))
def show_episode(call):
    kod = call.data.split(":")[1]
    file_n_i = get_file(kod)

    k = -1

    for f in file_n_i:
        if f:
            saved_file_id, file_name, file_type = f
            k += 1
            # Send file using its file_id
            if file_type == "photo":
                bot.send_photo(call.message.chat.id, saved_file_id, caption=file_name, protect_content=True)

            elif file_type == 'video':
                if k == 0:
                    bot.send_video(call.message.chat.id, saved_file_id, caption=file_name, protect_content=True)
                else:
                    bot.send_video(call.message.chat.id, saved_file_id, caption=f"{k} - qism", protect_content=True)

            else:
                try:
                    bot.send_document(call.message.chat.id, saved_file_id, caption=f"{k} - qism", protect_content=True)
                except:
                    bot.reply_to(call.message, "⭕️Unknown file type.")
        else:
            bot.reply_to(call.message, "⭕️File not found.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("show_ep:"))
def show_episode(call):
    t, ep_id, kod = call.data.split(":")
    file_n_i = get_file(kod)
    k = 0
    st = 0
    ln = len(file_n_i)
    for f in file_n_i:
        saved_file_id, file_name, file_type = f
        if k == int(ep_id):
            if file_type == "photo":
                bot.send_photo(call.message.chat.id, saved_file_id, caption=file_name,
                               reply_markup=get_ani_button(kod, saved_file_id, k // 24), protect_content=True)
            else:
                bot.send_video(call.message.chat.id, saved_file_id, caption=file_name,
                               reply_markup=get_ani_button(kod, saved_file_id, k // 24), protect_content=True)
        k += 1


@bot.message_handler(content_types=["text", "photo", "video", "audio", "document", "sticker"],
                     func=lambda message: holatbot)
def kod_check(message):
    global anime_kod, broadcast_mode

    mmm = message.text
    if message.chat.type in ["group", "supergroup"] and "kkk" not in message.text.lower():
        return
    elif message.chat.type in ["group", "supergroup"] and "kkk" in message.text.lower():
        mmm = message.text[4:]

    if is_admin(message.chat.id) and broadcast_mode:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users;")
            peaple = cursor.fetchall()

        except Exception as e:
            print(f"Database connection error: {e}")
            exit()
        finally:
            cursor.close()
            release_connection(conn)
        for user in peaple:

            try:
                user_id = user[1]
                if int(user_id) == 7651554989:
                    print("bo'timiz")
                elif message.content_type == "text":
                    bot.send_message(user_id, message.text, protect_content=True)
                    # Broadcast photos
                elif message.content_type == "photo":
                    bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption, protect_content=True)
                    # Broadcast videos
                elif message.content_type == "video":
                    bot.send_video(user_id, message.video.file_id, caption=message.caption, protect_content=True)
                    # Broadcast audio
                elif message.content_type == "audio":
                    bot.send_audio(user_id, message.audio.file_id, caption=message.caption, protect_content=True)
                    # Broadcast documents
                elif message.content_type == "document":
                    bot.send_document(user_id, message.document.file_id, caption=message.caption, protect_content=True)
                elif message.content_type == "sticker":
                    bot.send_sticker(user_id, message.sticker.file_id)
            except Exception as e:
                print(f"⭕️️Bu userga xabar jo'natilmadi. {user}: {e}")
            finally:
                broadcast_mode = False
        bot.send_message(message.chat.id, "Xabar yuborib tugallandi.")
    else:
        try:

            file_kod = int(mmm)
            if file_kod <= anime_kod and get_file(file_kod) != 0:

                file_n_i = get_file(file_kod)
                saved_file_id, file_name, file_type = file_n_i[0]

                if file_type == "photo":
                    bot.send_photo(message.chat.id, saved_file_id, caption=file_name,
                                   reply_markup=get_ani_button(file_kod, saved_file_id, 0), protect_content=True)
                elif file_type == 'video':
                    bot.send_video(message.chat.id, saved_file_id, caption=file_name,
                                   reply_markup=get_ani_button(file_kod, saved_file_id, 0), protect_content=True)

            else:
                bot.send_message(message.chat.id, "🙁This kod wasn't found in anime list.")
        except ValueError:
            ani_res_list = get_ani_kod(mmm.lower())
            l = ""
            for x in ani_res_list:
                l += f"{x[1]}:  {x[2]}\n"
            if l != "":
                bot.send_message(message.chat.id, l)
            else:
                bot.send_message(message.chat.id, "🙁This kod wasn't found in anime list.")


        except Exception as e:
            bot.send_message(message.chat.id, f"💥A system error has occurred. Please try again later.: {e}")


def get_result(list1):
    results: list = []
    dont_rety: list = []
    for p in list1:
        if p[1] not in dont_rety:
            dont_rety.append(p[1])
            word = p[2].split("\n")[1]
            ans = word.split(":")[1]
            results.append(
                InlineQueryResultArticle(
                    id=str(p[0]),
                    title=ans,
                    description=f"Anime is the best thing in the world 😇",
                    input_message_content=InputTextMessageContent(f"{p[1]}"),
                )
            )

    return results


@bot.inline_handler(lambda query: len(query.query) > 0)  # Only trigger when user types something
def inline_query_handler(query):
    results = get_result(get_ani_kod(query.query.lower()))

    bot.answer_inline_query(query.id, results, cache_time=1)


print("Your bot is running")
bot.remove_webhook()
#bot.polling(none_stop=True)
# bot.polling(none_stop=True, interval=1, timeout=2, long_polling_timeout=10)
bot.infinity_polling(skip_pending= True)

# Close the database connection properly when the script exits
