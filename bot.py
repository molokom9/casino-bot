import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import threading
import os
import json
import random

# ========== КОНФИГ ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8941440753:AAGejY76StUx3ae6paRaTIqQWXr3hPqWkXs')
WEBAPP_URL = os.environ.get('WEBAPP_URL', 'https://casino-bot-mw0h.onrender.com/')
ADMIN_ID = '8663798936'
REFILL_LINK = 'https://t.me/Qwile_Games'

# ========== БАЗА ДАННЫХ ==========
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///casino.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    balance = db.Column(db.Integer, default=25)
    total_won = db.Column(db.Integer, default=0)
    total_lost = db.Column(db.Integer, default=0)
    games_played = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    amount = db.Column(db.Integer)
    type = db.Column(db.String(50))
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GameHistory(db.Model):
    __tablename__ = 'game_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    bet = db.Column(db.Integer)
    win = db.Column(db.Integer)
    symbols = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ========== СОЗДАНИЕ ТАБЛИЦ ==========
with app.app_context():
    db.create_all()
    admin = User.query.filter_by(telegram_id=ADMIN_ID).first()
    if not admin:
        admin = User(
            telegram_id=ADMIN_ID,
            username='admin',
            first_name='Admin',
            is_admin=True,
            balance=1000
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Админ создан!")

# ========== БОТ ==========
bot = telebot.TeleBot(BOT_TOKEN)

# ========== HTML (без изменений) ==========
HTML = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CASINO ROYALE</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0f;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 16px;
        }
        
        .container {
            background: #12121a;
            border-radius: 24px;
            padding: 24px 20px 20px;
            max-width: 400px;
            width: 100%;
            border: 1px solid #2a2a3a;
            box-shadow: 0 20px 60px rgba(0,0,0,0.8);
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .logo {
            font-size: 22px;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: 1px;
        }
        
        .logo span {
            color: #ffd700;
        }
        
        .status {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            color: #4a4a5a;
            letter-spacing: 1px;
        }
        
        .status-dot {
            width: 6px;
            height: 6px;
            background: #00ff88;
            border-radius: 50%;
            animation: blink 1.5s infinite;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        
        .balance-card {
            background: #1a1a26;
            border: 1px solid #2a2a3a;
            border-radius: 14px;
            padding: 14px 18px;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .balance-label {
            color: #6a6a7a;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        
        .balance-value {
            font-size: 26px;
            font-weight: 700;
            color: #ffd700;
        }
        
        .balance-value small {
            font-size: 14px;
            color: #6a6a7a;
        }
        
        .btn-refill {
            display: block;
            width: 100%;
            padding: 10px;
            background: linear-gradient(135deg, #00d4ff, #0088cc);
            color: #ffffff;
            border: none;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 16px;
            text-align: center;
            text-decoration: none;
            transition: all 0.3s;
            letter-spacing: 0.5px;
        }
        
        .btn-refill:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 30px rgba(0, 212, 255, 0.2);
        }
        
        .slots-container {
            background: #0d0d15;
            border-radius: 16px;
            padding: 24px 16px;
            margin-bottom: 16px;
            border: 1px solid #1a1a2a;
        }
        
        .slots {
            display: flex;
            justify-content: center;
            gap: 12px;
        }
        
        .slot-wrapper {
            background: #0a0a10;
            border-radius: 12px;
            padding: 8px;
            border: 1px solid #1a1a2a;
            flex: 1;
            max-width: 90px;
        }
        
        .slot {
            width: 100%;
            aspect-ratio: 1;
            background: #0d0d15;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 42px;
            transition: all 0.3s ease;
            user-select: none;
        }
        
        .slot.spinning {
            animation: slotSpin 1.2s cubic-bezier(0.1, 0.8, 0.2, 1);
        }
        
        @keyframes slotSpin {
            0% { transform: rotateX(0) scale(1); }
            15% { transform: rotateX(180deg) scale(1.1); }
            30% { transform: rotateX(360deg) scale(1); }
            50% { transform: rotateX(540deg) scale(1.1); }
            70% { transform: rotateX(720deg) scale(1); }
            85% { transform: rotateX(810deg) scale(1.02); }
            100% { transform: rotateX(900deg) scale(1); }
        }
        
        .slot.win {
            border-color: #ffd700;
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.1);
        }
        
        .controls {
            margin-bottom: 16px;
        }
        
        .bet-control {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            background: #1a1a26;
            border-radius: 12px;
            padding: 8px 14px;
            border: 1px solid #2a2a3a;
        }
        
        .bet-control label {
            color: #6a6a7a;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .bet-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .bet-btn {
            background: #2a2a3a;
            border: none;
            color: #ffffff;
            width: 32px;
            height: 32px;
            border-radius: 8px;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .bet-btn:hover {
            background: #3a3a4a;
        }
        
        .bet-btn:active {
            transform: scale(0.95);
        }
        
        .bet-input {
            background: #0d0d15;
            border: 1px solid #2a2a3a;
            border-radius: 8px;
            color: #ffffff;
            font-size: 18px;
            font-weight: 600;
            text-align: center;
            width: 70px;
            padding: 6px;
            outline: none;
        }
        
        .bet-input:focus {
            border-color: #ffd700;
        }
        
        .bet-input::-webkit-inner-spin-button,
        .bet-input::-webkit-outer-spin-button {
            -webkit-appearance: none;
        }
        .bet-input[type=number] {
            -moz-appearance: textfield;
        }
        
        .btn-spin {
            background: linear-gradient(135deg, #ffd700, #f7a81e);
            color: #0a0a10;
            border: none;
            padding: 16px;
            font-size: 18px;
            font-weight: 700;
            border-radius: 12px;
            cursor: pointer;
            width: 100%;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-top: 12px;
        }
        
        .btn-spin:hover:not(:disabled) {
            transform: scale(1.02);
            box-shadow: 0 4px 30px rgba(255, 215, 0, 0.2);
        }
        
        .btn-spin:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-spin:active:not(:disabled) {
            transform: scale(0.97);
        }
        
        .result {
            text-align: center;
            font-size: 18px;
            font-weight: 700;
            min-height: 50px;
            padding: 12px;
            border-radius: 10px;
            margin-top: 14px;
            background: #0d0d15;
            border: 1px solid #1a1a2a;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            color: #ffffff;
        }
        
        .result.win {
            color: #00ff88;
            border-color: rgba(0, 255, 136, 0.2);
        }
        
        .result.lose {
            color: #ff4466;
            border-color: rgba(255, 68, 102, 0.2);
        }
        
        .result.bigwin {
            color: #ffd700;
            border-color: rgba(255, 215, 0, 0.3);
        }
        
        .btn-close {
            width: 100%;
            padding: 12px;
            background: #1a1a26;
            color: #4a4a5a;
            border: 1px solid #2a2a3a;
            border-radius: 12px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 16px;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .btn-close:hover {
            background: #2a2a3a;
            color: #8a8a9a;
        }
        
        .btn-close:active {
            transform: scale(0.97);
        }
        
        .footer {
            text-align: center;
            margin-top: 12px;
            font-size: 9px;
            color: #2a2a3a;
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        
        @media (max-width: 380px) {
            .slot {
                font-size: 32px;
            }
            .slot-wrapper {
                max-width: 70px;
            }
            .balance-value {
                font-size: 22px;
            }
        }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="logo">CASINO <span>ROYALE</span></div>
        <div class="status"><span class="status-dot"></span> LIVE</div>
    </div>
    
    <div class="balance-card">
        <span class="balance-label">💰 Баланс</span>
        <span class="balance-value" id="balance">25 <small>₴</small></span>
    </div>
    
    <a href="https://t.me/Qwile_Games" class="btn-refill" target="_blank">💳 ПОПОЛНИТЬ</a>
    
    <div class="slots-container">
        <div class="slots">
            <div class="slot-wrapper"><div class="slot" id="slot1">🍒</div></div>
            <div class="slot-wrapper"><div class="slot" id="slot2">🍋</div></div>
            <div class="slot-wrapper"><div class="slot" id="slot3">🍇</div></div>
        </div>
    </div>
    
    <div class="controls">
        <div class="bet-control">
            <label>Ставка</label>
            <div class="bet-actions">
                <button class="bet-btn" id="betMinus">−</button>
                <input type="number" class="bet-input" id="betAmount" value="25" min="25" step="25">
                <button class="bet-btn" id="betPlus">+</button>
            </div>
        </div>
        <button class="btn-spin" id="spinBtn">🎰 SPIN</button>
    </div>
    
    <div id="result" class="result">Нажми SPIN</div>
    
    <button class="btn-close" id="closeBtn">✖ Закрыть</button>
    <div class="footer">18+ · Играй ответственно</div>
</div>

<script>
const tg = window.Telegram.WebApp;
tg.expand();

let balance = 25;
let isSpinning = false;

const symbols = ['🍒', '🍋', '🍊', '🍇', '💎', '7️⃣', '⭐', '🍉'];

const s1 = document.getElementById('slot1');
const s2 = document.getElementById('slot2');
const s3 = document.getElementById('slot3');
const spinBtn = document.getElementById('spinBtn');
const betInput = document.getElementById('betAmount');
const betMinus = document.getElementById('betMinus');
const betPlus = document.getElementById('betPlus');
const resultDiv = document.getElementById('result');
const balanceSpan = document.getElementById('balance');

function getUserId() {
    const p = new URLSearchParams(window.location.search);
    return p.get('user_id') || '';
}

function updateBalance(b) {
    balance = b;
    balanceSpan.textContent = balance + ' ₴';
}

function spinSlots() {
    if (isSpinning) return;
    
    const bet = parseInt(betInput.value) || 25;
    if (bet < 25 || bet > balance) {
        resultDiv.textContent = '❌ Минимальная ставка 25 ₴';
        resultDiv.className = 'result lose';
        return;
    }
    
    isSpinning = true;
    spinBtn.disabled = true;
    resultDiv.textContent = '🌀 Вращение...';
    resultDiv.className = 'result';
    
    const slots = [s1, s2, s3];
    
    let delay = 0;
    const results = [];
    const finalResults = slots.map(() => symbols[Math.floor(Math.random() * symbols.length)]);
    
    slots.forEach((slot, index) => {
        setTimeout(() => {
            slot.classList.add('spinning');
            
            let interval = setInterval(() => {
                if (slot.classList.contains('spinning')) {
                    slot.textContent = symbols[Math.floor(Math.random() * symbols.length)];
                }
            }, 80);
            
            setTimeout(() => {
                clearInterval(interval);
                slot.textContent = finalResults[index];
                slot.classList.remove('spinning');
                results[index] = finalResults[index];
                
                if (results.length === 3 && results.every(r => r !== undefined)) {
                    setTimeout(() => {
                        checkWin(finalResults);
                        isSpinning = false;
                        spinBtn.disabled = false;
                    }, 300);
                }
            }, 1200);
        }, delay);
        delay += 350;
    });
}

function checkWin(results) {
    const bet = parseInt(betInput.value) || 25;
    const [r1, r2, r3] = results;
    
    let win = 0;
    let msg = '';
    let className = 'lose';
    let isBigWin = false;
    
    const winChance = Math.random();
    
    if (winChance > 0.10) {
        win = 0;
        msg = '😔 Повезет в следующий раз';
        className = 'lose';
    }
    else if (r1 === r2 && r2 === r3) {
        if (Math.random() < 0.05) {
            if (r1 === '💎') {
                win = bet * 10;
                msg = '💎💎💎 ДЖЕКПОТ! x10!';
                className = 'bigwin';
                isBigWin = true;
            } else if (r1 === '7️⃣') {
                win = bet * 8;
                msg = '7️⃣7️⃣7️⃣ СЧАСТЛИВЧИК! x8!';
                className = 'bigwin';
                isBigWin = true;
            } else if (r1 === '⭐') {
                win = bet * 12;
                msg = '⭐⭐⭐ СУПЕР! x12!';
                className = 'bigwin';
                isBigWin = true;
            } else {
                win = bet * 4;
                msg = '🎉 ТРИ ' + r1 + '! x4!';
                className = 'win';
            }
        } else {
            win = 0;
            msg = '😔 Почти получилось!';
            className = 'lose';
        }
    }
    else if (r1 === r2 || r2 === r3 || r1 === r3) {
        if (Math.random() < 0.2) {
            win = bet * 1.5;
            msg = '✨ ПАРА! x1.5!';
            className = 'win';
        } else {
            win = 0;
            msg = '😔 Почти получилось!';
            className = 'lose';
        }
    }
    else if (r1 === '💎' || r2 === '💎' || r3 === '💎') {
        if (Math.random() < 0.1) {
            win = bet * 1.5;
            msg = '💎 БРИЛЛИАНТ! x1.5!';
            className = 'win';
        } else {
            win = 0;
            msg = '😔 Повезет в следующий раз';
            className = 'lose';
        }
    }
    else {
        win = 0;
        msg = '😔 Повезет в следующий раз';
        className = 'lose';
    }
    
    win = Math.floor(win);
    const net = win - bet;
    balance += net;
    updateBalance(balance);
    
    if (net > 0) {
        const slots = [s1, s2, s3];
        slots.forEach(s => s.classList.add('win'));
        setTimeout(() => {
            slots.forEach(s => s.classList.remove('win'));
        }, 800);
    }
    
    resultDiv.textContent = msg + ' ' + (net > 0 ? '+' : '') + net + ' ₴';
    resultDiv.className = 'result ' + className;
    
    const userId = getUserId();
    if (userId) {
        fetch('/game_result', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                bet: bet,
                win: net,
                symbols: results.join('')
            })
        });
    }
}

function loadBalance() {
    const userId = getUserId();
    if (userId) {
        fetch('/get_balance?user_id=' + userId)
            .then(r => r.json())
            .then(data => {
                if (data.balance !== undefined) {
                    updateBalance(data.balance);
                }
            })
            .catch(() => {});
    }
}

setInterval(loadBalance, 10000);

spinBtn.addEventListener('click', spinSlots);

betMinus.addEventListener('click', () => {
    let val = parseInt(betInput.value) || 25;
    val = Math.max(val - 25, 25);
    betInput.value = val;
});

betPlus.addEventListener('click', () => {
    let val = parseInt(betInput.value) || 25;
    val = Math.min(val + 25, balance);
    betInput.value = val;
});

betInput.addEventListener('change', () => {
    let val = parseInt(betInput.value) || 25;
    if (val < 25) val = 25;
    if (val % 25 !== 0) val = Math.round(val / 25) * 25;
    if (val > balance) val = balance;
    betInput.value = val;
});

document.getElementById('closeBtn').addEventListener('click', () => tg.close());

loadBalance();
</script>
</body>
</html>'''

# ========== МАРШРУТЫ ==========
@app.route('/')
def index():
    return HTML

@app.route('/get_balance')
def get_balance():
    user_id = request.args.get('user_id')
    if user_id:
        user = User.query.filter_by(telegram_id=user_id).first()
        if user:
            return jsonify({'balance': user.balance})
    return jsonify({'balance': 25})

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
    markup.row(
        InlineKeyboardButton("🎰 Играть", web_app=WebAppInfo(url=f"{WEBAPP_URL}?user_id={user_id}")),
        InlineKeyboardButton("💳 Пополнить", url=REFILL_LINK)
    )
    if user.is_admin:
        markup.row(InlineKeyboardButton("👑 Админ-панель", callback_data="admin"))
    
    bot.send_message(
        message.chat.id,
        f"🎲 Добро пожаловать в Casino Royale, {message.from_user.first_name}!",
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
        
        if call.data == "admin" and user.is_admin:
            show_admin_panel(call.message, user)

def show_admin_panel(message, admin):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📋 Список пользователей", callback_data="admin_users"),
        InlineKeyboardButton("🔍 Найти пользователя", callback_data="admin_find")
    )
    markup.row(
        InlineKeyboardButton("🔙 Назад", callback_data="back")
    )
    
    bot.send_message(
        message.chat.id,
        "👑 **Админ-панель**\n\nВыберите действие:",
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_") or call.data == "back")
def admin_callback(call):
    user_id = str(call.from_user.id)
    
    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        if not user or not user.is_admin:
            bot.answer_callback_query(call.id, "Нет прав!")
            return
        
        if call.data == "admin_users":
            show_users_list(call.message, 0)
        
        elif call.data.startswith("admin_page_"):
            page = int(call.data.split("_")[2])
            show_users_list(call.message, page)
        
        elif call.data == "admin_find":
            bot.send_message(call.message.chat.id, "Введите ID пользователя или username (с @):")
            bot.register_next_step_handler(call.message, admin_find_user)
        
        elif call.data.startswith("admin_action_"):
            parts = call.data.split("_")
            target_id = parts[2]
            action = parts[3]
            handle_user_action(call.message, target_id, action)
        
        elif call.data == "back":
            start(call.message)

def show_users_list(message, page=0):
    try:
        with app.app_context():
            total_users = User.query.count()
            if total_users == 0:
                bot.send_message(message.chat.id, "📋 **Список пользователей пуст**\n\nПока нет зарегистрированных пользователей.", parse_mode='Markdown')
                return
            
            users = User.query.order_by(User.balance.desc()).offset(page * 5).limit(5).all()
            total_pages = (total_users - 1) // 5 + 1
            
            text = f"👥 **Список пользователей (стр. {page+1}/{total_pages})**\n\n"
            for i, u in enumerate(users, start=page*5+1):
                text += f"{i}. {u.first_name} (@{u.username or 'нет'})\n"
                text += f"   ID: `{u.telegram_id}` | Баланс: {u.balance} ₴\n\n"
            
            markup = InlineKeyboardMarkup()
            row = []
            if page > 0:
                row.append(InlineKeyboardButton("◀️ Назад", callback_data=f"admin_page_{page-1}"))
            if (page + 1) * 5 < total_users:
                row.append(InlineKeyboardButton("Вперед ▶️", callback_data=f"admin_page_{page+1}"))
            if row:
                markup.row(*row)
            markup.row(InlineKeyboardButton("🔄 Обновить", callback_data=f"admin_page_{page}"))
            markup.row(InlineKeyboardButton("🔙 Назад", callback_data="back"))
            
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при загрузке списка: {str(e)}")

def admin_find_user(message):
    try:
        query = message.text.strip()
        if not query:
            bot.send_message(message.chat.id, "❌ Введите ID или username!")
            return
        
        with app.app_context():
            if query.startswith('@'):
                username = query[1:]
                user = User.query.filter_by(username=username).first()
            else:
                user = User.query.filter_by(telegram_id=query).first()
            
            if user:
                markup = InlineKeyboardMarkup()
                markup.row(
                    InlineKeyboardButton("➕ Выдать", callback_data=f"admin_action_{user.telegram_id}_give"),
                    InlineKeyboardButton("➖ Забрать", callback_data=f"admin_action_{user.telegram_id}_take")
                )
                markup.row(
                    InlineKeyboardButton("🗑 Удалить", callback_data=f"admin_action_{user.telegram_id}_delete"),
                    InlineKeyboardButton("👑 Сделать админом", callback_data=f"admin_action_{user.telegram_id}_makeadmin")
                )
                markup.row(InlineKeyboardButton("🔙 Назад", callback_data="back"))
                
                bot.send_message(
                    message.chat.id,
                    f"👤 **Найден пользователь**\n\n"
                    f"ID: `{user.telegram_id}`\n"
                    f"Имя: {user.first_name}\n"
                    f"Юзернейм: @{user.username or 'нет'}\n"
                    f"💰 Баланс: {user.balance} ₴\n"
                    f"🎮 Игр: {user.games_played}\n"
                    f"🏆 Выиграно: {user.total_won} ₴\n"
                    f"💔 Проиграно: {user.total_lost} ₴\n"
                    f"👑 Админ: {'Да' if user.is_admin else 'Нет'}",
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
            else:
                bot.send_message(message.chat.id, "❌ Пользователь не найден. Проверьте ID или username.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

def handle_user_action(message, target_id, action):
    try:
        with app.app_context():
            user = User.query.filter_by(telegram_id=target_id).first()
            if not user:
                bot.send_message(message.chat.id, "❌ Пользователь не найден")
                return
            
            if action == "give":
                bot.send_message(message.chat.id, f"Введите сумму для выдачи пользователю {user.first_name} (кратно 25):")
                bot.register_next_step_handler(message, lambda m: admin_give_currency(m, target_id))
            
            elif action == "take":
                bot.send_message(message.chat.id, f"Введите сумму для забора у пользователя {user.first_name} (кратно 25):")
                bot.register_next_step_handler(message, lambda m: admin_take_currency(m, target_id))
            
            elif action == "delete":
                db.session.delete(user)
                db.session.commit()
                bot.send_message(message.chat.id, f"✅ Пользователь {user.first_name} удалён!")
            
            elif action == "makeadmin":
                user.is_admin = True
                db.session.commit()
                bot.send_message(message.chat.id, f"✅ Пользователь {user.first_name} теперь администратор!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

def admin_give_currency(message, target_id):
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма должна быть больше 0")
            return
        if amount % 25 != 0:
            bot.send_message(message.chat.id, "❌ Сумма должна быть кратна 25")
            return
        
        with app.app_context():
            user = User.query.filter_by(telegram_id=target_id).first()
            if user:
                user.balance += amount
                db.session.commit()
                bot.send_message(message.chat.id, f"✅ Выдано {amount} ₴ пользователю {user.first_name}")
            else:
                bot.send_message(message.chat.id, "❌ Пользователь не найден")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите число!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

def admin_take_currency(message, target_id):
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма должна быть больше 0")
            return
        if amount % 25 != 0:
            bot.send_message(message.chat.id, "❌ Сумма должна быть кратна 25")
            return
        
        with app.app_context():
            user = User.query.filter_by(telegram_id=target_id).first()
            if user:
                if user.balance >= amount:
                    user.balance -= amount
                    db.session.commit()
                    bot.send_message(message.chat.id, f"✅ Забрано {amount} ₴ у {user.first_name}")
                else:
                    bot.send_message(message.chat.id, "❌ Недостаточно средств")
            else:
                bot.send_message(message.chat.id, "❌ Пользователь не найден")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите число!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['balance'])
def balance_command(message):
    user_id = str(message.from_user.id)
    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        if user:
            bot.send_message(
                message.chat.id,
                f"💰 Баланс: {user.balance} ₴\n"
                f"🏆 Выиграно: {user.total_won} ₴\n"
                f"💔 Проиграно: {user.total_lost} ₴\n"
                f"🎮 Игр: {user.games_played}"
            )
        else:
            bot.send_message(message.chat.id, "❌ Пользователь не найден. Напишите /start")

@bot.message_handler(commands=['admin'])
def admin_command(message):
    user_id = str(message.from_user.id)
    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        if user and user.is_admin:
            show_admin_panel(message, user)
        else:
            bot.send_message(message.chat.id, "❌ Нет прав!")

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    threading.Thread(target=lambda: bot.polling(non_stop=True), daemon=True).start()
    app.run(host='0.0.0.0', port=port)
