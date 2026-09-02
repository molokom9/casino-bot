import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from flask import Flask
import threading
import os

# ========== КОНФИГ ==========
BOT_TOKEN = '8941440753:AAGejY76StUx3ae6paRaTIqQWXr3hPqWkXs'
WEBAPP_URL = 'https://casino-bot-mw0h.onrender.com/'

# ========== БОТ ==========
bot = telebot.TeleBot(BOT_TOKEN)

# ========== ВЕБ-СЕРВЕР ==========
app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Casino</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:Arial;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;justify-content:center;align-items:center;padding:10px}
        .container{background:rgba(255,255,255,0.95);border-radius:20px;padding:20px;max-width:400px;width:100%}
        h1{text-align:center;color:#333;margin-bottom:15px}
        .balance{background:#f0f0f0;padding:12px;border-radius:10px;text-align:center;font-size:20px;font-weight:bold;margin-bottom:15px}
        .slots{display:flex;justify-content:space-around;margin:15px 0}
        .slot{width:70px;height:70px;background:white;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:40px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
        .slot.spinning{animation:spin 0.5s}
        @keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
        .btn-spin{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border:none;padding:15px;font-size:20px;border-radius:10px;cursor:pointer;width:100%;margin:10px 0}
        .btn-spin:disabled{opacity:0.6}
        .bet-control{display:flex;align-items:center;justify-content:center;gap:10px;margin:10px 0}
        .bet-control input{padding:8px;border:2px solid #ddd;border-radius:8px;width:100px;text-align:center}
        .result{text-align:center;font-size:18px;font-weight:bold;min-height:30px;margin:10px 0}
        .result.win{color:#28a745}
        .result.lose{color:#dc3545}
        .history{margin-top:15px;padding-top:15px;border-top:2px solid #eee}
        #historyList{max-height:150px;overflow-y:auto}
        .history-item{padding:5px 10px;margin:5px 0;background:#f8f9fa;border-radius:5px;display:flex;justify-content:space-between}
        .btn-close{width:100%;padding:12px;background:#dc3545;color:#fff;border:none;border-radius:10px;font-size:16px;cursor:pointer;margin-top:10px}
    </style>
</head>
<body>
<div class="container">
    <h1>🎰 Casino</h1>
    <div class="balance">💰 <span id="balance">1000</span></div>
    <div class="slots">
        <div class="slot" id="slot1">🍒</div>
        <div class="slot" id="slot2">🍋</div>
        <div class="slot" id="slot3">🍒</div>
    </div>
    <div class="bet-control">
        <label>Ставка:</label>
        <input type="number" id="betAmount" value="10" min="1">
    </div>
    <button class="btn-spin" id="spinBtn">🎰 КРУТИТЬ</button>
    <div id="result" class="result"></div>
    <div class="history">
        <h3>История:</h3>
        <div id="historyList"></div>
    </div>
    <button class="btn-close" id="closeBtn">✖ Закрыть</button>
</div>
<script>
const tg = window.Telegram.WebApp;
tg.expand();
let balance = 1000;
const symbols = ['🍒','🍋','🍊','🍇','💎','7️⃣'];
const slot1 = document.getElementById('slot1');
const slot2 = document.getElementById('slot2');
const slot3 = document.getElementById('slot3');
const spinBtn = document.getElementById('spinBtn');
const betInput = document.getElementById('betAmount');
const resultDiv = document.getElementById('result');
const balanceSpan = document.getElementById('balance');
const historyList = document.getElementById('historyList');

function getRandomSymbol() {
    return symbols[Math.floor(Math.random() * symbols.length)];
}

function spinSlots() {
    const slots = [slot1, slot2, slot3];
    slots.forEach(s => s.classList.add('spinning'));
    const results = slots.map(() => getRandomSymbol());
    setTimeout(() => {
        slots.forEach((s, i) => {
            s.textContent = results[i];
            s.classList.remove('spinning');
        });
        checkWin(results);
    }, 500);
}

function checkWin(results) {
    const bet = parseInt(betInput.value) || 0;
    if (bet <= 0 || bet > balance) {
        resultDiv.textContent = '❌ Неверная ставка!';
        resultDiv.className = 'result lose';
        return;
    }
    const [r1, r2, r3] = results;
    let win = 0;
    let msg = '';
    if (r1 === r2 && r2 === r3) {
        win = r1 === '💎' ? bet * 10 : r1 === '7️⃣' ? bet * 5 : bet * 3;
        msg = '🎉 ТРИ! x' + (win/bet) + '!';
    } else if (r1 === r2 || r2 === r3 || r1 === r3) {
        win = bet * 2;
        msg = '✨ ПАРА! x2!';
    } else if (r1 === '💎' || r2 === '💎' || r3 === '💎') {
        win = bet * 1.5;
        msg = '💎 БРИЛЛИАНТ! x1.5!';
    } else {
        win = 0;
        msg = '😔 Повезет в следующий раз!';
    }
    const net = win - bet;
    balance += net;
    balanceSpan.textContent = balance;
    resultDiv.textContent = msg + ' ' + (net > 0 ? '+' : '') + net + '💰';
    resultDiv.className = 'result ' + (net > 0 ? 'win' : 'lose');
    const item = document.createElement('div');
    item.className = 'history-item';
    item.innerHTML = '<span>' + results.join(' ') + '</span><span style="color:' + (net>=0?'#28a745':'#dc3545') + '">' + (net>=0?'+':'') + net + '💰</span>';
    historyList.prepend(item);
    if (historyList.children.length > 10) historyList.removeChild(historyList.lastChild);
    tg.sendData(JSON.stringify({balance, win: net, symbols: results}));
}

spinBtn.addEventListener('click', () => {
    spinBtn.disabled = true;
    const bet = parseInt(betInput.value) || 0;
    if (bet <= 0 || bet > balance) {
        resultDiv.textContent = '❌ Ошибка ставки!';
        resultDiv.className = 'result lose';
        spinBtn.disabled = false;
        return;
    }
    resultDiv.textContent = '🌀 Вращение...';
    resultDiv.className = 'result';
    spinSlots();
    setTimeout(() => spinBtn.disabled = false, 600);
});

document.getElementById('closeBtn').addEventListener('click', () => tg.close());
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML

@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎰 Играть", web_app=WebAppInfo(url=WEBAPP_URL)))
    bot.send_message(message.chat.id, "🎲 Добро пожаловать в Casino!\n\nНажмите «Играть» для старта.", reply_markup=markup)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    threading.Thread(target=lambda: bot.polling(non_stop=True), daemon=True).start()
    app.run(host='0.0.0.0', port=port)
