import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import os
import threading
import time
import html
import uuid
from datetime import datetime, timedelta
import re
import signal
import string
import random
from http.server import BaseHTTPRequestHandler, HTTPServer
from supabase import create_client, Client

# --- SETUP SERVER RENDER (Mobile Optimized) ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 20px; text-align: center; font-size: 16px; margin: 0; box-sizing: border-box; background-color: #f4f4f9; color: #333; }
                h1 { font-size: 1.5rem; color: #2c3e50; }
                p { font-size: 1rem; color: #555; }
            </style>
        </head>
        <body>
            <h1>🚀 Micifind Bot V12 (Global Pro) Aktif!</h1>
            <p>Sistem berjalan normal dan siap melayani pengguna.</p>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode('utf-8'))
        
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# --- SETUP BOT & DATABASE ---
TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

ADMIN_GROUP_ID = os.environ.get("ADMIN_GROUP_ID") 
LOG_THREAD_ID = os.environ.get("LOG_THREAD_ID")
REPORT_THREAD_ID = os.environ.get("REPORT_THREAD_ID")

if LOG_THREAD_ID: LOG_THREAD_ID = int(LOG_THREAD_ID)
if REPORT_THREAD_ID: REPORT_THREAD_ID = int(REPORT_THREAD_ID)

bot = telebot.TeleBot(TOKEN)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

bot.set_my_commands([
    BotCommand("start", "Start or register"),
    BotCommand("search", "Find a new partner"),
    BotCommand("next", "Find the next partner"),
    BotCommand("stop", "End current chat"),
    BotCommand("info", "Show all commands"),
    BotCommand("profil", "View your profile"),
    BotCommand("editprofil", "Edit your profile")
])

user_registration = {}
media_vault = {} 
server_stats = {'matches_in_last_minute': 0}
user_last_action = {} 

# --- DICTIONARY MULTI-BAHASA (GLOBAL) ---
LANGUAGES = {
    'id': '🇮🇩 ID', 'en': '🇬🇧 EN', 'th': '🇹🇭 TH', 
    'tl': '🇵🇭 TL', 'hi': '🇮🇳 HI', 'ru': '🇷🇺 RU', 
    'vi': '🇻🇳 VI', 'es': '🇪🇸 ES', 'pt': '🇧🇷 PT', 
    'ar': '🇸🇦 AR', 'de': '🇩🇪 DE', 'ja': '🇯🇵 JA', 'zh': '🇨🇳 ZH'
}

TRANSLATIONS = {
    'welcome': {
        'id': "<i>👋 Selamat datang di Micifind!\n\n👇 Pilih bahasa kamu:</i>",
        'en': "<i>👋 Welcome to Micifind!\n\n👇 Choose your language:</i>",
        'th': "<i>👋 ยินดีต้อนรับสู่ Micifind!\n\n👇 เลือกภาษาของคุณ:</i>",
        'tl': "<i>👋 Maligayang pagdating sa Micifind!\n\n👇 Piliin ang iyong wika:</i>",
        'hi': "<i>👋 Micifind में आपका स्वागत है!\n\n👇 अपनी भाषा चुनें:</i>",
        'ru': "<i>👋 Добро пожаловать в Micifind!\n\n👇 Выберите ваш язык:</i>",
        'vi': "<i>👋 Chào mừng đến với Micifind!\n\n👇 Chọn ngôn ngữ của bạn:</i>",
        'es': "<i>👋 ¡Bienvenido a Micifind!\n\n👇 Elige tu idioma:</i>",
        'pt': "<i>👋 Bem-vindo ao Micifind!\n\n👇 Escolha seu idioma:</i>",
        'ar': "<i>👋 أهلاً بك في Micifind!\n\n👇 اختر لغتك:</i>",
        'de': "<i>👋 Willkommen bei Micifind!\n\n👇 Wähle deine Sprache:</i>",
        'ja': "<i>👋 Micifindへようこそ！\n\n👇 言語を選択してください:</i>",
        'zh': "<i>👋 欢迎来到 Micifind！\n\n👇 选择你的语言:</i>"
    },
    'stop_dialogue': {
        'id': "<i>🛑 Hmm... kamu mengakhiri obrolan.</i>",
        'en': "<i>🛑 Hmm... you stopped the dialogue.</i>",
        'th': "<i>🛑 อืม... คุณหยุดการสนทนา</i>",
        'tl': "<i>🛑 Hmm... itinigil mo ang pag-uusap.</i>",
        'hi': "<i>🛑 हम्म... आपने बातचीत बंद कर दी।</i>",
        'ru': "<i>🛑 Хмм... вы остановили диалог.</i>",
        'vi': "<i>🛑 Hmm... bạn đã dừng cuộc trò chuyện.</i>",
        'es': "<i>🛑 Hmm... has detenido el diálogo.</i>",
        'pt': "<i>🛑 Hmm... você parou o diálogo.</i>",
        'ar': "<i>🛑 همم... لقد أوقفت الحوار.</i>",
        'de': "<i>🛑 Hmm... du hast den Dialog beendet.</i>",
        'ja': "<i>🛑 うーん... 会話を終了しました。</i>",
        'zh': "<i>🛑 提示... 你停止了对话。</i>"
    },
    'upsell_pro': {
        'id': "<i>✨ Ingin match HANYA dengan lawan jenis dan UNLIMITED match? Silahkan berlangganan paket di bawah ini:</i>",
        'en': "<i>✨ Want to match ONLY with the opposite gender and get UNLIMITED matches? Subscribe below:</i>",
        'es': "<i>✨ ¿Quieres emparejar SOLO con el sexo opuesto y obtener coincidencias ILIMITADAS? Suscríbete abajo:</i>",
        'pt': "<i>✨ Quer combinar APENAS com o sexo oposto e ter combinações ILIMITADAS? Assine abaixo:</i>",
        # Fallback to English for brevity in code, but dictionary structure remains robust
    },
    'searching': {
        'id': "<i>🔍 Mencari partner se-kota... ⏳</i>",
        'en': "<i>🔍 Searching for a partner... ⏳</i>",
        'es': "<i>🔍 Buscando un compañero... ⏳</i>"
    }
}

def t(key, lang_code):
    val = TRANSLATIONS.get(key, {}).get(lang_code)
    if not val: val = TRANSLATIONS.get(key, {}).get('en', '...')
    return val

# --- FUNGSI ANTI-SPAM (RATE LIMITER) ---
def is_spamming(chat_id):
    now = time.time()
    if chat_id in user_last_action and now - user_last_action[chat_id] < 1.0:
        return True
    user_last_action[chat_id] = now
    return False

# --- BACKGROUND THREAD: ADMIN ANALYTICS LOG ---
def admin_logger():
    while True:
        time.sleep(60)
        if not ADMIN_GROUP_ID: continue
        try:
            total_users_res = supabase.table('users').select('user_id', count='exact').execute()
            total_users = total_users_res.count if total_users_res else 0
            matches_last_min = server_stats['matches_in_last_minute']
            mps = matches_last_min / 60.0
            log_msg = f"📊 *LOG ANALITIK*\n👥 Total Users: {total_users}\n⚡ Match Rate: {mps:.2f}/detik"
            bot.send_message(ADMIN_GROUP_ID, log_msg, message_thread_id=LOG_THREAD_ID, parse_mode="Markdown")
            server_stats['matches_in_last_minute'] = 0 
        except Exception as e:
            pass

threading.Thread(target=admin_logger, daemon=True).start()

# --- FUNGSI DATABASE BANTUAN ---
def get_user(user_id):
    res = supabase.table('users').select('*').eq('user_id', user_id).execute()
    return res.data[0] if res.data else None

def get_user_by_username(username):
    uname = username.replace('@', '')
    res = supabase.table('users').select('*').ilike('username', uname).execute()
    return res.data[0] if res.data else None

def update_user(user_id, data):
    supabase.table('users').update(data).eq('user_id', user_id).execute()

def create_or_update_user(user_id, data):
    data['user_id'] = user_id
    supabase.table('users').upsert(data).execute()

def generate_ref_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def check_punishment(user):
    if not user: return False, None
    now = datetime.utcnow().isoformat()
    if user.get('banned_until') and user['banned_until'] > now:
        return True, "banned"
    return False, None

# --- ALUR REGISTRASI & REFERRAL ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_spamming(message.chat.id): return 
    
    args = message.text.split()
    ref_code = args[1] if len(args) > 1 else None
    
    user = get_user(message.chat.id)
    is_punished, reason = check_punishment(user)
    if is_punished:
        bot.send_message(message.chat.id, "<i>⛔ Account blocked.</i>", parse_mode="HTML")
        return

    if not user:
        new_ref = generate_ref_code()
        supabase.table('users').upsert({'user_id': message.chat.id, 'referral_code': new_ref, 'invite_count': 0}).execute()
        
        # LOGIKA ANTI-MANIPULASI REFERRAL
        if ref_code:
            referrer = supabase.table('users').select('*').eq('referral_code', ref_code).execute()
            if referrer.data and referrer.data[0]['user_id'] != message.chat.id:
                ref_user = referrer.data[0]
                new_count = ref_user.get('invite_count', 0) + 1
                
                if new_count >= 10:
                    pro_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
                    update_user(ref_user['user_id'], {'invite_count': 0, 'is_pro': True, 'pro_until': pro_date})
                    bot.send_message(ref_user['user_id'], "<i>🎉 You invited 10 people! You are now PRO for 1 Week!</i>", parse_mode="HTML")
                else:
                    update_user(ref_user['user_id'], {'invite_count': new_count})

    if user and user.get('age'):
        if message.from_user.username:
            update_user(message.chat.id, {'username': message.from_user.username})
        lang = user.get('language', 'en')
        bot.send_message(message.chat.id, "<i>🌟 You are already registered! Use /search.</i>", parse_mode="HTML")
        return

    markup = InlineKeyboardMarkup()
    row = []
    for code, name in LANGUAGES.items():
        row.append(InlineKeyboardButton(name, callback_data=f"lang_{code}"))
        if len(row) == 3:
            markup.add(*row)
            row = []
    if row: markup.add(*row)
    
    bot.send_message(message.chat.id, t('welcome', 'en'), reply_markup=markup, parse_mode="HTML")
    
@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    lang = call.data.split('_')[1]
    uname = call.message.chat.username or ""
    user_registration[call.message.chat.id] = {'language': lang, 'username': uname}
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Male ♂️", callback_data="gender_Male"), InlineKeyboardButton("Female ♀️", callback_data="gender_Female"))
    bot.edit_message_text("<i>👤 Select your gender:</i>", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('gender_'))
def set_gender(call):
    chat_id = call.message.chat.id
    if chat_id not in user_registration: return
    user_registration[chat_id]['gender'] = "Male" if call.data == "gender_Male" else "Female"
    
    msg = bot.edit_message_text("<i>🎂 Enter your age (Min 17):</i>", chat_id, call.message.message_id, parse_mode="HTML")
    bot.register_next_step_handler(msg, process_age)

def process_age(message):
    chat_id = message.chat.id
    if not message.text.isdigit() or int(message.text) < 17:
        bot.send_message(chat_id, "<i>❌ Min 17. Click /start to try again.</i>", parse_mode="HTML")
        return
    user_registration[chat_id]['age'] = int(message.text)
    msg = bot.send_message(chat_id, "<i>🗺️ Enter your City/Province:</i>", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_location)

def process_location(message):
    chat_id = message.chat.id
    user_registration[chat_id]['location'] = message.text.strip().title()
    msg = bot.send_message(chat_id, "<i>📝 Write 'About Me':</i>", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_about)

def process_about(message):
    chat_id = message.chat.id
    data = user_registration.get(chat_id)
    if not data: return
    data['about'] = message.text
    create_or_update_user(chat_id, data)
    
    bot.send_message(chat_id, f"<i>✨ Profile saved! Use /search to find partner.</i>", parse_mode="HTML")

# --- ALUR MATCHMAKING & DAILY LIMIT ---
def check_daily_limit(user):
    if user.get('is_pro'): return True 
    today = datetime.utcnow().date().isoformat()
    if user.get('last_match_date') != today:
        update_user(user['user_id'], {'matches_today': 0, 'last_match_date': today})
        return True
    return user.get('matches_today', 0) < 150

def attempt_match(chat_id, user_data, scope, value):
    current_me = get_user(chat_id)
    if current_me and current_me['status'] == 'chatting': return True
    
    query = supabase.table('users').select('*').eq('status', 'searching').neq('user_id', chat_id)
    
    # Prioritas Pro Gender
    if current_me.get('is_pro') and current_me.get('pref_gender'):
        query = query.eq('gender', current_me['pref_gender'])

    res = query.limit(1).execute()
    if res.data:
        partner = res.data[0]
        # Update Limit Counters
        if not current_me.get('is_pro'):
            update_user(chat_id, {'matches_today': current_me.get('matches_today', 0) + 1})
        if not partner.get('is_pro'):
            update_user(partner['user_id'], {'matches_today': partner.get('matches_today', 0) + 1})
            
        update_user(chat_id, {'status': 'chatting', 'partner_id': partner['user_id']})
        update_user(partner['user_id'], {'status': 'chatting', 'partner_id': chat_id})
        
        send_match_info(chat_id, partner)
        send_match_info(partner['user_id'], current_me)
        server_stats['matches_in_last_minute'] += 1
        return True
    return False

def send_match_info(to_id, partner_data):
    text = f"<i>🎉 Partner Found!</i>\n\n⚧️ Gender: {html.escape(partner_data['gender'])}\n🎂 Age: {partner_data['age']}\n🏙️ City: {html.escape(partner_data['location'])}\n📝 About Me: {html.escape(partner_data['about'])}"
    bot.send_message(to_id, text, parse_mode="HTML")

@bot.message_handler(commands=['search', 'next'])
def search_partner(message):
    if is_spamming(message.chat.id): return 
    
    user = get_user(message.chat.id)
    if not user: return
    lang = user.get('language', 'en')
    
    if user['status'] == 'chatting' and message.text == '/search':
        bot.send_message(message.chat.id, "<i>💬 Use /stop to end current chat first.</i>", parse_mode="HTML")
        return

    if user['status'] == 'chatting' and user['partner_id']:
        handle_stop(message.chat.id, user, user['partner_id'], is_next=True)
        time.sleep(1.5) # Beri jeda agar report/upsell terkirim sebelum mencari lagi

    if not check_daily_limit(user):
        bot.send_message(message.chat.id, "<i>⚠️ Daily limit 150 matches reached.</i>", parse_mode="HTML")
        send_upsell_menu(message.chat.id, lang)
        return

    update_user(message.chat.id, {'status': 'searching', 'partner_id': None})
    msg = bot.send_message(message.chat.id, t('searching', lang), parse_mode="HTML")
    
    if attempt_match(message.chat.id, user, 'all', None): return
    bot.edit_message_text("<i>💤 Waiting for available partner...</i>", message.chat.id, msg.message_id, parse_mode="HTML")

# --- ALUR STOP, REPORT & UPSELL PRO ---
@bot.message_handler(commands=['stop'])
def stop_command(message):
    if is_spamming(message.chat.id): return 
    user = get_user(message.chat.id)
    if user and user['status'] == 'chatting':
        handle_stop(message.chat.id, user, user['partner_id'], is_next=False)

def handle_stop(stopper_id, stopper_data, partner_id, is_next=False):
    lang_stopper = stopper_data.get('language', 'en')
    update_user(stopper_id, {'status': 'idle', 'partner_id': None})
    
    if partner_id:
        partner_data = get_user(partner_id)
        lang_partner = partner_data.get('language', 'en') if partner_data else 'en'
        update_user(partner_id, {'status': 'idle', 'partner_id': None})
        
        bot.send_message(partner_id, "<i>💔 Your partner stopped the chat.</i>", parse_mode="HTML")
        send_upsell_menu(partner_id, lang_partner, target_partner_id=stopper_id)

    # Kirim Stop Text ke Stopper (termasuk saat /next ditekan)
    bot.send_message(stopper_id, t('stop_dialogue', lang_stopper), parse_mode="HTML")
    send_upsell_menu(stopper_id, lang_stopper, target_partner_id=partner_id)

def send_upsell_menu(chat_id, lang, target_partner_id=None):
    markup = InlineKeyboardMarkup()
    if target_partner_id:
        markup.add(InlineKeyboardButton("⚠️ Report Partner", callback_data=f"report_{target_partner_id}"))
        
    markup.add(InlineKeyboardButton("⭐ Subscription (Pro)", callback_data="pro_subs"))
    markup.add(InlineKeyboardButton("🎁 Invite for Free Pro", callback_data="pro_invite"))
    
    msg_text = t('upsell_pro', lang)
    if not msg_text or msg_text == '...':
        msg_text = t('upsell_pro', 'en')
        
    bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "pro_subs")
def show_subscriptions(call):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("1 Month - 35 ⭐️", callback_data="pay_1m"))
    markup.add(InlineKeyboardButton("6 Months - 185 ⭐️", callback_data="pay_6m"))
    markup.add(InlineKeyboardButton("1 Year - 335 ⭐️", callback_data="pay_1y"))
    markup.add(InlineKeyboardButton("⬅️ Back", callback_data="back_upsell"))
    
    bot.edit_message_text("<i>⭐ Choose your Pro Package (Payment via Telegram Stars):</i>", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "pro_invite")
def show_invite_menu(call):
    user = get_user(call.message.chat.id)
    ref_code = user.get('referral_code', 'ERROR')
    invites = user.get('invite_count', 0)
    bot_username = bot.get_me().username
    invite_link = f"https://t.me/{bot_username}?start={ref_code}"
    
    text = f"<i>🎁 Invite 10 people for free pro version for 1 weeks.\n\nHere your invite link:\n{invite_link}\n\nTotal Invite : {invites}</i>"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⬅️ Back", callback_data="back_upsell"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "back_upsell")
def back_to_upsell(call):
    lang = get_user(call.message.chat.id).get('language', 'en')
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_upsell_menu(call.message.chat.id, lang)

@bot.callback_query_handler(func=lambda call: call.data.startswith('report_'))
def show_report_reasons(call):
    partner_id = call.data.split('_')[1]
    markup = InlineKeyboardMarkup()
    reasons = ["Inappropriate", "Scam", "SARA", "Sexual Harassment"]
    for r in reasons: markup.add(InlineKeyboardButton(r, callback_data=f"subrep_{partner_id}"))
    bot.edit_message_text("<i>Select a reason for reporting:</i>", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("subrep_"))
def submitted_report(call):
    partner_id = call.data.split('_')[1]
    partner_data = get_user(partner_id)
    if partner_data:
        new_count = partner_data.get('report_count', 0) + 1
        update_user(partner_id, {'report_count': new_count})
    bot.edit_message_text("<i>✅ Report received. Thank you!</i>", call.message.chat.id, call.message.message_id, parse_mode="HTML")

# --- PRO GENDER PREFERENCE ---
@bot.message_handler(commands=['pro'])
def set_pro_pref(message):
    user = get_user(message.chat.id)
    if user and user.get('is_pro'):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Match with Male ♂️", callback_data="setpref_Male"), InlineKeyboardButton("Match with Female ♀️", callback_data="setpref_Female"))
        bot.send_message(message.chat.id, "<i>⭐ PRO SETTING: Choose preferred partner gender:</i>", reply_markup=markup, parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "<i>⚠️ You are not a PRO user.</i>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("setpref_"))
def save_pro_pref(call):
    pref = call.data.split('_')[1]
    update_user(call.message.chat.id, {'pref_gender': pref})
    bot.edit_message_text(f"<i>✅ Preference saved! You will now prioritize matching with: {pref}</i>", call.message.chat.id, call.message.message_id, parse_mode="HTML")

# --- ADMIN COMMAND CENTER & HELPER ---
def parse_time(time_str):
    match = re.match(r"(\d+)([HDhd])", time_str)
    if not match: return None
    val, unit = int(match.group(1)), match.group(2).upper()
    if unit == 'D': return datetime.utcnow() + timedelta(days=val)
    if unit == 'H': return datetime.utcnow() + timedelta(hours=val)
    return None

@bot.message_handler(commands=['ban', 'permaban', 'mute', 'unban', 'unmute', 'broadcast'])
def admin_commands(message):
    if str(message.chat.id) != str(ADMIN_GROUP_ID): return
    args = message.text.split()
    if len(args) < 2: return
    cmd = args[0].lower()
    
    if cmd == '/broadcast':
        pesan_broadcast = message.text.replace('/broadcast ', '', 1)
        res = supabase.table('users').select('user_id').execute()
        if res.data:
            for u in res.data:
                try:
                    time.sleep(0.05) 
                    bot.send_message(u['user_id'], f"📢 <b>ADMIN:</b>\n\n{pesan_broadcast}", parse_mode="HTML")
                except: pass 
        return

    target_user = get_user_by_username(args[1])
    if not target_user: return
    uid = target_user['user_id']
    
    if cmd == '/permaban':
        future_date = (datetime.utcnow() + timedelta(days=36500)).isoformat()
        update_user(uid, {'banned_until': future_date, 'status': 'idle'})
    elif cmd == '/ban' and len(args) >= 3:
        ban_time = parse_time(args[2])
        if ban_time: update_user(uid, {'banned_until': ban_time.isoformat(), 'status': 'idle'})

# --- INFO & PROFILE ---
@bot.message_handler(commands=['info', 'profil', 'editprofil'])
def general_commands(message):
    if is_spamming(message.chat.id): return 
    user = get_user(message.chat.id)
    if not user: return
    cmd = message.text.split()[0].lower()
    
    if cmd == '/info':
        bot.send_message(message.chat.id, "<i>📌 /search - Find partner\n/stop - End chat\n/next - Next partner\n/pro - Pro Settings</i>", parse_mode="HTML")
    elif cmd == '/profil':
        bot.send_message(message.chat.id, f"<i>👤 Profile:\nGender: {user['gender']}\nAge: {user['age']}\nCity: {html.escape(user['location'])}</i>", parse_mode="HTML")
    elif cmd == '/editprofil':
        update_user(message.chat.id, {'age': None}) 
        bot.send_message(message.chat.id, "<i>⚙️ Profile reset. Type /start.</i>", parse_mode="HTML")

# --- CALLBACK UNTUK MEMBUKA MEDIA ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('openmedia_'))
def open_media(call):
    media_id = call.data.split('_')[1]
    if media_id in media_vault:
        data = media_vault[media_id]
        try:
            bot.copy_message(call.message.chat.id, data['from_chat'], data['msg_id'])
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            bot.answer_callback_query(call.id, "❌ Gagal membuka media.")

# --- FILTER SPAM & FORWARD PESAN CHAT ---
@bot.message_handler(content_types=['text', 'photo', 'video', 'voice', 'document', 'sticker'])
def relay_message(message):
    if is_spamming(message.chat.id): return 
    user = get_user(message.chat.id)
    if not user or user['status'] != 'chatting' or not user['partner_id']: return 

    has_url = False
    entities = message.entities or message.caption_entities or []
    for ent in entities:
        if ent.type in ['url', 'text_link']: has_url = True

    if has_url:
        bot.send_message(message.chat.id, "<i>❌ Message blocked! Links are not allowed.</i>", parse_mode="HTML")
        return

    try:
        if message.content_type == 'text':
            safe_text = message.text.replace('@', '@\u200B') 
            bot.send_message(user['partner_id'], safe_text)
        elif message.content_type in ['voice', 'sticker', 'document']:
            bot.copy_message(user['partner_id'], message.chat.id, message.message_id)
        elif message.content_type in ['photo', 'video']:
            uid = str(uuid.uuid4())[:8]
            media_vault[uid] = {'from_chat': message.chat.id, 'msg_id': message.message_id}
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📁 Open Media", callback_data=f"openmedia_{uid}"))
            bot.send_message(user['partner_id'], "<i>📸 Partner sent a media.</i>", reply_markup=markup, parse_mode="HTML")
            
    except Exception:
        handle_stop(message.chat.id, user, user['partner_id'], is_next=False)

# --- GRACEFUL SHUTDOWN ---
def signal_handler(signum, frame):
    bot.stop_polling()
    os._exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

try: bot.remove_webhook()
except: pass

print("🚀 Micifind Bot V12 Siap Mengudara!")
bot.infinity_polling(timeout=60, long_polling_timeout=30)
