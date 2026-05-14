import telebot
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

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
                body { font-family: sans-serif; text-align: center; padding: 20px; }
                h1 { font-size: 24px; }
                @media (max-width: 600px) { body { padding: 10px; } h1 { font-size: 18px; } }
            </style>
        </head>
        <body>
            <h1>Bot Telegram Menyala di Render!</h1>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Wah, server Render gratisanmu beneran jalan tanpa error!")

print("Memulai bot...")
bot.infinity_polling()
