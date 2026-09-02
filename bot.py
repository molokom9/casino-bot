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
    balance = db.Column(db.Integer, default=1000)
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
            balance=10000
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Админ создан!")

# ========== БОТ ==========
bot = telebot.TeleBot(BOT_TOKEN)

# ========== HTML ==========
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
            margin-bottom: 20px;
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
        
        .slots-container {
            background: #0d0d15;
            border-radius: 16px;
            padding: 24px 16px;
            margin-bottom: 20px;
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
            animation: slotSpin 2.5s cubic-bezier(0.1, 0.8, 0.2, 1);
        }
        
        @keyframes slotSpin {
            0% { transform: rotateX(0) scale(1); }
            10% { transform: rotateX(360deg) scale(1.05); }
            30% { transform: rotateX(720deg) scale(1); }
            50% { transform: rotateX(1080deg) scale(1.05); }
            70% { transform: rotateX(1440deg) scale(1); }
            85% { transform: rotateX(1620deg) scale(1.02); }
            100% { transform: rotateX(1800deg) scale(1); }
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
            font-size: 16px;
            font-weight: 600;
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
            font-size: 16px;
            font-weight: 600;
            min-height: 40px;
            padding: 10px;
            border-radius: 10px;
            margin-top: 14px;
            background: #0d0d15;
            border: 1px solid #1a1a2a;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
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
        
        .history-section {
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #1a1a2a;
        }
        
        .history-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .history-header h3 {
            color: #4a4a5a;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        
        .history-count {
            color: #4a4a5a;
            font-size: 11px;
        }
        
        #historyList {
            max-height: 120px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        
        #historyList::-webkit-scrollbar {
            width: 3px;
        }
        
        #historyList::-webkit-scrollbar-track {
            background: #0d0d15;
        }
        
        #historyList::-webkit-scrollbar-thumb {
            background: #2a2a3a;
            border-radius: 2px;
        }
        
        .history-item {
            padding: 6px 12px;
            background: #0d0d15;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
            border-left: 2px solid #2a2a3a;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            0% { opacity: 0; transform: translateX(-10px); }
            100% { opacity: 1; transform: translateX(0); }
        }
        
        .history-item .symbols {
            color: #8a8a9a;
            font-size: 15px;
            letter-spacing: 1px;
        }
        
        .history-item .amount {
            font-weight: 600;
        }
        
        .history-item .amount.positive {
            color: #00ff88;
        }
        
        .history-item .amount.negative {
            color: #ff4466;
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
        <span class="balance-value" id="balance">1000 <small>₽</small></span>
    </div>
    
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
                <button class="bet-btn" id="betHalf">½</button>
                <input type="number" class="bet-input" id="betAmount" value="10" min="1">
                <button class="bet-btn" id="betDouble">2×</button>
            </div>
        </div>
        <button class="btn-spin" id="spinBtn">🎰 SPIN</button>
    </div>
    
    <div id="result" class="result">Нажми SPIN</div>
    
    <div class="history-section">
        <div class="history-header">
            <h3>📜 История</h3>
            <span class="history-count" id="historyCount">0</span>
        </div>
        <div id="historyList"></div>
    </div>
    
    <button class="btn-close" id="closeBtn">✖ Закрыть</button>
    <div class="footer">18+ · Играй ответственно</div>
</div>

<script>
const tg = window.Telegram.WebApp;
tg.expand();

let balance = 1000;
let isSpinning = false;

const symbols = ['🍒', '🍋', '🍊', '🍇', '💎', '7️⃣', '⭐', '🍉'];

const s1 = document.getElementById('slot1');
const s2 = document.getElementById('slot2');
const s3 = document.getElementById('slot3');
const spinBtn = document.getElementById('spinBtn');
const betInput = document.getElementById('betAmount');
const betHalf = document.getElementById('betHalf');
const betDouble = document.getElementById('betDouble');
const resultDiv = document.getElementById('result');
const balanceSpan = document.getElementById('balance');
const historyList = document.getElementById('historyList');
const historyCount = document.getElementById('historyCount');

function getUserId() {
    const p = new URLSearchParams(window.location.search);
    return p.get('user_id') || '';
}

function updateBalance(b) {
    balance = b;
    balanceSpan.textContent = balance + ' ₽';
}

function addHistory(symbolsStr, amount) {
    const item = document.createElement('div');
    item.className = 'history-item';
    const sign = amount >= 0 ? '+' : '';
    const cls = amount >= 0 ? 'positive' : 'negative';
    item.innerHTML = `<span class="symbols">${symbolsStr}</span><span class="amount ${cls}">${sign}${amount} ₽</span>`;
    historyList.prepend(item);
    
    while (historyList.children.length > 15) {
        historyList.removeChild(historyList.lastChild);
    }
    historyCount.textContent = historyList.children.length;
}

function spinSlots() {
    if (isSpinning) return;
    
    const bet = parseInt(betInput.value) || 0;
    if (bet <= 0 || bet > balance) {
        resultDiv.textContent = '❌ Неверная ставка';
        resultDiv.className = 'result lose';
        return;
    }
    
    isSpinning = true;
    spinBtn.disabled = true;
    resultDiv.textContent = '🌀 Вращение...';
    resultDiv.className = 'result';
    
    const slots = [s1, s2, s3];
    slots.forEach(s => s.classList.add('spinning'));
    
    // Генерируем результаты
    const results = slots.map(() => symbols[Math.floor(Math.random() * symbols.length)]);
    
    // Медленная остановка
    const totalDuration = 2500;
    const startTime = Date.now();
    
    function updateSlots() {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / totalDuration, 1);
        
        // Плавное замедление
        const easeOut = 1 - Math.pow(1 - progress, 3);
        
        slots.forEach((s, i) => {
            if (progress < 0.85) {
                // Быстрое вращение
                const randomIndex = Math.floor(Math.random() * symbols.length);
                s.textContent = symbols[randomIndex];
            } else {
                // Медленная остановка к финальному результату
                const stopProgress = (progress - 0.85) / 0.15;
                if (stopProgress > 0.5) {
                    s.textContent = results[i];
                }
            }
        });
        
        if (progress < 1) {
            requestAnimationFrame(updateSlots);
        } else {
            // Финал
            slots.forEach((s, i) => {
                s.textContent = results[i];
                s.classList.remove('spinning');
            });
            checkWin(results);
        }
    }
    
    updateSlots();
}

function checkWin(results) {
    const bet = parseInt(betInput.value) || 0;
    const [r1, r2, r3] = results;
    
    let win = 0;
    let msg = '';
    let className = 'lose';
    let isBigWin = false;
    
    // Проверка на виноград 🍉
    if (r1 === '🍉' || r2 === '🍉' || r3 === '🍉') {
        const grapeCount = results.filter(r => r === '🍉').length;
        if (grapeCount === 3) {
            win = bet * 8;
            msg = '🍉🍉🍉 ВИНОГРАД! x8!';
            className = 'bigwin';
            isBigWin = true;
        } else if (grapeCount === 2) {
            win = bet * 3;
            msg = '🍉🍉 ДВА ВИНОГРАДА! x3!';
            className = 'win';
        } else {
            win = bet * 1.5;
            msg = '🍉 ВИНОГРАД! x1.5!';
            className = 'win';
        }
    }
    // Джекпоты
    else if (r1 === r2 && r2 === r3) {
        if (r1 === '💎') {
            win = bet * 15;
            msg = '💎💎💎 ДЖЕКПОТ! x15!';
            className = 'bigwin';
            isBigWin = true;
        } else if (r1 === '7️⃣') {
            win = bet * 10;
            msg = '7️⃣7️⃣7️⃣ СЧАСТЛИВЧИК! x10!';
            className = 'bigwin';
            isBigWin = true;
        } else if (r1 === '⭐') {
            win = bet * 20;
            msg = '⭐⭐⭐ СУПЕР! x20!';
            className = 'bigwin';
            isBigWin = true;
        } else {
            win = bet * 5;
            msg = `🎉 ТРИ ${r1}! x5!`;
            className = 'win';
        }
    }
    // Пара
    else if (r1 === r2 || r2 === r3 || r1 === r3) {
        win = bet * 2;
        msg = '✨ ПАРА! x2!';
        className = 'win';
    }
    // Бриллиант
    else if (r1 === '💎' || r2 === '💎' || r3 === '💎') {
        win = bet * 1.5;
        msg = '💎 БРИЛЛИАНТ! x1.5!';
        className = 'win';
    }
    // Звезда
    else if (r1 === '⭐' || r2 === '⭐' || r3 === '⭐') {
        win = bet * 2;
        msg = '⭐ ЗВЕЗДА! x2!';
        className = 'win';
    }
    else {
        win = 0;
        msg = '😔 Повезет в следующий раз';
        className = 'lose';
    }
    
    const net = win - bet;
    balance += net;
    updateBalance(balance);
    
    // Подсветка победных слотов
    if (net > 0) {
        const slots = [s1, s2, s3];
        slots.forEach(s => s.classList.add('win'));
        setTimeout(() => {
            slots.forEach(s => s.classList.remove('win'));
        }, 800);
    }
    
    resultDiv.textContent = `${msg} ${net > 0 ? '+' : ''}${net} ₽`;
    resultDiv.className = `result ${className}`;
    
    addHistory(results.join(' '), net);
    
    // Отправка на сервер
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
    
    isSpinning = false;
    spinBtn.disabled = false;
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

// Периодическое обновление баланса
setInterval(loadBalance, 10000);

spinBtn.addEventListener('click', spinSlots);

betHalf.addEventListener('click', () => {
    let val = parseInt(betInput.value) || 10;
    val = Math.floor(val / 2);
    if (val < 1) val = 1;
    betInput.value = val;
});

betDouble.addEventListener('click', () => {
    let val = parseInt(betInput.value) || 10;
    val = Math.min(val * 2, balance);
    if (val < 1) val = 1;
    betInput.value = val;
});

betInput.addEventListener('change', () => {
    let val = parseInt(betInput.value) || 10;
    if (val < 1) val = 1;
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
        f"💰 Ваш баланс: {user.balance} ₽\n"
        f"🎮 Игр сыграно: {user.games_played}\n"
        f"🏆 Выиграно: {user.total_won} ₽\n"
        f"💔 Проиграно: {user.total_lost} ₽\n\n"
        "⬇️ Нажми кнопку ниже, чтобы открыть игровой зал!",
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
                f"💰 Баланс: {user.balance} ₽\n"
                f"🏆 Выиграно: {user.total_won} ₽\n"
                f"💔 Проиграно: {user.total_lost} ₽\n"
                f"🎮 Игр: {user.games_played}",
                show_alert=True
            )
        
        elif call.data == "stats":
            bot.answer_callback_query(
                call.id,
                f"📊 Статистика:\n"
                f"🎮 Игр: {user.games_played}\n"
                f"🏆 Выигрышей: {user.total_won} ₽\n"
                f"💔 Проигрышей: {user.total_lost} ₽\n"
                f"💰 Баланс: {user.balance} ₽",
                show_alert=True
            )
        
        elif call.data == "admin" and user.is_admin:
            show_admin_panel(call.message, user)

def show_admin_panel(message, admin):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("➕ Выдать", callback_data="admin_give"),
        InlineKeyboardButton("➖ Забрать", callback_data="admin_take")
    )
    markup.row(
        InlineKeyboardButton("👤 Инфо", callback_data="admin_info"),
        InlineKeyboardButton("📊 Топ", callback_data="admin_top")
    )
    markup.row(InlineKeyboardButton("🔙 Назад", callback_data="back"))
    
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
        
        if call.data == "admin_give":
            bot.send_message(call.message.chat.id, "Введите ID и сумму:\n`123456789 100`", parse_mode='Markdown')
            bot.register_next_step_handler(call.message, admin_give_currency)
        
        elif call.data == "admin_take":
            bot.send_message(call.message.chat.id, "Введите ID и сумму:\n`123456789 50`", parse_mode='Markdown')
            bot.register_next_step_handler(call.message, admin_take_currency)
        
        elif call.data == "admin_info":
            bot.send_message(call.message.chat.id, "Введите ID пользователя:")
            bot.register_next_step_handler(call.message, admin_get_user_info)
        
        elif call.data == "admin_top":
            show_top_players(call.message)
        
        elif call.data == "back":
            start(call.message)

def admin_give_currency(message):
    try:
        parts = message.text.split()
        user_id = parts[0]
        amount = int(parts[1])
        
        with app.app_context():
            user = User.query.filter_by(telegram_id=user_id).first()
            if user:
                user.balance += amount
                db.session.commit()
                bot.send_message(message.chat.id, f"✅ Выдано {amount} ₽ пользователю {user.first_name}")
            else:
                bot.send_message(message.chat.id, "❌ Пользователь не найден")
    except:
        bot.send_message(message.chat.id, "❌ Ошибка! Формат: ID СУММА")

def admin_take_currency(message):
    try:
        parts = message.text.split()
        user_id = parts[0]
        amount = int(parts[1])
        
        with app.app_context():
            user = User.query.filter_by(telegram_id=user_id).first()
            if user:
                if user.balance >= amount:
                    user.balance -= amount
                    db.session.commit()
                    bot.send_message(message.chat.id, f"✅ Забрано {amount} ₽ у {user.first_name}")
                else:
                    bot.send_message(message.chat.id, "❌ Недостаточно средств")
            else:
                bot.send_message(message.chat.id, "❌ Пользователь не найден")
    except:
        bot.send_message(message.chat.id, "❌ Ошибка! Формат: ID СУММА")

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
                    f"💰 Баланс: {user.balance} ₽\n"
                    f"🎮 Игр: {user.games_played}\n"
                    f"🏆 Выиграно: {user.total_won} ₽\n"
                    f"💔 Проиграно: {user.total_lost} ₽",
                    parse_mode='Markdown'
                )
            else:
                bot.send_message(message.chat.id, "❌ Пользователь не найден")
    except:
        bot.send_message(message.chat.id, "❌ О
