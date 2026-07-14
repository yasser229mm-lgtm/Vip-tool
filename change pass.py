import os
import sys
import re
import time
import random
import string
import sqlite3
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===================== الإعدادات =====================
BOT_TOKEN = "8694295004:AAGKCo5vcgFpxHJNW2_zB6FNpfXfTe7jWh4"
CHANNEL_URL = "https://t.me/accountcpm1"

# ===================== الألوان =====================
G = '\x1b[92m'
C = '\x1b[96m'
Y = '\x1b[93m'
BOLD = '\x1b[1m'
RESET = '\x1b[0m'

# ===================== قاعدة البيانات =====================
def init_db():
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (user_id INTEGER PRIMARY KEY, email TEXT, password TEXT)''')
    conn.commit()
    conn.close()

def save_session(user_id, email, password):
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO sessions (user_id, email, password) VALUES (?, ?, ?)", 
              (user_id, email, password))
    conn.commit()
    conn.close()

def get_session(user_id):
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute("SELECT email, password FROM sessions WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result

def delete_session(user_id):
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

init_db()

# ===================== Car Parking API =====================
class CarParkingAPI:
    def change_password(self, email, password, new_password):
        try:
            fb_api = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM"
            login_resp = requests.post(fb_api, json={"email": email, "password": password, "returnSecureToken": True}, timeout=10)
            
            if login_resp.status_code != 200:
                return False, "❌ فشل تسجيل الدخول"
            
            data = login_resp.json()
            if 'idToken' not in data:
                return False, "❌ بيانات غير صحيحة"
            
            id_token = data['idToken']
            
            change_api = "https://identitytoolkit.googleapis.com/v1/accounts:update?key=AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM"
            change_resp = requests.post(change_api, json={"idToken": id_token, "password": new_password, "returnSecureToken": True}, timeout=10)
            
            if change_resp.status_code == 200:
                return True, f"✅ تم تغيير كلمة المرور بنجاح!\n🔑 `{new_password}`"
            else:
                return False, "❌ فشل تغيير كلمة المرور"
        except:
            return False, "❌ خطأ تقني"

api = CarParkingAPI()
user_states = {}

# ===================== دوال البوت =====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دالة /start"""
    user_id = update.effective_user.id
    session = get_session(user_id)
    
    if session:
        await dashboard(update, context)
        return
    
    keyboard = [
        [InlineKeyboardButton("🔑 تسجيل الدخول", callback_data="login")],
        [InlineKeyboardButton("📢 القناة", url=CHANNEL_URL)],
        [InlineKeyboardButton("ℹ️ عن البوت", callback_data="about")]
    ]
    
    text = (
        "🔐 **CPM PASSWORD CHANGER**\n"
        "═══════════════════════\n"
        "🚗 Car Parking Multiplayer 1\n\n"
        "✨ أداة VIP لتغيير كلمة المرور\n"
        "📌 بسرعة وأمان\n\n"
        "═══════════════════════\n"
        "⚠️ **تنبيهات:**\n"
        "• كلمة المرور الجديدة 6 أحرف\n"
        "• احتفظ بها في مكان آمن\n"
        "═══════════════════════\n\n"
        "📌 **ابدأ بتسجيل الدخول**"
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def start_callback(query, context):
    """دالة start عند استخدامها من callback"""
    user_id = query.from_user.id
    session = get_session(user_id)
    
    if session:
        await dashboard_callback(query, context)
        return
    
    keyboard = [
        [InlineKeyboardButton("🔑 تسجيل الدخول", callback_data="login")],
        [InlineKeyboardButton("📢 القناة", url=CHANNEL_URL)],
        [InlineKeyboardButton("ℹ️ عن البوت", callback_data="about")]
    ]
    
    text = (
        "🔐 **CPM PASSWORD CHANGER**\n"
        "═══════════════════════\n"
        "🚗 Car Parking Multiplayer 1\n\n"
        "✨ أداة VIP لتغيير كلمة المرور\n"
        "📌 بسرعة وأمان\n\n"
        "═══════════════════════\n"
        "⚠️ **تنبيهات:**\n"
        "• كلمة المرور الجديدة 6 أحرف\n"
        "• احتفظ بها في مكان آمن\n"
        "═══════════════════════\n\n"
        "📌 **ابدأ بتسجيل الدخول**"
    )
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لوحة التحكم من Update"""
    user_id = update.effective_user.id
    session = get_session(user_id)
    if not session:
        await update.message.reply_text("❌ يجب تسجيل الدخول أولاً")
        return
    
    email, password = session
    masked = email[:3] + "***" + email[email.index('@'):]
    
    keyboard = [
        [InlineKeyboardButton("🔑 تغيير كلمة المرور", callback_data="change_password")],
        [InlineKeyboardButton("📊 معلومات الحساب", callback_data="account_info")],
        [InlineKeyboardButton("🚪 تسجيل الخروج", callback_data="logout")]
    ]
    
    text = (
        "🔐 **لوحة التحكم**\n"
        "═══════════════════════\n"
        f"👤 {masked}\n"
        "✅ مسجل الدخول\n"
        f"🕐 {datetime.now().strftime('%I:%M %p')}\n"
        "═══════════════════════\n\n"
        "📌 **اختر الخدمة:**"
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def dashboard_callback(query, context):
    """لوحة التحكم من CallbackQuery"""
    user_id = query.from_user.id
    session = get_session(user_id)
    if not session:
        await query.edit_message_text("❌ يجب تسجيل الدخول أولاً")
        return
    
    email, password = session
    masked = email[:3] + "***" + email[email.index('@'):]
    
    keyboard = [
        [InlineKeyboardButton("🔑 تغيير كلمة المرور", callback_data="change_password")],
        [InlineKeyboardButton("📊 معلومات الحساب", callback_data="account_info")],
        [InlineKeyboardButton("🚪 تسجيل الخروج", callback_data="logout")]
    ]
    
    text = (
        "🔐 **لوحة التحكم**\n"
        "═══════════════════════\n"
        f"👤 {masked}\n"
        "✅ مسجل الدخول\n"
        f"🕐 {datetime.now().strftime('%I:%M %p')}\n"
        "═══════════════════════\n\n"
        "📌 **اختر الخدمة:**"
    )
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ===================== معالجة الأزرار =====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    # ===== رجوع =====
    if data == "back":
        session = get_session(user_id)
        if session:
            await dashboard_callback(query, context)
        else:
            await start_callback(query, context)
        return
    
    # ===== عن البوت =====
    if data == "about":
        text = (
            "ℹ️ **عن البوت**\n"
            "═══════════════════════\n"
            "📌 **الاسم:** CPM Password Changer\n"
            "🎮 **اللعبة:** Car Parking 1\n"
            "👨‍💻 **المطور:** yasser_cpm\n"
            "📢 **القناة:** @accountcpm1\n"
            "═══════════════════════\n"
            "🔐 **الخدمات:**\n"
            "• تغيير كلمة المرور\n"
            "• حماية الحساب\n"
            "═══════════════════════\n\n"
            "💡 للمساعدة: @Twassele_bot"
        )
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    # ===== معلومات الحساب =====
    if data == "account_info":
        session = get_session(user_id)
        if not session:
            await query.edit_message_text("❌ يجب تسجيل الدخول أولاً")
            return
        
        email, password = session
        
        text = (
            "📊 **معلومات الحساب**\n"
            "═══════════════════════\n"
            f"📧 {email}\n"
            f"🔑 {'•' * 8}\n"
            f"🕐 {datetime.now().strftime('%Y-%m-%d %I:%M %p')}\n"
            "✅ الحالة: نشط\n"
            "═══════════════════════\n\n"
            "⚠️ غير كلمة المرور بانتظام"
        )
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    # ===== تسجيل الدخول - الخطوة 1: الإيميل =====
    if data == "login":
        text = (
            "🔑 **تسجيل الدخول**\n"
            "═══════════════════════\n\n"
            "📧 **أدخل الإيميل:**"
        )
        await query.edit_message_text(text)
        user_states[user_id] = "login_email"
        return
    
    # ===== تغيير كلمة المرور =====
    if data == "change_password":
        session = get_session(user_id)
        if not session:
            await query.edit_message_text("❌ يجب تسجيل الدخول أولاً")
            return
        
        text = (
            "🔑 **تغيير كلمة المرور**\n"
            "═══════════════════════\n\n"
            "🔑 **أدخل كلمة المرور الحالية:**"
        )
        await query.edit_message_text(text)
        user_states[user_id] = "change_password_old"
        return
    
    # ===== تسجيل الخروج =====
    if data == "logout":
        delete_session(user_id)
        text = (
            "✅ **تم تسجيل الخروج**\n"
            "═══════════════════════\n"
            "👋 نتمنى زيارتك مرة أخرى\n"
            "📢 @accountcpm1"
        )
        keyboard = [[InlineKeyboardButton("🔑 تسجيل الدخول", callback_data="login")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

# ===================== معالجة النصوص =====================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    state = user_states.get(user_id)
    
    if not state:
        await update.message.reply_text("❌ استخدم الأزرار للتنقل")
        return
    
    # ===== تسجيل الدخول - الخطوة 1: الإيميل =====
    if state == "login_email":
        if '@' not in text or '.' not in text:
            await update.message.reply_text("❌ إيميل غير صحيح!\nأعد المحاولة")
            return
        
        user_states[user_id] = "login_password"
        context.user_data['login_email'] = text
        
        text_msg = (
            "🔑 **تسجيل الدخول**\n"
            "═══════════════════════\n\n"
            f"📧 الإيميل: `{text}`\n\n"
            "🔑 **أدخل كلمة المرور:**"
        )
        await update.message.reply_text(text_msg)
        return
    
    # ===== تسجيل الدخول - الخطوة 2: كلمة المرور =====
    if state == "login_password":
        email = context.user_data.get('login_email')
        password = text
        
        msg = await update.message.reply_text("⏳ جاري تسجيل الدخول...")
        
        save_session(user_id, email, password)
        await msg.delete()
        await update.message.reply_text("✅ **تم تسجيل الدخول بنجاح!**")
        await dashboard(update, context)
        
        user_states[user_id] = None
        return
    
    # ===== تغيير كلمة المرور - الخطوة 1: كلمة المرور الحالية =====
    if state == "change_password_old":
        session = get_session(user_id)
        if not session:
            await update.message.reply_text("❌ يجب تسجيل الدخول أولاً")
            user_states[user_id] = None
            return
        
        context.user_data['old_password'] = text
        user_states[user_id] = "change_password_new"
        
        text_msg = (
            "🔑 **تغيير كلمة المرور**\n"
            "═══════════════════════\n\n"
            "🔑 **أدخل كلمة المرور الجديدة:**\n"
            "⚠️ (6 أحرف على الأقل)"
        )
        await update.message.reply_text(text_msg)
        return
    
    # ===== تغيير كلمة المرور - الخطوة 2: كلمة المرور الجديدة =====
    if state == "change_password_new":
        session = get_session(user_id)
        if not session:
            await update.message.reply_text("❌ يجب تسجيل الدخول أولاً")
            user_states[user_id] = None
            return
        
        new_pass = text
        
        if len(new_pass) < 6:
            await update.message.reply_text("❌ كلمة المرور الجديدة يجب أن تكون 6 أحرف على الأقل")
            return
        
        email, password = session
        old_pass = context.user_data.get('old_password')
        
        msg = await update.message.reply_text("⏳ جاري تغيير كلمة المرور...")
        
        success, message = api.change_password(email, old_pass, new_pass)
        
        if success:
            save_session(user_id, email, new_pass)
            await msg.edit_text(
                f"✅ **تم التغيير بنجاح!**\n"
                "═══════════════════════\n"
                f"🔑 `{new_pass}`\n"
                "═══════════════════════\n"
                "⚠️ احتفظ بها في مكان آمن"
            )
        else:
            await msg.edit_text(
                f"❌ **فشل التغيير**\n"
                "═══════════════════════\n"
                f"{message}\n"
                "═══════════════════════\n"
                "💡 تأكد من صحة البيانات"
            )
        
        user_states[user_id] = None
        return

# ===================== التشغيل =====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print(f"{BOLD}{G}[*] البوت يعمل...{RESET}")
    print(f"{BOLD}{C}[*] التوكن: {BOT_TOKEN}{RESET}")
    app.run_polling()

if __name__ == "__main__":
    main()