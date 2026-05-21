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
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"></head>
        <body style="font-family: sans-serif; text-align: center; padding: 20px;">
            <h1>🚀 Micifind Bot V13.2 (Full Global) Aktif!</h1>
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
user_last_action = {}

# --- DICTIONARY BAHASA GLOBAL ---
LANGUAGES = {
    'en': '🇬🇧 English', 'id': '🇮🇩 Indonesia', 'th': '🇹🇭 Thai', 
    'tl': '🇵🇭 Tagalog', 'hi': '🇮🇳 Hindi', 'ru': '🇷🇺 Russian', 
    'vi': '🇻🇳 Vietnamese', 'es': '🇪🇸 Spanish', 'pt': '🇧🇷 Portuguese', 
    'ar': '🇸🇦 Arabic', 'de': '🇩🇪 German', 'ja': '🇯🇵 Japanese', 'zh': '🇨🇳 Chinese'
}

WELCOME_EN_ONLY = "<i>👋 Welcome to the Micifind bot! Here you can anonymously find people around you!\n\n⚠️ By using this bot, you agree that Micifind is not responsible for any personal data shared in chats.\n\n👇 Please select your language below:</i>"

# DICTIONARY PENUH 13 BAHASA UNTUK SEMUA TEKS
TEXTS = {
    'already_registered': {
        'en': "<i>🌟 You are already registered! Use /search to find a partner.</i>",
        'id': "<i>🌟 Kamu sudah terdaftar! Gunakan /search untuk mencari partner.</i>",
        'th': "<i>🌟 คุณลงทะเบียนแล้ว! ใช้ /search เพื่อหาคู่สนทนา</i>",
        'tl': "<i>🌟 Nakarehistro ka na! Gamitin ang /search para maghanap.</i>",
        'hi': "<i>🌟 आप पहले से पंजीकृत हैं! साथी खोजने के लिए /search का उपयोग करें।</i>",
        'ru': "<i>🌟 Вы уже зарегистрированы! Используйте /search для поиска.</i>",
        'vi': "<i>🌟 Bạn đã đăng ký! Sử dụng /search để tìm đối tác.</i>",
        'es': "<i>🌟 ¡Ya estás registrado! Usa /search para buscar pareja.</i>",
        'pt': "<i>🌟 Você já está registrado! Use /search para encontrar um parceiro.</i>",
        'ar': "<i>🌟 أنت مسجل بالفعل! استخدم /search للبحث عن شريك.</i>",
        'de': "<i>🌟 Du bist bereits registriert! Nutze /search zum Suchen.</i>",
        'ja': "<i>🌟 すでに登録されています！/search を使用してパートナーを見つけてください。</i>",
        'zh': "<i>🌟 您已经注册！使用 /search 寻找伙伴。</i>"
    },
    'banned': {
        'en': "<i>⛔ Your account is blocked due to rules violation.</i>",
        'id': "<i>⛔ Akun kamu sedang diblokir karena melanggar aturan komunitas.</i>",
        'th': "<i>⛔ บัญชีของคุณถูกบล็อกเนื่องจากการละเมิดกฎ</i>",
        'tl': "<i>⛔ Naka-block ang iyong account dahil sa paglabag sa mga patakaran.</i>",
        'hi': "<i>⛔ नियमों के उल्लंघन के कारण आपका खाता अवरुद्ध कर दिया गया है।</i>",
        'ru': "<i>⛔ Ваш аккаунт заблокирован за нарушение правил.</i>",
        'vi': "<i>⛔ Tài khoản của bạn bị chặn do vi phạm quy tắc.</i>",
        'es': "<i>⛔ Tu cuenta está bloqueada por violación de reglas.</i>",
        'pt': "<i>⛔ Sua conta está bloqueada devido a violação de regras.</i>",
        'ar': "<i>⛔ تم حظر حسابك بسبب انتهاك القواعد.</i>",
        'de': "<i>⛔ Dein Konto ist aufgrund eines Regelverstoßes gesperrt.</i>",
        'ja': "<i>⛔ ルール違反のため、アカウントがブロックされました。</i>",
        'zh': "<i>⛔ 由于违反规定，您的帐户已被封禁。</i>"
    },
    'invite_success': {
        'en': "<i>🎉 You successfully invited 10 people! You are now PRO for 1 Week!</i>",
        'id': "<i>🎉 Kamu berhasil mengundang 10 orang! Akunmu sekarang PRO selama 1 Minggu!</i>",
        'th': "<i>🎉 คุณเชิญคน 10 คนสำเร็จแล้ว! ตอนนี้คุณคือ PRO เป็นเวลา 1 สัปดาห์!</i>",
        'tl': "<i>🎉 Matagumpay kang nakapag-imbita ng 10 tao! PRO ka na ngayon ng 1 Linggo!</i>",
        'hi': "<i>🎉 आपने 10 लोगों को सफलतापूर्वक आमंत्रित किया! अब आप 1 सप्ताह के लिए प्रो हैं!</i>",
        'ru': "<i>🎉 Вы успешно пригласили 10 человек! Теперь вы PRO на 1 неделю!</i>",
        'vi': "<i>🎉 Bạn đã mời thành công 10 người! Bây giờ bạn là PRO trong 1 Tuần!</i>",
        'es': "<i>🎉 ¡Invitaste a 10 personas con éxito! ¡Ahora eres PRO por 1 semana!</i>",
        'pt': "<i>🎉 Você convidou 10 pessoas com sucesso! Agora você é PRO por 1 Semana!</i>",
        'ar': "<i>🎉 لقد قمت بدعوة 10 أشخاص بنجاح! أنت الآن PRO لمدة أسبوع!</i>",
        'de': "<i>🎉 Du hast erfolgreich 10 Leute eingeladen! Du bist jetzt PRO für 1 Woche!</i>",
        'ja': "<i>🎉 10人を招待することに成功しました！これで1週間PROになります！</i>",
        'zh': "<i>🎉 您成功邀请了 10 个人！您现在是 PRO 级别，为期 1 周！</i>"
    },
    'select_gender': {
        'en': "<i>👤 Select your gender:</i>", 'id': "<i>👤 Pilih gender kamu:</i>",
        'th': "<i>👤 เลือกเพศของคุณ:</i>", 'tl': "<i>👤 Piliin ang iyong kasarian:</i>",
        'hi': "<i>👤 अपना लिंग चुनें:</i>", 'ru': "<i>👤 Выберите ваш пол:</i>",
        'vi': "<i>👤 Chọn giới tính của bạn:</i>", 'es': "<i>👤 Selecciona tu género:</i>",
        'pt': "<i>👤 Selecione seu gênero:</i>", 'ar': "<i>👤 اختر جنسك:</i>",
        'de': "<i>👤 Wähle dein Geschlecht:</i>", 'ja': "<i>👤 性別を選択してください:</i>",
        'zh': "<i>👤 选择您的性别：</i>"
    },
    'enter_age': {
        'en': "<i>🎂 Enter your age (Min 17):</i>", 'id': "<i>🎂 Masukkan umur kamu (Minimal 17):</i>",
        'th': "<i>🎂 ใส่อายุของคุณ (ขั้นต่ำ 17):</i>", 'tl': "<i>🎂 Ilagay ang iyong edad (Min 17):</i>",
        'hi': "<i>🎂 अपनी उम्र दर्ज करें (न्यूनतम 17):</i>", 'ru': "<i>🎂 Введите ваш возраст (Мин. 17):</i>",
        'vi': "<i>🎂 Nhập tuổi của bạn (Tối thiểu 17):</i>", 'es': "<i>🎂 Ingresa tu edad (Mínimo 17):</i>",
        'pt': "<i>🎂 Digite sua idade (Mínimo 17):</i>", 'ar': "<i>🎂 أدخل عمرك (الحد الأدنى 17):</i>",
        'de': "<i>🎂 Gib dein Alter ein (Min. 17):</i>", 'ja': "<i>🎂 年齢を入力してください (17歳以上):</i>",
        'zh': "<i>🎂 输入您的年龄（最小 17 岁）：</i>"
    },
    'age_error': {
        'en': "<i>❌ You must be at least 17 years old. Click /start to try again.</i>",
        'id': "<i>❌ Kamu harus berumur minimal 17 tahun. Klik /start untuk mengulang.</i>",
        'th': "<i>❌ คุณต้องมีอายุอย่างน้อย 17 ปี คลิก /start เพื่อลองอีกครั้ง</i>",
        'tl': "<i>❌ Dapat ay 17 taong gulang ka pataas. I-click ang /start para subukan muli.</i>",
        'hi': "<i>❌ आपकी आयु कम से कम 17 वर्ष होनी चाहिए। पुनः प्रयास करने के लिए /start पर क्लिक करें।</i>",
        'ru': "<i>❌ Вам должно быть не менее 17 лет. Нажмите /start, чтобы попробовать снова.</i>",
        'vi': "<i>❌ Bạn phải ít nhất 17 tuổi. Nhấp vào /start để thử lại.</i>",
        'es': "<i>❌ Debes tener al menos 17 años. Haz clic en /start para intentar de nuevo.</i>",
        'pt': "<i>❌ Você deve ter pelo menos 17 anos. Clique em /start para tentar novamente.</i>",
        'ar': "<i>❌ يجب أن يكون عمرك 17 عامًا على الأقل. انقر على /start للمحاولة مرة أخرى.</i>",
        'de': "<i>❌ Du musst mindestens 17 Jahre alt sein. Klicke auf /start, um es erneut zu versuchen.</i>",
        'ja': "<i>❌ 17歳以上である必要があります。 /start をクリックしてやり直してください。</i>",
        'zh': "<i>❌ 您必须年满 17 岁。 点击 /start 重试。</i>"
    },
    'enter_prov': {
        'en': "<i>🗺️ Enter your Province/State:</i>", 'id': "<i>🗺️ Masukkan Provinsi kamu (Contoh: Jawa Timur):</i>",
        'th': "<i>🗺️ ใส่จังหวัด/รัฐของคุณ:</i>", 'tl': "<i>🗺️ Ilagay ang iyong Probinsya/Rehiyon:</i>",
        'hi': "<i>🗺️ अपना राज्य/प्रांत दर्ज करें:</i>", 'ru': "<i>🗺️ Введите вашу провинцию/область:</i>",
        'vi': "<i>🗺️ Nhập Tỉnh/Tiểu bang của bạn:</i>", 'es': "<i>🗺️ Ingresa tu Provincia/Estado:</i>",
        'pt': "<i>🗺️ Digite sua Província/Estado:</i>", 'ar': "<i>🗺️ أدخل محافظتك/ولايتك:</i>",
        'de': "<i>🗺️ Gib dein Bundesland/deine Region ein:</i>", 'ja': "<i>🗺️ 都道府県を入力してください:</i>",
        'zh': "<i>🗺️ 输入您的省/州：</i>"
    },
    'enter_city': {
        'en': "<i>🏙️ Enter your City:</i>", 'id': "<i>🏙️ Masukkan Kota kamu (Contoh: Malang):</i>",
        'th': "<i>🏙️ ใส่เมืองของคุณ:</i>", 'tl': "<i>🏙️ Ilagay ang iyong Siyudad:</i>",
        'hi': "<i>🏙️ अपना शहर दर्ज करें:</i>", 'ru': "<i>🏙️ Введите ваш город:</i>",
        'vi': "<i>🏙️ Nhập Thành phố của bạn:</i>", 'es': "<i>🏙️ Ingresa tu Ciudad:</i>",
        'pt': "<i>🏙️ Digite sua Cidade:</i>", 'ar': "<i>🏙️ أدخل مدينتك:</i>",
        'de': "<i>🏙️ Gib deine Stadt ein:</i>", 'ja': "<i>🏙️ 市区町村を入力してください:</i>",
        'zh': "<i>🏙️ 输入您的城市：</i>"
    },
    'enter_about': {
        'en': "<i>📝 Write a short 'About Me' or your description:</i>",
        'id': "<i>📝 Tulis deskripsi singkat 'Tentang Saya':</i>",
        'th': "<i>📝 เขียนคำอธิบาย 'เกี่ยวกับฉัน' สั้นๆ:</i>",
        'tl': "<i>📝 Magsulat ng maikling 'Tungkol Sa Akin' o paglalarawan:</i>",
        'hi': "<i>📝 'मेरे बारे में' या अपना विवरण संक्षेप में लिखें:</i>",
        'ru': "<i>📝 Напишите коротко 'О себе' или ваше описание:</i>",
        'vi': "<i>📝 Viết một đoạn ngắn 'Về tôi' hoặc mô tả của bạn:</i>",
        'es': "<i>📝 Escribe una breve descripción 'Sobre mí':</i>",
        'pt': "<i>📝 Escreva um breve 'Sobre Mim' ou sua descrição:</i>",
        'ar': "<i>📝 اكتب وصفًا قصيرًا 'عني':</i>",
        'de': "<i>📝 Schreibe ein kurzes 'Über mich' oder deine Beschreibung:</i>",
        'ja': "<i>📝 簡単な自己紹介を書いてください:</i>",
        'zh': "<i>📝 写一个简短的“关于我”或您的描述：</i>"
    },
    'profile_saved': {
        'en': "<i>✨ Cool! Here's what your profile looks like:</i>", 'id': "<i>✨ Keren! Ini tampilan profilmu:</i>",
        'th': "<i>✨ เยี่ยมเลย! นี่คือโปรไฟล์ของคุณ:</i>", 'tl': "<i>✨ Astig! Ganito ang hitsura ng profile mo:</i>",
        'hi': "<i>✨ बहुत बढ़िया! आपकी प्रोफ़ाइल इस तरह दिखती है:</i>", 'ru': "<i>✨ Отлично! Вот как выглядит ваш профиль:</i>",
        'vi': "<i>✨ Tuyệt vời! Đây là hồ sơ của bạn:</i>", 'es': "<i>✨ ¡Genial! Así es como se ve tu perfil:</i>",
        'pt': "<i>✨ Legal! Assim que o seu perfil ficou:</i>", 'ar': "<i>✨ رائع! هكذا يبدو ملفك الشخصي:</i>",
        'de': "<i>✨ Cool! So sieht dein Profil aus:</i>", 'ja': "<i>✨ いいですね！あなたのプロフィールはこちらです:</i>",
        'zh': "<i>✨ 酷！这是您的个人资料：</i>"
    },
    'cmds': {
        'en': "<b>📌 Commands:</b>\n/search - Find a new partner 🔍\n/stop - End the chat 🛑\n/next - Find the next partner ⏭️\n/info - Show all commands ℹ️",
        'id': "<b>📌 Daftar Perintah:</b>\n/search - Cari partner baru 🔍\n/stop - Akhiri obrolan 🛑\n/next - Cari partner selanjutnya ⏭️\n/info - Lihat semua perintah ℹ️",
        'th': "<b>📌 คำสั่ง:</b>\n/search - หาคู่ใหม่ 🔍\n/stop - จบการสนทนา 🛑\n/next - หาคู่คนต่อไป ⏭️\n/info - ดูคำสั่งทั้งหมด ℹ️",
        'tl': "<b>📌 Mga Command:</b>\n/search - Maghanap ng bagong partner 🔍\n/stop - Tapusin ang chat 🛑\n/next - Hanapin ang susunod na partner ⏭️\n/info - Ipakita ang lahat ng commands ℹ️",
        'hi': "<b>📌 आदेश:</b>\n/search - नया साथी खोजें 🔍\n/stop - चैट समाप्त करें 🛑\n/next - अगला साथी खोजें ⏭️\n/info - सभी आदेश दिखाएं ℹ️",
        'ru': "<b>📌 Команды:</b>\n/search - Найти партнера 🔍\n/stop - Завершить чат 🛑\n/next - Следующий партнер ⏭️\n/info - Показать все команды ℹ️",
        'vi': "<b>📌 Lệnh:</b>\n/search - Tìm đối tác mới 🔍\n/stop - Kết thúc trò chuyện 🛑\n/next - Đối tác tiếp theo ⏭️\n/info - Tất cả các lệnh ℹ️",
        'es': "<b>📌 Comandos:</b>\n/search - Buscar nueva pareja 🔍\n/stop - Finalizar chat 🛑\n/next - Siguiente pareja ⏭️\n/info - Todos los comandos ℹ️",
        'pt': "<b>📌 Comandos:</b>\n/search - Encontrar parceiro 🔍\n/stop - Encerrar o chat 🛑\n/next - Próximo parceiro ⏭️\n/info - Todos os comandos ℹ️",
        'ar': "<b>📌 الأوامر:</b>\n/search - ابحث عن شريك جديد 🔍\n/stop - إنهاء الدردشة 🛑\n/next - الشريك التالي ⏭️\n/info - إظهار كل الأوامر ℹ️",
        'de': "<b>📌 Befehle:</b>\n/search - Neuen Partner finden 🔍\n/stop - Chat beenden 🛑\n/next - Nächsten Partner finden ⏭️\n/info - Alle Befehle anzeigen ℹ️",
        'ja': "<b>📌 コマンド:</b>\n/search - パートナーを探す 🔍\n/stop - チャットを終了 🛑\n/next - 次のパートナー ⏭️\n/info - 全コマンド表示 ℹ️",
        'zh': "<b>📌 命令:</b>\n/search - 寻找新伙伴 🔍\n/stop - 结束聊天 🛑\n/next - 寻找下一个伙伴 ⏭️\n/info - 显示所有命令 ℹ️"
    },
    'disclaimer': {
        'en': "<i>⚠️ Disclaimer: Always start conversations politely and never make your partner uncomfortable by discussing 18+ topics!</i>",
        'id': "<i>⚠️ Peringatan: Selalu mulai percakapan dengan sopan dan jangan pernah membuat partnermu tidak nyaman dengan membahas topik 18+!</i>",
        'th': "<i>⚠️ ข้อจำกัดความรับผิดชอบ: เริ่มต้นการสนทนาอย่างสุภาพและอย่าทำให้คู่ของคุณอึดอัดด้วยหัวข้อ 18+!</i>",
        'tl': "<i>⚠️ Babala: Magsimula ng usapan ng may paggalang at huwag pag-usapan ang mga 18+ na paksa!</i>",
        'hi': "<i>⚠️ अस्वीकरण: हमेशा विनम्रता से बातचीत शुरू करें और 18+ विषयों पर चर्चा करके साथी को असहज न करें!</i>",
        'ru': "<i>⚠️ Внимание: Начинайте общение вежливо и не обсуждайте темы 18+, чтобы не смущать партнера!</i>",
        'vi': "<i>⚠️ Cảnh báo: Bắt đầu cuộc trò chuyện lịch sự và không bao giờ thảo luận về chủ đề 18+!</i>",
        'es': "<i>⚠️ Advertencia: ¡Inicia las conversaciones de forma educada y nunca hables de temas +18!</i>",
        'pt': "<i>⚠️ Aviso: Comece as conversas educadamente e nunca fale sobre temas +18!</i>",
        'ar': "<i>⚠️ تحذير: ابدأ دائمًا المحادثات بأدب ولا تجعل شريكك غير مرتاح بمناقشة مواضيع 18+!</i>",
        'de': "<i>⚠️ Haftungsausschluss: Starte Gespräche höflich und diskutiere keine 18+ Themen!</i>",
        'ja': "<i>⚠️ 注意：会話は常に丁寧に行い、18禁の話題で相手を不快にさせないでください！</i>",
        'zh': "<i>⚠️ 免责声明：始终礼貌地开始对话，切勿通过讨论 18+ 话题让您的伙伴感到不舒服！</i>"
    },
    'partner_found': {
        'en': "<i>🎉 Partner Found!</i>", 'id': "<i>🎉 Partner Ditemukan!</i>",
        'th': "<i>🎉 ค้นพบพาร์ทเนอร์แล้ว!</i>", 'tl': "<i>🎉 May nakita nang Partner!</i>",
        'hi': "<i>🎉 साथी मिल गया!</i>", 'ru': "<i>🎉 Партнер Найден!</i>",
        'vi': "<i>🎉 Đã tìm thấy đối tác!</i>", 'es': "<i>🎉 ¡Compañero Encontrado!</i>",
        'pt': "<i>🎉 Parceiro Encontrado!</i>", 'ar': "<i>🎉 تم العثور على شريك!</i>",
        'de': "<i>🎉 Partner Gefunden!</i>", 'ja': "<i>🎉 パートナーが見つかりました！</i>",
        'zh': "<i>🎉 找到伙伴了！</i>"
    },
    'please_start': {
        'en': "<i>⚠️ Please /start first.</i>", 'id': "<i>⚠️ Silakan /start terlebih dahulu.</i>",
        'th': "<i>⚠️ กรุณาพิมพ์ /start ก่อน</i>", 'tl': "<i>⚠️ Paki-/start muna.</i>",
        'hi': "<i>⚠️ कृपया पहले /start करें।</i>", 'ru': "<i>⚠️ Пожалуйста, введите /start.</i>",
        'vi': "<i>⚠️ Vui lòng /start trước.</i>", 'es': "<i>⚠️ Por favor, usa /start primero.</i>",
        'pt': "<i>⚠️ Por favor, digite /start primeiro.</i>", 'ar': "<i>⚠️ يرجى الضغط على /start أولاً.</i>",
        'de': "<i>⚠️ Bitte tippe zuerst /start.</i>", 'ja': "<i>⚠️ まずは /start を送信してください。</i>",
        'zh': "<i>⚠️ 请先发送 /start。</i>"
    },
    'limit_reached': {
        'en': "<i>⚠️ You have reached the daily limit of 150 matches.</i>", 'id': "<i>⚠️ Kamu telah mencapai batas harian 150 match hari ini.</i>",
        'th': "<i>⚠️ คุณถึงขีดจำกัดรายวัน 150 การจับคู่แล้ว</i>", 'tl': "<i>⚠️ Naabot mo na ang araw-araw na limitasyon na 150 matches.</i>",
        'hi': "<i>⚠️ आप 150 मैचों की दैनिक सीमा तक पहुंच गए हैं।</i>", 'ru': "<i>⚠️ Вы достигли дневного лимита в 150 совпадений.</i>",
        'vi': "<i>⚠️ Bạn đã đạt giới hạn 150 lượt ghép mỗi ngày.</i>", 'es': "<i>⚠️ Has alcanzado el límite diario de 150 coincidencias.</i>",
        'pt': "<i>⚠️ Você atingiu o limite diário de 150 matches.</i>", 'ar': "<i>⚠️ لقد وصلت إلى الحد اليومي البالغ 150 مطابقة.</i>",
        'de': "<i>⚠️ Du hast das Tageslimit von 150 Matches erreicht.</i>", 'ja': "<i>⚠️ 1日の制限である150マッチに達しました。</i>",
        'zh': "<i>⚠️ 您已达到每天150次匹配的限制。</i>"
    },
    'already_searching': {
        'en': "<i>⏳ You are already searching! Please wait, or type /stop to cancel.</i>",
        'id': "<i>⏳ Kamu sedang dalam antrean pencarian! Mohon tunggu, atau ketik /stop untuk membatalkan.</i>",
        'th': "<i>⏳ คุณกำลังค้นหาอยู่แล้ว! กรุณารอหรือพิมพ์ /stop เพื่อยกเลิก</i>",
        'tl': "<i>⏳ Naghahanap ka na! Maghintay o i-type ang /stop para kanselahin.</i>",
        'hi': "<i>⏳ आप पहले से ही खोज रहे हैं! कृपया प्रतीक्षा करें, या रद्द करने के लिए /stop टाइप करें।</i>",
        'ru': "<i>⏳ Вы уже в поиске! Подождите или введите /stop для отмены.</i>",
        'vi': "<i>⏳ Bạn đang tìm kiếm! Vui lòng chờ, hoặc gõ /stop để hủy.</i>",
        'es': "<i>⏳ ¡Ya estás buscando! Por favor espera, o escribe /stop para cancelar.</i>",
        'pt': "<i>⏳ Você já está procurando! Aguarde ou digite /stop para cancelar.</i>",
        'ar': "<i>⏳ أنت تبحث بالفعل! يرجى الانتظار، أو اكتب /stop للإلغاء.</i>",
        'de': "<i>⏳ Du suchst bereits! Bitte warte oder tippe /stop zum Abbrechen.</i>",
        'ja': "<i>⏳ すでに検索中です！お待ちいただくか、 /stop を入力してキャンセルしてください。</i>",
        'zh': "<i>⏳ 您已经在搜索中了！请稍等，或输入 /stop 取消。</i>"
    },
    'in_chat': {
        'en': "<i>💬 You are in a chat! Use /stop to end it. 🔄</i>", 'id': "<i>💬 Kamu sedang obrolan aktif! Gunakan /stop untuk mengakhiri. 🔄</i>",
        'th': "<i>💬 คุณกำลังสนทนาอยู่! ใช้ /stop เพื่อจบการสนทนา 🔄</i>", 'tl': "<i>💬 Nasa loob ka ng chat! Gamitin ang /stop. 🔄</i>",
        'hi': "<i>💬 आप चैट में हैं! समाप्त करने के लिए /stop का उपयोग करें। 🔄</i>", 'ru': "<i>💬 Вы в чате! Используйте /stop для завершения. 🔄</i>",
        'vi': "<i>💬 Bạn đang trong cuộc trò chuyện! Dùng /stop để kết thúc. 🔄</i>", 'es': "<i>💬 ¡Estás en un chat! Usa /stop para terminar. 🔄</i>",
        'pt': "<i>💬 Você está em um chat! Use /stop para encerrar. 🔄</i>", 'ar': "<i>💬 أنت في محادثة! استخدم /stop لإنهائها. 🔄</i>",
        'de': "<i>💬 Du bist in einem Chat! Nutze /stop zum Beenden. 🔄</i>", 'ja': "<i>💬 チャット中です！ /stop で終了してください。 🔄</i>",
        'zh': "<i>💬 您正在聊天！使用 /stop 结束。 🔄</i>"
    },
    'searching': {
        'en': "<i>🔍 Searching for a partner in your city... ⏳</i>", 'id': "<i>🔍 Mencari partner di kotamu... ⏳</i>",
        'th': "<i>🔍 กำลังหาพาร์ทเนอร์ในเมืองของคุณ... ⏳</i>", 'tl': "<i>🔍 Naghahanap ng partner sa iyong siyudad... ⏳</i>",
        'hi': "<i>🔍 आपके शहर में साथी की तलाश... ⏳</i>", 'ru': "<i>🔍 Поиск партнера в вашем городе... ⏳</i>",
        'vi': "<i>🔍 Đang tìm đối tác trong thành phố của bạn... ⏳</i>", 'es': "<i>🔍 Buscando un compañero en tu ciudad... ⏳</i>",
        'pt': "<i>🔍 Procurando um parceiro na sua cidade... ⏳</i>", 'ar': "<i>🔍 جاري البحث عن شريك في مدينتك... ⏳</i>",
        'de': "<i>🔍 Suche Partner in deiner Stadt... ⏳</i>", 'ja': "<i>🔍 あなたの都市でパートナーを検索中... ⏳</i>",
        'zh': "<i>🔍 正在您的城市寻找伙伴... ⏳</i>"
    },
    'expanding_prov': {
        'en': "<i>📡 Expanding search to your province... ⏳</i>", 'id': "<i>📡 Belum ada, memperluas pencarian ke provinsimu... ⏳</i>",
        'th': "<i>📡 ขยายการค้นหาไปยังจังหวัดของคุณ... ⏳</i>", 'tl': "<i>📡 Pinapalawak ang paghahanap sa iyong probinsya... ⏳</i>",
        'hi': "<i>📡 आपके राज्य में खोज का विस्तार किया जा رہا है... ⏳</i>", 'ru': "<i>📡 Расширяем поиск на вашу провинцию... ⏳</i>",
        'vi': "<i>📡 Đang mở rộng tìm kiếm đến tỉnh của bạn... ⏳</i>", 'es': "<i>📡 Expandiendo la búsqueda a tu provincia... ⏳</i>",
        'pt': "<i>📡 Expandindo a busca para sua província... ⏳</i>", 'ar': "<i>📡 توسيع البحث إلى محافظتك... ⏳</i>",
        'de': "<i>📡 Weite Suche auf dein Bundesland aus... ⏳</i>", 'ja': "<i>📡 検索範囲を都道府県に拡大中... ⏳</i>",
        'zh': "<i>📡 正在将搜索范围扩大到您的省份... ⏳</i>"
    },
    'expanding_glob': {
        'en': "<i>🌍 Expanding search globally... ⏳</i>", 'id': "<i>🌍 Memperluas pencarian secara acak... ⏳</i>",
        'th': "<i>🌍 ขยายการค้นหาทั่วโลก... ⏳</i>", 'tl': "<i>🌍 Pinapalawak ang paghahanap sa buong mundo... ⏳</i>",
        'hi': "<i>🌍 वैश्विक स्तर पर खोज का विस्तार किया जा रहा है... ⏳</i>", 'ru': "<i>🌍 Глобальный поиск... ⏳</i>",
        'vi': "<i>🌍 Đang mở rộng tìm kiếm toàn cầu... ⏳</i>", 'es': "<i>🌍 Expandiendo la búsqueda globalmente... ⏳</i>",
        'pt': "<i>🌍 Expandindo a busca globalmente... ⏳</i>", 'ar': "<i>🌍 توسيع البحث عالميًا... ⏳</i>",
        'de': "<i>🌍 Weite Suche global aus... ⏳</i>", 'ja': "<i>🌍 検索範囲をグローバルに拡大中... ⏳</i>",
        'zh': "<i>🌍 正在将搜索范围扩大到全球... ⏳</i>"
    },
    'no_partner': {
        'en': "<i>💤 No partners available right now. We will connect you as soon as someone joins! (Type /stop to cancel)</i>",
        'id': "<i>💤 Belum ada partner yang tersedia. Kamu akan otomatis terhubung begitu ada yang masuk! (Ketik /stop untuk membatalkan)</i>",
        'th': "<i>💤 ไม่มีพาร์ทเนอร์ในขณะนี้ เราจะเชื่อมต่อคุณทันทีที่มีคนเข้าร่วม! (พิมพ์ /stop เพื่อยกเลิก)</i>",
        'tl': "<i>💤 Walang partner ngayon. Iko-connect ka namin kapag may pumasok! (I-type ang /stop para kanselahin)</i>",
        'hi': "<i>💤 अभी कोई साथी उपलब्ध नहीं है। जैसे ही कोई जुड़ेगा हम आपको कनेक्ट कर देंगे! (रद्द करने के लिए /stop टाइप करें)</i>",
        'ru': "<i>💤 Сейчас нет партнеров. Мы подключим вас, как только кто-то зайдет! (Введите /stop для отмены)</i>",
        'vi': "<i>💤 Không có đối tác nào ngay bây giờ. Chúng tôi sẽ kết nối bạn ngay khi có người vào! (Gõ /stop để hủy)</i>",
        'es': "<i>💤 No hay parejas disponibles ahora. ¡Te conectaremos tan pronto alguien entre! (Escribe /stop para cancelar)</i>",
        'pt': "<i>💤 Sem parceiros agora. Vamos conectar você assim que alguém entrar! (Digite /stop para cancelar)</i>",
        'ar': "<i>💤 لا يوجد شركاء متاحون الآن. سنقوم بتوصيلك فور دخول أحدهم! (اكتب /stop للإلغاء)</i>",
        'de': "<i>💤 Momentan keine Partner verfügbar. Wir verbinden dich, sobald jemand beitritt! (Tippe /stop zum Abbrechen)</i>",
        'ja': "<i>💤 現在パートナーがいません。誰かが参加次第、自動的に接続します！ (キャンセルするには /stop)</i>",
        'zh': "<i>💤 目前没有可用的伙伴。一旦有人加入，我们将为您连接！ (输入 /stop 取消)</i>"
    },
    'search_cancelled': {
        'en': "<i>🛑 Search cancelled.\nPress /search for a new partner! 🔄</i>", 'id': "<i>🛑 Pencarian dibatalkan.\nTekan /search untuk mencari partner baru! 🔄</i>",
        'th': "<i>🛑 ยกเลิกการค้นหา\nกด /search สำหรับพาร์ทเนอร์ใหม่! 🔄</i>", 'tl': "<i>🛑 Kinansela ang paghahanap.\nI-press ang /search para sa bagong partner! 🔄</i>",
        'hi': "<i>🛑 खोज रद्द कर दी गई।\nनया साथी खोजने के लिए /search दबाएं! 🔄</i>", 'ru': "<i>🛑 Поиск отменен.\nНажмите /search для нового партнера! 🔄</i>",
        'vi': "<i>🛑 Đã hủy tìm kiếm.\nNhấn /search cho đối tác mới! 🔄</i>", 'es': "<i>🛑 Búsqueda cancelada.\n¡Presiona /search para nueva pareja! 🔄</i>",
        'pt': "<i>🛑 Busca cancelada.\nPressione /search para um novo parceiro! 🔄</i>", 'ar': "<i>🛑 تم إلغاء البحث.\nاضغط /search لشريك جديد! 🔄</i>",
        'de': "<i>🛑 Suche abgebrochen.\nDrücke /search für neuen Partner! 🔄</i>", 'ja': "<i>🛑 検索をキャンセルしました。\n新しいパートナーを探すには /search！ 🔄</i>",
        'zh': "<i>🛑 搜索已取消。\n点击 /search 寻找新伙伴！ 🔄</i>"
    },
    'not_in_chat': {
        'en': "<i>🚫 You are not in a chat right now.\nPress /search for a new partner! 🔄</i>", 'id': "<i>🚫 Kamu sedang tidak dalam obrolan saat ini.\nTekan /search untuk mencari partner baru! 🔄</i>",
        'th': "<i>🚫 คุณไม่ได้อยู่ในแชท\nกด /search สำหรับพาร์ทเนอร์ใหม่! 🔄</i>", 'tl': "<i>🚫 Wala ka sa chat ngayon.\nI-press ang /search! 🔄</i>",
        'hi': "<i>🚫 आप अभी किसी चैट में नहीं हैं।\nनया साथी खोजने के लिए /search दबाएं! 🔄</i>", 'ru': "<i>🚫 Вы не в чате.\nНажмите /search для нового партнера! 🔄</i>",
        'vi': "<i>🚫 Hiện tại bạn không ở trong cuộc trò chuyện.\nNhấn /search cho đối tác mới! 🔄</i>", 'es': "<i>🚫 No estás en un chat.\n¡Presiona /search para uno nuevo! 🔄</i>",
        'pt': "<i>🚫 Você não está num chat.\nPressione /search para um novo parceiro! 🔄</i>", 'ar': "<i>🚫 أنت لست في محادثة الآن.\nاضغط /search لشريك جديد! 🔄</i>",
        'de': "<i>🚫 Du bist in keinem Chat.\nDrücke /search für neuen Partner! 🔄</i>", 'ja': "<i>🚫 現在チャット中ではありません。\n新しいパートナーを探すには /search！ 🔄</i>",
        'zh': "<i>🚫 您现在不在聊天中。\n点击 /search 寻找新伙伴！ 🔄</i>"
    },
    'partner_stopped': {
        'en': "<i>💔 Your partner has ended the chat.\nClick /next or /search to find a new partner!</i>", 'id': "<i>💔 Partnermu telah mengakhiri obrolan.\nTekan /next atau /search untuk mencari partner baru!</i>",
        'th': "<i>💔 พาร์ทเนอร์ของคุณได้จบการสนทนา\nคลิก /next หรือ /search สำหรับพาร์ทเนอร์ใหม่!</i>", 'tl': "<i>💔 Tinapos ng partner mo ang chat.\nI-click ang /next o /search!</i>",
        'hi': "<i>💔 आपके साथी ने चैट समाप्त कर दी है।\nनया साथी खोजने के लिए /next या /search क्लिक करें!</i>", 'ru': "<i>💔 Ваш партнер завершил чат.\nНажмите /next или /search для нового партнера!</i>",
        'vi': "<i>💔 Đối tác của bạn đã kết thúc trò chuyện.\nNhấp /next hoặc /search để tìm đối tác mới!</i>", 'es': "<i>💔 Tu compañero ha finalizado el chat.\n¡Haz clic en /next o /search!</i>",
        'pt': "<i>💔 Seu parceiro encerrou o chat.\nClique em /next ou /search!</i>", 'ar': "<i>💔 شريكك أنهى الدردشة.\nانقر على /next أو /search للبحث من جديد!</i>",
        'de': "<i>💔 Dein Partner hat den Chat beendet.\nKlicke /next oder /search!</i>", 'ja': "<i>💔 パートナーがチャットを終了しました。\n/next または /search をクリックしてください！</i>",
        'zh': "<i>💔 您的伙伴已结束聊天。\n点击 /next 或 /search 寻找新伙伴！</i>"
    },
    'stop_dialogue': {
        'en': "<i>🛑 Hmmmm... you stopped the dialogue.\nPress /search for a new partner! 🔄</i>", 'id': "<i>🛑 Hmmmm... kamu mengakhiri obrolan.\nTekan /search untuk mencari partner baru! 🔄</i>",
        'th': "<i>🛑 อืม... คุณหยุดการสนทนา\nกด /search สำหรับคนใหม่! 🔄</i>", 'tl': "<i>🛑 Hmmmm... itinigil mo ang usapan.\nI-press ang /search para sa bago! 🔄</i>",
        'hi': "<i>🛑 हम्म... आपने बातचीत बंद कर दी।\nनया साथी खोजने के लिए /search दबाएं! 🔄</i>", 'ru': "<i>🛑 Хммм... вы остановили диалог.\nНажмите /search для нового партнера! 🔄</i>",
        'vi': "<i>🛑 Hmmmm... bạn đã dừng cuộc trò chuyện.\nNhấn /search để tìm đối tác mới! 🔄</i>", 'es': "<i>🛑 Hmmmm... detuviste el diálogo.\n¡Presiona /search para uno nuevo! 🔄</i>",
        'pt': "<i>🛑 Hmmmm... você parou o diálogo.\nPressione /search para um novo parceiro! 🔄</i>", 'ar': "<i>🛑 همم... لقد أوقفت الحوار.\nاضغط /search لشريك جديد! 🔄</i>",
        'de': "<i>🛑 Hmmmm... du hast den Dialog beendet.\nDrücke /search für neuen Partner! 🔄</i>", 'ja': "<i>🛑 うーん... 会話を終了しました。\n新しいパートナーを探すには /search！ 🔄</i>",
        'zh': "<i>🛑 提示... 你停止了对话。\n点击 /search 寻找新伙伴！ 🔄</i>"
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
    'invite_msg': {
        'en': "<i>🎁 Invite 10 people for free pro version for 1 weeks.\n\nHere your invite link :\n\n{link}\n\nTotal Invite : {invites}/10</i>",
        'id': "<i>🎁 Undang 10 orang untuk mendapatkan versi pro gratis selama 1 minggu.\n\nBerikut tautan undanganmu:\n\n{link}\n\nTotal Undangan : {invites}/10</i>",
        'th': "<i>🎁 เชิญ 10 คนรับรุ่นโปรฟรี 1 สัปดาห์\n\nลิงก์เชิญของคุณ:\n\n{link}\n\nเชิญทั้งหมด : {invites}/10</i>",
        'tl': "<i>🎁 Mag-imbita ng 10 tao para sa libreng pro version ng 1 linggo.\n\nNarito ang iyong invite link:\n\n{link}\n\nTotal na Imbita : {invites}/10</i>",
        'hi': "<i>🎁 1 सप्ताह के लिए मुफ़्त प्रो संस्करण के लिए 10 लोगों को आमंत्रित करें।\n\nयहाँ आपका आमंत्रण लिंक है:\n\n{link}\n\nकुल आमंत्रण : {invites}/10</i>",
        'ru': "<i>🎁 Пригласите 10 человек для бесплатной PRO на 1 неделю.\n\nВаша ссылка:\n\n{link}\n\nВсего приглашений : {invites}/10</i>",
        'vi': "<i>🎁 Mời 10 người để nhận bản pro miễn phí trong 1 tuần.\n\nLiên kết mời của bạn:\n\n{link}\n\nTổng số lời mời : {invites}/10</i>",
        'es': "<i>🎁 Invita a 10 personas para obtener la versión pro gratis por 1 semana.\n\nAquí tienes tu enlace:\n\n{link}\n\nInvitados en total : {invites}/10</i>",
        'pt': "<i>🎁 Convide 10 pessoas para a versão pro grátis por 1 semana.\n\nSeu link de convite:\n\n{link}\n\nConvites totais : {invites}/10</i>",
        'ar': "<i>🎁 ادع 10 أشخاص للحصول على نسخة البرو مجانًا لمدة أسبوع.\n\nرابط الدعوة الخاص بك:\n\n{link}\n\nإجمالي الدعوات : {invites}/10</i>",
        'de': "<i>🎁 Lade 10 Personen für 1 Woche kostenlos PRO ein.\n\nDein Einladungslink:\n\n{link}\n\nEinladungen gesamt : {invites}/10</i>",
        'ja': "<i>🎁 10人を招待して1週間の無料PRO版をゲット！\n\nあなたの招待リンク：\n\n{link}\n\n招待合計 : {invites}/10</i>",
        'zh': "<i>🎁 邀请 10 人免费获得 1 周的 pro 版本。\n\n这是您的邀请链接：\n\n{link}\n\n总邀请 : {invites}/10</i>"
    },
    'report_reason': {
        'en': "<i>Select a reason for reporting:</i>", 'id': "<i>Pilih alasan melaporkan:</i>",
        'th': "<i>เลือกเหตุผลที่รายงาน:</i>", 'tl': "<i>Pumili ng dahilan ng pag-report:</i>",
        'hi': "<i>रिपोर्टिंग का कारण चुनें:</i>", 'ru': "<i>Выберите причину жалобы:</i>",
        'vi': "<i>Chọn lý do báo cáo:</i>", 'es': "<i>Selecciona una razón para reportar:</i>",
        'pt': "<i>Selecione um motivo para reportar:</i>", 'ar': "<i>اختر سبب الإبلاغ:</i>",
        'de': "<i>Wähle einen Grund für die Meldung:</i>", 'ja': "<i>報告の理由を選択してください:</i>",
        'zh': "<i>选择举报原因:</i>"
    },
    'report_received': {
        'en': "<i>✅ Report received. Thank you for keeping the community safe!</i>", 'id': "<i>✅ Laporan diterima. Terima kasih telah menjaga keamanan komunitas ini!</i>",
        'th': "<i>✅ ได้รับรายงานแล้ว ขอบคุณที่รักษาชุมชนให้ปลอดภัย!</i>", 'tl': "<i>✅ Natanggap ang report. Salamat!</i>",
        'hi': "<i>✅ रिपोर्ट प्राप्त हुई। सुरक्षित रखने के लिए धन्यवाद!</i>", 'ru': "<i>✅ Жалоба получена. Спасибо за помощь!</i>",
        'vi': "<i>✅ Đã nhận báo cáo. Cảm ơn bạn!</i>", 'es': "<i>✅ Reporte recibido. ¡Gracias por tu ayuda!</i>",
        'pt': "<i>✅ Relatório recebido. Obrigado por ajudar!</i>", 'ar': "<i>✅ تم استلام التقرير. شكراً لك!</i>",
        'de': "<i>✅ Meldung erhalten. Danke für deine Hilfe!</i>", 'ja': "<i>✅ 報告を受信しました。ありがとうございます！</i>",
        'zh': "<i>✅ 收到举报。谢谢你的支持！</i>"
    },
    'pro_setting': {
        'en': "<i>⭐ PRO SETTING: Choose preferred partner gender:</i>", 'id': "<i>⭐ PENGATURAN PRO: Pilih prioritas gender partner:</i>",
        'th': "<i>⭐ การตั้งค่า PRO: เลือกเพศพาร์ทเนอร์:</i>", 'tl': "<i>⭐ PRO SETTING: Piliin ang gender ng partner:</i>",
        'hi': "<i>⭐ प्रो सेटिंग: पसंदीदा साथी लिंग चुनें:</i>", 'ru': "<i>⭐ НАСТРОЙКИ PRO: Выберите пол партнера:</i>",
        'vi': "<i>⭐ CÀI ĐẶT PRO: Chọn giới tính đối tác:</i>", 'es': "<i>⭐ AJUSTES PRO: Elige el género de tu pareja:</i>",
        'pt': "<i>⭐ CONFIGURAÇÃO PRO: Escolha o gênero do parceiro:</i>", 'ar': "<i>⭐ إعدادات البرو: اختر جنس الشريك:</i>",
        'de': "<i>⭐ PRO-EINSTELLUNG: Wähle das Geschlecht:</i>", 'ja': "<i>⭐ PRO設定: パートナーの性別を選択:</i>",
        'zh': "<i>⭐ PRO 设置：选择首选伙伴性别：</i>"
    },
    'not_pro': {
        'en': "<i>⚠️ You are not a PRO user or PRO expired.</i>", 'id': "<i>⚠️ Kamu bukan pengguna PRO atau masa PRO telah habis.</i>",
        'th': "<i>⚠️ คุณไม่ใช่ PRO หรือสิทธิ์หมดอายุแล้ว</i>", 'tl': "<i>⚠️ Hindi ka PRO o expired na ang iyong PRO.</i>",
        'hi': "<i>⚠️ आप प्रो उपयोगकर्ता नहीं हैं या प्रो समाप्त हो गया है।</i>", 'ru': "<i>⚠️ Вы не являетесь PRO или срок истек.</i>",
        'vi': "<i>⚠️ Bạn không phải PRO hoặc PRO đã hết hạn.</i>", 'es': "<i>⚠️ No eres PRO o tu suscripción ha expirado.</i>",
        'pt': "<i>⚠️ Você não é PRO ou seu PRO expirou.</i>", 'ar': "<i>⚠️ أنت لست مستخدم PRO أو انتهت صلاحية اشتراكك.</i>",
        'de': "<i>⚠️ Du bist kein PRO-Benutzer oder abgelaufen.</i>", 'ja': "<i>⚠️ PROユーザーではないか、PROの有効期限が切れています。</i>",
        'zh': "<i>⚠️ 您不是 PRO 用户或 PRO 已过期。</i>"
    },
    'pref_saved': {
        'en': "<i>✅ Preference saved! You will now prioritize matching with: {pref}</i>", 'id': "<i>✅ Preferensi disimpan! Kamu sekarang memprioritaskan match dengan: {pref}</i>",
        'th': "<i>✅ บันทึกแล้ว! คุณจะให้ความสำคัญกับเพศ: {pref}</i>", 'tl': "<i>✅ Na-save na! Uunahin mong i-match sa: {pref}</i>",
        'hi': "<i>✅ वरीयता सहेजी गई! अब प्राथमिकता: {pref}</i>", 'ru': "<i>✅ Сохранено! Приоритет совпадений: {pref}</i>",
        'vi': "<i>✅ Đã lưu tùy chọn! Ưu tiên ghép với: {pref}</i>", 'es': "<i>✅ ¡Preferencias guardadas! Priorizarás: {pref}</i>",
        'pt': "<i>✅ Preferência salva! Você priorizará: {pref}</i>", 'ar': "<i>✅ تم الحفظ! أولوية التطابق مع: {pref}</i>",
        'de': "<i>✅ Präferenz gespeichert! Priorität für: {pref}</i>", 'ja': "<i>✅ 保存されました！優先マッチング: {pref}</i>",
        'zh': "<i>✅ 偏好已保存！您现在将优先匹配：{pref}</i>"
    },
    'info_text': {
        'en': "<b>📌 Bot Commands</b>\n\n/search - Find a new partner 🔍\n/stop - End the chat 🛑\n/next - Find the next partner ⏭️\n/info - See all commands ℹ️\n/Profil - View your profile 👤\n/EditProfil - Edit your profile setting ⚙️\n/pro - Pro settings ⭐",
        'id': "<b>📌 Daftar Perintah</b>\n\n/search - Cari partner baru 🔍\n/stop - Akhiri obrolan 🛑\n/next - Cari partner selanjutnya ⏭️\n/info - Lihat semua perintah ℹ️\n/Profil - Lihat profilmu 👤\n/EditProfil - Edit pengaturan profil ⚙️\n/pro - Pengaturan Pro ⭐",
        'th': "<b>📌 คำสั่งของบอท</b>\n\n/search - หาคู่ใหม่ 🔍\n/stop - จบการสนทนา 🛑\n/next - หาคู่คนต่อไป ⏭️\n/info - ดูคำสั่งทั้งหมด ℹ️\n/Profil - ดูโปรไฟล์ของคุณ 👤\n/EditProfil - แก้ไขการตั้งค่าโปรไฟล์ ⚙️\n/pro - การตั้งค่า Pro ⭐",
        'tl': "<b>📌 Mga Bot Command</b>\n\n/search - Maghanap ng partner 🔍\n/stop - Tapusin ang chat 🛑\n/next - Susunod na partner ⏭️\n/info - Tingnan ang commands ℹ️\n/Profil - Tingnan ang profile 👤\n/EditProfil - I-edit ang profile ⚙️\n/pro - Pro settings ⭐",
        'hi': "<b>📌 बॉट कमांड</b>\n\n/search - नया साथी खोजें 🔍\n/stop - चैट समाप्त करें 🛑\n/next - अगला साथी ⏭️\n/info - सभी कमांड ℹ️\n/Profil - प्रोफ़ाइल 👤\n/EditProfil - प्रोफ़ाइल संपादित करें ⚙️\n/pro - प्रो सेटिंग्स ⭐",
        'ru': "<b>📌 Команды</b>\n\n/search - Найти партнера 🔍\n/stop - Завершить чат 🛑\n/next - Следующий партнер ⏭️\n/info - Все команды ℹ️\n/Profil - Ваш профиль 👤\n/EditProfil - Настройки профиля ⚙️\n/pro - Настройки PRO ⭐",
        'vi': "<b>📌 Lệnh Bot</b>\n\n/search - Tìm đối tác mới 🔍\n/stop - Kết thúc trò chuyện 🛑\n/next - Đối tác tiếp theo ⏭️\n/info - Xem tất cả các lệnh ℹ️\n/Profil - Xem hồ sơ của bạn 👤\n/EditProfil - Chỉnh sửa hồ sơ ⚙️\n/pro - Cài đặt Pro ⭐",
        'es': "<b>📌 Comandos del Bot</b>\n\n/search - Buscar nueva pareja 🔍\n/stop - Terminar el chat 🛑\n/next - Siguiente pareja ⏭️\n/info - Ver todos los comandos ℹ️\n/Profil - Ver tu perfil 👤\n/EditProfil - Editar perfil ⚙️\n/pro - Configuración Pro ⭐",
        'pt': "<b>📌 Comandos do Bot</b>\n\n/search - Encontrar novo parceiro 🔍\n/stop - Terminar o chat 🛑\n/next - Próximo parceiro ⏭️\n/info - Ver todos os comandos ℹ️\n/Profil - Ver seu perfil 👤\n/EditProfil - Editar perfil ⚙️\n/pro - Configurações Pro ⭐",
        'ar': "<b>📌 أوامر البوت</b>\n\n/search - ابحث عن شريك جديد 🔍\n/stop - إنهاء الدردشة 🛑\n/next - الشريك التالي ⏭️\n/info - رؤية جميع الأوامر ℹ️\n/Profil - عرض ملفك الشخصي 👤\n/EditProfil - تعديل ملفك ⚙️\n/pro - إعدادات البرو ⭐",
        'de': "<b>📌 Bot-Befehle</b>\n\n/search - Neuen Partner finden 🔍\n/stop - Chat beenden 🛑\n/next - Nächsten Partner finden ⏭️\n/info - Alle Befehle sehen ℹ️\n/Profil - Dein Profil 👤\n/EditProfil - Profil bearbeiten ⚙️\n/pro - Pro-Einstellungen ⭐",
        'ja': "<b>📌 ボットのコマンド</b>\n\n/search - 新しいパートナーを探す 🔍\n/stop - チャットを終了する 🛑\n/next - 次のパートナーを探す ⏭️\n/info - 全てのコマンドを見る ℹ️\n/Profil - プロフィールを見る 👤\n/EditProfil - プロフィールを編集 ⚙️\n/pro - プロ設定 ⭐",
        'zh': "<b>📌 机器人命令</b>\n\n/search - 寻找新伙伴 🔍\n/stop - 结束聊天 🛑\n/next - 寻找下一个伙伴 ⏭️\n/info - 查看所有命令 ℹ️\n/Profil - 查看您的个人资料 👤\n/EditProfil - 编辑个人资料 ⚙️\n/pro - Pro 设置 ⭐"
    },
    'profile_title': {
        'en': "<b>👤 Your Profile:</b>", 'id': "<b>👤 Profil Kamu:</b>",
        'th': "<b>👤 โปรไฟล์ของคุณ:</b>", 'tl': "<b>👤 Iyong Profile:</b>",
        'hi': "<b>👤 आपकी प्रोफ़ाइल:</b>", 'ru': "<b>👤 Ваш профиль:</b>",
        'vi': "<b>👤 Hồ sơ của bạn:</b>", 'es': "<b>👤 Tu perfil:</b>",
        'pt': "<b>👤 Seu perfil:</b>", 'ar': "<b>👤 ملفك الشخصي:</b>",
        'de': "<b>👤 Dein Profil:</b>", 'ja': "<b>👤 あなたのプロフィール:</b>",
        'zh': "<b>👤 您的个人资料：</b>"
    },
    'profile_reset': {
        'en': "<i>⚙️ Profile reset. Please type /start to create a new profile.</i>", 'id': "<i>⚙️ Profil direset. Silakan ketik /start untuk membuat profil baru.</i>",
        'th': "<i>⚙️ รีเซ็ตโปรไฟล์แล้ว กรุณาพิมพ์ /start</i>", 'tl': "<i>⚙️ Na-reset ang profile. I-type ang /start.</i>",
        'hi': "<i>⚙️ प्रोफ़ाइल रीसेट। कृपया /start टाइप करें।</i>", 'ru': "<i>⚙️ Профиль сброшен. Введите /start.</i>",
        'vi': "<i>⚙️ Đặt lại hồ sơ. Nhập /start để tạo mới.</i>", 'es': "<i>⚙️ Perfil restablecido. Escribe /start.</i>",
        'pt': "<i>⚙️ Perfil resetado. Digite /start.</i>", 'ar': "<i>⚙️ تمت إعادة تعيين الملف الشخصي. اكتب /start.</i>",
        'de': "<i>⚙️ Profil zurückgesetzt. Tippe /start.</i>", 'ja': "<i>⚙️ プロフィールがリセットされました。 /start と入力してください。</i>",
        'zh': "<i>⚙️ 个人资料已重置。请键入 /start。</i>"
    },
    'media_expired': {
        'en': "⚠️ Media expired or retracted.", 'id': "⚠️ Media sudah kedaluwarsa atau ditarik.",
        'th': "⚠️ สื่อหมดอายุหรือถูกดึงกลับ", 'tl': "⚠️ Expired o binawi na ang media.",
        'hi': "⚠️ मीडिया समाप्त हो गया या वापस ले लिया गया।", 'ru': "⚠️ Медиа истекло или отозвано.",
        'vi': "⚠️ Phương tiện đã hết hạn hoặc bị rút lại.", 'es': "⚠️ Medio expirado o retirado.",
        'pt': "⚠️ Mídia expirada ou retirada.", 'ar': "⚠️ انتهت صلاحية الوسائط أو تم سحبها.",
        'de': "⚠️ Medium abgelaufen oder zurückgezogen.", 'ja': "⚠️ メディアの有効期限が切れたか、取り消されました。",
        'zh': "⚠️ 媒体已过期或被撤回。"
    },
    'muted': {
        'en': "<i>🔇 You are muted by the admin system.</i>", 'id': "<i>🔇 Kamu sedang di-mute oleh sistem admin.</i>",
        'th': "<i>🔇 คุณถูกปิดเสียงโดยระบบ</i>", 'tl': "<i>🔇 Naka-mute ka ng admin system.</i>",
        'hi': "<i>🔇 आपको एडमिन सिस्टम द्वारा म्यूट कर दिया गया है।</i>", 'ru': "<i>🔇 Вы заглушены администратором.</i>",
        'vi': "<i>🔇 Bạn bị hệ thống admin tắt tiếng.</i>", 'es': "<i>🔇 Has sido silenciado por el sistema administrador.</i>",
        'pt': "<i>🔇 Você foi silenciado pelo sistema de administração.</i>", 'ar': "<i>🔇 تم كتم صوتك من قبل النظام الإداري.</i>",
        'de': "<i>🔇 Du wurdest vom Adminsystem stummgeschaltet.</i>", 'ja': "<i>🔇 管理システムによりミュートされています。</i>",
        'zh': "<i>🔇 您已被管理员系统禁言。</i>"
    },
    'no_links': {
        'en': "<i>❌ Message blocked! Links are not allowed.</i>", 'id': "<i>❌ Pesan diblokir! Dilarang mengirim tautan/link di bot ini.</i>",
        'th': "<i>❌ ข้อความถูกบล็อก! ไม่อนุญาตให้ใช้ลิงก์</i>", 'tl': "<i>❌ Naka-block ang mensahe! Bawal ang links.</i>",
        'hi': "<i>❌ संदेश अवरुद्ध! लिंक की अनुमति नहीं है।</i>", 'ru': "<i>❌ Сообщение заблокировано! Ссылки запрещены.</i>",
        'vi': "<i>❌ Tin nhắn bị chặn! Không cho phép liên kết.</i>", 'es': "<i>❌ ¡Mensaje bloqueado! No se permiten enlaces.</i>",
        'pt': "<i>❌ Mensagem bloqueada! Links não são permitidos.</i>", 'ar': "<i>❌ تم حظر الرسالة! الروابط غير مسموح بها.</i>",
        'de': "<i>❌ Nachricht blockiert! Links sind nicht erlaubt.</i>", 'ja': "<i>❌ メッセージがブロックされました！リンクは禁止されています。</i>",
        'zh': "<i>❌ 消息被屏蔽！不允许发送链接。</i>"
    },
    'media_sent': {
        'en': "<i>📸 Partner sent a {media}.</i>", 'id': "<i>📸 Partner mengirim sebuah {media}.</i>",
        'th': "<i>📸 พาร์ทเนอร์ส่ง {media}</i>", 'tl': "<i>📸 Nagpadala ng {media} ang iyong partner.</i>",
        'hi': "<i>📸 साथी ने {media} भेजा।</i>", 'ru': "<i>📸 Партнер прислал {media}.</i>",
        'vi': "<i>📸 Đối tác đã gửi một {media}.</i>", 'es': "<i>📸 Tu compañero envió {media}.</i>",
        'pt': "<i>📸 O parceiro enviou {media}.</i>", 'ar': "<i>📸 أرسل الشريك {media}.</i>",
        'de': "<i>📸 Partner hat ein {media} gesendet.</i>", 'ja': "<i>📸 パートナーが {media} を送信しました。</i>",
        'zh': "<i>📸 伙伴发送了一个 {media}。</i>"
    },
    'message_failed': {
        'en': "<i>⚠️ Message failed. Your partner may have blocked the bot. Chat ended.</i>", 'id': "<i>⚠️ Pesan gagal terkirim. Partnermu sepertinya memblokir bot ini. Obrolan dihentikan.</i>",
        'th': "<i>⚠️ ส่งข้อความไม่สำเร็จ แชทจบลงแล้ว</i>", 'tl': "<i>⚠️ Bigong ipadala. Tapos na ang chat.</i>",
        'hi': "<i>⚠️ संदेश विफल रहा। चैट समाप्त।</i>", 'ru': "<i>⚠️ Ошибка отправки. Чат завершен.</i>",
        'vi': "<i>⚠️ Tin nhắn thất bại. Trò chuyện kết thúc.</i>", 'es': "<i>⚠️ Mensaje fallido. Chat finalizado.</i>",
        'pt': "<i>⚠️ Falha na mensagem. Chat encerrado.</i>", 'ar': "<i>⚠️ فشل إرسال الرسالة. انتهت الدردشة.</i>",
        'de': "<i>⚠️ Nachricht fehlgeschlagen. Chat beendet.</i>", 'ja': "<i>⚠️ メッセージ送信に失敗しました。チャット終了。</i>",
        'zh': "<i>⚠️ 消息发送失败。聊天结束。</i>"
    },
    'pro_expired': {
        'en': "<i>⚠️ Your Pro subscription has expired. Daily limits are re-enabled.</i>", 'id': "<i>⚠️ Langganan Pro kamu telah berakhir. Fitur limit harian diaktifkan kembali.</i>",
        'th': "<i>⚠️ การสมัคร PRO ของคุณหมดอายุแล้ว เริ่มใช้ขีดจำกัดรายวัน</i>", 'tl': "<i>⚠️ Expired na ang iyong PRO. Balik na ang daily limits.</i>",
        'hi': "<i>⚠️ आपकी प्रो सदस्यता समाप्त हो गई है। दैनिक सीमाएँ फिर से सक्षम कर दी गई हैं।</i>", 'ru': "<i>⚠️ Ваша подписка PRO истекла. Возвращены дневные лимиты.</i>",
        'vi': "<i>⚠️ Gói Pro của bạn đã hết hạn. Bật lại giới hạn hàng ngày.</i>", 'es': "<i>⚠️ Tu suscripción Pro ha expirado. Los límites diarios están activados nuevamente.</i>",
        'pt': "<i>⚠️ Sua assinatura Pro expirou. Limites diários reativados.</i>", 'ar': "<i>⚠️ انتهت صلاحية اشتراك Pro الخاص بك. عادت الحدود اليومية للعمل.</i>",
        'de': "<i>⚠️ Dein Pro-Abo ist abgelaufen. Tageslimits sind wieder aktiv.</i>", 'ja': "<i>⚠️ PROの有効期限が切れました。1日の制限が再び有効になります。</i>",
        'zh': "<i>⚠️ 您的 Pro 订阅已过期。每日限制已重新启用。</i>"
    },
    'payment_success': {
        'en': "<i>🎉 Payment successful! You are now PRO until {date}. Use /pro to set your preferences!</i>", 'id': "<i>🎉 Pembayaran sukses! Akunmu sekarang menjadi PRO sampai tanggal {date}. Gunakan /pro untuk mengatur preferensi!</i>",
        'th': "<i>🎉 ชำระเงินสำเร็จ! คุณคือ PRO จนถึง {date} ใช้ /pro เพื่อตั้งค่า!</i>", 'tl': "<i>🎉 Tagumpay ang pagbabayad! Ikaw ay PRO na hanggang {date}. Gamitin ang /pro!</i>",
        'hi': "<i>🎉 भुगतान सफल! अब आप {date} तक PRO हैं। /pro का प्रयोग करें!</i>", 'ru': "<i>🎉 Оплата успешна! Вы PRO до {date}. Используйте /pro!</i>",
        'vi': "<i>🎉 Thanh toán thành công! Bạn là PRO đến {date}. Dùng /pro!</i>", 'es': "<i>🎉 ¡Pago exitoso! Ahora eres PRO hasta el {date}. ¡Usa /pro!</i>",
        'pt': "<i>🎉 Pagamento bem-sucedido! Você é PRO até {date}. Use /pro!</i>", 'ar': "<i>🎉 تم الدفع بنجاح! أنت الآن PRO حتى {date}. استخدم /pro!</i>",
        'de': "<i>🎉 Zahlung erfolgreich! Du bist PRO bis {date}. Nutze /pro!</i>", 'ja': "<i>🎉 支払い成功！ {date} までPROです。 /pro を使用してください！</i>",
        'zh': "<i>🎉 支付成功！您现在是 PRO，直到 {date}。 使用 /pro！</i>"
    },
    'btn_find_new': {
        'en': "Find New Partner! 🔄", 'id': "Cari Partner Baru! 🔄",
        'th': "หาคู่ใหม่! 🔄", 'tl': "Maghanap ng Bago! 🔄",
        'hi': "नया साथी खोजें! 🔄", 'ru': "Найти Нового! 🔄",
        'vi': "Tìm Đối Tác Mới! 🔄", 'es': "¡Buscar Nueva Pareja! 🔄",
        'pt': "Encontrar Novo Parceiro! 🔄", 'ar': "ابحث عن شريك جديد! 🔄",
        'de': "Neuen Partner finden! 🔄", 'ja': "新しいパートナーを探す! 🔄",
        'zh': "寻找新伙伴！ 🔄"
    },
    'btn_report': {
        'en': "⚠️ Report Partner", 'id': "⚠️ Laporkan Partner",
        'th': "⚠️ รายงานพาร์ทเนอร์", 'tl': "⚠️ I-report ang Partner",
        'hi': "⚠️ साथी की रिपोर्ट करें", 'ru': "⚠️ Пожаловаться",
        'vi': "⚠️ Báo cáo Đối tác", 'es': "⚠️ Reportar Pareja",
        'pt': "⚠️ Reportar Parceiro", 'ar': "⚠️ الإبلاغ عن الشريك",
        'de': "⚠️ Partner melden", 'ja': "⚠️ パートナーを報告",
        'zh': "⚠️ 举报伙伴"
    },
    'btn_open_media': {
        'en': "📁 Open {media}", 'id': "📁 Buka {media}",
        'th': "📁 เปิด {media}", 'tl': "📁 Buksan {media}",
        'hi': "📁 खोलें {media}", 'ru': "📁 Открыть {media}",
        'vi': "📁 Mở {media}", 'es': "📁 Abrir {media}",
        'pt': "📁 Abrir {media}", 'ar': "📁 فتح {media}",
        'de': "📁 Öffne {media}", 'ja': "📁 開く {media}",
        'zh': "📁 打开 {media}"
    }
}

def get_t(lang, key, **kwargs):
    text = TEXTS.get(key, {}).get(lang)
    if not text: 
        text = TEXTS.get(key, {}).get('en', '')
    if kwargs:
        return text.format(**kwargs)
    return text

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
            
            log_msg = f"📊 *LOG ANALITIK (1 Menit Terakhir)*\n\n👥 Total Users DB: {total_users}\n⚡ Match Making: {mps:.2f} match/detik\n🟢 Status VPS: AMAN"
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

def check_punishment(user):
    if not user: return False, None
    now = datetime.utcnow().isoformat()
    if user.get('banned_until') and user['banned_until'] > now:
        return True, "banned"
    return False, None

def generate_ref_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# --- LOGIKA PENGECEKAN KEDALUWARSA PRO ---
def validate_pro_status(user):
    if user.get('is_pro') and user.get('pro_until'):
        pro_end_str = user['pro_until'].replace("Z", "").split("+")[0] 
        pro_end = datetime.fromisoformat(pro_end_str)
        if datetime.utcnow() > pro_end:
            update_user(user['user_id'], {'is_pro': False, 'pref_gender': None})
            lang = user.get('language', 'en')
            bot.send_message(user['user_id'], get_t(lang, 'pro_expired'), parse_mode="HTML")
            return False
    return user.get('is_pro', False)

# --- LOGIKA DAILY LIMIT (150 MATCH) ---
def check_daily_limit(user):
    if validate_pro_status(user): return True 
    today = datetime.utcnow().date().isoformat()
    if user.get('last_match_date') != today:
        update_user(user['user_id'], {'matches_today': 0, 'last_match_date': today})
        return True
    return user.get('matches_today', 0) < 150

# --- HANDLER PEMBAYARAN TELEGRAM STARS ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
def send_pro_invoice(call):
    chat_id = call.message.chat.id
    plan = call.data.split('_')[1]
    
    if plan == '1m':
        title, desc, payload, amount = "Pro 1 Month", "1 Month Unlimited & Gender Priority", "pro_1m", 35
    elif plan == '6m':
        title, desc, payload, amount = "Pro 6 Months", "6 Months Unlimited & Gender Priority", "pro_6m", 185
    elif plan == '1y':
        title, desc, payload, amount = "Pro 1 Year", "1 Year Unlimited & Gender Priority", "pro_1y", 335
    
    prices = [telebot.types.LabeledPrice(label=title, amount=amount)]
    
    bot.send_invoice(
        chat_id=chat_id, title=title, description=desc,
        invoice_payload=payload, provider_token="", 
        currency="XTR", prices=prices
    )

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    payload = message.successful_payment.invoice_payload
    user = get_user(message.chat.id)
    lang = user.get('language', 'en') if user else 'en'
    now = datetime.utcnow()
    
    if payload == 'pro_1m': days_to_add = 30
    elif payload == 'pro_6m': days_to_add = 180
    elif payload == 'pro_1y': days_to_add = 365
    
    if user.get('is_pro') and user.get('pro_until'):
        current_end_str = user['pro_until'].replace("Z", "").split("+")[0]
        start_date = datetime.fromisoformat(current_end_str)
        if start_date < now: start_date = now
    else:
        start_date = now
        
    new_pro_date = (start_date + timedelta(days=days_to_add)).isoformat()
    update_user(message.chat.id, {'is_pro': True, 'pro_until': new_pro_date})
    
    date_str = start_date.strftime('%Y-%m-%d')
    bot.send_message(message.chat.id, get_t(lang, 'payment_success', date=date_str), parse_mode="HTML")

# --- ALUR REGISTRASI ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_spamming(message.chat.id): return 
    
    args = message.text.split()
    ref_code = args[1] if len(args) > 1 else None

    user = get_user(message.chat.id)
    is_punished, reason = check_punishment(user)
    if is_punished:
        lang = user.get('language', 'en') if user else 'en'
        bot.send_message(message.chat.id, get_t(lang, 'banned'), parse_mode="HTML")
        return

    # LOGIKA REFERRAL ANTI-TUYUL
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
                    ref_lang = ref_user.get('language', 'en')
                    bot.send_message(ref_user['user_id'], get_t(ref_lang, 'invite_success'), parse_mode="HTML")
                else:
                    update_user(ref_user['user_id'], {'invite_count': new_count})

    if user and user.get('age'):
        if message.from_user.username:
            update_user(message.chat.id, {'username': message.from_user.username})
        lang = user.get('language', 'en')
        bot.send_message(message.chat.id, get_t(lang, 'already_registered'), parse_mode="HTML")
        return

    markup = InlineKeyboardMarkup()
    row = []
    for code, name in LANGUAGES.items():
        row.append(InlineKeyboardButton(name, callback_data=f"lang_{code}"))
        if len(row) == 2:
            markup.add(*row)
            row = []
    if row: markup.add(*row)
    
    # PESAN WELCOME ALWAYS ENGLISH
    bot.send_message(message.chat.id, WELCOME_EN_ONLY, reply_markup=markup, parse_mode="HTML")
    
@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    lang = call.data.split('_')[1]
    uname = call.message.chat.username or ""
    user_registration[call.message.chat.id] = {'language': lang, 'username': uname}
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Male ♂️", callback_data="gender_male"), InlineKeyboardButton("Female ♀️", callback_data="gender_female"))
    bot.edit_message_text(get_t(lang, 'select_gender'), call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('gender_'))
def set_gender(call):
    chat_id = call.message.chat.id
    if chat_id not in user_registration: return
    lang = user_registration[chat_id]['language']
    user_registration[chat_id]['gender'] = "Male" if call.data == "gender_male" else "Female"
    
    msg = bot.edit_message_text(get_t(lang, 'enter_age'), chat_id, call.message.message_id, parse_mode="HTML")
    bot.register_next_step_handler(msg, process_age)

def process_age(message):
    chat_id = message.chat.id
    lang = user_registration.get(chat_id, {}).get('language', 'en')
    if not message.text.isdigit() or int(message.text) < 17:
        bot.send_message(chat_id, get_t(lang, 'age_error'), parse_mode="HTML")
        return
    user_registration[chat_id]['age'] = int(message.text)
    msg = bot.send_message(chat_id, get_t(lang, 'enter_prov'), parse_mode="HTML")
    bot.register_next_step_handler(msg, process_province)

def process_province(message):
    chat_id = message.chat.id
    lang = user_registration.get(chat_id, {}).get('language', 'en')
    user_registration[chat_id]['province'] = message.text.strip().title()
    msg = bot.send_message(chat_id, get_t(lang, 'enter_city'), parse_mode="HTML")
    bot.register_next_step_handler(msg, process_location)

def process_location(message):
    chat_id = message.chat.id
    lang = user_registration.get(chat_id, {}).get('language', 'en')
    user_registration[chat_id]['location'] = message.text.strip().title()
    msg = bot.send_message(chat_id, get_t(lang, 'enter_about'), parse_mode="HTML")
    bot.register_next_step_handler(msg, process_about)

def process_about(message):
    chat_id = message.chat.id
    data = user_registration.get(chat_id)
    if not data: return
    data['about'] = message.text
    create_or_update_user(chat_id, data)
    
    lang = data['language']
    profile_text = f"{get_t(lang, 'profile_saved')}\n\n⚧️ Gender: {html.escape(data['gender'])}\n🎂 Age: {data['age']}\n🗺️ Province: {html.escape(data.get('province', '-'))}\n🏙️ City: {html.escape(data['location'])}\n📝 About Me: {html.escape(data['about'])}\n\n{get_t(lang, 'cmds')}"
    bot.send_message(chat_id, profile_text, parse_mode="HTML")

# --- ALUR MATCHMAKING ---
def attempt_match(chat_id, user_data, scope, value):
    current_me = get_user(chat_id)
    if current_me and current_me['status'] == 'chatting': return True
    
    query = supabase.table('users').select('*').eq('status', 'searching').neq('user_id', chat_id)
    if scope == 'location': query = query.eq('location', value)
    elif scope == 'province': query = query.eq('province', value)
    
    if validate_pro_status(current_me) and current_me.get('pref_gender'):
        query = query.eq('gender', current_me['pref_gender'])

    res = query.limit(1).execute()
    if res.data:
        partner = res.data[0]
        
        if not validate_pro_status(current_me):
            update_user(chat_id, {'matches_today': current_me.get('matches_today', 0) + 1})
        if not validate_pro_status(partner):
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
    text = f"{get_t(lang, 'partner_found')}\n\n⚧️ Gender: {html.escape(partner_data['gender'])}\n🎂 Age: {partner_data['age']}\n🗺️ Province: {html.escape(partner_data.get('province', '-'))}\n🏙️ City: {html.escape(partner_data['location'])}\n📝 About Me: {html.escape(partner_data['about'])}\n\n{get_t(lang, 'disclaimer')}\n@micifindbot"
    bot.send_message(to_id, text, parse_mode="HTML")

@bot.message_handler(commands=['search', 'next'])
def search_partner(message):
    if is_spamming(message.chat.id): return 
    
    user = get_user(message.chat.id)
    if not user:
        bot.send_message(message.chat.id, get_t('en', 'please_start'), parse_mode="HTML")
        return
    
    is_punished, reason = check_punishment(user)
    lang = user.get('language', 'en')
    
    if is_punished:
        bot.send_message(message.chat.id, get_t(lang, 'banned'), parse_mode="HTML")
        return

    if not check_daily_limit(user):
        bot.send_message(message.chat.id, get_t(lang, 'limit_reached'), parse_mode="HTML")
        send_upsell_menu(message.chat.id, lang)
        return
    
    if user['status'] == 'searching':
        bot.send_message(message.chat.id, get_t(lang, 'already_searching'), parse_mode="HTML")
        return

    if user['status'] == 'chatting' and message.text == '/search':
        bot.send_message(message.chat.id, get_t(lang, 'in_chat'), parse_mode="HTML")
        return

    if user['status'] == 'chatting' and user['partner_id']:
        handle_stop(message.chat.id, user, user['partner_id'], is_next=True)
        time.sleep(1.5)

    update_user(message.chat.id, {'status': 'searching', 'partner_id': None})
    
    msg = bot.send_message(message.chat.id, get_t(lang, 'searching'), parse_mode="HTML")
    if attempt_match(message.chat.id, user, 'location', user['location']): return
    time.sleep(3)
    
    if get_user(message.chat.id)['status'] != 'searching': return
    if attempt_match(message.chat.id, user, 'location', user['location']): return
    
    try: bot.edit_message_text(get_t(lang, 'expanding_prov'), message.chat.id, msg.message_id, parse_mode="HTML")
    except: pass
    
    if attempt_match(message.chat.id, user, 'province', user['province']): return
    time.sleep(3)
    
    if get_user(message.chat.id)['status'] != 'searching': return
    if attempt_match(message.chat.id, user, 'province', user['province']): return
    
    try: bot.edit_message_text(get_t(lang, 'expanding_glob'), message.chat.id, msg.message_id, parse_mode="HTML")
    except: pass
    
    if attempt_match(message.chat.id, user, 'all', None): return
    
    try: bot.edit_message_text(get_t(lang, 'no_partner'), message.chat.id, msg.message_id, parse_mode="HTML")
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
        bot.send_message(message.chat.id, get_t(lang, 'search_cancelled'), parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, get_t(lang, 'not_in_chat'), parse_mode="HTML")

def handle_stop(stopper_id, stopper_data, partner_id, is_next=False):
    lang_stopper = stopper_data.get('language', 'en')
    update_user(stopper_id, {'status': 'idle', 'partner_id': None})
    
    if partner_id:
        partner_data = get_user(partner_id)
        lang_partner = partner_data.get('language', 'en') if partner_data else 'en'
        update_user(partner_id, {'status': 'idle', 'partner_id': None})
        
        markup_partner = InlineKeyboardMarkup()
        markup_partner.add(InlineKeyboardButton(get_t(lang_partner, 'btn_find_new'), callback_data="btn_search"))
        
        try:
            bot.send_message(partner_id, get_t(lang_partner, 'partner_stopped'), reply_markup=markup_partner, parse_mode="HTML")
            send_upsell_menu(partner_id, lang_partner)
        except:
            pass 

    markup_report = InlineKeyboardMarkup()
    markup_report.add(InlineKeyboardButton(get_t(lang_stopper, 'btn_report'), callback_data=f"report_{partner_id}"))
    
    try:
        bot.send_message(stopper_id, get_t(lang_stopper, 'stop_dialogue'), reply_markup=markup_report, parse_mode="HTML")
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
    lang = user.get('language', 'en')
    ref_code = user.get('referral_code', 'ERROR')
    invites = user.get('invite_count', 0)
    bot_username = bot.get_me().username
    invite_link = f"https://t.me/{bot_username}?start={ref_code}"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⬅️ Back", callback_data="back_upsell"))
    bot.edit_message_text(get_t(lang, 'invite_msg', link=invite_link, invites=invites), call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

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
        
    bot.edit_message_text(get_t(lang, 'report_reason'), call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

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

    bot.edit_message_text(get_t(lang, 'report_received'), call.message.chat.id, call.message.message_id, parse_mode="HTML")

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
    lang = user.get('language', 'en') if user else 'en'
    
    if user and validate_pro_status(user):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Match with Male ♂️", callback_data="setpref_Male"), 
                   InlineKeyboardButton("Match with Female ♀️", callback_data="setpref_Female"))
        bot.send_message(message.chat.id, get_t(lang, 'pro_setting'), reply_markup=markup, parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, get_t(lang, 'not_pro'), parse_mode="HTML")
        
@bot.callback_query_handler(func=lambda call: call.data.startswith("setpref_"))
def save_pro_pref(call):
    pref = call.data.split('_')[1]
    lang = get_user(call.message.chat.id).get('language', 'en')
    update_user(call.message.chat.id, {'pref_gender': pref})
    bot.edit_message_text(get_t(lang, 'pref_saved', pref=pref), call.message.chat.id, call.message.message_id, parse_mode="HTML")

# --- INFO & PROFILE ---
@bot.message_handler(commands=['info', 'profil', 'Profil', 'editprofil', 'EditProfil'])
def general_commands(message):
    if is_spamming(message.chat.id): return 
    
    user = get_user(message.chat.id)
    if not user: return
    lang = user.get('language', 'en')
    cmd = message.text.split()[0].lower()
    
    if cmd == '/info':
        bot.send_message(message.chat.id, get_t(lang, 'info_text'), parse_mode="HTML")
    
    elif cmd in ['/profil', '/Profil']:
        status_pro = "⭐ VIP PRO" if validate_pro_status(user) else "Regular"
        text = f"{get_t(lang, 'profile_title')}\n\n🎫 Status: {status_pro}\n⚧️ Gender: {html.escape(user['gender'])}\n🎂 Age: {user['age']}\n🗺️ Province: {html.escape(user.get('province', '-'))}\n🏙️ City: {html.escape(user['location'])}\n📝 About Me: {html.escape(user['about'])}"
        bot.send_message(message.chat.id, text, parse_mode="HTML")
    
    elif cmd in ['/editprofil', '/EditProfil']:
        update_user(message.chat.id, {'age': None}) 
        bot.send_message(message.chat.id, get_t(lang, 'profile_reset'), parse_mode="HTML")

# --- CALLBACK UNTUK MEMBUKA MEDIA ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('openmedia_'))
def open_media(call):
    media_id = call.data.split('_')[1]
    lang = get_user(call.message.chat.id).get('language', 'en')
    
    if media_id in media_vault:
        data = media_vault[media_id]
        try:
            bot.copy_message(call.message.chat.id, data['from_chat'], data['msg_id'])
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception as e:
            bot.answer_callback_query(call.id, "❌ Gagal membuka media.")
    else:
        bot.answer_callback_query(call.id, get_t(lang, 'media_expired'), show_alert=True)
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
        bot.send_message(message.chat.id, get_t(lang, 'muted'), parse_mode="HTML")
        return

    has_url = False
    entities = message.entities or message.caption_entities or []
    for ent in entities:
        if ent.type in ['url', 'text_link']:
            has_url = True

    if has_url:
        bot.send_message(message.chat.id, get_t(lang, 'no_links'), parse_mode="HTML")
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
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(get_t(partner_lang, 'btn_open_media', media=media_name), callback_data=f"openmedia_{uid}"))
            
            bot.send_message(user['partner_id'], get_t(partner_lang, 'media_sent', media=media_name), reply_markup=markup, parse_mode="HTML")
            
    except Exception as e:
        handle_stop(message.chat.id, user, user['partner_id'], is_next=False)
        bot.send_message(message.chat.id, get_t(lang, 'message_failed'), parse_mode="HTML")

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

print("🚀 Micifind Bot V13.2 (Ultimate Global Localization) Siap Mengudara!")
bot.infinity_polling(timeout=60, long_polling_timeout=30)
