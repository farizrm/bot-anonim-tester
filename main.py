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

# --- SETUP SERVER RENDER (Mobile Responsive) ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family: sans-serif; text-align: center; padding: 20px;">
            <h1>🚀 Micifind Bot V8 (Production Final + Pro Update) Aktif!</h1>
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
    BotCommand("editprofil", "Edit your profile"),
    BotCommand("pro", "Pro user settings")
])

user_registration = {}
media_vault = {} 
server_stats = {'matches_in_last_minute': 0}
user_last_action = {} # Menyimpan jejak waktu untuk Anti-Spam

# --- DICTIONARY BAHASA GLOBAL ---
LANGUAGES = {
    'en': '🇬🇧 English', 'id': '🇮🇩 Indonesia', 'th': '🇹🇭 Thai', 
    'tl': '🇵🇭 Tagalog', 'hi': '🇮🇳 Hindi', 'ru': '🇷🇺 Russian', 
    'vi': '🇻🇳 Vietnamese', 'es': '🇪🇸 Spanish', 'pt': '🇧🇷 Portuguese', 
    'ar': '🇸🇦 Arabic', 'de': '🇩🇪 German', 'ja': '🇯🇵 Japanese', 'zh': '🇨🇳 Chinese'
}

# Teks dipertahankan SAMA PERSIS dengan skrip asli untuk 'en' dan 'id'
TEXTS = {
    'welcome': {
        'en': "<i>👋 Welcome to the Micifind bot! Here you can anonymously find people around you!\n\n⚠️ By using this bot, you agree that Micifind is not responsible for any personal data shared in chats.\n\n👇 Please select your language below:</i>",
        'id': "<i>👋 Selamat datang di bot Micifind! Di sini kamu bisa mencari orang di sekitarmu secara anonim!\n\n⚠️ Dengan menggunakan bot ini, kamu setuju bahwa Micifind tidak bertanggung jawab atas data pribadi apa pun yang dibagikan di dalam obrolan.\n\n👇 Silakan pilih bahasamu di bawah ini:</i>",
        'th': "<i>👋 ยินดีต้อนรับสู่ Micifind! ค้นหาผู้คนรอบตัวคุณแบบไม่ระบุตัวตน\n\n👇 โปรดเลือกภาษาของคุณ:</i>",
        'tl': "<i>👋 Maligayang pagdating sa Micifind! Maghanap ng mga tao sa paligid mo.\n\n👇 Piliin ang iyong wika:</i>",
        'hi': "<i>👋 Micifind में आपका स्वागत है! अपने आस-पास के लोगों को खोजें।\n\n👇 अपनी भाषा चुनें:</i>",
        'ru': "<i>👋 Добро пожаловать в Micifind! Ищите людей вокруг анонимно.\n\n👇 Выберите язык:</i>",
        'vi': "<i>👋 Chào mừng đến với Micifind! Tìm kiếm mọi người xung quanh bạn.\n\n👇 Chọn ngôn ngữ:</i>",
        'es': "<i>👋 ¡Bienvenido a Micifind! Encuentra personas a tu alrededor de forma anónima.\n\n👇 Selecciona tu idioma:</i>",
        'pt': "<i>👋 Bem-vindo ao Micifind! Encontre pessoas ao seu redor anonimamente.\n\n👇 Selecione seu idioma:</i>",
        'ar': "<i>👋 أهلاً بك في Micifind! ابحث عن أشخاص حولك بهوية مجهولة.\n\n👇 اختر لغتك:</i>",
        'de': "<i>👋 Willkommen bei Micifind! Finde Leute in deiner Nähe anonym.\n\n👇 Wähle deine Sprache:</i>",
        'ja': "<i>👋 Micifindへようこそ！周りの人を匿名で見つけましょう。\n\n👇 言語を選択してください:</i>",
        'zh': "<i>👋 欢迎来到 Micifind！匿名寻找你周围的人。\n\n👇 请选择你的语言:</i>"
    },
    'upsell_pro': {
        'en': "<i>✨ Want to match ONLY with the opposite gender and get UNLIMITED matches? Subscribe to the package below:</i>",
        'id': "<i>✨ Ingin match hanya dengan lawan jenis dan unlimited match? silahkan berlangganan paket di bawah ini :</i>",
        'th': "<i>✨ ต้องการจับคู่กับเพศตรงข้ามและจับคู่ได้ไม่จำกัดหรือไม่ สมัครสมาชิกด้านล่าง:</i>",
        'tl': "<i>✨ Gustong makipag-match LAMANG sa opposite gender at UNLIMITED matches? Mag-subscribe sa ibaba:</i>",
        'hi': "<i>✨ केवल विपरीत लिंग के साथ मैच करना चाहते हैं और असीमित मैच चाहते हैं? नीचे सदस्यता लें:</i>",
        'ru': "<i>✨ Хотите совпадения ТОЛЬКО с противоположным полом и БЕЗЛИМИТ? Подпишитесь ниже:</i>",
        'vi': "<i>✨ Muốn CHỈ ghép đôi với người khác giới và KHÔNG GIỚI HẠN? Đăng ký bên dưới:</i>",
        'es': "<i>✨ ¿Quieres coincidir SOLO con el sexo opuesto y coincidencias ILIMITADAS? Suscríbete abajo:</i>",
        'pt': "<i>✨ Quer dar match APENAS com o sexo oposto e ILIMITADO? Assine abaixo:</i>",
        'ar': "<i>✨ هل تريد التطابق فقط مع الجنس الآخر ومطابقات غير محدودة؟ اشترك أدناه:</i>",
        'de': "<i>✨ Möchtest du NUR mit dem anderen Geschlecht matchen und UNBEGRENZT? Abonniere unten:</i>",
        'ja': "<i>✨ 異性とのみマッチし、無制限のマッチをご希望ですか？ 以下で購読してください:</i>",
        'zh': "<i>✨ 想要仅与异性匹配并获得无限匹配吗？在下面订阅:</i>"
    },
    'limit_reached': {
        'en': "<i>⚠️ You have reached the daily limit of 150 matches.</i>",
        'id': "<i>⚠️ Kamu telah mencapai batas harian 150 match hari ini.</i>",
        'th': "<i>⚠️ คุณถึงขีดจำกัดรายวัน 150 การจับคู่แล้ว</i>",
        'tl': "<i>⚠️ Naabot mo na ang araw-araw na limitasyon na 150 matches.</i>",
        'hi': "<i>⚠️ आप 150 मैचों की दैनिक सीमा तक पहुंच गए हैं।</i>",
        'ru': "<i>⚠️ Вы достигли дневного лимита в 150 совпадений.</i>",
        'vi': "<i>⚠️ Bạn đã đạt giới hạn 150 lượt ghép mỗi ngày.</i>",
        'es': "<i>⚠️ Has alcanzado el límite diario de 150 coincidencias.</i>",
        'pt': "<i>⚠️ Você atingiu o limite diário de 150 matches.</i>",
        'ar': "<i>⚠️ لقد وصلت إلى الحد اليومي البالغ 150 مطابقة.</i>",
        'de': "<i>⚠️ Du hast das Tageslimit von 150 Matches erreicht.</i>",
        'ja': "<i>⚠️ 1日の制限である150マッチに達しました。</i>",
        'zh': "<i>⚠️ 您已达到每天150次匹配的限制。</i>"
    }
}

def get_t(lang, key):
    return TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get('en', ''))

# --- FUNGSI ANTI-SPAM (RATE LIMITER) ---
def is_spamming(chat_id):
    """Mengembalikan True jika user mengirim pesan kurang dari 1 detik yang lalu."""
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
            
            log_msg = f"📊 *LOG ANALITIK (1 Menit Terakhir)*\n\n👥 Total Users DB: {total_users}\n⚡ Match Making: {mps:.2f} match/detik\n🟢 Status VPS: AMAN"
            bot.send_message(ADMIN_GROUP_ID, log_msg, message_thread_id=LOG_THREAD_ID, parse_mode="Markdown")
            
            server_stats['matches_in_last_minute'] = 0 
        except Exception as e:
            print("Log error:", e)

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

def check_punishment(user):
    if not user: return False, None
    now = datetime.utcnow().isoformat()
    if user.get('banned_until') and user['banned_until'] > now:
        return True, "banned"
    return False, None

def generate_ref_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# --- LOGIKA DAILY LIMIT (150 MATCH) ---
def check_daily_limit(user):
    if user.get('is_pro'): return True 
    today = datetime.utcnow().date().isoformat()
    if user.get('last_match_date') != today:
        update_user(user['user_id'], {'matches_today': 0, 'last_match_date': today})
        return True
    return user.get('matches_today', 0) < 150

# --- ALUR REGISTRASI ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_spamming(message.chat.id): return 
    
    args = message.text.split()
    ref_code = args[1] if len(args) > 1 else None

    user = get_user(message.chat.id)
    is_punished, reason = check_punishment(user)
    if is_punished:
        bot.send_message(message.chat.id, "<i>⛔ Akun kamu sedang diblokir karena melanggar aturan komunitas.</i>", parse_mode="HTML")
        return

    # LOGIKA REFERRAL ANTI-TUYUL (Hanya berjalan jika user BENAR-BENAR belum ada di database)
    if not user:
        new_ref = generate_ref_code()
        supabase.table('users').upsert({'user_id': message.chat.id, 'referral_code': new_ref, 'invite_count': 0}).execute()
        
        if ref_code:
            referrer = supabase.table('users').select('*').eq('referral_code', ref_code).execute()
            if referrer.data and str(referrer.data[0]['user_id']) != str(message.chat.id):
                ref_user = referrer.data[0]
                new_count = ref_user.get('invite_count', 0) + 1
                
                if new_count >= 10:
                    pro_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
                    update_user(ref_user['user_id'], {'invite_count': 0, 'is_pro': True, 'pro_until': pro_date})
                    bot.send_message(ref_user['user_id'], "<i>🎉 You successfully invited 10 people! You are now PRO for 1 Week!</i>", parse_mode="HTML")
                else:
                    update_user(ref_user['user_id'], {'invite_count': new_count})

    if user and user.get('age'):
        if message.from_user.username:
            update_user(message.chat.id, {'username': message.from_user.username})
        lang = user.get('language', 'en')
        text = "<i>🌟 You are already registered! Use /search to find a partner.</i>" if lang == "en" else "<i>🌟 Kamu sudah terdaftar! Gunakan /search untuk mencari partner.</i>"
        bot.send_message(message.chat.id, text, parse_mode="HTML")
        return

    markup = InlineKeyboardMarkup()
    row = []
    for code, name in LANGUAGES.items():
        row.append(InlineKeyboardButton(name, callback_data=f"lang_{code}"))
        if len(row) == 2:
            markup.add(*row)
            row = []
    if row: markup.add(*row)
    
    # Menyesuaikan bahasa OS Pengguna saat /start, fallback ke English
    user_lang_code = message.from_user.language_code
    if user_lang_code not in LANGUAGES: user_lang_code = 'en'
    
    bot.send_message(message.chat.id, get_t(user_lang_code, 'welcome'), reply_markup=markup, parse_mode="HTML")
    
@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    lang = call.data.split('_')[1]
    uname = call.message.chat.username or ""
    user_registration[call.message.chat.id] = {'language': lang, 'username': uname}
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Male ♂️", callback_data="gender_male"), InlineKeyboardButton("Female ♀️", callback_data="gender_female"))
    text = "<i>👤 Select your gender:</i>" if lang == "en" else "<i>👤 Pilih gender kamu:</i>"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('gender_'))
def set_gender(call):
    chat_id = call.message.chat.id
    if chat_id not in user_registration: return
    lang = user_registration[chat_id]['language']
    user_registration[chat_id]['gender'] = "Male" if call.data == "gender_male" else "Female"
    
    text = "<i>🎂 Enter your age (Min 17):</i>" if lang == "en" else "<i>🎂 Masukkan umur kamu (Minimal 17):</i>"
    msg = bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="HTML")
    bot.register_next_step_handler(msg, process_age)

def process_age(message):
    chat_id = message.chat.id
    lang = user_registration.get(chat_id, {}).get('language', 'en')
    if not message.text.isdigit() or int(message.text) < 17:
        text = "<i>❌ You must be at least 17 years old. Click /start to try again.</i>" if lang == "en" else "<i>❌ Kamu harus berumur minimal 17 tahun. Klik /start untuk mengulang.</i>"
        bot.send_message(chat_id, text, parse_mode="HTML")
        return
    user_registration[chat_id]['age'] = int(message.text)
    text = "<i>🗺️ Enter your Province (e.g., Jawa Timur):</i>" if lang == "en" else "<i>🗺️ Masukkan Provinsi kamu (Contoh: Jawa Timur):</i>"
    msg = bot.send_message(chat_id, text, parse_mode="HTML")
    bot.register_next_step_handler(msg, process_province)

def process_province(message):
    chat_id = message.chat.id
    lang = user_registration.get(chat_id, {}).get('language', 'en')
    user_registration[chat_id]['province'] = message.text.strip().title()
    text = "<i>🏙️ Enter your City (e.g., Malang):</i>" if lang == "en" else "<i>🏙️ Masukkan Kota kamu (Contoh: Malang):</i>"
    msg = bot.send_message(chat_id, text, parse_mode="HTML")
    bot.register_next_step_handler(msg, process_location)

def process_location(message):
    chat_id = message.chat.id
    lang = user_registration.get(chat_id, {}).get('language', 'en')
    user_registration[chat_id]['location'] = message.text.strip().title()
    text = "<i>📝 Write a short 'About Me' or your description:</i>" if lang == "en" else "<i>📝 Tulis deskripsi singkat 'Tentang Saya':</i>"
    msg = bot.send_message(chat_id, text, parse_mode="HTML")
    bot.register_next_step_handler(msg, process_about)

def process_about(message):
    chat_id = message.chat.id
    data = user_registration.get(chat_id)
    if not data: return
    data['about'] = message.text
    create_or_update_user(chat_id, data)
    
    lang = data['language']
    cool_txt = "<i>✨ Cool! Here's what your profile looks like:</i>" if lang == "en" else "<i>✨ Keren! Ini tampilan profilmu:</i>"
    cmds = "<b>📌 Commands:</b>\n/search - Find a new partner 🔍\n/stop - End the chat 🛑\n/next - Find the next partner ⏭️\n/info - Show all commands ℹ️" if lang == "en" else "<b>📌 Daftar Perintah:</b>\n/search - Cari partner baru 🔍\n/stop - Akhiri obrolan 🛑\n/next - Cari partner selanjutnya ⏭️\n/info - Lihat semua perintah ℹ️"
    
    profile_text = f"{cool_txt}\n\n⚧️ Gender: {html.escape(data['gender'])}\n🎂 Age: {data['age']}\n🏙️ City: {html.escape(data['location'])}\n📝 About Me: {html.escape(data['about'])}\n\n{cmds}"
    bot.send_message(chat_id, profile_text, parse_mode="HTML")

# --- ALUR MATCHMAKING ---
def attempt_match(chat_id, user_data, scope, value):
    current_me = get_user(chat_id)
    if current_me and current_me['status'] == 'chatting': return True
    
    query = supabase.table('users').select('*').eq('status', 'searching').neq('user_id', chat_id)
    if scope == 'location': query = query.eq('location', value)
    elif scope == 'province': query = query.eq('province', value)
    
    # LOGIKA PRO PRIORITY GENDER
    if current_me.get('is_pro') and current_me.get('pref_gender'):
        query = query.eq('gender', current_me['pref_gender'])

    res = query.limit(1).execute()
    if res.data:
        partner = res.data[0]
        
        # Tambah counter Daily Limit
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
    lang = get_user(to_id).get('language', 'en')
    title = "<i>🎉 Partner Found!</i>" if lang == "en" else "<i>🎉 Partner Ditemukan!</i>"
    disc = "<i>⚠️ Disclaimer: Always start conversations politely and never make your partner uncomfortable by discussing 18+ topics!</i>" if lang == "en" else "<i>⚠️ Peringatan: Selalu mulai percakapan dengan sopan dan jangan pernah membuat partnermu tidak nyaman dengan membahas topik 18+!</i>"
    
    text = f"{title}\n\n⚧️ Gender: {html.escape(partner_data['gender'])}\n🎂 Age: {partner_data['age']}\n🏙️ City: {html.escape(partner_data['location'])}\n📝 About Me: {html.escape(partner_data['about'])}\n\n{disc}\n@micifindbot"
    bot.send_message(to_id, text, parse_mode="HTML")

@bot.message_handler(commands=['search', 'next'])
def search_partner(message):
    if is_spamming(message.chat.id): return 
    
    user = get_user(message.chat.id)
    if not user:
        bot.send_message(message.chat.id, "<i>⚠️ Please /start first.</i>", parse_mode="HTML")
        return
    
    is_punished, reason = check_punishment(user)
    if is_punished:
        bot.send_message(message.chat.id, "<i>⛔ Kamu tidak bisa mencari partner karena akun diblokir.</i>", parse_mode="HTML")
        return

    lang = user.get('language', 'en')

    # CHECK DAILY LIMIT
    if not check_daily_limit(user):
        bot.send_message(message.chat.id, get_t(lang, 'limit_reached'), parse_mode="HTML")
        send_upsell_menu(message.chat.id, lang)
        return
    
    if user['status'] == 'searching':
        text_wait = "<i>⏳ You are already searching! Please wait, or type /stop to cancel.</i>" if lang == "en" else "<i>⏳ Kamu sedang dalam antrean pencarian! Mohon tunggu, atau ketik /stop untuk membatalkan.</i>"
        bot.send_message(message.chat.id, text_wait, parse_mode="HTML")
        return

    if user['status'] == 'chatting' and message.text == '/search':
        text = "<i>💬 You are in a chat! Use /stop to end it. 🔄</i>" if lang == "en" else "<i>💬 Kamu sedang obrolan aktif! Gunakan /stop untuk mengakhiri. 🔄</i>"
        bot.send_message(message.chat.id, text, parse_mode="HTML")
        return

    if user['status'] == 'chatting' and user['partner_id']:
        handle_stop(message.chat.id, user, user['partner_id'], is_next=True)
        time.sleep(1.5) # Memberi jeda agar pesan report/upsell terkirim dulu sebelum searching

    update_user(message.chat.id, {'status': 'searching', 'partner_id': None})
    
    text_search = "<i>🔍 Searching for a partner in your city... ⏳</i>" if lang == "en" else "<i>🔍 Mencari partner di kotamu... ⏳</i>"
    msg = bot.send_message(message.chat.id, text_search, parse_mode="HTML")
    
    if attempt_match(message.chat.id, user, 'location', user['location']): return
    time.sleep(3)
    
    if get_user(message.chat.id)['status'] != 'searching': return
    if attempt_match(message.chat.id, user, 'location', user['location']): return
    
    text_prov = "<i>📡 Expanding search to your province... ⏳</i>" if lang == "en" else "<i>📡 Belum ada, memperluas pencarian ke provinsimu... ⏳</i>"
    try: bot.edit_message_text(text_prov, message.chat.id, msg.message_id, parse_mode="HTML")
    except: pass
    
    if attempt_match(message.chat.id, user, 'province', user['province']): return
    time.sleep(3)
    
    if get_user(message.chat.id)['status'] != 'searching': return
    if attempt_match(message.chat.id, user, 'province', user['province']): return
    
    text_rnd = "<i>🌍 Expanding search globally... ⏳</i>" if lang == "en" else "<i>🌍 Memperluas pencarian secara acak... ⏳</i>"
    try: bot.edit_message_text(text_rnd, message.chat.id, msg.message_id, parse_mode="HTML")
    except: pass
    
    if attempt_match(message.chat.id, user, 'all', None): return
    
    text_wait = "<i>💤 No partners available right now. We will connect you as soon as someone joins! (Type /stop to cancel)</i>" if lang == "en" else "<i>💤 Belum ada partner yang tersedia. Kamu akan otomatis terhubung begitu ada yang masuk! (Ketik /stop untuk membatalkan)</i>"
    try: bot.edit_message_text(text_wait, message.chat.id, msg.message_id, parse_mode="HTML")
    except: pass

# --- ALUR STOP, REPORT & UPSELL ---
@bot.message_handler(commands=['stop'])
def stop_command(message):
    if is_spamming(message.chat.id): return 
    
    user = get_user(message.chat.id)
    if not user: return
    lang = user.get('language', 'en')
    
    if user['status'] == 'chatting':
        handle_stop(message.chat.id, user, user['partner_id'], is_next=False)
    elif user['status'] == 'searching':
        update_user(message.chat.id, {'status': 'idle', 'partner_id': None})
        text = "<i>🛑 Search cancelled.\nPress /search for a new partner! 🔄</i>" if lang == "en" else "<i>🛑 Pencarian dibatalkan.\nTekan /search untuk mencari partner baru! 🔄</i>"
        bot.send_message(message.chat.id, text, parse_mode="HTML")
    else:
        text = "<i>🚫 You are not in a chat right now.\nPress /search for a new partner! 🔄</i>" if lang == "en" else "<i>🚫 Kamu sedang tidak dalam obrolan saat ini.\nTekan /search untuk mencari partner baru! 🔄</i>"
        bot.send_message(message.chat.id, text, parse_mode="HTML")

def handle_stop(stopper_id, stopper_data, partner_id, is_next=False):
    lang_stopper = stopper_data.get('language', 'en')
    update_user(stopper_id, {'status': 'idle', 'partner_id': None})
    
    if partner_id:
        partner_data = get_user(partner_id)
        lang_partner = partner_data.get('language', 'en') if partner_data else 'en'
        update_user(partner_id, {'status': 'idle', 'partner_id': None})
        
        markup_partner = InlineKeyboardMarkup()
        btn_text = "Find New Partner! 🔄" if lang_partner == "en" else "Cari Partner Baru! 🔄"
        markup_partner.add(InlineKeyboardButton(btn_text, callback_data="btn_search"))
        msg_partner = "<i>💔 Your partner has ended the chat.\nClick /next or /search to find a new partner!</i>" if lang_partner == "en" else "<i>💔 Partnermu telah mengakhiri obrolan.\nTekan /next atau /search untuk mencari partner baru!</i>"
        
        try:
            bot.send_message(partner_id, msg_partner, reply_markup=markup_partner, parse_mode="HTML")
            send_upsell_menu(partner_id, lang_partner)
        except:
            pass 

    # Ini akan tereksekusi pada /stop maupun /next, memunculkan report terlebih dahulu
    markup_report = InlineKeyboardMarkup()
    markup_report.add(InlineKeyboardButton("⚠️ Report Partner", callback_data=f"report_{partner_id}"))
    msg_stopper = "<i>🛑 Hmmmm... you stopped the dialogue.\nPress /search for a new partner! 🔄</i>" if lang_stopper == "en" else "<i>🛑 Hmmmm... kamu mengakhiri obrolan.\nTekan /search untuk mencari partner baru! 🔄</i>"
    
    try:
        bot.send_message(stopper_id, msg_stopper, reply_markup=markup_report, parse_mode="HTML")
        send_upsell_menu(stopper_id, lang_stopper)
    except:
        pass

def send_upsell_menu(chat_id, lang):
    markup_upsell = InlineKeyboardMarkup()
    markup_upsell.add(InlineKeyboardButton("1 Month - 35 ⭐️", callback_data="pay_1m"))
    markup_upsell.add(InlineKeyboardButton("6 Month - 185 ⭐️", callback_data="pay_6m"))
    markup_upsell.add(InlineKeyboardButton("1 Years - 335 ⭐️", callback_data="pay_1y"))
    markup_upsell.add(InlineKeyboardButton("Invite for free Pro 🎁", callback_data="pro_invite"))
    bot.send_message(chat_id, get_t(lang, 'upsell_pro'), reply_markup=markup_upsell, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "btn_search")
def btn_search_handler(call):
    message = call.message
    message.text = '/search'
    search_partner(message)

# --- MENU PRO PAYMENT & INVITE CALLBACKS ---
@bot.callback_query_handler(func=lambda call: call.data == "pro_invite")
def show_invite_menu(call):
    user = get_user(call.message.chat.id)
    ref_code = user.get('referral_code', 'ERROR')
    invites = user.get('invite_count', 0)
    bot_username = bot.get_me().username
    invite_link = f"https://t.me/{bot_username}?start={ref_code}"
    
    text = f"<i>🎁 Invite 10 people for free pro version for 1 weeks.\n\nHere your invite link :\n\n{invite_link}\n\nTotal Invite : {invites}</i>"
    
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
    lang = get_user(call.message.chat.id).get('language', 'en')
    markup = InlineKeyboardMarkup()
    reasons = ["Inappropriate / Tidak senonoh", "Scam / Penipuan", "SARA", "Sexual Harassment"]
    for r in reasons:
        markup.add(InlineKeyboardButton(r, callback_data=f"subrep_{partner_id}"))
        
    text = "<i>Select a reason for reporting:</i>" if lang == "en" else "<i>Pilih alasan melaporkan:</i>"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("subrep_"))
def submitted_report(call):
    partner_id = call.data.split('_')[1]
    lang = get_user(call.message.chat.id).get('language', 'en')
    
    partner_data = get_user(partner_id)
    if partner_data:
        new_count = partner_data.get('report_count', 0) + 1
        update_user(partner_id, {'report_count': new_count})
        
        if new_count % 50 == 0 and ADMIN_GROUP_ID:
            uname = partner_data.get('username', 'Tidak ada username')
            ban_count = partner_data.get('ban_count', 0)
            alert = f"🚨 *URGENT REPORT ALERT* 🚨\n\nUser: @{uname}\nID: `{partner_id}`\nTelah mencapai *{new_count} Report* dari user lain!\nJumlah di-Ban sebelumnya: {ban_count} kali.\n\n_Gunakan command /ban atau /permaban di grup ini._"
            bot.send_message(ADMIN_GROUP_ID, alert, message_thread_id=REPORT_THREAD_ID, parse_mode="Markdown")

    text = "<i>✅ Report received. Thank you for keeping the community safe!</i>" if lang == "en" else "<i>✅ Laporan diterima. Terima kasih telah menjaga keamanan komunitas ini!</i>"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML")

# --- ADMIN COMMAND CENTER & HELPER ---
@bot.message_handler(commands=['get_topic_id'])
def helper_get_topic(message):
    if message.message_thread_id:
        bot.reply_to(message, f"📌 ID Topik ini adalah: `{message.message_thread_id}`\n\n_Copy angka di atas dan jadikan Value di pengaturan Environment Render._", parse_mode="Markdown")
    else:
        bot.reply_to(message, "Grup ini tidak menggunakan fitur Topik (Thread).")

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
    if len(args) < 2:
        bot.reply_to(message, "Format salah. Contoh: /ban @username 1D atau /broadcast Pesan")
        return
        
    cmd = args[0].lower()
    
    if cmd == '/broadcast':
        pesan_broadcast = message.text.replace('/broadcast ', '', 1)
        res = supabase.table('users').select('user_id').execute()
        if res.data:
            berhasil = 0
            for u in res.data:
                try:
                    time.sleep(0.05) 
                    bot.send_message(u['user_id'], f"📢 <b>PENGUMUMAN ADMIN:</b>\n\n{pesan_broadcast}", parse_mode="HTML")
                    berhasil += 1
                except:
                    pass 
            bot.reply_to(message, f"✅ Broadcast selesai! Berhasil dikirim ke {berhasil} user.")
        return

    target_user = get_user_by_username(args[1])
    if not target_user:
        bot.reply_to(message, "Username tidak ditemukan di database.")
        return
        
    uid = target_user['user_id']
    
    if cmd == '/permaban':
        future_date = (datetime.utcnow() + timedelta(days=36500)).isoformat()
        update_user(uid, {'banned_until': future_date, 'ban_count': target_user['ban_count'] + 1, 'status': 'idle'})
        bot.reply_to(message, f"🔨 User @{args[1]} di-BANNED PERMANEN.")
    
    elif cmd == '/ban' and len(args) >= 3:
        ban_time = parse_time(args[2])
        if ban_time:
            update_user(uid, {'banned_until': ban_time.isoformat(), 'ban_count': target_user['ban_count'] + 1, 'status': 'idle'})
            bot.reply_to(message, f"🔨 User @{args[1]} di-Banned sampai {ban_time.strftime('%Y-%m-%d %H:%M:%S')} UTC.")
    
    elif cmd == '/mute' and len(args) >= 3:
        mute_time = parse_time(args[2])
        if mute_time:
            update_user(uid, {'muted_until': mute_time.isoformat()})
            bot.reply_to(message, f"🔇 User @{args[1]} di-Mute sampai {mute_time.strftime('%Y-%m-%d %H:%M:%S')} UTC.")
            
    elif cmd in ['/unban', '/unmute']:
        update_user(uid, {'banned_until': None, 'muted_until': None})
        bot.reply_to(message, f"🕊️ User @{args[1]} telah dilepas dari status Ban/Mute.")

# --- SETTING PRO & GENDER PRIORITY ---
@bot.message_handler(commands=['pro'])
def set_pro_pref(message):
    user = get_user(message.chat.id)
    if user and user.get('is_pro'):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Match with Male ♂️", callback_data="setpref_Male"), 
                   InlineKeyboardButton("Match with Female ♀️", callback_data="setpref_Female"))
        bot.send_message(message.chat.id, "<i>⭐ PRO SETTING: Choose preferred partner gender:</i>", reply_markup=markup, parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "<i>⚠️ You are not a PRO user or PRO expired.</i>", parse_mode="HTML")
        
@bot.callback_query_handler(func=lambda call: call.data.startswith("setpref_"))
def save_pro_pref(call):
    pref = call.data.split('_')[1]
    update_user(call.message.chat.id, {'pref_gender': pref})
    bot.edit_message_text(f"<i>✅ Preference saved! You will now prioritize matching with: {pref}</i>", call.message.chat.id, call.message.message_id, parse_mode="HTML")

# --- INFO & PROFILE ---
@bot.message_handler(commands=['info', 'profil', 'Profil', 'editprofil', 'EditProfil'])
def general_commands(message):
    if is_spamming(message.chat.id): return 
    
    user = get_user(message.chat.id)
    if not user: return
    lang = user.get('language', 'en')
    cmd = message.text.split()[0].lower()
    
    if cmd == '/info':
        info_en = "<b>📌 Bot Commands</b>\n\n/search - Find a new partner 🔍\n/stop - End the chat 🛑\n/next - Find the next partner ⏭️\n/info - See all commands ℹ️\n/Profil - View your profile 👤\n/EditProfil - Edit your profile setting ⚙️\n/pro - Pro settings ⭐"
        info_id = "<b>📌 Daftar Perintah</b>\n\n/search - Cari partner baru 🔍\n/stop - Akhiri obrolan 🛑\n/next - Cari partner selanjutnya ⏭️\n/info - Lihat semua perintah ℹ️\n/Profil - Lihat profilmu 👤\n/EditProfil - Edit pengaturan profil ⚙️\n/pro - Pengaturan Pro ⭐"
        bot.send_message(message.chat.id, info_en if lang == "en" else info_id, parse_mode="HTML")
    
    elif cmd == '/profil':
        title = "<b>👤 Your Profile:</b>" if lang == "en" else "<b>👤 Profil Kamu:</b>"
        bot.send_message(message.chat.id, f"{title}\n\n⚧️ Gender: {html.escape(user['gender'])}\n🎂 Age: {user['age']}\n🗺️ Province: {html.escape(user.get('province', '-'))}\n🏙️ City: {html.escape(user['location'])}\n📝 About Me: {html.escape(user['about'])}", parse_mode="HTML")
    
    elif cmd == '/editprofil':
        update_user(message.chat.id, {'age': None}) 
        text = "<i>⚙️ Profile reset. Please type /start to create a new profile.</i>" if lang == "en" else "<i>⚙️ Profil direset. Silakan ketik /start untuk membuat profil baru.</i>"
        bot.send_message(message.chat.id, text, parse_mode="HTML")

# --- CALLBACK UNTUK MEMBUKA MEDIA ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('openmedia_'))
def open_media(call):
    media_id = call.data.split('_')[1]
    
    if media_id in media_vault:
        data = media_vault[media_id]
        try:
            bot.copy_message(call.message.chat.id, data['from_chat'], data['msg_id'])
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception as e:
            bot.answer_callback_query(call.id, "❌ Gagal membuka media.")
    else:
        bot.answer_callback_query(call.id, "⚠️ Media sudah kedaluwarsa atau ditarik.", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

# --- FILTER SPAM & FORWARD PESAN CHAT ---
@bot.message_handler(content_types=['text', 'photo', 'video', 'voice', 'document', 'sticker'])
def relay_message(message):
    if is_spamming(message.chat.id): return 
    
    user = get_user(message.chat.id)
    if not user: return
    lang = user.get('language', 'en')

    if user['status'] != 'chatting' or not user['partner_id']:
        return 
        
    now = datetime.utcnow().isoformat()
    if user.get('muted_until') and user['muted_until'] > now:
        bot.send_message(message.chat.id, "<i>🔇 Kamu sedang di-mute oleh sistem admin.</i>", parse_mode="HTML")
        return

    has_url = False
    entities = message.entities or message.caption_entities or []
    for ent in entities:
        if ent.type in ['url', 'text_link']:
            has_url = True

    if has_url:
        warn = "<i>❌ Pesan diblokir! Dilarang mengirim tautan/link di bot ini.</i>" if lang == "id" else "<i>❌ Message blocked! Links are not allowed.</i>"
        bot.send_message(message.chat.id, warn, parse_mode="HTML")
        return

    try:
        if message.content_type == 'text':
            safe_text = message.text.replace('@', '@\u200B') 
            bot.send_message(user['partner_id'], safe_text)
            
        elif message.content_type in ['voice', 'sticker', 'document']:
            bot.copy_message(user['partner_id'], message.chat.id, message.message_id)

        elif message.content_type in ['photo', 'video']:
            partner_lang = get_user(user['partner_id']).get('language', 'en')
            
            media_name = "Foto" if message.content_type == 'photo' else "Video"
            if partner_lang == 'en':
                media_name = "Photo" if message.content_type == 'photo' else "Video"
                
            uid = str(uuid.uuid4())[:8]
            media_vault[uid] = {'from_chat': message.chat.id, 'msg_id': message.message_id}
            
            btn_text = f"📁 Buka {media_name}" if partner_lang == "id" else f"📁 Open {media_name}"
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(btn_text, callback_data=f"openmedia_{uid}"))
            
            notif = f"<i>📸 Partner mengirim sebuah {media_name}.</i>" if partner_lang == "id" else f"<i>📸 Partner sent a {media_name}.</i>"
            bot.send_message(user['partner_id'], notif, reply_markup=markup, parse_mode="HTML")
            
    except Exception as e:
        handle_stop(message.chat.id, user, user['partner_id'], is_next=False)
        warn_msg = "<i>⚠️ Pesan gagal terkirim. Partnermu sepertinya telah menghapus akun atau memblokir bot ini. Obrolan dihentikan secara otomatis.</i>" if lang == "id" else "<i>⚠️ Message failed. Your partner may have blocked the bot. Chat ended.</i>"
        bot.send_message(message.chat.id, warn_msg, parse_mode="HTML")

# --- GRACEFUL SHUTDOWN (Mencegah Error 409 saat Render Deploy) ---
def signal_handler(signum, frame):
    print("Menerima perintah shutdown dari Render. Mematikan koneksi lama...")
    bot.stop_polling()
    os._exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

try:
    bot.remove_webhook()
except:
    pass

print("🚀 Micifind Bot V8 (Production Final + Pro Update) Siap Mengudara!")
bot.infinity_polling(timeout=60, long_polling_timeout=30)
