import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from flask import Flask, request, jsonify
import threading
import os
import json
from database import db, User, Transaction, GameHistory, init_db

# ========== КОНФИГ ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8941440753:AAGejY76StUx3ae6paRaTIqQWXr3hPqWkXs')
WEBAPP_URL = os.environ.get('WEBAPP_URL', 'https://casino-bot-mw0h.onrender.com/')
ADMIN_ID = '8663798936'  # ВАШ TELEGRAM ID

# ========== БОТ ==========
bot = telebot.TeleBot(BOT_TOKEN)

# ========== ВЕБ-СЕРВЕР ==========
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///casino.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
init_db(app)

# HTML страница казино (обновленная)
HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎰 Casino Royale</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
        
        body {
            font-family: 'Orbitron', sans-serif;
            background: linear-gradient(135deg, #0a0015 0%, #1a0030 50%, #0a0015 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px;
            overflow: hidden;
        }
        
        .container {
            background: linear-gradient(145deg, rgba(20, 0, 40, 0.95), rgba(10, 0, 20, 0.98));
            border-radius: 30px;
            padding: 25px;
            max-width: 420px;
            width: 100%;
            border: 2px solid rgba(255, 215, 0, 0.3);
            box-shadow: 0 0 60px rgba(255, 215, 0, 0.1), inset 0 0 60px rgba(255, 215, 0, 0.05);
            position: relative;
        }
        
        .container::before {
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            background: linear-gradient(45deg, #ffd700, #ff6b00, #ffd700, #ff6b00);
            background-size: 400% 400%;
            border-radius: 30px;
            z-index: -1;
            animation: gradient 3s ease infinite;
        }
        
        @keyframes gradient {
            0%{background-position:0% 50%}
            50%{background-position:100% 50%}
            100%{background-position:0% 50%}
        }
        
        h1 {
            text-align: center;
            color: #ffd700;
            font-size: 28px;
            text-shadow: 0 0 20px rgba(255, 215, 0, 0.5), 0 0 40px rgba(255, 215, 0, 0.2);
            margin-bottom: 15px;
            letter-spacing: 3px;
        }
        
        .balance {
            background: linear-gradient(145deg, rgba(255, 215, 0, 0.1), rgba(255, 215, 0, 0.05));
            padding: 12px;
            border-radius: 15px;
            text-align: center;
            font-size: 22px;
            font-weight: bold;
            color: #ffd700;
            border: 1px solid rgba(255, 215, 0, 0.2);
            margin-bottom: 20px;
            text-shadow: 0 0 10px rgba(255, 215, 0, 0.3);
        }
        
        .slots {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
            padding: 20px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 20px;
            border: 1px solid rgba(255, 215, 0, 0.1);
        }
        
        .slot {
            width: 80px;
            height: 80px;
            background: linear-gradient(145deg, #1a0030, #0a0015);
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 50px;
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.1), inset 0 0 30px rgba(255, 215, 0, 0.05);
            border: 2px solid rgba(255, 215, 0, 0.2);
            transition: all 0.3s;
        }
        
        .slot.spinning {
            animation: slotSpin 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            border-color: #ffd700;
            box-shadow: 0 0 40px rgba(255, 215, 0, 0.4);
        }
        
        @keyframes slotSpin {
            0% { transform: rotateX(0deg) scale(1); }
            25% { transform: rotateX(90deg) scale(1.2); }
            50% { transform: rotateX(180deg) scale(1); }
            75% { transform: rotateX(270deg) scale(1.2); }
            100% { transform: rotateX(360deg) scale(1); }
        }
        
        .btn-spin {
            background: linear-gradient(145deg, #ffd700, #ff8c00);
            color: #0a0015;
            border: none;
            padding: 18px;
            font-size: 22px;
            font-weight: 900;
            border-radius: 15px;
            cursor: pointer;
            width: 100%;
            margin: 15px 0;
            transition: all 0.3s;
            font-family: 'Orbitron', sans-serif;
            text-shadow: 0 0 10px rgba(255, 215, 0, 0.3);
            letter-spacing: 2px;
        }
        
        .btn-spin:hover {
            transform: scale(1.02);
            box-shadow: 0 0 40px rgba(255, 215, 0, 0.4);
        }
        
        .btn-spin:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .bet-control {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            margin: 15px 0;
            color: #ffd700;
        }
        
        .bet-control label {
            font-size: 14px;
            letter-spacing: 1px;
        }
        
        .bet-control input {
            padding: 10px 15px;
            border: 2px solid rgba(255, 215, 0, 0.3);
            border-radius: 10px;
            width: 120px;
            text-align: center;
            font-size: 16px;
            font-family: 'Orbitron', sans-serif;
            background: rgba(0, 0, 0, 0.5);
            color: #ffd700;
        }
        
        .bet-control input:focus {
            outline: none;
            border-color: #ffd700;
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.2);
        }
        
        .result {
            text-align: center;
            font-size: 20px;
            font-weight: bold;
            min-height: 40px;
            margin: 15px 0;
            padding: 10px;
            border-radius: 10px;
            background: rgba(0, 0, 0, 0.3);
        }
        
        .result.win {
            color: #00ff88;
            text-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
            animation: winPulse 0.5s ease;
        }
        
        .result.lose {
            color: #ff4444;
            text-shadow: 0 0 20px rgba(255, 68, 68, 0.5);
        }
        
        .result.bigwin {
            color: #ffd700;
            text-shadow: 0 0 30px rgba(255, 215, 0, 0.8);
            animation: bigWin 1s ease;
        }
        
        @keyframes winPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        
        @keyframes bigWin {
            0% { transform: scale(1); }
            25% { transform: scale(1.2) rotate(-5deg); }
            50% { transform: scale(1.2) rotate(5deg); }
            75% { transform: scale(1.2) rotate(-5deg); }
            100% { transform: scale(1); }
        }
        
        .history {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid rgba(255, 215, 0, 0.1);
        }
        
        .history h3 {
            color: #ffd700;
            font-size: 14px;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }
        
        #historyList {
            max-height: 150px;
            overflow-y: auto;
        }
        
        .history-item {
            padding: 8px 12px;
            margin: 5px 0;
            background: rgba(255, 215, 0, 0.05);
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            color: #aaa;
            font-size: 13px;
            border-left: 3px solid rgba(255, 215, 0, 0.2);
        }
        
        .history-item.win {
            border-left-color: #00ff88;
        }
        
        .history-item.lose {
            border-left-color: #ff4444;
        }
        
        .btn-close {
            width: 100%;
            padding: 12px;
            background: linear-gradient(145deg, #ff4444, #cc0000);
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 15px;
            transition: all 0.3s;
            font-family: 'Orbitron', sans-serif;
        }
        
        .btn-close:hover {
            transform: scale(1.02);
            box-shadow: 0 0 30px rgba(255, 68, 68, 0.3);
        }
        
        .footer {
            text-align: center;
            margin-top: 10px;
            font-size: 10px;
            color: rgba(255, 215, 0, 0.3);
            letter-spacing: 1px;
        }
        
        .emoji-big {
            font-size: 60px;
        }
        
        ::-webkit-scrollbar {
            width: 4px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255, 215, 0, 0.05);
        }
        
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 215, 0, 0.3);
            border-radius: 2px;
        }
    </style>
</head>
<body>
<div class="container">
    <h1>🎰 CASINO</h1>
    <div class="balance">💰 <span id="balance">1000</span></div>
    <div class="slots">
        <div class="slot" id="slot1">🍒</div>
        <div class="slot" id="slot2">🍋</div>
        <div class="slot" id="slot3">🍒</div>
    </div>
    <div class="bet-control">
        <label>СТАВКА:</label>
        <input type="number" id="betAmount" value="10" min="1">
    </div>
    <button class="btn-spin" id="spinBtn">🎰 SPIN</button>
    <div id="result" class="result">Нажми SPIN!</div>
    <div class="history">
        <h3>📜 ИСТОРИЯ</h3>
        <div id="historyList"></div>
    </div>
    <button class="btn-close" id="closeBtn">✖ ЗАКРЫТЬ</button>
    <div class="footer">18+ | ИГРАЙ ОТВЕТСТВЕННО</div>
</div>
<script>
const tg = window.Telegram.WebApp;
tg.expand();

let balance = 1000;
const symbols = ['🍒','🍋','🍊','🍇','💎','7️⃣','⭐'];
const slot1 = document.getElementById('slot1');
const slot2 = document.getElementById('slot2');
const slot3 = document.getElementById('slot3');
const spinBtn = document.getElementById('spinBtn');
const betInput = document.getElementById('betAmount');
const resultDiv = document.getElementById('result');
const balanceSpan = document.getElementById('balance');
const historyList = document.getElementById('historyList');

// Получаем начальный баланс от бота
fetch('/get_balance')
    .then(res => res.json())
    .then(data => {
        if (data.balance !== undefined) {
            balance = data.balance;
            balanceSpan.textContent = balance;
        }
    });

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
    }, 600);
}

function checkWin(results) {
    const bet = parseInt(betInput.value) || 0;
    if (bet <= 0 || bet > balance) {
        resultDiv.textContent = '❌ НЕВЕРНАЯ СТАВКА!';
        resultDiv.className = 'result lose';
        return;
    }
    
    const [r1, r2, r3] = results;
    let win = 0;
    let msg = '';
    let className = 'lose';
    
    if (r1 === r2 && r2 === r3) {
        if (r1 === '💎') {
            win = bet * 15;
            msg = '💎💎💎 ДЖЕКПОТ! x15!';
            className = 'bigwin';
        } else if (r1 === '7️⃣') {
            win = bet * 10;
            msg = '7️⃣7️⃣7️⃣ СЧАСТЛИВЧИК! x10!';
            className = 'bigwin';
        } else if (r1 === '⭐') {
            win = bet * 20;
            msg = '⭐⭐⭐ СУПЕР ДЖЕКПОТ! x20!';
            className = 'bigwin';
        } else {
            win = bet * 5;
            msg = `🎉 ТРИ ${r1}! x5!`;
            className = 'win';
        }
    } else if (r1 === r2 || r2 === r3 || r1 === r3) {
        win = bet * 2;
        msg = '✨ ПАРА! x2!';
        className = 'win';
    } else if (r1 === '💎' || r2 === '💎' || r3 === '💎') {
        win = bet * 1.5;
        msg = '💎 БРИЛЛИАНТ! x1.5!';
        className = 'win';
    } else if (r1 === '⭐' || r2 === '⭐' || r3 === '⭐') {
        win = bet * 3;
        msg = '⭐ ЗВЕЗДА! x3!';
        className = 'win';
    } else {
        win = 0;
        msg = '😔 ПОВЕЗЕТ В СЛЕДУЮЩИЙ РАЗ!';
        className = 'lose';
    }
    
    const net = win - bet;
    balance += net;
    balanceSpan.textContent = balance;
    resultDiv.textContent = `${msg} ${net > 0 ? '+' : ''}${net}💰`;
    resultDiv.className = `result ${className}`;
    
    // История
    const item = document.createElement('div');
    item.className = `history-item ${net >= 0 ? 'win' : 'lose'}`;
    const sign = net >= 0 ? '+' : '';
    item.innerHTML = `<span>${results.join(' ')}</span><span>${sign}${net}💰</span>`;
    historyList.prepend(item);
    if (historyList.children.length > 10) historyList.removeChild(historyList.lastChild);
    
    // Отправка данных в бот
    fetch('/game_result', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            bet: bet,
            win: net,
            symbols: results.join(''),
            balance: balance
        })
    });
}

spinBtn.addEventListener('click', () => {
    spinBtn.disabled = true;
    const bet = parseInt(betInput.value) || 0;
    if (bet <= 0 || bet > balance) {
        resultDiv.textContent = '❌ ОШИБКА СТАВКИ!';
        resultDiv.className = 'result lose';
        spinBtn.disabled = false;
        return;
    }
    resultDiv.textContent = '🌀 SPIN...';
    resultDiv.className = 'result';
    spinSlots();
    setTimeout(() => spinBtn.disabled = false, 700);
});

document.getElementById('closeBtn').addEventListener('click', () => tg.close());

// Обновление баланса при открытии
setInterval(() => {
    fetch('/get_balance')
        .then(res => res.json())
        .then(data => {
            if (data.balance !== undefined) {
                balance = data.balance;
                balanceSpan.textContent = balance;
            }
        });
}, 5000);
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML

@app.route('/get_balance')
def get_balance():
    from flask import request
    user_id = request.args.get('user_id')
    if user_id:
        user = User.query.filter_by(telegram_id=user_id).first()
        if user:
            return jsonify({'balance': user.balance})
    return jsonify({'balance': 1000})

@app.route('/game_result', methods=['POST'])
def game_result():
    data = request.json
    user_id = data.get('user_id')
    bet = data.get('bet')
    win = data.get('win')
    symbols = data.get('symbols')
    
    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        if user:
            user.balance += win
            user.games_played += 1
            if win > 0:
                user.total_won += win
            else:
                user.total_lost += abs(win)
            db.session.commit()
            
            # Сохраняем историю
            history = GameHistory(
                user_id=user.id,
                bet=bet,
                win=win,
                symbols=symbols
            )
            db.session.add(history)
            db.session.commit()
    
    return jsonify({'status': 'ok'})

# ========== КОМАНДЫ БОТА ==========

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    
    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        if not user:
            user = User(
                telegram_id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            db.session.add(user)
            db.session.commit()
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🎰 Играть", web_app=WebAppInfo(url=f"{WEBAPP_URL}?user_id={user_id}")))
    markup.row(
        InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        InlineKeyboardButton("📊 Статистика", callback_data="stats")
    )
    if user.is_admin:
        markup.row(InlineKeyboardButton("👑 Админ-панель", callback_data="admin"))
    
    bot.send_message(
        message.chat.id,
        f"🎲 Добро пожаловать в Casino Royale, {message.from_user.first_name}!\n\n"
        f"💰 Ваш баланс: {user.balance}\n"
        f"🎮 Игр сыграно: {user.games_played}\n\n"
        "Нажми «Играть» чтобы начать!",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = str(call.from_user.id)
    
    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        if not user:
            bot.answer_callback_query(call.id, "Ошибка! Напишите /start")
            return
        
        if call.data == "balance":
            bot.answer_callback_query(
                call.id,
                f"💰 Ваш баланс: {user.balance}\n"
                f"🏆 Всего выиграно: {user.total_won}\n"
                f"💔 Всего проиграно: {user.total_lost}\n"
                f"🎮 Игр: {user.games_played}",
                show_alert=True
            )
        
        elif call.data == "stats":
            bot.answer_callback_query(
                call.id,
                f"📊 Статистика:\n"
                f"🎮 Игр: {user.games_played}\n"
                f"🏆 Выигрышей: {user.total_won}\n"
                f"💔 Проигрышей: {user.total_lost}\n"
                f"💰 Баланс: {user.balance}",
                show_alert=True
            )
        
        elif call.data == "admin" and user.is_admin:
            show_admin_panel(call.message, user)
        
        elif call.data.startswith("admin_"):
            handle_admin_action(call, user)

def show_admin_panel(message, admin):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("➕ Выдать валюту", callback_data="admin_give"),
        InlineKeyboardButton("➖ Забрать валюту", callback_data="admin_take")
    )
    markup.row(
        InlineKeyboardButton("👤 Информация о пользователе", callback_data="admin_info"),
        InlineKeyboardButton("📊 Топ игроков", callback_data="admin_top")
    )
    markup.row(
        InlineKeyboardButton("📋 История транзакций", callback_data="admin_history"),
        InlineKeyboardButton("🔙 Назад", callback_data="back")
    )
    
    bot.send_message(
        message.chat.id,
        "👑 **Админ-панель**\n\n"
        "Выберите действие:",
        reply_markup=markup,
        parse_mode='Markdown'
    )

def handle_admin_action(call, admin):
    # Простая обработка админских команд
    if call.data == "admin_give":
        bot.send_message(call.message.chat.id, "Введите ID пользователя и сумму через пробел:\n`123456789 100`", parse_mode='Markdown')
        bot.register_next_step_handler(call.message, admin_give_currency, admin)
    
    elif call.data == "admin_take":
        bot.send_message(call.message.chat.id, "Введите ID пользователя и сумму через пробел:\n`123456789 50`", parse_mode='Markdown')
        bot.register_next_step_handler(call.message, admin_take_currency, admin)
    
    elif call.data == "admin_info":
        bot.send_message(call.message.chat.id, "Введите ID пользователя:")
        bot.register_next_step_handler(call.message, admin_get_user_info)
    
    elif call.data == "admin_top":
        show_top_players(call.message)
    
    elif call.data == "back":
        start(call.message)

def admin_give_currency(message, admin):
    try:
        parts = message.text.split()
        user_id = parts[0]
        amount = int(parts[1])
        
        with app.app_context():
            user = User.query.filter_by(telegram_id=user_id).first()
            if user:
                user.balance += amount
                transaction = Transaction(
                    user_id=user.id,
                    amount=amount,
                    type='admin',
                    description=f'Выдано админом {amount}'
                )
                db.session.add(transaction)
                db.session.commit()
                bot.send_message(message.chat.id, f"✅ Выдано {amount} пользователю {user.first_name}")
            else:
                bot.send_message(message.chat.id, "❌ Пользователь не найден")
    except:
        bot.send_message(message.chat.id, "❌ Ошибка! Формат: `ID СУММА`", parse_mode='Markdown')

def admin_take_currency(message, admin):
    try:
        parts = message.text.split()
        user_id = parts[0]
        amount = int(parts[1])
        
        with app.app_context():
            user = User.query.filter_by(telegram_id=user_id).first()
            if user:
                if user.balance >= amount:
                    user.balance -= amount
                    transaction = Transaction(
                        user_id=user.id,
                        amount=-amount,
                        type='admin',
                        description=f'Забрано админом {amount}'
                    )
                    db.session.add(transaction)
                    db.session.commit()
                    bot.send_message(message.chat.id, f"✅ Забрано {amount} у пользователя {user.first_name}")
                else:
                    bot.send_message(message.chat.id, "❌ Недостаточно средств")
            else:
                bot.send_message(message.chat.id, "❌ Пользователь не найден")
    except:
        bot.send_message(message.chat.id, "❌ Ошибка! Формат: `ID СУММА`", parse_mode='Markdown')

def admin_get_user_info(message):
    try:
        user_id = message.text.strip()
        with app.app_context():
            user = User.query.filter_by(telegram_id=user_id).first()
            if user:
                bot.send_message(
                    message.chat.id,
                    f"👤 **Информация о пользователе**\n\n"
                    f"ID: `{user.telegram_id}`\n"
                    f"Имя: {user.first_name}\n"
                    f"Юзернейм: @{user.username or 'Нет'}\n"
                    f"💰 Баланс: {user.balance}\n"
                    f"🎮 Игр: {user.games_played}\n"
                    f"🏆 Выиграно: {user.total_won}\n"
                    f"💔 Проиграно: {user.total_lost}",
                    parse_mode='Markdown'
                )
            else:
                bot.send_message(message.chat.id, "❌ Пользователь не найден")
    except:
        bot.send_message(message.chat.id, "❌ Ошибка!")

def show_top_players(message):
    with app.app_context():
        top = User.query.order_by(User.balance.desc()).limit(10).all()
        text = "🏆 **Топ игроков**\n\n"
        for i, user in enumerate(top, 1):
            text += f"{i}. {user.first_name} — {user.balance}💰\n"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['balance'])
def balance_command(message):
    user_id = str(message.from_user.id)
    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        if user:
            bot.send_message(
                message.chat.id,
                f"💰 Ваш баланс: {user.balance}\n"
                f"🏆 Всего выиграно: {user.total_won}\n"
                f"💔 Всего проиграно: {user.total_lost}\n"
                f"🎮 Игр сыграно: {user.games_played}"
            )

@bot.message_handler(commands=['admin'])
def admin_command(message):
    user_id = str(message.from_user.id)
    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        if user and user.is_admin:
            show_admin_panel(message, user)
        else:
            bot.send_message(message.chat.id, "❌ У вас нет прав администратора!")

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    # Запускаем бота в отдельном потоке
    def run_bot():
        bot.polling(non_stop=True)
    
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Запускаем Flask
    app.run(host='0.0.0.0', port=port)import telebot
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
