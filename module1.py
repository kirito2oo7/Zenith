from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import telebot
# import psycopg2
from psycopg2 import Error
# from urllib.parse import urlparse
from psycopg2 import pool
import logging
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())
API_key = os.getenv("API_KOD1")
bot_username = os.getenv("BOT_USERNAME1")

bot = telebot.TeleBot(API_key)

bmd = "CAACAgIAAxkBAAIBlmdxZi6sK42VCA3-ogaIn30MXGrmAAJnIAACKVtpSNxijIXcPOrMNgQ"

logging.basicConfig(
    level=logging.INFO,  # Can be DEBUG, INFO, WARNING, ERROR, or CRITICAL
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')

# db_pool = pool.SimpleConnectionPool(
#     minconn=1,
#     maxconn=5,  # Adjust this based on your needs
#     dbname="neondb",
#     user="neondb_owner",
#     password="npg_wD1sRuaxK0Ve",
#     host="ep-shiny-cherry-a1bp74yw-pooler.ap-southeast-1.aws.neon.tech",
#     port="5432",  # Default PostgreSQL port
#     sslmode="require"
# )
db_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=5,  # adjust as needed
    dbname="neondb",
    user="neondb_owner",
    password="npg_Jc4Qiz8POUYy",
    host="ep-orange-paper-agem8p43-pooler.c-2.eu-central-1.aws.neon.tech",
    port="5432",
    sslmode="require"
)


def get_connection():
    return db_pool.getconn()


def release_connection(conn):
    db_pool.putconn(conn)


# url = urlparse(DATABASE_URL)

def is_admin(user_id):
    user_id = str(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    ids_of_admin = ()
    try:
        cursor.execute("SELECT user_id FROM admins;")
        ids_of_admin = cursor.fetchall()
    except Exception as e:
        logger.info(f"[anipower] Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)
    for x in ids_of_admin:
        if user_id == str(x[0]) or user_id == "6945876603":
            return True
    return False


def main_keyboard(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_al = types.KeyboardButton('🫀 Animes')
    markup.row(item_al)
    if is_admin(message.chat.id):
        item_bh = types.KeyboardButton(text="🛂Boshqaruv")
        markup.row(item_bh)
    return markup


def get_file(file_kod):
    conn = get_connection()
    cursor = conn.cursor()
    file = ()
    try:
        if file_kod >= 1000:
            cursor.execute('SELECT  file_id, file_name, file_type FROM files_manga WHERE file_kod = %s', (file_kod,))
        else:
            cursor.execute('SELECT  file_id, file_name, file_type FROM files WHERE file_kod = %s', (file_kod,))

        file = cursor.fetchall()
    except Exception as e:
        logger.info(f"[anipower]get_file Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)
    return file


def check_user_in_channel(message):
    conn = get_connection()
    cursor = conn.cursor()
    ll = ()
    try:
        cursor.execute("SELECT channel_url FROM followers;")
        ll = cursor.fetchall()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)
    for i in ll:
        try:
            s: str = i[0]
            url1: str = f"@{s[13:]}"
            member = bot.get_chat_member(chat_id=url1, user_id=message.chat.id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            print(f"channel_Error: {e}")
            return False
    return True


def log_user(user_id, username, first_name, last_name):
    conn = get_connection()
    cursor = conn.cursor()
    try:

        cursor.execute('''
                    INSERT INTO users (user_id, username, first_name, last_name)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id) DO NOTHING;
                ''', (user_id, username, first_name, last_name))
        conn.commit()

    except Exception as e:
        logger.info(f"[anipower]log_user Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)
    # conn = sqlite3.connect("bot_users.db", check_same_thread=False)


def log_user_konkurs(user_id, username, first_name, last_name, referrer_user_id, referrer_username, referrer_first_name,
                     referrer_last_name):
    conn = get_connection()
    cursor = conn.cursor()
    try:

        cursor.execute('''
                    INSERT INTO konkurs (user_id, username, first_name, last_name, referrer_user_id, referrer_username, referrer_first_name, referrer_last_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO NOTHING;
                ''', (
            user_id, username, first_name, last_name, referrer_user_id, referrer_username, referrer_first_name,
            referrer_last_name))
        conn.commit()

    except Exception as e:
        logger.info(f"[zenith]log_user_konkurs Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)


def handle_start_button(call, knlar):
    bot.answer_callback_query(call.id, "Sending /start command...")
    if check_user_in_channel(call.message):
        conn = get_connection()
        cursor = conn.cursor()
        ll = ()
        try:
            cursor.execute("SELECT * FROM followers;")
            ll = cursor.fetchall()
            for chan in ll:
                if chan[0] in knlar:
                    s: str = chan[2]
                    n: int = chan[4]
                    print(s, n)
                    cursor.execute("UPDATE followers SET now_follower = %s WHERE channel_url = %s", (n + 1, s))
                    conn.commit()
                    m: int = chan[3]
                    if n >= m:
                        cursor.execute("DELETE FROM followers WHERE channel_url = %s", (s,))
                        conn.commit()

                        bot.send_message(call.message.chat.id,
                                         f"✅ {chan[1]} kanal {n} ta obunachi qo'shilgani uchun o'chirildi")
        except Exception as e:
            logger.info(f"[anipower]handle_start_button Database connection error: {e}")
        finally:
            cursor.close()
            release_connection(conn)


def get_ani_button(kod, file_id, st):
    ls_anime = InlineKeyboardMarkup()
    file_n_i = get_file(kod)
    k = -1
    a = (len(file_n_i) - 1) // 24
    b = (len(file_n_i) - 1 - a * 24) % 3
    arr = []
    choosen = 0
    bo = True
    for f in file_n_i:
        k += 1
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
        if k >= 24:
            bo = False
            break

    if bo:
        for i in arr:
            ls_anime.add(i)

    if choosen % 24 == 0:
        choosen -= 1
    fw = InlineKeyboardButton(text=f"Forward⏩", callback_data=f"forward:{choosen // 24}:{kod}")
    bc = InlineKeyboardButton(text=f"⏪Back", callback_data=f"back:{choosen // 24}:{kod}")
    ls_anime.add(bc, fw)
    ls_anime.add(InlineKeyboardButton(text=f"📋All episodes", callback_data=f"show_all:{kod}"))

    return ls_anime


@bot.callback_query_handler(func=lambda call: call.data.startswith("back:"))
def back_episode(call):
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
    bc = InlineKeyboardButton(text=f"⏪Back", callback_data=f"back:{st}:{kod}")
    ls_anime.add(bc, fw)

    ls_anime.add(InlineKeyboardButton(text=f"📋All episodes", callback_data=f"show_all:{kod}"))
    bot.send_video(call.message.chat.id, sv_fl_id, caption=f_n,
                   reply_markup=ls_anime, protect_content=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith("forward:"))
def forward_episode(call):
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
    fw = InlineKeyboardButton(text=f"Forward⏩", callback_data=f"forward:{st}:{kod}")
    bc = InlineKeyboardButton(text=f"⏪Back", callback_data=f"back:{st}:{kod}")
    ls_anime.add(bc, fw)
    ls_anime.add(InlineKeyboardButton(text=f"📋All episodes", callback_data=f"show_all:{kod}"))
    bot.send_video(call.message.chat.id, sv_fl_id, caption=f_n,
                   reply_markup=ls_anime, protect_content=True)


def send_welcome(message: types.Message):
    args: list = message.text.split()
    user = message.from_user
    log_user(user.id, user.username, user.first_name, user.last_name)
    file_kod: int = 0
    bot.send_message(message.chat.id, f"Hello, {user.first_name}.?",
                     reply_markup=main_keyboard(message))
    if check_user_in_channel(message):

        try:

            if len(args) > 1 and int(args[1]) < 100:
                file_kod = int(args[1])

                file_n_i = get_file(file_kod)
                saved_file_id, file_name, file_type = file_n_i[0]
                if file_type == "photo":
                    bot.send_photo(message.chat.id, saved_file_id, caption=file_name,
                                   reply_markup=get_ani_button(file_kod, saved_file_id, 0), protect_content=True)
                elif file_type == 'video':
                    bot.send_video(message.chat.id, saved_file_id, caption=file_name,
                                   reply_markup=get_ani_button(file_kod, saved_file_id, 0), protect_content=True)


            elif len(args) > 1 and int(args[1]) > 100:

                referrer_id = int(args[1])
                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT  user_id FROM konkurs;')
                list_people = cursor.fetchall()
                in_bool = False
                for i in list_people:
                    if message.chat.id in i:
                        in_bool = True
                        break
                if in_bool == False:
                    cursor.execute('SELECT  username, first_name, last_name FROM users WHERE user_id = %s', (referrer_id,))
                    referrer = cursor.fetchall()[0]
                    cursor.close()
                    release_connection(conn)
    
                    log_user_konkurs(user.id, user.username, user.first_name, user.last_name, referrer_id, referrer[0],
                                     referrer[1], referrer[2])
                    bot.send_message(message.chat.id,
                                     f"✅You have successfully registered.\n✅Siz muvaffaqiyatli ravishda ro'yhatdan o'tdingiz.\n\nReferrer: {referrer[0]} {referrer[1]}")
                    bot.send_message(referrer_id,
                                     f"✅Sizning havolaniz orqali {user.first_name} {user.last_name} konkursga qo'shildi.")
                    bot.send_message(message.chat.id,
                                     f"🎁 MOBILE LEGENDS KONKURSI! 🎁\nYangi Mobile Legends olmoslari bo‘yicha konkurs boshlanganini mamnuniyat bilan e’lon qilaman!\n📅 Konkurs 2025-yil 19-iyuldan 21-iyulgacha davom etadi.\n\n✨ Bitta omadli ishtirokchi tasodifiy tarzda tanlanadi.\n✨ Bu safar faqat g‘olib emas, balki uni taklif qilgan odam ham 56 olmosga ega bo‘ladi! 💎\n📢 Bor-yo‘g‘i 3 kun — imkoniyatni qo‘ldan boy bermang!\n\n📥 Ishtirok etish uchun havola: https://t.me/{bot_username}?start={message.chat.id}")
                    # bot.send_message(message.chat.id,
                    # f"🎁 MOBILE LEGENDS GIVEAWAY! 🎁\nI'm excited to announce the launch of a brand new Mobile Legends diamond giveaway!\n📅 The giveaway will run from July 19 to July 21, 2025.\n\n✨ One lucky participant will be selected randomly.\n✨ This time, not only the winner but also the person who invited them will receive 56 diamonds each! 💎\n📢 Only 3 days — don’t miss your chance!\n\n📥 Join here: https://t.me/{bot_username}?start={message.chat.id}")
                else:
                    cursor.close()
                    release_connection(conn)
                    bot.send_message(message.chat.id,
                                     f"✅Siz allaqachon konkursga qo'shilgansiz.")

        except Exception as e:
            print(e)
        finally:

            print("----")

    else:
        try:
            if len(args) > 1:
                file_kod = int(args[1])
            else:
                file_kod = 0
        except:
            file_kod = 0
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM followers;")
            l = cursor.fetchall()
        except Exception as e:
            print(f"Database connection error: {e}")
            exit()
        finally:
            cursor.close()
            release_connection(conn)
        keyboard = InlineKeyboardMarkup()
        kn = []
        for c in l:
            s: str = c[2]
            url1: str = f"@{s[13:]}"
            member = bot.get_chat_member(chat_id=url1, user_id=message.chat.id)
            if member.status not in ['member', 'administrator', 'creator']:
                keyboard.add(InlineKeyboardButton(text=c[1], url=c[2]))
                kn.append(c[0])
        kn = [str(element) for element in kn]
        ans = ",".join(kn)
        keyboard.add(InlineKeyboardButton(text="Renegade o'lmas", url="https://t.me/+nZhPaTKv9Es2Yzky"))
        if file_kod != 0:
            start_button = InlineKeyboardButton("✅Check", url=f"https://t.me/{bot_username}?start={file_kod}",
                                                callback_data=f"send_start:{ans}")
        else:
            start_button = InlineKeyboardButton("✅Check", callback_data=f"send_start:{ans}")
        keyboard.add(start_button)
        kn = []
        
        bot.send_message(message.chat.id,
                         f"If you want to use our services, subscribe to the channels below!",
                         reply_markup=keyboard)
        bot.send_sticker(message.chat.id, sticker=bmd)
