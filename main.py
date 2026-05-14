import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from supabase import create_client, Client

# --- SETUP SERVER RENDER (RESPONSIF MOBILE) ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        html = """
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
        self.wfile.write(html.encode('utf-8'))

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
        text = "🌟 You are already registered! Use /search to find a partner." if lang == "en" else "🌟 Kamu sudah terdaftar! Gunakan /search untuk mencari partner."
        bot.send_message(message.chat.id, text)
        return

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
               InlineKeyboardButton("Indonesia 🇮🇩", callback_data="lang_id"))
    
    bot.send_message(message.chat.id, 
                     "👋 Welcome to the Micifind bot! Here you can anonymously find people around you!\n"
                     "🎉 Have fun chatting and make sure your conversations are fun!\n\n"
                     "👇 Please select your language below:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    lang = "en" if call.data == "lang_en" else "id"
    user_registration[call.message.chat.id] = {'language': lang}
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Male ♂️", callback_data="gender_male"),
               InlineKeyboardButton("Female ♀️", callback_data="gender_female"))
    
    text = "👤 Select your gender:" if lang == "en" else "👤 Pilih gender kamu:"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('gender_'))
def set_gender(call):
    chat_id = call.message.chat.id
    if chat_id not in user_registration: return
        
    lang = user_registration[chat_id]['language']
    gender = "Male" if call.data == "gender_male" else "Female"
    user_registration[chat_id]['gender'] = gender
    
    text = "🎂 Enter your age (Min 17):" if lang == "en" else "🎂 Masukkan umur kamu (Minimal 17):"
    msg = bot.edit_message_text(text, chat_id, call.message.message_id)
    bot.register_next_step_handler(msg, process_age)

def process_age(message):
    chat_id = message.chat.id
    lang = user_registration.get(chat_id, {}).get('language', 'en')
    
    if not message.text.isdigit() or int(message.text) < 17:
        text = "❌ You must be at least 17 years old to use this bot. Click /start to try again." if lang == "en" else "❌ Kamu harus berumur minimal 17 tahun. Klik /start untuk mengulang."
        bot.send_message(chat_id, text)
        return
        
    user_registration[chat_id]['age'] = int(message.text)
    text = "🗺️ Enter your Province (e.g., Jawa Timur):" if lang == "en" else "🗺️ Masukkan Provinsi kamu (Contoh: Jawa Timur):"
    msg = bot.send_message(chat_id, text)
    bot.register_next_step_handler(msg, process_province)

def process_province(message):
    chat_id = message.chat.id
    lang = user_registration.get(chat_id, {}).get('language', 'en')
    user_registration[chat_id]['province'] = message.text.strip().title()
    
    text = "🏙️ Enter your City (e.g., Malang):" if lang == "en" else "🏙️ Masukkan Kota kamu (Contoh: Malang):"
    msg = bot.send_message(chat_id, text)
    bot.register_next_step_handler(msg, process_location)

def process_location(message):
    chat_id = message.chat.id
    lang = user_registration.get(chat_id, {}).get('language', 'en')
    user_registration[chat_id]['location'] = message.text.strip().title()
    
    text = "📝 Write a short 'About Me' or your description:" if lang == "en" else "📝 Tulis deskripsi singkat 'Tentang Saya':"
    msg = bot.send_message(chat_id, text)
    bot.register_next_step_handler(msg, process_about)

def process_about(message):
    chat_id = message.chat.id
    data = user_registration.get(chat_id)
    if not data: return
    
    data['about'] = message.text
    create_or_update_user(chat_id, data)
    
    lang = data['language']
    cool_txt = "✨ Cool! Here's what your profile looks like:" if lang == "en" else "✨ Keren! Ini tampilan profilmu:"
    disclaimer = "\n\n⚠️ *Disclaimer:* Always start conversations politely and never make your partner uncomfortable by discussing 18+ topics!" if lang == "en" else "\n\n⚠️ *Peringatan:* Selalu mulai percakapan dengan sopan dan jangan pernah membuat partnermu tidak nyaman dengan membahas topik 18+!"
    cmds = "\n\n📌 *Commands:*\n/search - Find a new partner 🔍\n/stop - End the chat 🛑\n/next - Find the next partner ⏭️\n/info - Show all commands ℹ️" if lang == "en" else "\n\n📌 *Daftar Perintah:*\n/search - Cari partner baru 🔍\n/stop - Akhiri obrolan 🛑\n/next - Cari partner selanjutnya ⏭️\n/info - Lihat semua perintah ℹ️"
    
    profile_text = f"{cool_txt}\n\n⚧️ Gender: {data['gender']}\n🎂 Age: {data['age']}\n🗺️ Province: {data['province']}\n🏙️ City: {data['location']}\n📝 About Me: {data['about']}{cmds}{disclaimer}"
    bot.send_message(chat_id, profile_text, parse_mode="Markdown")

# --- ALUR MATCHMAKING (PRIORITAS 3 LAPIS) ---
@bot.message_handler(commands=['search', 'next'])
def search_partner(message):
    user = get_user(message.chat.id)
    if not user:
        bot.send_message(message.chat.id, "⚠️ Please /start first.")
        return
        
    lang = user.get('language', 'en')
        
    if user['status'] == 'chatting' and message.text == '/search':
        text = "💬 You are currently in a chat!\nUse /stop to end it, or /next to find someone else. 🔄" if lang == "en" else "💬 Kamu sedang berada dalam obrolan aktif!\nGunakan /stop untuk mengakhiri, atau /next untuk mencari orang lain. 🔄"
        bot.send_message(message.chat.id, text)
        return

    # Putuskan chat sebelumnya jika pakai /next
    if user['status'] == 'chatting' and user['partner_id']:
        handle_stop(message.chat.id, user, user['partner_id'], is_next=True)

    text_search = "🔍 Searching for a partner... Please wait! ⏳" if lang == "en" else "🔍 Sedang mencari partner... Mohon tunggu! ⏳"
    bot.send_message(message.chat.id, text_search)
    update_user(message.chat.id, {'status': 'searching', 'partner_id': None})
    
    partner = None

    # Prioritas 1: Kota Sama (City)
    res1 = supabase.table('users').select('*').eq('status', 'searching').eq('location', user['location']).neq('user_id', message.chat.id).limit(1).execute()
    if res1.data:
        partner = res1.data[0]
    else:
        # Prioritas 2: Provinsi Sama
        if user.get('province'):
            res2 = supabase.table('users').select('*').eq('status', 'searching').eq('province', user['province']).neq('user_id', message.chat.id).limit(1).execute()
            if res2.data:
                partner = res2.data[0]
        
        # Prioritas 3: Random (Siapapun yang sedang mencari)
        if not partner:
            res3 = supabase.table('users').select('*').eq('status', 'searching').neq('user_id', message.chat.id).limit(1).execute()
            if res3.data:
                partner = res3.data[0]
    
    if partner:
        # Jodohkan keduanya!
        update_user(message.chat.id, {'status': 'chatting', 'partner_id': partner['user_id']})
        update_user(partner['user_id'], {'status': 'chatting', 'partner_id': message.chat.id})
        
        send_match_info(message.chat.id, partner)
        send_match_info(partner['user_id'], user)

def send_match_info(to_id, partner_data):
    lang = get_user(to_id).get('language', 'en')
    title = "🎉 Partner Found!" if lang == "en" else "🎉 Partner Ditemukan!"
    disc = "\n\n⚠️ *Disclaimer:* Always start conversations politely and never make your partner uncomfortable by discussing 18+ topics!" if lang == "en" else "\n\n⚠️ *Peringatan:* Selalu mulai percakapan dengan sopan dan jangan pernah membuat partnermu tidak nyaman dengan membahas topik 18+!"
    text = f"{title}\n\n⚧️ Gender: {partner_data['gender']}\n🎂 Age: {partner_data['age']}\n🏙️ City: {partner_data['location']}\n📝 About Me: {partner_data['about']}{disc}"
    bot.send_message(to_id, text, parse_mode="Markdown")

# --- ALUR STOP & REPORT ---
@bot.message_handler(commands=['stop'])
def stop_command(message):
    user = get_user(message.chat.id)
    if not user: return
    lang = user.get('language', 'en')

    if user['status'] == 'chatting':
        handle_stop(message.chat.id, user, user['partner_id'], is_next=False)
    else:
        text = "🚫 You are not in a chat right now.\nPress /search for a new partner! 🔄" if lang == "en" else "🚫 Kamu sedang tidak dalam obrolan saat ini.\nTekan /search untuk mencari partner baru! 🔄"
        bot.send_message(message.chat.id, text)

def handle_stop(stopper_id, stopper_data, partner_id, is_next=False):
    lang_stopper = stopper_data.get('language', 'en')
    
    update_user(stopper_id, {'status': 'idle', 'partner_id': None})
    if partner_id:
        partner_data = get_user(partner_id)
        lang_partner = partner_data.get('language', 'en') if partner_data else 'en'
        
        update_user(partner_id, {'status': 'idle', 'partner_id': None})
        
        # Pesan ke Partner yang ditinggalkan
        markup_partner = InlineKeyboardMarkup()
        btn_text = "Find New Partner! 🔄" if lang_partner == "en" else "Cari Partner Baru! 🔄"
        markup_partner.add(InlineKeyboardButton(btn_text, callback_data="btn_search"))
        
        msg_partner = "💔 Your partner has ended the chat.\nClick /next or /search to find a new partner!" if lang_partner == "en" else "💔 Partnermu telah mengakhiri obrolan.\nTekan /next atau /search untuk mencari partner baru!"
        bot.send_message(partner_id, msg_partner, reply_markup=markup_partner)

    # Pesan ke Stopper (Orang yang menekan stop)
    if not is_next:
        markup_report = InlineKeyboardMarkup()
        markup_report.add(InlineKeyboardButton("⚠️ Report Partner", callback_data=f"report_{partner_id}"))
        msg_stopper = "🛑 Hmmmm... you stopped the dialogue.\nPress /search for a new partner! 🔄" if lang_stopper == "en" else "🛑 Hmmmm... kamu mengakhiri obrolan.\nTekan /search untuk mencari partner baru! 🔄"
        bot.send_message(stopper_id, msg_stopper, reply_markup=markup_report)

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
        
    text = "Select a reason for reporting:" if lang == "en" else "Pilih alasan melaporkan:"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "submitted_report")
def submitted_report(call):
    user = get_user(call.message.chat.id)
    lang = user.get('language', 'en') if user else 'en'
    text = "✅ Report received. Thank you for keeping the community safe!" if lang == "en" else "✅ Laporan diterima. Terima kasih telah menjaga keamanan komunitas ini!"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

# --- INFO & PROFILE ---
@bot.message_handler(commands=['info'])
def cmd_info(message):
    user = get_user(message.chat.id)
    lang = user.get('language', 'en') if user else 'en'
    
    if lang == "en":
        info = ("📌 *Bot Commands*\n\n/search - Find a new partner 🔍\n/stop - End the chat 🛑\n/next - Find the next partner ⏭️\n"
                "/info - See all commands ℹ️\n/Profil - View your profile 👤\n/EditProfil - Edit your profile setting ⚙️")
    else:
        info = ("📌 *Daftar Perintah*\n\n/search - Cari partner baru 🔍\n/stop - Akhiri obrolan 🛑\n/next - Cari partner selanjutnya ⏭️\n"
                "/info - Lihat semua perintah ℹ️\n/Profil - Lihat profilmu 👤\n/EditProfil - Edit pengaturan profil ⚙️")
    bot.send_message(message.chat.id, info, parse_mode="Markdown")

@bot.message_handler(commands=['profil', 'Profil'])
def cmd_profil(message):
    user = get_user(message.chat.id)
    if not user: return
    lang = user.get('language', 'en')
    
    title = "👤 Your Profile:" if lang == "en" else "👤 Profil Kamu:"
    bot.send_message(message.chat.id, f"{title}\n\n⚧️ Gender: {user['gender']}\n🎂 Age: {user['age']}\n🗺️ Province: {user.get('province', '-')}\n🏙️ City: {user['location']}\n📝 About Me: {user['about']}")

@bot.message_handler(commands=['editprofil', 'EditProfil'])
def cmd_editprofil(message):
    user = get_user(message.chat.id)
    lang = user.get('language', 'en') if user else 'en'
    update_user(message.chat.id, {'age': None}) 
    
    text = "⚙️ Profile reset. Please type /start to create a new profile." if lang == "en" else "⚙️ Profil direset. Silakan ketik /start untuk membuat profil baru."
    bot.send_message(message.chat.id, text)

# --- FORWARD PESAN CHAT ---
@bot.message_handler(func=lambda message: True)
def relay_message(message):
    user = get_user(message.chat.id)
    if not user:
        bot.send_message(message.chat.id, "⚠️ Please /start first.")
        return
        
    lang = user.get('language', 'en')

    if user['status'] == 'chatting' and user['partner_id']:
        try:
            bot.copy_message(user['partner_id'], message.chat.id, message.message_id)
        except:
            err_msg = "❌ Error: Could not send message to partner." if lang == "en" else "❌ Error: Tidak dapat mengirim pesan ke partner."
            bot.send_message(message.chat.id, err_msg)
    else:
        text = "🚫 You are not in a chat right now. Press /search for a new partner! 🔄" if lang == "en" else "🚫 Kamu sedang tidak dalam obrolan saat ini. Tekan /search untuk mencari partner baru! 🔄"
        bot.send_message(message.chat.id, text)

print("🚀 Micifind Bot siap mencari pasangan!")
bot.infinity_polling()
