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
            <h1>Micifind Bot Sedang Berjalan!</h1>
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

# Menyematkan tombol menu otomatis di sebelah kiri chat
bot.set_my_commands([
    BotCommand("start", "Start or register"),
    BotCommand("search", "Find a new partner"),
    BotCommand("next", "Find the next partner"),
    BotCommand("stop", "End current chat"),
    BotCommand("info", "Show all commands"),
    BotCommand("profil", "View your profile"),
    BotCommand("editprofil", "Edit your profile")
])

# Memori sementara untuk pendaftaran
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
        bot.send_message(message.chat.id, "You are already registered! Use /search to find a partner.")
        return

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
               InlineKeyboardButton("Indonesia 🇮🇩", callback_data="lang_id"))
    
    bot.send_message(message.chat.id, 
                     "Welcome to the Micifind bot! Here you can anonymously find people around you!\n"
                     "Have fun chatting and make sure your conversations are fun!\n\n"
                     "Please select your language below:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    lang = "en" if call.data == "lang_en" else "id"
    user_registration[call.message.chat.id] = {'language': lang}
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Male ♂️", callback_data="gender_male"),
               InlineKeyboardButton("Female ♀️", callback_data="gender_female"))
    
    text = "Select your gender:" if lang == "en" else "Pilih gender kamu:"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('gender_'))
def set_gender(call):
    chat_id = call.message.chat.id
    if chat_id not in user_registration:
        return
        
    lang = user_registration[chat_id]['language']
    gender = "Male" if call.data == "gender_male" else "Female"
    user_registration[chat_id]['gender'] = gender
    
    text = "Enter your age (Min 17):" if lang == "en" else "Masukkan umur kamu (Minimal 17):"
    msg = bot.edit_message_text(text, chat_id, call.message.message_id)
    bot.register_next_step_handler(msg, process_age)

def process_age(message):
    chat_id = message.chat.id
    lang = user_registration.get(chat_id, {}).get('language', 'en')
    
    if not message.text.isdigit() or int(message.text) < 17:
        text = "You must be at least 17 years old to use this bot. /start to try again." if lang == "en" else "Kamu harus berumur minimal 17 tahun. Klik /start untuk mengulang."
        bot.send_message(chat_id, text)
        return
        
    user_registration[chat_id]['age'] = int(message.text)
    text = "Enter your Province/City:" if lang == "en" else "Masukkan Provinsi/Kota kamu (Contoh: Malang):"
    msg = bot.send_message(chat_id, text)
    bot.register_next_step_handler(msg, process_location)

def process_location(message):
    chat_id = message.chat.id
    lang = user_registration.get(chat_id, {}).get('language', 'en')
    user_registration[chat_id]['location'] = message.text.strip().title()
    
    text = "Write a short 'About Me' or your description:" if lang == "en" else "Tulis deskripsi singkat 'Tentang Saya':"
    msg = bot.send_message(chat_id, text)
    bot.register_next_step_handler(msg, process_about)

def process_about(message):
    chat_id = message.chat.id
    data = user_registration.get(chat_id)
    if not data: return
    
    data['about'] = message.text
    create_or_update_user(chat_id, data)
    
    lang = data['language']
    cool_txt = "Cool! Here's what your profile looks like:" if lang == "en" else "Keren! Ini tampilan profilmu:"
    disclaimer = "\n\nDisclaimer: Always start conversations politely and never make your partner uncomfortable by discussing 18+ topics!" if lang == "en" else "\n\nPeringatan: Selalu mulai percakapan dengan sopan dan jangan pernah membuat partnermu tidak nyaman dengan membahas topik 18+!"
    cmds = "\n\nHere are the commands you can use to start a chat:\nClick /search to find a new partner\nClick /stop to end the chat\nClick /next to find the next new partner\nClick /info to see all the commands you can use in this bot"
    
    profile_text = f"{cool_txt}\nGender: {data['gender']}\nAge: {data['age']}\nCity: {data['location']}\nAbout Me: {data['about']}{cmds}{disclaimer}"
    bot.send_message(chat_id, profile_text)

# --- ALUR MATCHMAKING ---
@bot.message_handler(commands=['search', 'next'])
def search_partner(message):
    user = get_user(message.chat.id)
    if not user:
        bot.send_message(message.chat.id, "Please /start first.")
        return
        
    if user['status'] == 'chatting' and message.text == '/search':
        bot.send_message(message.chat.id, "You are currently in a chat. Use /stop to end it, or /next to find someone else.")
        return

    # Jika pakai /next saat sedang chat, hentikan chat dulu secara otomatis
    if user['status'] == 'chatting' and user['partner_id']:
        handle_stop(message.chat.id, user, user['partner_id'], is_next=True)

    bot.send_message(message.chat.id, "Searching for a partner in your area...")
    update_user(message.chat.id, {'status': 'searching', 'partner_id': None})
    
    # Mencari partner di kota yang sama yang sedang searching
    res = supabase.table('users').select('*').eq('status', 'searching').eq('location', user['location']).neq('user_id', message.chat.id).limit(1).execute()
    
    if res.data:
        partner = res.data[0]
        # Jodohkan keduanya!
        update_user(message.chat.id, {'status': 'chatting', 'partner_id': partner['user_id']})
        update_user(partner['user_id'], {'status': 'chatting', 'partner_id': message.chat.id})
        
        # Kirim profil ke masing-masing
        send_match_info(message.chat.id, partner)
        send_match_info(partner['user_id'], user)

def send_match_info(to_id, partner_data):
    lang = get_user(to_id).get('language', 'en')
    title = "Partner Found!" if lang == "en" else "Partner Ditemukan!"
    disc = "\n\nDisclaimer: Always start conversations politely and never make your partner uncomfortable by discussing 18+ topics!"
    text = f"{title}\nGender: {partner_data['gender']}\nAge: {partner_data['age']}\nCity: {partner_data['location']}\nAbout Me: {partner_data['about']}{disc}"
    bot.send_message(to_id, text)

# --- ALUR STOP & REPORT ---
@bot.message_handler(commands=['stop'])
def stop_command(message):
    user = get_user(message.chat.id)
    if user and user['status'] == 'chatting':
        handle_stop(message.chat.id, user, user['partner_id'], is_next=False)
    else:
        bot.send_message(message.chat.id, "You are not in a chat right now.")

def handle_stop(stopper_id, stopper_data, partner_id, is_next=False):
    # Putuskan hubungan keduanya di database
    update_user(stopper_id, {'status': 'idle', 'partner_id': None})
    if partner_id:
        update_user(partner_id, {'status': 'idle', 'partner_id': None})
        
        # Pesan untuk Partner
        markup_partner = InlineKeyboardMarkup()
        markup_partner.add(InlineKeyboardButton("Find New Partner!", callback_data="btn_search"))
        bot.send_message(partner_id, "Your partner has ended the chat, click /next to find a new partner!", reply_markup=markup_partner)

    # Pesan untuk Stopper
    if not is_next:
        markup_report = InlineKeyboardMarkup()
        markup_report.add(InlineKeyboardButton("⚠️ Report Partner", callback_data=f"report_{partner_id}"))
        bot.send_message(stopper_id, "Hmmmm... you stopped the dialogue.", reply_markup=markup_report)

@bot.callback_query_handler(func=lambda call: call.data == "btn_search")
def btn_search_handler(call):
    message = call.message
    message.text = '/search'
    search_partner(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('report_'))
def show_report_reasons(call):
    markup = InlineKeyboardMarkup()
    reasons = ["Percakapan tidak senonoh", "Melakukan penipuan", "SARA", "Hal tidak pantas", "Kekerasan seksual", "Other"]
    for r in reasons:
        markup.add(InlineKeyboardButton(r, callback_data="submitted_report"))
    bot.edit_message_text("Pilih alasan report:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "submitted_report")
def submitted_report(call):
    bot.edit_message_text("Report received. Thank you for keeping the community safe!", call.message.chat.id, call.message.message_id)

# --- INFO & PROFILE ---
@bot.message_handler(commands=['info'])
def cmd_info(message):
    info = ("/search to find a new partner\n/stop to end the chat\n/next to find the next new partner\n"
            "/info to see all the commands you can use in this bot\n/Profil to view your own profile\n/EditProfil to edit your profile setting")
    bot.send_message(message.chat.id, info)

@bot.message_handler(commands=['profil', 'Profil'])
def cmd_profil(message):
    user = get_user(message.chat.id)
    if not user: return
    bot.send_message(message.chat.id, f"Your Profile:\nGender: {user['gender']}\nAge: {user['age']}\nCity: {user['location']}\nAbout Me: {user['about']}")

@bot.message_handler(commands=['editprofil', 'EditProfil'])
def cmd_editprofil(message):
    update_user(message.chat.id, {'age': None}) # Mereset data usia untuk validasi
    bot.send_message(message.chat.id, "Profile reset. Please type /start to create a new profile.")

# --- FORWARD PESAN CHAT ---
@bot.message_handler(func=lambda message: True)
def relay_message(message):
    user = get_user(message.chat.id)
    if user and user['status'] == 'chatting' and user['partner_id']:
        try:
            bot.copy_message(user['partner_id'], message.chat.id, message.message_id)
        except:
            bot.send_message(message.chat.id, "Error: Could not send message to partner.")
    else:
        bot.send_message(message.chat.id, "You are not connected to anyone. Use /search to find a partner.")

print("Micifind Bot siap mencari pasangan!")
bot.infinity_polling()
