import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import os
import threading
import time
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from supabase import create_client, Client

# --- SETUP SERVER RENDER (RESPONSIF MOBILE) ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: sans-serif; text-align: center; padding: 20px; background-color: #f4f4f9; }
                h1 { font-size: 24px; color: #333; }
                @media (max-width: 600px) { body { padding: 10px; } h1 { font-size: 18px; } }
            </style>
        </head>
        <body>
            <h1>🚀 Micifind Bot Sedang Berjalan Sempurna!</h1>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode('utf-8'))

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# --- SETUP BOT & DATABASE ---
TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

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

# --- FUNGSI BANTUAN DATABASE ---
def get_user(user_id):
    res = supabase.table('users').select('*').eq('user_id', user_id).execute()
    return res.data[0] if res.data else None

def update_user(user_id, data):
    supabase.table('users').update(data).eq('user_id', user_id).execute()

def create_or_update_user(user_id, data):
    data['user_id'] = user_id
    supabase.table('users').upsert(data).execute()

# --- ALUR REGISTRASI ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = get_user(message.chat.id)
    if user and user.get('age'):
        lang = user.get('language', 'en')
        text = "<i>🌟 You are already registered! Use /search to find a partner.</i>" if lang == "en" else "<i>🌟 Kamu sudah terdaftar! Gunakan /search untuk mencari partner.</i>"
        bot.send_message(message.chat.id, text, parse_mode="HTML")
        return

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
               InlineKeyboardButton("Indonesia 🇮🇩", callback_data="lang_id"))
    
    welcome_msg = ("<i>👋 Welcome to the Micifind bot! Here you can anonymously find people around you!\n"
                   "🎉 Have fun chatting and make sure your conversations are fun!\n\n"
                   "👇 Please select your language below:</i>")
    bot.send_message(message.chat.id, welcome_msg, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    lang = "en" if call.data == "lang_en" else "id"
    user_registration[call.message.chat.id] = {'language': lang}
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Male ♂️", callback_data="gender_male"),
               InlineKeyboardButton("Female ♀️", callback_data="gender_female"))
    
    text = "<i>👤 Select your gender:</i>" if lang == "en" else "<i>👤 Pilih gender kamu:</i>"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('gender_'))
def set_gender(call):
    chat_id = call.message.chat.id
    if chat_id not in user_registration: return
        
    lang = user_registration[chat_id]['language']
    gender = "Male" if call.data == "gender_male" else "Female"
    user_registration[chat_id]['gender'] = gender
    
    text = "<i>🎂 Enter your age (Min 17):</i>" if lang == "en" else "<i>🎂 Masukkan umur kamu (Minimal 17):</i>"
    msg = bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="HTML")
    bot.register_next_step_handler(msg, process_age)

def process_age(message):
    chat_id = message.chat.id
    lang = user_registration.get(chat_id, {}).get('language', 'en')
    
    if not message.text.isdigit() or int(message.text) < 17:
        text = "<i>❌ You must be at least 17 years old to use this bot. Click /start to try again.</i>" if lang == "en" else "<i>❌ Kamu harus berumur minimal 17 tahun. Klik /start untuk mengulang.</i>"
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
    disclaimer = "<i>⚠️ Disclaimer: Always start conversations politely and never make your partner uncomfortable by discussing 18+ topics!</i>" if lang == "en" else "<i>⚠️ Peringatan: Selalu mulai percakapan dengan sopan dan jangan pernah membuat partnermu tidak nyaman dengan membahas topik 18+!</i>"
    cmds = "<b>📌 Commands:</b>\n/search - Find a new partner 🔍\n/stop - End the chat 🛑\n/next - Find the next partner ⏭️\n/info - Show all commands ℹ️" if lang == "en" else "<b>📌 Daftar Perintah:</b>\n/search - Cari partner baru 🔍\n/stop - Akhiri obrolan 🛑\n/next - Cari partner selanjutnya ⏭️\n/info - Lihat semua perintah ℹ️"
    
    p_gender = html.escape(data['gender'])
    p_age = html.escape(str(data['age']))
    p_prov = html.escape(data['province'])
    p_city = html.escape(data['location'])
    p_about = html.escape(data['about'])

    profile_text = f"{cool_txt}\n\n⚧️ Gender: {p_gender}\n🎂 Age: {p_age}\n🗺️ Province: {p_prov}\n🏙️ City: {p_city}\n📝 About Me: {p_about}\n\n{cmds}\n\n{disclaimer}"
    bot.send_message(chat_id, profile_text, parse_mode="HTML")

# --- ALUR MATCHMAKING (PROGRESIF DENGAN WAKTU) ---
def attempt_match(chat_id, user_data, scope, value):
    # Cek apakah selama menunggu, ada orang lain yang lebih dulu menemukan user ini
    current_me = get_user(chat_id)
    if current_me and current_me['status'] == 'chatting':
        return True
    
    query = supabase.table('users').select('*').eq('status', 'searching').neq('user_id', chat_id)
    if scope == 'location':
        query = query.eq('location', value)
    elif scope == 'province':
        query = query.eq('province', value)
        
    res = query.limit(1).execute()
    
    if res.data:
        partner = res.data[0]
        # Jodohkan!
        update_user(chat_id, {'status': 'chatting', 'partner_id': partner['user_id']})
        update_user(partner['user_id'], {'status': 'chatting', 'partner_id': chat_id})
        
        send_match_info(chat_id, partner)
        send_match_info(partner['user_id'], current_me)
        return True
    return False

def send_match_info(to_id, partner_data):
    lang = get_user(to_id).get('language', 'en')
    title = "<i>🎉 Partner Found!</i>" if lang == "en" else "<i>🎉 Partner Ditemukan!</i>"
    disc = "<i>⚠️ Disclaimer: Always start conversations politely and never make your partner uncomfortable by discussing 18+ topics!</i>" if lang == "en" else "<i>⚠️ Peringatan: Selalu mulai percakapan dengan sopan dan jangan pernah membuat partnermu tidak nyaman dengan membahas topik 18+!</i>"
    
    p_gender = html.escape(partner_data['gender'])
    p_age = html.escape(str(partner_data['age']))
    p_city = html.escape(partner_data['location'])
    p_about = html.escape(partner_data['about'])
    
    text = f"{title}\n\n⚧️ Gender: {p_gender}\n🎂 Age: {p_age}\n🏙️ City: {p_city}\n📝 About Me: {p_about}\n\n{disc} @micifindbot"
    bot.send_message(to_id, text, parse_mode="HTML")

@bot.message_handler(commands=['search', 'next'])
def search_partner(message):
    user = get_user(message.chat.id)
    if not user:
        bot.send_message(message.chat.id, "<i>⚠️ Please /start first.</i>", parse_mode="HTML")
        return
        
    lang = user.get('language', 'en')
        
    if user['status'] == 'chatting' and message.text == '/search':
        text = "<i>💬 You are currently in a chat!\nUse /stop to end it, or /next to find someone else. 🔄</i>" if lang == "en" else "<i>💬 Kamu sedang berada dalam obrolan aktif!\nGunakan /stop untuk mengakhiri, atau /next untuk mencari orang lain. 🔄</i>"
        bot.send_message(message.chat.id, text, parse_mode="HTML")
        return

    # Putuskan chat sebelumnya jika pakai /next
    if user['status'] == 'chatting' and user['partner_id']:
        handle_stop(message.chat.id, user, user['partner_id'], is_next=True)

    update_user(message.chat.id, {'status': 'searching', 'partner_id': None})
    
    # Memulai pencarian progresif
    text_search = "<i>🔍 Searching for a partner in your city... ⏳</i>" if lang == "en" else "<i>🔍 Mencari partner di kotamu... ⏳</i>"
    msg = bot.send_message(message.chat.id, text_search, parse_mode="HTML")
    
    # 1. Prioritas Kota (Tunggu sampai 3 detik)
    if attempt_match(message.chat.id, user, 'location', user['location']): return
    time.sleep(3)
    if attempt_match(message.chat.id, user, 'location', user['location']): return
    
    # 2. Prioritas Provinsi (Tunggu sampai 3 detik)
    text_prov = "<i>📡 Expanding search to your province... ⏳</i>" if lang == "en" else "<i>📡 Belum ada, memperluas pencarian ke provinsimu... ⏳</i>"
    try: bot.edit_message_text(text_prov, message.chat.id, msg.message_id, parse_mode="HTML")
    except: pass
    
    if attempt_match(message.chat.id, user, 'province', user['province']): return
    time.sleep(3)
    if attempt_match(message.chat.id, user, 'province', user['province']): return
    
    # 3. Prioritas Random
    text_rnd = "<i>🌍 Expanding search globally... ⏳</i>" if lang == "en" else "<i>🌍 Memperluas pencarian secara acak... ⏳</i>"
    try: bot.edit_message_text(text_rnd, message.chat.id, msg.message_id, parse_mode="HTML")
    except: pass
    
    if attempt_match(message.chat.id, user, 'all', None): return
    
    # Jika masih kosong, biarkan status 'searching'
    text_wait = "<i>💤 No partners available right now. We will connect you as soon as someone joins!</i>" if lang == "en" else "<i>💤 Belum ada partner yang tersedia. Kamu akan otomatis terhubung begitu ada yang masuk!</i>"
    try: bot.edit_message_text(text_wait, message.chat.id, msg.message_id, parse_mode="HTML")
    except: pass

# --- ALUR STOP & REPORT ---
@bot.message_handler(commands=['stop'])
def stop_command(message):
    user = get_user(message.chat.id)
    if not user: return
    lang = user.get('language', 'en')

    if user['status'] == 'chatting':
        handle_stop(message.chat.id, user, user['partner_id'], is_next=False)
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
        bot.send_message(partner_id, msg_partner, reply_markup=markup_partner, parse_mode="HTML")

    if not is_next:
        markup_report = InlineKeyboardMarkup()
        markup_report.add(InlineKeyboardButton("⚠️ Report Partner", callback_data=f"report_{partner_id}"))
        msg_stopper = "<i>🛑 Hmmmm... you stopped the dialogue.\nPress /search for a new partner! 🔄</i>" if lang_stopper == "en" else "<i>🛑 Hmmmm... kamu mengakhiri obrolan.\nTekan /search untuk mencari partner baru! 🔄</i>"
        bot.send_message(stopper_id, msg_stopper, reply_markup=markup_report, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "btn_search")
def btn_search_handler(call):
    message = call.message
    message.text = '/search'
    search_partner(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('report_'))
def show_report_reasons(call):
    user = get_user(call.message.chat.id)
    lang = user.get('language', 'en') if user else 'en'
    
    markup = InlineKeyboardMarkup()
    reasons = ["Inappropriate / Tidak senonoh", "Scam / Penipuan", "SARA", "Sexual Harassment", "Other / Lainnya"]
    for r in reasons:
        markup.add(InlineKeyboardButton(r, callback_data="submitted_report"))
        
    text = "<i>Select a reason for reporting:</i>" if lang == "en" else "<i>Pilih alasan melaporkan:</i>"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "submitted_report")
def submitted_report(call):
    user = get_user(call.message.chat.id)
    lang = user.get('language', 'en') if user else 'en'
    text = "<i>✅ Report received. Thank you for keeping the community safe!</i>" if lang == "en" else "<i>✅ Laporan diterima. Terima kasih telah menjaga keamanan komunitas ini!</i>"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML")

# --- INFO & PROFILE ---
@bot.message_handler(commands=['info'])
def cmd_info(message):
    user = get_user(message.chat.id)
    lang = user.get('language', 'en') if user else 'en'
    
    if lang == "en":
        info = ("<b>📌 Bot Commands</b>\n\n/search - Find a new partner 🔍\n/stop - End the chat 🛑\n/next - Find the next partner ⏭️\n"
                "/info - See all commands ℹ️\n/Profil - View your profile 👤\n/EditProfil - Edit your profile setting ⚙️")
    else:
        info = ("<b>📌 Daftar Perintah</b>\n\n/search - Cari partner baru 🔍\n/stop - Akhiri obrolan 🛑\n/next - Cari partner selanjutnya ⏭️\n"
                "/info - Lihat semua perintah ℹ️\n/Profil - Lihat profilmu 👤\n/EditProfil - Edit pengaturan profil ⚙️")
    bot.send_message(message.chat.id, info, parse_mode="HTML")

@bot.message_handler(commands=['profil', 'Profil'])
def cmd_profil(message):
    user = get_user(message.chat.id)
    if not user: return
    lang = user.get('language', 'en')
    
    title = "<b>👤 Your Profile:</b>" if lang == "en" else "<b>👤 Profil Kamu:</b>"
    
    p_gender = html.escape(user['gender'])
    p_age = html.escape(str(user['age']))
    p_prov = html.escape(user.get('province', '-'))
    p_city = html.escape(user['location'])
    p_about = html.escape(user['about'])
    
    bot.send_message(message.chat.id, f"{title}\n\n⚧️ Gender: {p_gender}\n🎂 Age: {p_age}\n🗺️ Province: {p_prov}\n🏙️ City: {p_city}\n📝 About Me: {p_about}", parse_mode="HTML")

@bot.message_handler(commands=['editprofil', 'EditProfil'])
def cmd_editprofil(message):
    user = get_user(message.chat.id)
    lang = user.get('language', 'en') if user else 'en'
    update_user(message.chat.id, {'age': None}) 
    
    text = "<i>⚙️ Profile reset. Please type /start to create a new profile.</i>" if lang == "en" else "<i>⚙️ Profil direset. Silakan ketik /start untuk membuat profil baru.</i>"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# --- FORWARD PESAN CHAT ---
@bot.message_handler(func=lambda message: True)
def relay_message(message):
    user = get_user(message.chat.id)
    if not user:
        bot.send_message(message.chat.id, "<i>⚠️ Please /start first.</i>", parse_mode="HTML")
        return
        
    lang = user.get('language', 'en')

    if user['status'] == 'chatting' and user['partner_id']:
        try:
            bot.copy_message(user['partner_id'], message.chat.id, message.message_id)
        except:
            err_msg = "<i>❌ Error: Could not send message to partner.</i>" if lang == "en" else "<i>❌ Error: Tidak dapat mengirim pesan ke partner.</i>"
            bot.send_message(message.chat.id, err_msg, parse_mode="HTML")
    else:
        text = "<i>🚫 You are not in a chat right now. Press /search for a new partner! 🔄</i>" if lang == "en" else "<i>🚫 Kamu sedang tidak dalam obrolan saat ini. Tekan /search untuk mencari partner baru! 🔄</i>"
        bot.send_message(message.chat.id, text, parse_mode="HTML")

print("🚀 Micifind Bot siap mencari pasangan!")
bot.infinity_polling()
