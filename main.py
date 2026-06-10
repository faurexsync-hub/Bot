#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════╗
║         FUZZY BOT — v9.0             ║
║  Railway | Professional | Full       ║
╚══════════════════════════════════════╝
"""

import telebot
import json
import os
import time
import threading
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ════════════════════════════════════════
#   SOZLAMALAR
# ════════════════════════════════════════
BOT_TOKEN  = os.environ.get("BOT_TOKEN",  "BU_YERGA_TOKEN_YOZING")
ADMIN_ID   = int(os.environ.get("ADMIN_ID", "8355611778"))
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@fuzzssss")

DATA_FILE   = "/tmp/data.json"
STATS_FILE  = "/tmp/stats.json"
SCHED_FILE  = "/tmp/sched.json"
ORDER_FILE  = "/tmp/orders.json"
REVIEW_FILE = "/tmp/reviews.json"

# ════════════════════════════════════════
#   MA'LUMOTLAR
# ════════════════════════════════════════
def load(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return json.loads(json.dumps(default))

def dump(path, obj):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("save error:", e)

def get_data():
    return load(DATA_FILE, {
        "users":        {},
        "blocked":      [],
        "active":       True,
        "spam_limit":   5,
        "work_start":   9,
        "work_end":     18,
        "work_active":  False,
        "work_msg":     "Ish vaqti 09:00-18:00. Tez orada javob beramiz!",
        "welcome":      {
            "uz": "Salom! Fuzzy botga xush kelibsiz!",
            "ru": "Привет! Добро пожаловать в Fuzzy бот!",
            "en": "Hello! Welcome to Fuzzy bot!"
        },
        "faq":          {},
        "subscribers":  [],
        "order_count":  0
    })

def get_stats():
    return load(STATS_FILE, {
        "total": 0, "today": 0,
        "date":  str(datetime.now().date()),
        "counts": {},
        "daily": {}
    })

def get_sched():   return load(SCHED_FILE,  [])
def get_orders():  return load(ORDER_FILE,  [])
def get_reviews(): return load(REVIEW_FILE, [])

# ════════════════════════════════════════
#   BOT VA STATE
# ════════════════════════════════════════
bot      = telebot.TeleBot(BOT_TOKEN)
states   = {}
tmp      = {}
spam_log = {}

LANGS = {"uz": "🇺🇿 UZ", "ru": "🇷🇺 RU", "en": "🇬🇧 EN"}

# ════════════════════════════════════════
#   YORDAMCHI FUNKSIYALAR
# ════════════════════════════════════════
def clean(t):
    if not t: return ""
    for c in ["_","*","`","[","]","~"]: t = str(t).replace(c,"")
    return t

def is_admin(uid): return uid == ADMIN_ID

def get_lang(uid):
    d = get_data()
    return d["users"].get(str(uid), {}).get("lang", "uz")

def tr(uid, uz="", ru="", en=""):
    lang = get_lang(uid)
    return {"uz": uz, "ru": ru, "en": en}.get(lang, uz)

def is_work_time():
    d = get_data()
    if not d["work_active"]: return True
    h = datetime.now().hour
    return d["work_start"] <= h < d["work_end"]

def register_user(user):
    d   = get_data()
    key = str(user.id)
    if key not in d["users"]:
        name = ((user.first_name or "") + " " + (user.last_name or "")).strip() or "Nomsiz"
        d["users"][key] = {
            "id":       user.id,
            "name":     name,
            "username": user.username or "",
            "joined":   datetime.now().strftime("%d.%m.%Y %H:%M"),
            "lang":     "uz",
            "orders":   0,
            "rating":   []
        }
        dump(DATA_FILE, d)

def record_stat(uid):
    s     = get_stats()
    today = str(datetime.now().date())
    if s["date"] != today:
        s["today"] = 0
        s["date"]  = today
    s["total"] += 1
    s["today"] += 1
    s["counts"][str(uid)] = s["counts"].get(str(uid), 0) + 1
    s["daily"][today]     = s["daily"].get(today, 0) + 1
    dump(STATS_FILE, s)

def is_spam(uid):
    d   = get_data()
    key = str(uid)
    now = time.time()
    spam_log.setdefault(key, [])
    spam_log[key] = [t for t in spam_log[key] if now - t < 60]
    spam_log[key].append(now)
    return len(spam_log[key]) > d["spam_limit"]

def notify_admin(user, xabar, prefix="📨 Yangi xabar"):
    try:
        name = clean(((user.first_name or "") + " " + (user.last_name or "")).strip()) or "Nomsiz"
        un   = "@" + clean(user.username) if user.username else "—"
        bot.send_message(ADMIN_ID,
            prefix + "\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Ism: " + name + " (" + un + ")\n"
            "ID: " + str(user.id) + "\n\n"
            + xabar)
    except: pass

def send(cid, text, kb=None):
    try: bot.send_message(cid, text, reply_markup=kb)
    except Exception as e: print("send err:", e)

def edit_msg(call, text, kb=None):
    try:
        bot.edit_message_text(text, call.message.chat.id,
            call.message.message_id, reply_markup=kb)
    except:
        send(call.message.chat.id, text, kb)

# ════════════════════════════════════════
#   KLAVIATURALAR — ADMIN
# ════════════════════════════════════════
def kb_main():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 Statistika",       callback_data="m_stat"),
        InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="m_usr"),
        InlineKeyboardButton("📦 Buyurtmalar",      callback_data="m_orders"),
        InlineKeyboardButton("⭐ Reytinglar",        callback_data="m_reviews"),
        InlineKeyboardButton("📌 FAQ",              callback_data="m_faq"),
        InlineKeyboardButton("📢 Kanal",            callback_data="m_ch"),
        InlineKeyboardButton("📨 Broadcast",        callback_data="m_bc"),
        InlineKeyboardButton("🔔 Obuna",            callback_data="m_sub"),
        InlineKeyboardButton("⚙️ Sozlamalar",       callback_data="m_set"),
    )
    return kb

def kb_back(to="home"):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Asosiy menyu", callback_data=to))
    return kb

def kb_settings():
    d  = get_data()
    st = "🟢 Yoq" if d["active"] else "🔴 Off"
    wt = "🟢 Yoq" if d["work_active"] else "🔴 Off"
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🤖 Bot: " + st,       callback_data="s_tog"),
        InlineKeyboardButton("🕐 Ish vaqti: " + wt, callback_data="s_work"),
        InlineKeyboardButton("🔔 Xush kelibsiz",    callback_data="s_wel"),
        InlineKeyboardButton("⚠️ Spam limiti",      callback_data="s_spam"),
        InlineKeyboardButton("🕐 Ish vaqtini set",  callback_data="s_worktime"),
    )
    kb.add(InlineKeyboardButton("🔙 Asosiy menyu", callback_data="home"))
    return kb

def kb_faq():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("➕ Qoshish",  callback_data="faq_add"),
        InlineKeyboardButton("📋 Royxat",   callback_data="faq_list"),
        InlineKeyboardButton("🗑 Ochirish", callback_data="faq_del"),
    )
    kb.add(InlineKeyboardButton("🔙 Asosiy menyu", callback_data="home"))
    return kb

def kb_channel():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📝 Post yuborish",  callback_data="c_post"),
        InlineKeyboardButton("⏰ Rejalashtirish", callback_data="c_sched"),
        InlineKeyboardButton("📅 Rejalangan",     callback_data="c_list"),
    )
    kb.add(InlineKeyboardButton("🔙 Asosiy menyu", callback_data="home"))
    return kb

def kb_confirm(yes, no):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Ha",  callback_data=yes),
        InlineKeyboardButton("❌ Yoq", callback_data=no),
    )
    return kb

def kb_users():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📋 Royxat",           callback_data="u_list"),
        InlineKeyboardButton("🚫 Bloklash",          callback_data="u_blk"),
        InlineKeyboardButton("✅ Blokdan chiqarish", callback_data="u_ublk"),
        InlineKeyboardButton("🔴 Bloklangan",        callback_data="u_blklist"),
    )
    kb.add(InlineKeyboardButton("🔙 Asosiy menyu", callback_data="home"))
    return kb

def panel_text():
    d  = get_data()
    s  = get_stats()
    today = str(datetime.now().date())
    if s["date"] != today: s["today"] = 0
    orders  = get_orders()
    reviews = get_reviews()
    avg = 0
    if reviews:
        avg = round(sum(r["rating"] for r in reviews) / len(reviews), 1)
    st = "🟢 Yoqilgan" if d["active"] else "🔴 Ochiq emas"
    wt = "🟢 Yoqilgan" if d["work_active"] else "🔴 Off"
    return "\n".join([
        "👑 FUZZY BOT — Admin Panel",
        "━━━━━━━━━━━━━━━━━━━━━",
        "Bot: " + st + "  |  Ish vaqti: " + wt,
        "Foydalanuvchilar: " + str(len(d["users"])) + " ta",
        "Obunachi: " + str(len(d["subscribers"])) + " ta",
        "Bugungi xabarlar: " + str(s["today"]),
        "Jami xabarlar: " + str(s["total"]),
        "Buyurtmalar: " + str(len(orders)) + " ta",
        "Reyting: " + str(avg) + " / 5 (" + str(len(reviews)) + " ta)",
        "━━━━━━━━━━━━━━━━━━━━━",
        "Bolimni tanlang:",
    ])

# ════════════════════════════════════════
#   KLAVIATURALAR — FOYDALANUVCHI
# ════════════════════════════════════════
def kb_user_main(uid):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📌 FAQ",         callback_data="u_faq"),
        InlineKeyboardButton("📦 Buyurtma",    callback_data="u_order"),
        InlineKeyboardButton("⭐ Baho berish", callback_data="u_rate"),
        InlineKeyboardButton("🌐 Til",         callback_data="u_lang"),
        InlineKeyboardButton("🔔 Obuna",       callback_data="u_subscribe"),
    )
    return kb

def kb_lang():
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("🇺🇿 UZ", callback_data="lang_uz"),
        InlineKeyboardButton("🇷🇺 RU", callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 EN", callback_data="lang_en"),
    )
    return kb

def kb_rating():
    kb = InlineKeyboardMarkup(row_width=5)
    kb.add(
        InlineKeyboardButton("1⭐", callback_data="rate_1"),
        InlineKeyboardButton("2⭐", callback_data="rate_2"),
        InlineKeyboardButton("3⭐", callback_data="rate_3"),
        InlineKeyboardButton("4⭐", callback_data="rate_4"),
        InlineKeyboardButton("5⭐", callback_data="rate_5"),
    )
    return kb

# ════════════════════════════════════════
#   /START
# ════════════════════════════════════════
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    uid = msg.from_user.id
    if is_admin(uid):
        send(uid, "Xush kelibsiz Admin! Fuzzy Bot v9.0 ishga tayyor.")
        time.sleep(0.3)
        send(uid, panel_text(), kb_main())
    else:
        d = get_data()
        if not d["active"]: return
        register_user(msg.from_user)
        lang = get_lang(uid)
        welcome = d["welcome"].get(lang, d["welcome"]["uz"])
        send(uid, welcome, kb_user_main(uid))

# ════════════════════════════════════════
#   MEDIA HANDLER
# ════════════════════════════════════════
@bot.message_handler(content_types=[
    "sticker","photo","video","voice",
    "audio","document","location","contact"
])
def handle_media(msg):
    uid = msg.from_user.id
    if is_admin(uid): return
    d = get_data()
    if not d["active"]: return
    if uid in d["blocked"]: return
    if is_spam(uid):
        send(uid, tr(uid, "Juda tez!", "Слишком быстро!", "Too fast!")); return

    register_user(msg.from_user)
    record_stat(uid)

    turlar = {
        "sticker": "Stiker", "photo": "Rasm", "video": "Video",
        "voice": "Ovozli xabar", "audio": "Audio",
        "document": "Fayl", "location": "Joylashuv", "contact": "Kontakt"
    }
    notify_admin(msg.from_user, turlar.get(msg.content_type, "Media") + " yubordi")

    if not is_work_time():
        bot.reply_to(msg, d["work_msg"])
    else:
        bot.reply_to(msg, tr(uid,
            "Xabaringiz qabul qilindi! Tez orada javob beramiz.",
            "Ваше сообщение получено! Скоро ответим.",
            "Your message received! We'll reply soon."
        ))

# ════════════════════════════════════════
#   MATN XABARLARI
# ════════════════════════════════════════
@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_text(msg):
    uid  = msg.from_user.id
    text = msg.text.strip()

    # ── ADMIN HOLATLARI
    if is_admin(uid) and states.get(uid):
        st = states[uid]

        if st == "set_wel_uz":
            d = get_data(); d["welcome"]["uz"] = text; dump(DATA_FILE, d)
            states.pop(uid, None)
            send(uid, "✅ UZ xush kelibsiz saqlandi!", kb_back("s_wel_menu"))
            return

        elif st == "set_wel_ru":
            d = get_data(); d["welcome"]["ru"] = text; dump(DATA_FILE, d)
            states.pop(uid, None)
            send(uid, "✅ RU xush kelibsiz saqlandi!", kb_back("s_wel_menu"))
            return

        elif st == "set_wel_en":
            d = get_data(); d["welcome"]["en"] = text; dump(DATA_FILE, d)
            states.pop(uid, None)
            send(uid, "✅ EN xush kelibsiz saqlandi!", kb_back("s_wel_menu"))
            return

        elif st == "set_spam":
            try:
                n = int(text)
                if 1 <= n <= 20:
                    d = get_data(); d["spam_limit"] = n; dump(DATA_FILE, d)
                    states.pop(uid, None)
                    send(uid, "✅ Spam limiti: " + str(n), kb_back("m_set"))
                else:
                    send(uid, "1-20 oraligida kiriting.")
            except:
                send(uid, "Faqat raqam!")
            return

        elif st == "set_workmsg":
            d = get_data(); d["work_msg"] = text; dump(DATA_FILE, d)
            states.pop(uid, None)
            send(uid, "✅ Ish vaqti xabari saqlandi!", kb_back("m_set"))
            return

        elif st == "set_worktime":
            try:
                parts = text.split("-")
                s, e  = int(parts[0]), int(parts[1])
                if 0 <= s < e <= 24:
                    d = get_data()
                    d["work_start"] = s
                    d["work_end"]   = e
                    dump(DATA_FILE, d)
                    states.pop(uid, None)
                    send(uid, "✅ Ish vaqti: " + str(s) + ":00 - " + str(e) + ":00", kb_back("m_set"))
                else:
                    send(uid, "Notogri! Masalan: 9-18")
            except:
                send(uid, "Format: 9-18")
            return

        elif st == "faq_add_q":
            tmp[uid]    = {"q": text}
            states[uid] = "faq_add_a"
            send(uid, "Savol: " + text + "\n\nEndi javobni yozing:", kb_back("m_faq"))
            return

        elif st == "faq_add_a":
            q = tmp.get(uid, {}).get("q", "")
            if q:
                d = get_data(); d["faq"][q] = text; dump(DATA_FILE, d)
            states.pop(uid, None); tmp.pop(uid, None)
            send(uid, "✅ FAQ saqlandi!\nSavol: " + q + "\nJavob: " + text, kb_back("m_faq"))
            return

        elif st == "ch_post":
            states.pop(uid, None)
            try:
                bot.send_message(CHANNEL_ID, text)
                send(uid, "✅ Post kanalga yuborildi!", kb_back("m_ch"))
            except Exception as e:
                send(uid, "Xato: " + str(e), kb_back("m_ch"))
            return

        elif st == "sch_time":
            try:
                t = datetime.strptime(text, "%d.%m.%Y %H:%M")
                tmp[uid]    = {"time": t.strftime("%d.%m.%Y %H:%M")}
                states[uid] = "sch_txt"
                send(uid, "✅ Vaqt: " + text + "\n\nPost matnini yozing:", kb_back("m_ch"))
            except:
                send(uid, "Format: 25.12.2024 18:00")
            return

        elif st == "sch_txt":
            pt = tmp.get(uid, {}).get("time", "")
            if pt:
                posts = get_sched()
                posts.append({"time": pt, "text": text})
                dump(SCHED_FILE, posts)
            states.pop(uid, None); tmp.pop(uid, None)
            send(uid, "✅ Post rejalashtirildi! Vaqt: " + pt, kb_back("m_ch"))
            return

        elif st == "blk_id":
            states.pop(uid, None)
            try:
                bid = int(text)
                d   = get_data()
                if bid not in d["blocked"]:
                    d["blocked"].append(bid); dump(DATA_FILE, d)
                    send(uid, "🚫 " + str(bid) + " bloklandi.", kb_back("m_usr"))
                else:
                    send(uid, "Allaqachon bloklangan.", kb_back("m_usr"))
            except:
                send(uid, "Faqat ID (raqam)!", kb_back("m_usr"))
            return

        elif st == "bcast":
            tmp[uid] = {"text": text}
            states.pop(uid, None)
            d = get_data()
            send(uid,
                "📨 Broadcast tasdiqlash\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "Xabar:\n" + text[:100] + "\n\n"
                + str(len(d["users"])) + " ta foydalanuvchiga yuboriladi.",
                kb_confirm("bc_yes", "bc_no"))
            return

        elif st == "sub_msg":
            tmp[uid] = {"text": text}
            states.pop(uid, None)
            d = get_data()
            send(uid,
                "🔔 Obunachilarga yuborish\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "Xabar:\n" + text[:100] + "\n\n"
                + str(len(d["subscribers"])) + " ta obunachiga yuboriladi.",
                kb_confirm("sub_yes", "sub_no"))
            return

    # ── ADMIN — state yo'q
    if is_admin(uid): return

    # ── ODDIY FOYDALANUVCHI
    d = get_data()
    if not d["active"]: return
    if uid in d["blocked"]: return
    if is_spam(uid):
        send(uid, tr(uid, "Juda tez!", "Слишком быстро!", "Too fast!"))
        return

    register_user(msg.from_user)
    record_stat(uid)
    notify_admin(msg.from_user, "Xabar: " + clean(text))

    # FAQ tekshiruv
    faq = d.get("faq", {})
    t   = text.lower()
    for q, a in faq.items():
        if q.lower() in t:
            bot.reply_to(msg, a)
            return

    # Ish vaqti tekshiruv
    if not is_work_time():
        bot.reply_to(msg, d["work_msg"])
        return

    bot.reply_to(msg, tr(uid,
        "Xabaringiz qabul qilindi! Tez orada javob beramiz.",
        "Ваше сообщение получено! Скоро ответим.",
        "Your message received! We'll reply soon."
    ))

# ════════════════════════════════════════
#   CALLBACK QUERY
# ════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: True)
def handle_cb(call):
    uid = call.from_user.id
    cb  = call.data
    bot.answer_callback_query(call.id)

    # ── FOYDALANUVCHI CALLBACKLARI
    if cb == "u_faq":
        d = get_data()
        if not d.get("faq"):
            send(uid, tr(uid, "FAQ hali yoq.", "FAQ пусто.", "FAQ is empty."))
            return
        lines = [tr(uid, "📌 Tez-tez so'raladigan savollar:", "📌 FAQ:", "📌 FAQ:"), ""]
        for i, (q, a) in enumerate(d["faq"].items(), 1):
            lines.append(str(i) + ". " + q)
            lines.append("   " + a)
            lines.append("")
        send(uid, "\n".join(lines))
        return

    elif cb == "u_order":
        states[uid] = "order_name"
        send(uid, tr(uid,
            "📦 Buyurtma berish\n━━━━━━━━━━━━━━━━━━━━━\nIsm familiyangizni yozing:",
            "📦 Заказ\n━━━━━━━━━━━━━━━━━━━━━\nВведите ваше имя:",
            "📦 Order\n━━━━━━━━━━━━━━━━━━━━━\nEnter your name:"
        ))
        return

    elif cb == "u_rate":
        send(uid, tr(uid,
            "⭐ Xizmatimizga baho bering:",
            "⭐ Оцените наш сервис:",
            "⭐ Rate our service:"
        ), kb_rating())
        return

    elif cb.startswith("rate_"):
        stars = int(cb[5:])
        reviews = get_reviews()
        reviews.append({
            "uid":    uid,
            "name":   clean(call.from_user.first_name or ""),
            "rating": stars,
            "date":   datetime.now().strftime("%d.%m.%Y %H:%M")
        })
        dump(REVIEW_FILE, reviews)
        notify_admin(call.from_user, str(stars) + " ⭐ baho berdi", "⭐ Yangi baho!")
        send(uid, tr(uid,
            "✅ Rahmat! " + str(stars) + " ⭐ bahoingiz qabul qilindi.",
            "✅ Спасибо! Ваша оценка " + str(stars) + " ⭐ принята.",
            "✅ Thanks! Your " + str(stars) + " ⭐ rating received."
        ))
        return

    elif cb == "u_lang":
        send(uid, tr(uid, "Tilni tanlang:", "Выберите язык:", "Choose language:"), kb_lang())
        return

    elif cb.startswith("lang_"):
        lang = cb[5:]
        d    = get_data()
        key  = str(uid)
        if key in d["users"]:
            d["users"][key]["lang"] = lang
            dump(DATA_FILE, d)
        msgs = {"uz": "✅ Til: Uzbek", "ru": "✅ Язык: Русский", "en": "✅ Language: English"}
        send(uid, msgs.get(lang, "✅ OK"))
        return

    elif cb == "u_subscribe":
        d   = get_data()
        key = uid
        if key in d["subscribers"]:
            d["subscribers"].remove(key)
            dump(DATA_FILE, d)
            send(uid, tr(uid,
                "🔕 Obunadan chiqdingiz.",
                "🔕 Вы отписались.",
                "🔕 Unsubscribed."
            ))
        else:
            d["subscribers"].append(key)
            dump(DATA_FILE, d)
            send(uid, tr(uid,
                "🔔 Obuna bo'ldingiz! Yangiliklardan xabardor bo'lasiz.",
                "🔔 Вы подписались! Будете получать новости.",
                "🔔 Subscribed! You'll receive updates."
            ))
        return

    # ── ADMIN CALLBACKLARI
    if not is_admin(uid):
        bot.answer_callback_query(call.id, "Ruxsat yoq!")
        return

    # ASOSIY
    if cb == "home":
        edit_msg(call, panel_text(), kb_main())

    # STATISTIKA
    elif cb == "m_stat":
        d     = get_data()
        s     = get_stats()
        today = str(datetime.now().date())
        if s["date"] != today: s["today"] = 0
        top   = sorted(s["counts"].items(), key=lambda x: x[1], reverse=True)[:5]
        top_t = ""
        for i, (k, v) in enumerate(top, 1):
            info  = d["users"].get(k, {})
            top_t += "  " + str(i) + ". " + clean(info.get("name","?")) + " — " + str(v) + "\n"
        reviews = get_reviews()
        avg = round(sum(r["rating"] for r in reviews)/len(reviews), 1) if reviews else 0
        lines = [
            "📊 Statistika",
            "━━━━━━━━━━━━━━━━━━━━━",
            "Jami xabarlar: " + str(s["total"]),
            "Bugun: " + str(s["today"]),
            "Foydalanuvchilar: " + str(len(d["users"])),
            "Obunachi: " + str(len(d["subscribers"])),
            "Bloklangan: " + str(len(d["blocked"])),
            "Buyurtmalar: " + str(len(get_orders())),
            "Reytinglar: " + str(len(reviews)) + " ta | Ort: " + str(avg) + "/5",
            "Rejalangan post: " + str(len(get_sched())),
            "━━━━━━━━━━━━━━━━━━━━━",
            "Top 5:",
            top_t if top_t else "  Hali yoq"
        ]
        edit_msg(call, "\n".join(lines), kb_back("home"))

    # FOYDALANUVCHILAR
    elif cb == "m_usr":
        d = get_data()
        edit_msg(call,
            "👥 Foydalanuvchilar\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Jami: " + str(len(d["users"])) + " ta\n"
            "Bloklangan: " + str(len(d["blocked"])) + " ta",
            kb_users())

    elif cb == "u_list":
        d = get_data()
        if not d["users"]:
            edit_msg(call, "Hali foydalanuvchi yoq.", kb_back("m_usr")); return
        lines = ["👥 Songi 15:", "━━━━━━━━━━━━━━━━━━━━━", ""]
        for info in list(d["users"].values())[-15:]:
            un = "@" + clean(info["username"]) if info["username"] else "—"
            lines.append(clean(info["name"]) + " " + un)
            lines.append("ID: " + str(info["id"]) + " | " + info["joined"])
            lines.append("")
        edit_msg(call, "\n".join(lines), kb_back("m_usr"))

    elif cb == "u_blk":
        states[uid] = "blk_id"
        edit_msg(call, "🚫 Bloklash uchun ID yozing:", kb_back("m_usr"))

    elif cb == "u_ublk":
        d = get_data()
        if not d["blocked"]:
            edit_msg(call, "Bloklangan yoq.", kb_back("m_usr")); return
        kb = InlineKeyboardMarkup()
        for bid in d["blocked"]:
            info = d["users"].get(str(bid), {})
            kb.add(InlineKeyboardButton("✅ " + clean(info.get("name", str(bid))), callback_data="ubk_" + str(bid)))
        kb.add(InlineKeyboardButton("🔙 Ortga", callback_data="m_usr"))
        edit_msg(call, "Blokdan chiqarish:", kb)

    elif cb.startswith("ubk_"):
        bid = int(cb[4:])
        d   = get_data()
        if bid in d["blocked"]: d["blocked"].remove(bid); dump(DATA_FILE, d)
        edit_msg(call, "✅ " + str(bid) + " blokdan chiqarildi!", kb_back("m_usr"))

    elif cb == "u_blklist":
        d = get_data()
        if not d["blocked"]:
            edit_msg(call, "Bloklangan yoq.", kb_back("m_usr")); return
        lines = ["🔴 Bloklangan:", ""]
        for bid in d["blocked"]:
            info = d["users"].get(str(bid), {})
            lines.append("🚫 " + clean(info.get("name","?")) + " — " + str(bid))
        edit_msg(call, "\n".join(lines), kb_back("m_usr"))

    # BUYURTMALAR
    elif cb == "m_orders":
        orders = get_orders()
        if not orders:
            edit_msg(call, "Hali buyurtma yoq.", kb_back("home")); return
        lines = ["📦 Buyurtmalar (" + str(len(orders)) + " ta):", "━━━━━━━━━━━━━━━━━━━━━", ""]
        for i, o in enumerate(orders[-20:], 1):
            lines.append(str(i) + ". " + clean(o.get("name","?")) + " | " + o.get("date",""))
            lines.append("   " + clean(o.get("product","")) + " | " + o.get("status","yangi"))
            lines.append("")
        edit_msg(call, "\n".join(lines), kb_back("home"))

    # REYTINGLAR
    elif cb == "m_reviews":
        reviews = get_reviews()
        if not reviews:
            edit_msg(call, "Hali baho yoq.", kb_back("home")); return
        avg   = round(sum(r["rating"] for r in reviews)/len(reviews), 1)
        lines = ["⭐ Reytinglar", "━━━━━━━━━━━━━━━━━━━━━",
                 "Umumiy: " + str(avg) + "/5 (" + str(len(reviews)) + " ta)", ""]
        for r in reviews[-10:]:
            stars = "⭐" * r["rating"]
            lines.append(clean(r.get("name","?")) + " — " + stars + " | " + r.get("date",""))
        edit_msg(call, "\n".join(lines), kb_back("home"))

    # FAQ
    elif cb == "m_faq":
        d = get_data()
        edit_msg(call,
            "📌 FAQ boshqaruvi\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Jami: " + str(len(d.get("faq",{}))) + " ta savol",
            kb_faq())

    elif cb == "faq_add":
        states[uid] = "faq_add_q"
        edit_msg(call, "Savol matnini yozing:", kb_back("m_faq"))

    elif cb == "faq_list":
        d = get_data()
        if not d.get("faq"):
            edit_msg(call, "FAQ yoq.", kb_back("m_faq")); return
        lines = ["📌 FAQ royxati:", "━━━━━━━━━━━━━━━━━━━━━", ""]
        for i, (q, a) in enumerate(d["faq"].items(), 1):
            lines.append(str(i) + ". " + q)
            lines.append("   " + a[:60])
            lines.append("")
        edit_msg(call, "\n".join(lines), kb_back("m_faq"))

    elif cb == "faq_del":
        d = get_data()
        if not d.get("faq"):
            edit_msg(call, "FAQ yoq.", kb_back("m_faq")); return
        kb = InlineKeyboardMarkup()
        for q in d["faq"]:
            kb.add(InlineKeyboardButton("🗑 " + q[:30], callback_data="fdel_" + q))
        kb.add(InlineKeyboardButton("🔙 Ortga", callback_data="m_faq"))
        edit_msg(call, "Qaysi savolni ochirish?", kb)

    elif cb.startswith("fdel_"):
        q = cb[5:]
        d = get_data()
        if q in d["faq"]: del d["faq"][q]; dump(DATA_FILE, d)
        edit_msg(call, "✅ " + q + " ochirildi!", kb_back("m_faq"))

    # KANAL
    elif cb == "m_ch":
        edit_msg(call,
            "📢 Kanal: " + CHANNEL_ID + "\n"
            "Rejalangan: " + str(len(get_sched())) + " ta",
            kb_channel())

    elif cb == "c_post":
        states[uid] = "ch_post"
        edit_msg(call, "📝 Post matnini yozing:", kb_back("m_ch"))

    elif cb == "c_sched":
        states[uid] = "sch_time"
        edit_msg(call, "⏰ Vaqtni kiriting:\nFormat: 25.12.2024 18:00", kb_back("m_ch"))

    elif cb == "c_list":
        posts = get_sched()
        if not posts:
            edit_msg(call, "Rejalangan post yoq.", kb_back("m_ch")); return
        lines = ["📅 Rejalangan:", ""]
        kb = InlineKeyboardMarkup()
        for i, p in enumerate(posts):
            lines.append(str(i+1) + ". " + p["time"] + " — " + p["text"][:30])
            kb.add(InlineKeyboardButton("❌ " + str(i+1) + "-ni ochirish", callback_data="dsc_" + str(i)))
        kb.add(InlineKeyboardButton("🔙 Ortga", callback_data="m_ch"))
        edit_msg(call, "\n".join(lines), kb)

    elif cb.startswith("dsc_"):
        idx = int(cb[4:])
        posts = get_sched()
        if 0 <= idx < len(posts): posts.pop(idx); dump(SCHED_FILE, posts)
        edit_msg(call, "✅ Post ochirildi!", kb_back("m_ch"))

    # BROADCAST
    elif cb == "m_bc":
        d = get_data()
        states[uid] = "bcast"
        edit_msg(call,
            "📨 Broadcast\n"
            "Barcha " + str(len(d["users"])) + " foydalanuvchiga xabar yozing:",
            kb_back("home"))

    elif cb == "bc_yes":
        text = tmp.get(uid, {}).get("text", "")
        if not text: edit_msg(call, "Xabar topilmadi.", kb_back("home")); return
        d = get_data(); sent = failed = 0
        for user_id in d["users"]:
            try: bot.send_message(int(user_id), text); sent += 1; time.sleep(0.05)
            except: failed += 1
        tmp.pop(uid, None)
        edit_msg(call, "✅ Broadcast!\nYuborildi: " + str(sent) + "\nXato: " + str(failed), kb_back("home"))

    elif cb == "bc_no":
        tmp.pop(uid, None)
        edit_msg(call, "Bekor qilindi.", kb_main())

    # OBUNA
    elif cb == "m_sub":
        d = get_data()
        states[uid] = "sub_msg"
        edit_msg(call,
            "🔔 Obuna xabari\n"
            "Obunachilarga yubormoqchi bo'lgan xabarni yozing:\n"
            "(" + str(len(d["subscribers"])) + " ta obunachi)",
            kb_back("home"))

    elif cb == "sub_yes":
        text = tmp.get(uid, {}).get("text", "")
        if not text: edit_msg(call, "Xabar topilmadi.", kb_back("home")); return
        d = get_data(); sent = failed = 0
        for sub_id in d["subscribers"]:
            try: bot.send_message(int(sub_id), "🔔 Yangilik!\n\n" + text); sent += 1; time.sleep(0.05)
            except: failed += 1
        tmp.pop(uid, None)
        edit_msg(call, "✅ Obunachilarga yuborildi!\nYuborildi: " + str(sent), kb_back("home"))

    elif cb == "sub_no":
        tmp.pop(uid, None)
        edit_msg(call, "Bekor qilindi.", kb_main())

    # SOZLAMALAR
    elif cb == "m_set":
        edit_msg(call,
            "⚙️ Sozlamalar\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Barcha sozlamalar quyida:",
            kb_settings())

    elif cb == "s_tog":
        d = get_data(); d["active"] = not d["active"]; dump(DATA_FILE, d)
        bot.answer_callback_query(call.id, "Bot " + ("Yoqildi!" if d["active"] else "Ochiq emas!"))
        edit_msg(call, "⚙️ Sozlamalar:", kb_settings())

    elif cb == "s_work":
        d = get_data(); d["work_active"] = not d["work_active"]; dump(DATA_FILE, d)
        bot.answer_callback_query(call.id, "Ish vaqti " + ("Yoqildi!" if d["work_active"] else "Off!"))
        edit_msg(call, "⚙️ Sozlamalar:", kb_settings())

    elif cb == "s_wel":
        kb = InlineKeyboardMarkup(row_width=3)
        kb.add(
            InlineKeyboardButton("🇺🇿 UZ", callback_data="s_wel_uz"),
            InlineKeyboardButton("🇷🇺 RU", callback_data="s_wel_ru"),
            InlineKeyboardButton("🇬🇧 EN", callback_data="s_wel_en"),
        )
        kb.add(InlineKeyboardButton("🔙 Ortga", callback_data="m_set"))
        edit_msg(call, "Qaysi tilda xush kelibsiz o'zgartirish?", kb)

    elif cb == "s_wel_uz":
        states[uid] = "set_wel_uz"
        d = get_data()
        edit_msg(call, "UZ xush kelibsiz:\n" + d["welcome"]["uz"] + "\n\nYangi matn:", kb_back("m_set"))

    elif cb == "s_wel_ru":
        states[uid] = "set_wel_ru"
        d = get_data()
        edit_msg(call, "RU xush kelibsiz:\n" + d["welcome"]["ru"] + "\n\nYangi matn:", kb_back("m_set"))

    elif cb == "s_wel_en":
        states[uid] = "set_wel_en"
        d = get_data()
        edit_msg(call, "EN xush kelibsiz:\n" + d["welcome"]["en"] + "\n\nYangi matn:", kb_back("m_set"))

    elif cb == "s_spam":
        states[uid] = "set_spam"
        d = get_data()
        edit_msg(call, "Hozirgi: " + str(d["spam_limit"]) + "\nYangi raqam (1-20):", kb_back("m_set"))

    elif cb == "s_worktime":
        states[uid] = "set_worktime"
        d = get_data()
        edit_msg(call,
            "Hozirgi: " + str(d["work_start"]) + ":00 - " + str(d["work_end"]) + ":00\n\n"
            "Format: boshlanish-tugash\nMasolan: 9-18",
            kb_back("m_set"))

# ════════════════════════════════════════
#   BUYURTMA HOLATLARI
# ════════════════════════════════════════
@bot.message_handler(func=lambda m: states.get(m.from_user.id, "").startswith("order_"))
def handle_order(msg):
    uid  = msg.from_user.id
    text = msg.text.strip()
    st   = states[uid]

    if st == "order_name":
        tmp[uid]    = {"name": text}
        states[uid] = "order_product"
        send(uid, tr(uid,
            "Mahsulot/xizmat nomini yozing:",
            "Введите название товара/услуги:",
            "Enter product/service name:"
        ))

    elif st == "order_product":
        tmp[uid]["product"] = text
        states[uid] = "order_phone"
        send(uid, tr(uid,
            "Telefon raqamingizni yozing:",
            "Введите номер телефона:",
            "Enter your phone number:"
        ))

    elif st == "order_phone":
        tmp[uid]["phone"] = text
        states[uid] = "order_note"
        send(uid, tr(uid,
            "Qo'shimcha izoh (yoki 'yoq' deb yozing):",
            "Дополнительный комментарий (или напишите 'нет'):",
            "Additional note (or write 'no'):"
        ))

    elif st == "order_note":
        info     = tmp.get(uid, {})
        orders   = get_orders()
        order_id = len(orders) + 1
        order    = {
            "id":      order_id,
            "uid":     uid,
            "name":    info.get("name", ""),
            "product": info.get("product", ""),
            "phone":   info.get("phone", ""),
            "note":    text if text.lower() not in ["yoq","нет","no"] else "",
            "status":  "yangi",
            "date":    datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        orders.append(order)
        dump(ORDER_FILE, orders)
        states.pop(uid, None)
        tmp.pop(uid, None)

        send(uid, tr(uid,
            "✅ Buyurtmangiz qabul qilindi! #" + str(order_id) + "\nTez orada bog'lanamiz.",
            "✅ Заказ принят! #" + str(order_id) + "\nСкоро свяжемся.",
            "✅ Order accepted! #" + str(order_id) + "\nWe'll contact you soon."
        ), kb_user_main(uid))

        notify_admin(msg.from_user,
            "📦 Yangi buyurtma #" + str(order_id) + "\n"
            "Mahsulot: " + clean(order["product"]) + "\n"
            "Tel: " + clean(order["phone"]) + "\n"
            "Izoh: " + clean(order["note"]),
            "📦 Yangi buyurtma!")

# ════════════════════════════════════════
#   REJALI POSTLAR
# ════════════════════════════════════════
def run_scheduler():
    while True:
        try:
            posts = get_sched()
            now   = datetime.now().strftime("%d.%m.%Y %H:%M")
            left  = []
            for p in posts:
                if p["time"] <= now:
                    try:
                        bot.send_message(CHANNEL_ID, p["text"])
                        bot.send_message(ADMIN_ID, "✅ Post yuborildi!\n" + p["text"][:60])
                    except: pass
                else:
                    left.append(p)
            if len(left) != len(posts):
                dump(SCHED_FILE, left)
        except: pass
        time.sleep(30)

# ════════════════════════════════════════
#   KUNLIK HISOBOT
# ════════════════════════════════════════
def daily_report():
    while True:
        now = datetime.now()
        # Har kuni soat 21:00 da
        target = now.replace(hour=21, minute=0, second=0)
        if now >= target:
            target += timedelta(days=1)
        time.sleep((target - now).seconds)

        try:
            s       = get_stats()
            d       = get_data()
            orders  = get_orders()
            reviews = get_reviews()
            today   = str(datetime.now().date())
            today_orders  = [o for o in orders  if o.get("date","").startswith(today[:10])]
            today_reviews = [r for r in reviews if r.get("date","").startswith(today[:10])]
            avg = round(sum(r["rating"] for r in today_reviews)/len(today_reviews),1) if today_reviews else 0

            bot.send_message(ADMIN_ID,
                "📈 Kunlik hisobot — " + today + "\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "Xabarlar: " + str(s.get("today", 0)) + " ta\n"
                "Yangi foydalanuvchi: " + str(len([u for u in d["users"].values() if today in u.get("joined","")])) + " ta\n"
                "Buyurtmalar: " + str(len(today_orders)) + " ta\n"
                "Reytinglar: " + str(len(today_reviews)) + " ta | Ort: " + str(avg) + "/5\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "Jami foydalanuvchi: " + str(len(d["users"])) + " ta\n"
                "Obunachi: " + str(len(d["subscribers"])) + " ta"
            )
        except: pass

# ════════════════════════════════════════
#   ISHGA TUSHIRISH
# ════════════════════════════════════════
if __name__ == "__main__":
    print("╔══════════════════════════════╗")
    print("║   FUZZY BOT v9.0  🦊  ✅    ║")
    print("║   Admin:", ADMIN_ID, "      ║")
    print("║   Kanal:", CHANNEL_ID, "          ║")
    print("╚══════════════════════════════╝")

    threading.Thread(target=run_scheduler, daemon=True).start()
    threading.Thread(target=daily_report,  daemon=True).start()

    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            print("Polling xato:", e)
            time.sleep(5)
