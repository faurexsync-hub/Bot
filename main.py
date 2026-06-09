#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# FUZZY BOT v7.0 — Railway Ready

import telebot
import json
import os
import time
import threading
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ─────────────────────────────────────
#  SOZLAMALAR
# ─────────────────────────────────────
BOT_TOKEN  = os.environ.get("BOT_TOKEN", "BU_YERGA_TOKEN_YOZING")
ADMIN_ID   = int(os.environ.get("ADMIN_ID", "8355611778"))
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@fuzzssss")

DATA_FILE  = "/tmp/data.json"
STATS_FILE = "/tmp/stats.json"
SCHED_FILE = "/tmp/sched.json"

# ─────────────────────────────────────
#  MA'LUMOTLAR
# ─────────────────────────────────────
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
        "replies": {},
        "default_reply": "Xabaringiz qabul qilindi! Tez orada javob beramiz.",
        "welcome": "Salom! Fuzzy botga xush kelibsiz!",
        "users": {},
        "blocked": [],
        "spam_limit": 5,
        "active": True
    })

def get_stats():
    return load(STATS_FILE, {
        "total": 0,
        "today": 0,
        "date": str(datetime.now().date()),
        "counts": {}
    })

def get_sched():
    return load(SCHED_FILE, [])

# ─────────────────────────────────────
#  BOT VA GLOBAL STATE
# ─────────────────────────────────────
bot       = telebot.TeleBot(BOT_TOKEN)
states    = {}   # {uid: "holat_nomi"}
tmp       = {}   # {uid: {...vaqtinchalik ma'lumot...}}
spam_log  = {}   # {uid: [timestamp, ...]}

# ─────────────────────────────────────
#  YORDAMCHI FUNKSIYALAR
# ─────────────────────────────────────
def clean(text):
    """Markdown belgilarini olib tashlaydi"""
    if not text:
        return ""
    for ch in ["_", "*", "`", "[", "]", "~"]:
        text = str(text).replace(ch, "")
    return text

def is_admin(uid):
    return uid == ADMIN_ID

def register_user(user):
    d = get_data()
    key = str(user.id)
    if key not in d["users"]:
        first = user.first_name or ""
        last  = user.last_name  or ""
        name  = (first + " " + last).strip() or "Nomsiz"
        d["users"][key] = {
            "id":       user.id,
            "name":     name,
            "username": user.username or "",
            "joined":   datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        dump(DATA_FILE, d)

def record_stat(uid):
    s = get_stats()
    today = str(datetime.now().date())
    if s["date"] != today:
        s["today"] = 0
        s["date"]  = today
    s["total"] += 1
    s["today"] += 1
    s["counts"][str(uid)] = s["counts"].get(str(uid), 0) + 1
    dump(STATS_FILE, s)

def is_spam(uid):
    d = get_data()
    key = str(uid)
    now = time.time()
    spam_log.setdefault(key, [])
    spam_log[key] = [t for t in spam_log[key] if now - t < 60]
    spam_log[key].append(now)
    return len(spam_log[key]) > d["spam_limit"]

def find_reply(text):
    d = get_data()
    t = (text or "").lower()
    for keyword, reply in d["replies"].items():
        if keyword.lower() in t:
            return reply
    return d["default_reply"]

def send(chat_id, text, kb=None):
    try:
        bot.send_message(chat_id, text, reply_markup=kb)
    except Exception as e:
        print("send error:", e)

def edit_msg(call, text, kb=None):
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb
        )
    except:
        send(call.message.chat.id, text, kb)

# ─────────────────────────────────────
#  KLAVIATURALAR
# ─────────────────────────────────────
def kb_main():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💬 Auto-javoblar",    callback_data="m_rep"),
        InlineKeyboardButton("📢 Kanal",            callback_data="m_ch"),
        InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="m_usr"),
        InlineKeyboardButton("📊 Statistika",       callback_data="m_stat"),
        InlineKeyboardButton("⚙️ Sozlamalar",       callback_data="m_set"),
        InlineKeyboardButton("📨 Broadcast",        callback_data="m_bc"),
    )
    return kb

def kb_back(to="home"):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Asosiy menyu", callback_data=to))
    return kb

def kb_replies():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("➕ Qoshish",   callback_data="r_add"),
        InlineKeyboardButton("📋 Royxat",    callback_data="r_list"),
        InlineKeyboardButton("🗑 Ochirish",  callback_data="r_del"),
        InlineKeyboardButton("✏️ Standart",  callback_data="r_def"),
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

def kb_settings():
    d  = get_data()
    st = "🟢 Yoqilgan" if d["active"] else "🔴 Ochiq emas"
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🤖 Bot: " + st,    callback_data="s_tog"),
        InlineKeyboardButton("🔔 Xush kelibsiz", callback_data="s_wel"),
        InlineKeyboardButton("⚠️ Spam limiti",   callback_data="s_spam"),
    )
    kb.add(InlineKeyboardButton("🔙 Asosiy menyu", callback_data="home"))
    return kb

def kb_confirm(yes_cb, no_cb):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Ha",  callback_data=yes_cb),
        InlineKeyboardButton("❌ Yoq", callback_data=no_cb),
    )
    return kb

def panel_text():
    d  = get_data()
    s  = get_stats()
    today = str(datetime.now().date())
    if s["date"] != today:
        s["today"] = 0
    st = "🟢 Yoqilgan" if d["active"] else "🔴 Ochiq emas"
    lines = [
        "👑 FUZZY BOT — Admin Panel",
        "━━━━━━━━━━━━━━━━━━━━━",
        "Bot holati: " + st,
        "Foydalanuvchilar: " + str(len(d["users"])) + " ta",
        "Kalit sozlar: " + str(len(d["replies"])) + " ta",
        "Bugungi xabarlar: " + str(s["today"]),
        "Jami xabarlar: " + str(s["total"]),
        "━━━━━━━━━━━━━━━━━━━━━",
        "Bolimni tanlang:"
    ]
    return "\n".join(lines)

# ─────────────────────────────────────
#  /START
# ─────────────────────────────────────
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    uid = msg.from_user.id
    if is_admin(uid):
        send(uid, "Xush kelibsiz Admin! Fuzzy Bot ishga tayyor.")
        time.sleep(0.3)
        send(uid, panel_text(), kb_main())
    else:
        d = get_data()
        if not d["active"]:
            return
        register_user(msg.from_user)
        send(uid, d["welcome"])

# ─────────────────────────────────────
#  CALLBACK QUERY
# ─────────────────────────────────────
@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    uid = call.from_user.id
    if not is_admin(uid):
        bot.answer_callback_query(call.id, "Ruxsat yoq!")
        return
    bot.answer_callback_query(call.id)
    cb = call.data

    # ── Asosiy menyu
    if cb == "home":
        edit_msg(call, panel_text(), kb_main())

    # ── Auto-javoblar
    elif cb == "m_rep":
        d = get_data()
        edit_msg(call,
            "💬 Auto-javoblar bolimi\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Jami: " + str(len(d["replies"])) + " ta\n"
            "Standart javob:\n" + d["default_reply"][:50] + "\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Amalni tanlang:",
            kb_replies())

    elif cb == "r_add":
        states[uid] = "add_kw"
        edit_msg(call,
            "➕ Yangi auto-javob qoshish\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "1. Avval kalit sozni yozing\n"
            "Masalan: narx, buyurtma, manzil",
            kb_back("m_rep"))

    elif cb == "r_list":
        d = get_data()
        if not d["replies"]:
            edit_msg(call, "Hali kalit soz qoshilmagan.", kb_back("m_rep"))
            return
        lines = ["📋 Barcha auto-javoblar:", "━━━━━━━━━━━━━━━━━━━━━", ""]
        for i, (k, v) in enumerate(d["replies"].items(), 1):
            lines.append(str(i) + ". " + k)
            lines.append("   " + v[:60])
            lines.append("")
        edit_msg(call, "\n".join(lines), kb_back("m_rep"))

    elif cb == "r_del":
        d = get_data()
        if not d["replies"]:
            edit_msg(call, "Ochiriladigan kalit soz yoq.", kb_back("m_rep"))
            return
        kb = InlineKeyboardMarkup()
        for k in d["replies"]:
            kb.add(InlineKeyboardButton("🗑 " + k, callback_data="dk_" + k))
        kb.add(InlineKeyboardButton("🔙 Ortga", callback_data="m_rep"))
        edit_msg(call, "Qaysi kalit sozni ochirish?", kb)

    elif cb.startswith("dk_"):
        kw = cb[3:]
        d  = get_data()
        if kw in d["replies"]:
            del d["replies"][kw]
            dump(DATA_FILE, d)
            edit_msg(call, "✅ " + kw + " ochirildi!", kb_back("m_rep"))
        else:
            edit_msg(call, "Topilmadi.", kb_back("m_rep"))

    elif cb == "r_def":
        d = get_data()
        states[uid] = "set_def"
        edit_msg(call,
            "✏️ Standart javobni ozgartirish\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Hozirgi:\n" + d["default_reply"] + "\n\n"
            "Yangi standart javobni yozing:",
            kb_back("m_rep"))

    # ── Kanal
    elif cb == "m_ch":
        edit_msg(call,
            "📢 Kanal boshqaruvi\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Kanal: " + CHANNEL_ID + "\n"
            "Rejalangan postlar: " + str(len(get_sched())) + " ta\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Amalni tanlang:",
            kb_channel())

    elif cb == "c_post":
        states[uid] = "ch_post"
        edit_msg(call,
            "📝 Kanalga post yuborish\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Post matnini yozing:",
            kb_back("m_ch"))

    elif cb == "c_sched":
        states[uid] = "sch_time"
        edit_msg(call,
            "⏰ Post rejalashtirish\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Vaqtni kiriting:\nFormat: KK.OO.YYYY SS:DD\n"
            "Misol: 25.12.2024 18:00",
            kb_back("m_ch"))

    elif cb == "c_list":
        posts = get_sched()
        if not posts:
            edit_msg(call, "Rejalangan post yoq.", kb_back("m_ch"))
            return
        lines = ["📅 Rejalangan postlar:", "━━━━━━━━━━━━━━━━━━━━━", ""]
        kb = InlineKeyboardMarkup()
        for i, p in enumerate(posts):
            lines.append(str(i+1) + ". " + p["time"])
            lines.append("   " + p["text"][:40])
            lines.append("")
            kb.add(InlineKeyboardButton(
                "❌ " + str(i+1) + "-ni ochirish",
                callback_data="dsc_" + str(i)
            ))
        kb.add(InlineKeyboardButton("🔙 Ortga", callback_data="m_ch"))
        edit_msg(call, "\n".join(lines), kb)

    elif cb.startswith("dsc_"):
        idx   = int(cb[4:])
        posts = get_sched()
        if 0 <= idx < len(posts):
            posts.pop(idx)
            dump(SCHED_FILE, posts)
        edit_msg(call, "✅ Rejalangan post ochirildi!", kb_back("m_ch"))

    # ── Foydalanuvchilar
    elif cb == "m_usr":
        d = get_data()
        edit_msg(call,
            "👥 Foydalanuvchilar\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Jami: " + str(len(d["users"])) + " ta\n"
            "Bloklangan: " + str(len(d["blocked"])) + " ta\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Amalni tanlang:",
            kb_users())

    elif cb == "u_list":
        d = get_data()
        if not d["users"]:
            edit_msg(call, "Hali foydalanuvchi yoq.", kb_back("m_usr"))
            return
        lines = ["👥 So'nggi 15 foydalanuvchi:", "━━━━━━━━━━━━━━━━━━━━━", ""]
        for info in list(d["users"].values())[-15:]:
            un = "@" + clean(info["username"]) if info["username"] else "—"
            lines.append(clean(info["name"]) + " " + un)
            lines.append("ID: " + str(info["id"]) + " | " + info["joined"])
            lines.append("")
        edit_msg(call, "\n".join(lines), kb_back("m_usr"))

    elif cb == "u_blk":
        states[uid] = "blk_id"
        edit_msg(call,
            "🚫 Foydalanuvchi bloklash\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Foydalanuvchi ID sini yozing:",
            kb_back("m_usr"))

    elif cb == "u_ublk":
        d = get_data()
        if not d["blocked"]:
            edit_msg(call, "Bloklangan foydalanuvchi yoq.", kb_back("m_usr"))
            return
        kb = InlineKeyboardMarkup()
        for bid in d["blocked"]:
            info = d["users"].get(str(bid), {})
            name = clean(info.get("name", str(bid)))
            kb.add(InlineKeyboardButton(
                "✅ " + name + " (" + str(bid) + ")",
                callback_data="ubk_" + str(bid)
            ))
        kb.add(InlineKeyboardButton("🔙 Ortga", callback_data="m_usr"))
        edit_msg(call, "Blokdan chiqarish — kimni?", kb)

    elif cb.startswith("ubk_"):
        bid = int(cb[4:])
        d   = get_data()
        if bid in d["blocked"]:
            d["blocked"].remove(bid)
            dump(DATA_FILE, d)
        edit_msg(call, "✅ " + str(bid) + " blokdan chiqarildi!", kb_back("m_usr"))

    elif cb == "u_blklist":
        d = get_data()
        if not d["blocked"]:
            edit_msg(call, "Bloklangan foydalanuvchi yoq.", kb_back("m_usr"))
            return
        lines = ["🔴 Bloklangan foydalanuvchilar:", "━━━━━━━━━━━━━━━━━━━━━", ""]
        for bid in d["blocked"]:
            info = d["users"].get(str(bid), {})
            lines.append("🚫 " + clean(info.get("name", "?")) + " — " + str(bid))
        edit_msg(call, "\n".join(lines), kb_back("m_usr"))

    # ── Statistika
    elif cb == "m_stat":
        d     = get_data()
        s     = get_stats()
        today = str(datetime.now().date())
        if s["date"] != today:
            s["today"] = 0
        top   = sorted(s["counts"].items(), key=lambda x: x[1], reverse=True)[:5]
        lines = [
            "📊 Statistika",
            "━━━━━━━━━━━━━━━━━━━━━",
            "Jami xabarlar: " + str(s["total"]),
            "Bugun: " + str(s["today"]),
            "Foydalanuvchilar: " + str(len(d["users"])),
            "Bloklangan: " + str(len(d["blocked"])),
            "Kalit sozlar: " + str(len(d["replies"])),
            "Rejalangan post: " + str(len(get_sched())),
            "━━━━━━━━━━━━━━━━━━━━━",
            "Top 5 faol:",
        ]
        if top:
            for i, (k, v) in enumerate(top, 1):
                info = d["users"].get(k, {})
                lines.append("  " + str(i) + ". " + clean(info.get("name", "?")) + " — " + str(v) + " xabar")
        else:
            lines.append("  Hali yoq")
        edit_msg(call, "\n".join(lines), kb_back("home"))

    # ── Sozlamalar
    elif cb == "m_set":
        d  = get_data()
        st = "🟢 Yoqilgan" if d["active"] else "🔴 Ochiq emas"
        edit_msg(call,
            "⚙️ Sozlamalar\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Bot holati: " + st + "\n"
            "Spam limiti: " + str(d["spam_limit"]) + " xabar/daqiqa\n"
            "Xush kelibsiz:\n" + d["welcome"][:50] + "\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Nimani ozgartirish?",
            kb_settings())

    elif cb == "s_tog":
        d          = get_data()
        d["active"] = not d["active"]
        dump(DATA_FILE, d)
        msg_txt = "Bot Yoqildi!" if d["active"] else "Bot Ochiq emas!"
        bot.answer_callback_query(call.id, msg_txt)
        st = "🟢 Yoqilgan" if d["active"] else "🔴 Ochiq emas"
        edit_msg(call,
            "⚙️ Sozlamalar\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Bot holati: " + st + "\n"
            "Spam limiti: " + str(d["spam_limit"]) + " xabar/daqiqa\n"
            "Xush kelibsiz:\n" + d["welcome"][:50] + "\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Nimani ozgartirish?",
            kb_settings())

    elif cb == "s_wel":
        states[uid] = "set_wel"
        d = get_data()
        edit_msg(call,
            "🔔 Xush kelibsiz xabarini ozgartirish\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Hozirgi:\n" + d["welcome"] + "\n\n"
            "Yangi xabarni yozing:",
            kb_back("m_set"))

    elif cb == "s_spam":
        states[uid] = "set_spam"
        d = get_data()
        edit_msg(call,
            "⚠️ Spam limitini ozgartirish\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Hozirgi: " + str(d["spam_limit"]) + " xabar/daqiqa\n\n"
            "Yangi raqam (1-20):",
            kb_back("m_set"))

    # ── Broadcast
    elif cb == "m_bc":
        d = get_data()
        states[uid] = "bcast"
        edit_msg(call,
            "📨 Broadcast\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Barcha " + str(len(d["users"])) + " foydalanuvchiga\n"
            "yuboriladigan xabarni yozing:",
            kb_back("home"))

    elif cb == "bc_yes":
        text = tmp.get(uid, {}).get("text", "")
        if not text:
            edit_msg(call, "Xabar topilmadi.", kb_back("home"))
            return
        d      = get_data()
        sent   = 0
        failed = 0
        for user_id in d["users"]:
            try:
                bot.send_message(int(user_id), text)
                sent += 1
                time.sleep(0.05)
            except:
                failed += 1
        tmp.pop(uid, None)
        edit_msg(call,
            "✅ Broadcast yakunlandi!\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Yuborildi: " + str(sent) + "\n"
            "Xato: " + str(failed),
            kb_back("home"))

    elif cb == "bc_no":
        tmp.pop(uid, None)
        edit_msg(call, "Broadcast bekor qilindi.", kb_main())

# ─────────────────────────────────────
#  BARCHA MATN XABARLARI
# ─────────────────────────────────────
@bot.message_handler(content_types=["sticker"])
def handle_sticker(msg):
    uid = msg.from_user.id
    d   = get_data()
    if not d["active"]: return
    if uid in d["blocked"]: return
    if is_admin(uid): return

    register_user(msg.from_user)
    record_stat(uid)

    try:
        u    = msg.from_user
        name = clean(((u.first_name or "") + " " + (u.last_name or "")).strip()) or "Nomsiz"
        un   = "@" + clean(u.username) if u.username else "username yoq"
        bot.send_message(
            ADMIN_ID,
            "📨 Yangi xabar!\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Ism: " + name + " (" + un + ")\n"
            "ID: " + str(uid) + "\n\n"
            "Xabar: Stiker yubordi"
        )
    except:
        pass

    bot.reply_to(msg, d["default_reply"])


@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_text(msg):
    uid  = msg.from_user.id
    text = msg.text.strip()

    # ── Admin holatlari
    if is_admin(uid) and uid in states:
        st = states[uid]

        if st == "add_kw":
            tmp[uid]    = {"kw": text}
            states[uid] = "add_rep"
            send(uid,
                "Kalit soz: " + text + "\n\n"
                "Endi shu kalit sozga javobni yozing:",
                kb_back("m_rep"))
            return

        elif st == "add_rep":
            kw = tmp.get(uid, {}).get("kw", "")
            if kw:
                d = get_data()
                d["replies"][kw] = text
                dump(DATA_FILE, d)
            states.pop(uid, None)
            tmp.pop(uid, None)
            send(uid,
                "✅ Saqlandi!\n"
                "Kalit soz: " + kw + "\n"
                "Javob: " + text,
                kb_back("m_rep"))
            return

        elif st == "set_def":
            d = get_data()
            d["default_reply"] = text
            dump(DATA_FILE, d)
            states.pop(uid, None)
            send(uid, "✅ Standart javob saqlandi!", kb_back("m_rep"))
            return

        elif st == "set_wel":
            d = get_data()
            d["welcome"] = text
            dump(DATA_FILE, d)
            states.pop(uid, None)
            send(uid, "✅ Xush kelibsiz xabari saqlandi!", kb_back("m_set"))
            return

        elif st == "set_spam":
            try:
                n = int(text)
                if 1 <= n <= 20:
                    d = get_data()
                    d["spam_limit"] = n
                    dump(DATA_FILE, d)
                    states.pop(uid, None)
                    send(uid, "✅ Spam limiti: " + str(n) + " xabar/daqiqa", kb_back("m_set"))
                else:
                    send(uid, "1 dan 20 gacha raqam kiriting.")
            except:
                send(uid, "Faqat raqam kiriting!")
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
                send(uid,
                    "✅ Vaqt: " + text + "\n\n"
                    "Endi post matnini yozing:",
                    kb_back("m_ch"))
            except:
                send(uid, "Format notogri!\nMisol: 25.12.2024 18:00")
            return

        elif st == "sch_txt":
            pt = tmp.get(uid, {}).get("time", "")
            if pt:
                posts = get_sched()
                posts.append({"time": pt, "text": text})
                dump(SCHED_FILE, posts)
            states.pop(uid, None)
            tmp.pop(uid, None)
            send(uid,
                "✅ Post rejalashtirildi!\n"
                "Vaqt: " + pt + "\n"
                "Matn: " + text[:60],
                kb_back("m_ch"))
            return

        elif st == "blk_id":
            states.pop(uid, None)
            try:
                bid = int(text)
                d   = get_data()
                if bid not in d["blocked"]:
                    d["blocked"].append(bid)
                    dump(DATA_FILE, d)
                    send(uid, "🚫 " + str(bid) + " bloklandi.", kb_back("m_usr"))
                else:
                    send(uid, "Bu foydalanuvchi allaqachon bloklangan.", kb_back("m_usr"))
            except:
                send(uid, "Faqat raqam (ID) kiriting!", kb_back("m_usr"))
            return

        elif st == "bcast":
            tmp[uid] = {"text": text}
            states.pop(uid, None)
            d = get_data()
            send(uid,
                "📨 Broadcast tasdiqlash\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "Xabar:\n" + text[:100] + "\n\n"
                + str(len(d["users"])) + " ta foydalanuvchiga yuboriladi.\n"
                "Tasdiqlaysizmi?",
                kb_confirm("bc_yes", "bc_no"))
            return

    # ── Oddiy foydalanuvchi
    d = get_data()

    if not d["active"]:
        return

    if uid in d["blocked"]:
        return

    if is_spam(uid):
        send(uid, "Juda tez yuboryapsiz. Biroz kuting.")
        return

    register_user(msg.from_user)
    record_stat(uid)

    # Adminga xabar berish
    try:
        u    = msg.from_user
        name = clean(((u.first_name or "") + " " + (u.last_name or "")).strip()) or "Nomsiz"
        un   = "@" + clean(u.username) if u.username else "username yoq"
        bot.send_message(
            ADMIN_ID,
            "📨 Yangi xabar!\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Ism: " + name + " (" + un + ")\n"
            "ID: " + str(uid) + "\n\n"
            "Xabar: " + clean(text)
        )
    except:
        pass

    # Auto-javob
    bot.reply_to(msg, find_reply(text))

# ─────────────────────────────────────
#  REJALI POSTLAR
# ─────────────────────────────────────
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
                        bot.send_message(
                            ADMIN_ID,
                            "✅ Rejalangan post yuborildi!\n" + p["text"][:80]
                        )
                    except:
                        pass
                else:
                    left.append(p)
            if len(left) != len(posts):
                dump(SCHED_FILE, left)
        except:
            pass
        time.sleep(30)

# ─────────────────────────────────────
#  ISHGA TUSHIRISH
# ─────────────────────────────────────
if __name__ == "__main__":
    print("FUZZY BOT v7.0 ishga tushdi!")
    print("Admin ID:", ADMIN_ID)
    print("Kanal:", CHANNEL_ID)
    threading.Thread(target=run_scheduler, daemon=True).start()
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            print("Polling xato:", e)
            time.sleep(5)
