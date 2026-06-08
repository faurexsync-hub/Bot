#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# FUZZY BOT v5.0 — Railway
# pip install pyTelegramBotAPI

import telebot, time, threading
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, ADMIN_ID, CHANNEL_ID
from database import (get_data, save_data, get_stats,
                      save_stats, get_sched, save_sched)

bot    = telebot.TeleBot(BOT_TOKEN)
states = {}
tmp    = {}

# ── YORDAMCHILAR ─────────────────────────────────────
def esc(t):
    for c in ["_","*","`","[","]"]:
        t = str(t).replace(c, "")
    return t

def adm(uid): return uid == ADMIN_ID

def save_user(u):
    d = get_data()
    k = str(u.id)
    if k not in d["users"]:
        name = ((u.first_name or "") + " " + (u.last_name or "")).strip() or "Nomsiz"
        d["users"][k] = {
            "name": name, "username": u.username or "",
            "id": u.id, "date": datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        save_data(d)

def add_stat(uid):
    s = get_stats()
    today = str(datetime.now().date())
    if s["date"] != today:
        s["today"] = 0
        s["date"] = today
    s["total"] += 1
    s["today"] += 1
    s["counts"][str(uid)] = s["counts"].get(str(uid), 0) + 1
    save_stats(s)

def spam_check(uid):
    d = get_data()
    k = str(uid)
    now = time.time()
    d["spam_tracker"].setdefault(k, [])
    d["spam_tracker"][k] = [t for t in d["spam_tracker"][k] if now - t < 60]
    d["spam_tracker"][k].append(now)
    save_data(d)
    return len(d["spam_tracker"][k]) > d["spam_limit"]

def auto_reply(text):
    d = get_data()
    t = (text or "").lower()
    for k, v in d["replies"].items():
        if k.lower() in t:
            return v
    return d["default_reply"]

def send(cid, text, kb=None):
    try: bot.send_message(cid, text, reply_markup=kb)
    except Exception as e: print("send err:", e)

def edit(call, text, kb=None):
    try:
        bot.edit_message_text(text, call.message.chat.id,
            call.message.message_id, reply_markup=kb)
    except:
        try: bot.send_message(call.message.chat.id, text, reply_markup=kb)
        except Exception as e: print("edit err:", e)

# ── KLAVIATURALAR ────────────────────────────────────
def kb_main():
    m = InlineKeyboardMarkup(row_width=2)
    m.add(
        InlineKeyboardButton("💬 Auto-javoblar",    callback_data="m_rep"),
        InlineKeyboardButton("📢 Kanal",            callback_data="m_ch"),
        InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="m_usr"),
        InlineKeyboardButton("📊 Statistika",       callback_data="m_stat"),
        InlineKeyboardButton("⚙️ Sozlamalar",       callback_data="m_set"),
        InlineKeyboardButton("📨 Broadcast",        callback_data="m_bc"),
    )
    return m

def kb_back(cb="home"):
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("🔙 Asosiy menyu", callback_data=cb))
    return m

def kb_rep():
    m = InlineKeyboardMarkup(row_width=2)
    m.add(
        InlineKeyboardButton("➕ Qoshish",   callback_data="r_add"),
        InlineKeyboardButton("📋 Royxat",    callback_data="r_list"),
        InlineKeyboardButton("🗑 Ochirish",  callback_data="r_del"),
        InlineKeyboardButton("✏️ Standart",  callback_data="r_def"),
    )
    m.add(InlineKeyboardButton("🔙 Asosiy menyu", callback_data="home"))
    return m

def kb_ch():
    m = InlineKeyboardMarkup(row_width=2)
    m.add(
        InlineKeyboardButton("📝 Post yuborish",  callback_data="c_post"),
        InlineKeyboardButton("⏰ Rejalashtirish", callback_data="c_sched"),
        InlineKeyboardButton("📅 Rejalangan",     callback_data="c_list"),
    )
    m.add(InlineKeyboardButton("🔙 Asosiy menyu", callback_data="home"))
    return m

def kb_usr():
    m = InlineKeyboardMarkup(row_width=2)
    m.add(
        InlineKeyboardButton("📋 Royxat",           callback_data="u_list"),
        InlineKeyboardButton("🚫 Bloklash",          callback_data="u_blk"),
        InlineKeyboardButton("✅ Blokdan chiqarish", callback_data="u_ublk"),
        InlineKeyboardButton("🔴 Bloklangan",        callback_data="u_blklist"),
    )
    m.add(InlineKeyboardButton("🔙 Asosiy menyu", callback_data="home"))
    return m

def kb_set():
    d = get_data()
    st = "🟢 Yoqilgan" if d["active"] else "🔴 Ochiq emas"
    m = InlineKeyboardMarkup(row_width=2)
    m.add(
        InlineKeyboardButton("🤖 Bot: " + st,    callback_data="s_tog"),
        InlineKeyboardButton("🔔 Xush kelibsiz", callback_data="s_wel"),
        InlineKeyboardButton("⚠️ Spam limiti",   callback_data="s_spam"),
    )
    m.add(InlineKeyboardButton("🔙 Asosiy menyu", callback_data="home"))
    return m

def kb_ok(yes, no):
    m = InlineKeyboardMarkup(row_width=2)
    m.add(
        InlineKeyboardButton("✅ Ha", callback_data=yes),
        InlineKeyboardButton("❌ Yoq", callback_data=no),
    )
    return m

def panel():
    d = get_data()
    s = get_stats()
    today = str(datetime.now().date())
    if s["date"] != today: s["today"] = 0
    st = "🟢 Yoqilgan" if d["active"] else "🔴 Ochiq emas"
    return (
        "👑 FUZZY BOT — Admin Panel\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Bot holati: " + st + "\n"
        "Foydalanuvchilar: " + str(len(d["users"])) + " ta\n"
        "Kalit sozlar: " + str(len(d["replies"])) + " ta\n"
        "Bugungi xabarlar: " + str(s["today"]) + "\n"
        "Jami xabarlar: " + str(s["total"]) + "\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Bolimni tanlang:"
    )

# ── /START ───────────────────────────────────────────
@bot.message_handler(commands=["start"])
def on_start(msg):
    uid = msg.from_user.id
    if adm(uid):
        send(uid, "Xush kelibsiz Admin! Fuzzy Bot ishga tayyor.")
        time.sleep(0.3)
        send(uid, panel(), kb_main())
    else:
        d = get_data()
        if not d["active"]: return
        save_user(msg.from_user)
        send(uid, d["welcome"])

# ── CALLBACK ─────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: True)
def on_cb(call):
    uid = call.from_user.id
    if not adm(uid):
        bot.answer_callback_query(call.id, "Ruxsat yoq!")
        return
    bot.answer_callback_query(call.id)
    cb = call.data

    if cb == "home":
        edit(call, panel(), kb_main())

    # AUTO-JAVOBLAR
    elif cb == "m_rep":
        d = get_data()
        edit(call,
            "💬 Auto-javoblar bolimi\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Jami kalit sozlar: " + str(len(d["replies"])) + " ta\n"
            "Standart: " + d["default_reply"][:40] + "\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Amalni tanlang:", kb_rep())

    elif cb == "r_add":
        states[uid] = "add_kw"
        edit(call,
            "➕ Yangi auto-javob\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Kalit sozni yozing:\n(narx, buyurtma, manzil ...)",
            kb_back("m_rep"))

    elif cb == "r_list":
        d = get_data()
        if not d["replies"]:
            edit(call, "Hali kalit soz qoshilmagan.", kb_back("m_rep"))
            return
        text = "📋 Barcha auto-javoblar:\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, (k, v) in enumerate(d["replies"].items(), 1):
            text += str(i) + ". " + k + "\n" + v[:55] + "\n\n"
        edit(call, text, kb_back("m_rep"))

    elif cb == "r_del":
        d = get_data()
        if not d["replies"]:
            edit(call, "Ochiriladigan kalit soz yoq.", kb_back("m_rep"))
            return
        m = InlineKeyboardMarkup()
        for k in d["replies"]:
            m.add(InlineKeyboardButton("🗑 " + k, callback_data="dk_" + k))
        m.add(InlineKeyboardButton("🔙 Ortga", callback_data="m_rep"))
        edit(call, "Qaysi kalit sozni ochirish?", m)

    elif cb.startswith("dk_"):
        kw = cb[3:]
        d = get_data()
        if kw in d["replies"]:
            del d["replies"][kw]
            save_data(d)
        edit(call, kw + " ochirildi!", kb_back("m_rep"))

    elif cb == "r_def":
        d = get_data()
        states[uid] = "set_def"
        edit(call,
            "Standart javobni ozgartirish\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Hozirgi:\n" + d["default_reply"] + "\n\nYangi javobni yozing:",
            kb_back("m_rep"))

    # KANAL
    elif cb == "m_ch":
        posts = get_sched()
        edit(call,
            "📢 Kanal boshqaruvi\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Kanal: " + CHANNEL_ID + "\n"
            "Rejalangan: " + str(len(posts)) + " ta\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Amalni tanlang:", kb_ch())

    elif cb == "c_post":
        states[uid] = "ch_post"
        edit(call, "📝 Post matnini yozing:", kb_back("m_ch"))

    elif cb == "c_sched":
        states[uid] = "sch_time"
        edit(call,
            "⏰ Post rejalashtirish\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Vaqtni kiriting:\nFormat: KK.OO.YYYY SS:DD\nMisol: 25.12.2024 18:00",
            kb_back("m_ch"))

    elif cb == "c_list":
        posts = get_sched()
        if not posts:
            edit(call, "Rejalangan post yoq.", kb_back("m_ch"))
            return
        text = "📅 Rejalangan postlar:\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        m = InlineKeyboardMarkup()
        for i, p in enumerate(posts):
            text += str(i+1) + ". " + p["time"] + "\n" + p["text"][:40] + "\n\n"
            m.add(InlineKeyboardButton("❌ " + str(i+1) + "-ni ochirish", callback_data="dsc_" + str(i)))
        m.add(InlineKeyboardButton("🔙 Ortga", callback_data="m_ch"))
        edit(call, text, m)

    elif cb.startswith("dsc_"):
        idx = int(cb[4:])
        posts = get_sched()
        if 0 <= idx < len(posts):
            posts.pop(idx)
            save_sched(posts)
        edit(call, "Rejalangan post ochirildi!", kb_back("m_ch"))

    # FOYDALANUVCHILAR
    elif cb == "m_usr":
        d = get_data()
        edit(call,
            "👥 Foydalanuvchilar\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Jami: " + str(len(d["users"])) + " ta\n"
            "Bloklangan: " + str(len(d["blocked"])) + " ta\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Amalni tanlang:", kb_usr())

    elif cb == "u_list":
        d = get_data()
        if not d["users"]:
            edit(call, "Hali foydalanuvchi yoq.", kb_back("m_usr"))
            return
        text = "👥 Foydalanuvchilar (" + str(len(d["users"])) + " ta):\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        for k, info in list(d["users"].items())[-15:]:
            un = "@" + esc(info["username"]) if info["username"] else "—"
            text += esc(info["name"]) + " " + un + "\nID: " + str(info["id"]) + " | " + info["date"] + "\n\n"
        edit(call, text, kb_back("m_usr"))

    elif cb == "u_blk":
        states[uid] = "blk_id"
        edit(call,
            "🚫 Foydalanuvchi bloklash\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Foydalanuvchi ID sini yozing:", kb_back("m_usr"))

    elif cb == "u_ublk":
        d = get_data()
        if not d["blocked"]:
            edit(call, "Bloklangan foydalanuvchi yoq.", kb_back("m_usr"))
            return
        m = InlineKeyboardMarkup()
        for bid in d["blocked"]:
            info = d["users"].get(str(bid), {})
            name = esc(info.get("name", str(bid)))
            m.add(InlineKeyboardButton("✅ " + name + " (" + str(bid) + ")", callback_data="ubk_" + str(bid)))
        m.add(InlineKeyboardButton("🔙 Ortga", callback_data="m_usr"))
        edit(call, "Blokdan chiqarish — kimni?", m)

    elif cb.startswith("ubk_"):
        bid = int(cb[4:])
        d = get_data()
        if bid in d["blocked"]:
            d["blocked"].remove(bid)
            save_data(d)
        edit(call, str(bid) + " blokdan chiqarildi!", kb_back("m_usr"))

    elif cb == "u_blklist":
        d = get_data()
        if not d["blocked"]:
            edit(call, "Bloklangan foydalanuvchi yoq.", kb_back("m_usr"))
            return
        text = "🔴 Bloklangan:\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        for bid in d["blocked"]:
            info = d["users"].get(str(bid), {})
            text += "🚫 " + esc(info.get("name", "?")) + " — " + str(bid) + "\n"
        edit(call, text, kb_back("m_usr"))

    # STATISTIKA
    elif cb == "m_stat":
        d = get_data()
        s = get_stats()
        today = str(datetime.now().date())
        if s["date"] != today: s["today"] = 0
        top = sorted(s["counts"].items(), key=lambda x: x[1], reverse=True)[:5]
        top_t = ""
        for i, (k, v) in enumerate(top, 1):
            info = d["users"].get(k, {})
            top_t += "  " + str(i) + ". " + esc(info.get("name", "?")) + " — " + str(v) + " xabar\n"
        edit(call,
            "📊 Statistika\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Jami xabarlar: " + str(s["total"]) + "\n"
            "Bugun: " + str(s["today"]) + "\n"
            "Foydalanuvchilar: " + str(len(d["users"])) + "\n"
            "Bloklangan: " + str(len(d["blocked"])) + "\n"
            "Kalit sozlar: " + str(len(d["replies"])) + "\n"
            "Rejalangan post: " + str(len(get_sched())) + "\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Top 5 faol:\n" + (top_t if top_t else "  Hali yoq"),
            kb_back("home"))

    # SOZLAMALAR
    elif cb == "m_set":
        d = get_data()
        st = "🟢 Yoqilgan" if d["active"] else "🔴 Ochiq emas"
        edit(call,
            "⚙️ Sozlamalar\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Bot holati: " + st + "\n"
            "Spam limiti: " + str(d["spam_limit"]) + " xabar/daqiqa\n"
            "Xush kelibsiz:\n" + d["welcome"][:50] + "\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Nimani ozgartirish?", kb_set())

    elif cb == "s_tog":
        d = get_data()
        d["active"] = not d["active"]
        save_data(d)
        bot.answer_callback_query(call.id, "Bot " + ("Yoqildi!" if d["active"] else "Ochiq emas!"))
        d = get_data()
        st = "🟢 Yoqilgan" if d["active"] else "🔴 Ochiq emas"
        edit(call,
            "⚙️ Sozlamalar\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Bot holati: " + st + "\n"
            "Spam limiti: " + str(d["spam_limit"]) + " xabar/daqiqa\n"
            "Xush kelibsiz:\n" + d["welcome"][:50] + "\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Nimani ozgartirish?", kb_set())

    elif cb == "s_wel":
        states[uid] = "set_wel"
        d = get_data()
        edit(call,
            "🔔 Xush kelibsiz xabarini ozgartirish\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Hozirgi:\n" + d["welcome"] + "\n\nYangi xabarni yozing:",
            kb_back("m_set"))

    elif cb == "s_spam":
        states[uid] = "set_spam"
        d = get_data()
        edit(call,
            "⚠️ Spam limitini ozgartirish\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Hozirgi: " + str(d["spam_limit"]) + " xabar/daqiqa\n\nYangi raqam (1-20):",
            kb_back("m_set"))

    # BROADCAST
    elif cb == "m_bc":
        d = get_data()
        states[uid] = "bcast"
        edit(call,
            "📨 Broadcast\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Barcha " + str(len(d["users"])) + " foydalanuvchiga\nyuboriladigan xabarni yozing:",
            kb_back("home"))

    elif cb == "bc_yes":
        msg_text = tmp.get(uid, {}).get("text", "")
        if not msg_text:
            edit(call, "Xabar topilmadi.", kb_back("home"))
            return
        d = get_data()
        sent = failed = 0
        for user_id in d["users"]:
            try:
                bot.send_message(int(user_id), msg_text)
                sent += 1
                time.sleep(0.05)
            except:
                failed += 1
        tmp.pop(uid, None)
        edit(call,
            "✅ Broadcast yakunlandi!\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Yuborildi: " + str(sent) + "\n"
            "Xato: " + str(failed), kb_back("home"))

    elif cb == "bc_no":
        tmp.pop(uid, None)
        edit(call, "Broadcast bekor qilindi.", kb_main())

# ── MATN XABARLARI ──────────────────────────────────
@bot.message_handler(func=lambda m: True, content_types=["text"])
def on_text(msg):
    uid  = msg.from_user.id
    text = msg.text.strip()
    st   = states.get(uid)

    if adm(uid) and st:
        if st == "add_kw":
            tmp[uid] = {"kw": text}
            states[uid] = "add_rep"
            send(uid, "Kalit soz: " + text + "\n\nEndi javobni yozing:", kb_back("m_rep"))

        elif st == "add_rep":
            kw = tmp.get(uid, {}).get("kw")
            if kw:
                d = get_data()
                d["replies"][kw] = text
                save_data(d)
                states.pop(uid, None); tmp.pop(uid, None)
                send(uid, "✅ Saqlandi!\nKalit soz: " + kw + "\nJavob: " + text, kb_back("m_rep"))

        elif st == "set_def":
            d = get_data(); d["default_reply"] = text; save_data(d)
            states.pop(uid, None)
            send(uid, "✅ Standart javob saqlandi!", kb_back("m_rep"))

        elif st == "set_wel":
            d = get_data(); d["welcome"] = text; save_data(d)
            states.pop(uid, None)
            send(uid, "✅ Xush kelibsiz xabari saqlandi!", kb_back("m_set"))

        elif st == "set_spam":
            try:
                n = int(text)
                if 1 <= n <= 20:
                    d = get_data(); d["spam_limit"] = n; save_data(d)
                    states.pop(uid, None)
                    send(uid, "✅ Spam limiti: " + str(n) + " xabar/daqiqa", kb_back("m_set"))
                else:
                    send(uid, "1 dan 20 gacha raqam kiriting.")
            except:
                send(uid, "Faqat raqam kiriting!")

        elif st == "ch_post":
            states.pop(uid, None)
            try:
                bot.send_message(CHANNEL_ID, text)
                send(uid, "✅ Post kanalga yuborildi!", kb_back("m_ch"))
            except Exception as e:
                send(uid, "Xato: " + str(e), kb_back("m_ch"))

        elif st == "sch_time":
            try:
                t = datetime.strptime(text, "%d.%m.%Y %H:%M")
                tmp[uid] = {"time": t.strftime("%d.%m.%Y %H:%M")}
                states[uid] = "sch_txt"
                send(uid, "✅ Vaqt: " + text + "\n\nPost matnini yozing:", kb_back("m_ch"))
            except:
                send(uid, "Format notogri! Misol: 25.12.2024 18:00")

        elif st == "sch_txt":
            pt = tmp.get(uid, {}).get("time")
            if pt:
                posts = get_sched()
                posts.append({"time": pt, "text": text})
                save_sched(posts)
                states.pop(uid, None); tmp.pop(uid, None)
                send(uid, "✅ Post rejalashtirildi!\nVaqt: " + pt + "\nMatn: " + text[:80], kb_back("m_ch"))

        elif st == "blk_id":
            try:
                bid = int(text)
                d = get_data()
                if bid not in d["blocked"]:
                    d["blocked"].append(bid); save_data(d)
                    send(uid, str(bid) + " bloklandi.", kb_back("m_usr"))
                else:
                    send(uid, "Allaqachon bloklangan.", kb_back("m_usr"))
            except:
                send(uid, "Faqat raqam (ID) kiriting!")
            states.pop(uid, None)

        elif st == "bcast":
            tmp[uid] = {"text": text}
            states.pop(uid, None)
            d = get_data()
            send(uid,
                "📨 Broadcast tasdiqlash\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "Xabar: " + text[:100] + "\n\n"
                + str(len(d["users"])) + " ta foydalanuvchiga yuboriladi. Tasdiqlaysizmi?",
                kb_ok("bc_yes", "bc_no"))
        return

    # ODDIY FOYDALANUVCHI
    d = get_data()
    if not d["active"]: return
    if uid in d["blocked"]: return
    if spam_check(uid):
        send(uid, "Juda tez yuboryapsiz. Biroz kuting.")
        return

    save_user(msg.from_user)
    add_stat(uid)

    try:
        u = msg.from_user
        name = esc(((u.first_name or "") + " " + (u.last_name or "")).strip())
        un = "@" + esc(u.username) if u.username else "username yoq"
        bot.send_message(ADMIN_ID,
            "📨 Yangi xabar!\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Ism: " + name + " (" + un + ")\n"
            "ID: " + str(uid) + "\n\n"
            "Xabar: " + esc(text))
    except: pass

    bot.reply_to(msg, auto_reply(text))

# ── SCHEDULER ────────────────────────────────────────
def scheduler():
    while True:
        try:
            posts = get_sched()
            now = datetime.now().strftime("%d.%m.%Y %H:%M")
            left = []
            for p in posts:
                if p["time"] <= now:
                    try:
                        bot.send_message(CHANNEL_ID, p["text"])
                        bot.send_message(ADMIN_ID, "✅ Rejalangan post yuborildi!\n" + p["text"][:80])
                    except Exception as e:
                        try: bot.send_message(ADMIN_ID, "Post xatosi: " + str(e))
                        except: pass
                else:
                    left.append(p)
            if len(left) != len(posts):
                save_sched(left)
        except: pass
        time.sleep(30)

# ── ISHGA TUSHIRISH ──────────────────────────────────
if __name__ == "__main__":
    print("FUZZY BOT v5.0 ishga tushdi!")
    threading.Thread(target=scheduler, daemon=True).start()
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
