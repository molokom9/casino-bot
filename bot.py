import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import threading
import os
import random

# ========== КОНФИГ ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8941440753:AAGejY76StUx3ae6paRaTIqQWXr3hPqWkXs')
WEBAPP_URL = os.environ.get('WEBAPP_URL', 'https://casino-bot-mw0h.onrender.com/')
ADMIN_ID = '8663798936'
REFILL_LINK = 'https://t.me/Qwile_Games'

# ========== БАЗА ==========
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

class GameHistory(db.Model):
    __tablename__ = 'game_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    bet = db.Column(db.Integer)
    win = db.Column(db.Integer)
    symbols = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# ========== HTML (новый премиальный дизайн) ==========
HTML = '''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Casino Royale</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: #0c0c12;
    min-height: 100vh;
    color: #fff;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 12px;
}

.container {
    width: 100%;
    max-width: 380px;
    background: linear-gradient(180deg, #14141e 0%, #0f0f16 100%);
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.06);
    overflow: hidden;
    box-shadow: 0 25px 50px -12px rgba(0,0,0,0.7);
}

.header {
    padding: 18px 20px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.logo {
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 0.5px;
    color: #fff;
}

.logo span {
    background: linear-gradient(90deg, #f6d365, #fda085);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.live {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.live-dot {
    width: 7px;
    height: 7px;
    background: #22c55e;
    border-radius: 50%;
    box-shadow: 0 0 8px #22c55e;
    animation: pulse 1.8s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

.balance-section {
    padding: 18px 20px 12px;
}

.balance-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 16px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.balance-label {
    font-size: 12px;
    font-weight: 600;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

.balance-value {
    font-size: 26px;
    font-weight: 800;
    color: #fbbf24;
    letter-spacing: -0.5px;
}

.balance-value small {
    font-size: 14px;
    font-weight: 600;
    color: #9ca3af;
    margin-left: 2px;
}

.refill-btn {
    display: block;
    margin: 12px 20px 0;
    padding: 13px;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: #fff;
    text-align: center;
    text-decoration: none;
    font-size: 14px;
    font-weight: 700;
    border-radius: 12px;
    letter-spacing: 0.3px;
    transition: transform 0.15s, box-shadow 0.15s;
}

.refill-btn:active {
    transform: scale(0.98);
}

.slots-wrap {
    margin: 18px 16px;
    background: #0a0a10;
    border-radius: 16px;
    padding: 22px 14px;
    border: 1px solid rgba(255,255,255,0.04);
}

.slots {
    display: flex;
    justify-content: center;
    gap: 10px;
}

.slot-box {
    flex: 1;
    max-width: 88px;
    background: #111118;
    border-radius: 12px;
    padding: 6px;
    border: 1px solid rgba(255,255,255,0.05);
}

.slot {
    width: 100%;
    aspect-ratio: 1;
    background: #0d0d14;
    border-radius: 9px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 40px;
    transition: all 0.25s;
}

.slot.spinning {
    animation: spin 0.9s cubic-bezier(0.2, 0.8, 0.2, 1);
}

@keyframes spin {
    0% { transform: scale(1) rotateX(0); }
    30% { transform: scale(1.08) rotateX(180deg); }
    60% { transform: scale(1) rotateX(360deg); }
    100% { transform: scale(1) rotateX(720deg); }
}

.slot.win {
    box-shadow: 0 0 0 2px #fbbf24, 0 0 20px rgba(251,191,36,0.25);
}

.controls {
    padding: 0 20px 8px;
}

.bet-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 12px;
}

.bet-label {
    font-size: 12px;
    font-weight: 600;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

.bet-controls {
    display: flex;
    align-items: center;
    gap: 8px;
}

.bet-btn {
    width: 34px;
    height: 34px;
    border: none;
    background: rgba(255,255,255,0.08);
    color: #fff;
    font-size: 20px;
    font-weight: 600;
    border-radius: 9px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s;
}

.bet-btn:active {
    background: rgba(255,255,255,0.15);
}

.bet-input {
    width: 68px;
    height: 34px;
    background: #0a0a10;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 9px;
    color: #fff;
    font-size: 16px;
    font-weight: 700;
    text-align: center;
    outline: none;
}

.bet-input:focus {
    border-color: #fbbf24;
}

.spin-btn {
    width: 100%;
    padding: 16px;
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    color: #111;
    border: none;
    border-radius: 13px;
    font-size: 17px;
    font-weight: 800;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: transform 0.15s, box-shadow 0.15s;
}

.spin-btn:active:not(:disabled) {
    transform: scale(0.97);
}

.spin-btn:disabled {
    opacity: 0.45;
    cursor: not-allowed;
}

.result {
    margin: 14px 20px 0;
    min-height: 48px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
    font-weight: 600;
    color: #d1d5db;
    text-align: center;
    padding: 0 12px;
}

.result.win {
    color: #4ade80;
    border-color: rgba(74,222,128,0.2);
    background: rgba(74,222,128,0.05);
}

.result.lose {
    color: #f87171;
    border-color: rgba(248,113,113,0.15);
}

.result.bigwin {
    color: #fbbf24;
    border-color: rgba(251,191,36,0.3);
    background: rgba(251,191,36,0.06);
}

.close-btn {
    display: block;
    width: calc(100% - 40px);
    margin: 16px 20px 20px;
    padding: 13px;
    background: transparent;
    border: 1px solid rgba(255,255,255,0.08);
    color: #6b7280;
    font-size: 13px;
    font-weight: 600;
    border-radius: 12px;
    cursor: pointer;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    transition: all 0.15s;
}

.close-btn:active {
    background: rgba(255,255,255,0.04);
    color: #9ca3af;
}

.footer {
    text-align: center;
    padding-bottom: 16px;
    font-size: 10px;
    color: #4b5563;
    letter-spacing: 1.2px;
    text-transform: uppercase;
}

@media (max-width: 360px) {
    .slot { font-size: 34px; }
    .balance-value { font-size: 22px; }
}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="logo">CASINO <span>ROYALE</span></div>
        <div class="live"><span class="live-dot"></span> LIVE</div>
    </div>

    <div class="balance-section">
        <div class="balance-card">
            <div class="balance-label">Баланс</div>
            <div class="balance-value" id="balance">25 <small>₴</small></div>
        </div>
    </div>

    <a href="https://t.me/Qwile_Games" class="refill-btn" target="_blank">Пополнить баланс</a>

    <div class="slots-wrap">
        <div class="slots">
            <div class="slot-box"><div class="slot" id="slot1">🍒</div></div>
            <div class="slot-box"><div class="slot" id="slot2">🍋</div></div>
            <div class="slot-box"><div class="slot" id="slot3">🍇</div></div>
        </div>
    </div>

    <div class="controls">
        <div class="bet-row">
            <div class="bet-label">Ставка</div>
            <div class="bet-controls">
                <button class="bet-btn" id="betMinus">−</button>
                <input type="number" class="bet-input" id="betAmount" value="25" min="25" step="25">
                <button class="bet-btn" id="betPlus">+</button>
            </div>
        </div>
        <button class="spin-btn" id="spinBtn">SPIN</button>
    </div>

    <div class="result" id="result">Нажми SPIN</div>

    <button class="close-btn" id="closeBtn">Закрыть</button>
    <div class="footer">18+ · Играй ответственно</div>
</div>

<script>
const tg = window.Telegram.WebApp;
tg.expand();
tg.setHeaderColor('#0c0c12');
tg.setBackgroundColor('#0c0c12');

let balance = 25;
let isSpinning = false;
const symbols = ['🍒','🍋','🍊','🍇','💎','7️⃣','⭐','🍉'];

const s1 = document.getElementById('slot1');
const s2 = document.getElementById('slot2');
const s3 = document.getElementById('slot3');
const spinBtn = document.getElementById('spinBtn');
const betInput = document.getElementById('betAmount');
const resultDiv = document.getElementById('result');
const balanceEl = document.getElementById('balance');

function getUserId() {
    return new URLSearchParams(window.location.search).get('user_id') || '';
}

function updateBalance(val) {
    balance = val;
    balanceEl.innerHTML = val + ' <small>₴</small>';
}

function spinSlots() {
    if (isSpinning) return;
    const bet = parseInt(betInput.value) || 25;
    if (bet < 25 || bet > balance) {
        resultDiv.textContent = 'Минимальная ставка 25 ₴';
        resultDiv.className = 'result lose';
        return;
    }

    isSpinning = true;
    spinBtn.disabled = true;
    resultDiv.textContent = 'Вращение...';
    resultDiv.className = 'result';

    const slots = [s1, s2, s3];
    const final = slots.map(() => symbols[Math.floor(Math.random() * symbols.length)]);
    let finished = 0;

    slots.forEach((slot, i) => {
        setTimeout(() => {
            slot.classList.add('spinning');
            const interval = setInterval(() => {
                if (slot.classList.contains('spinning')) {
                    slot.textContent = symbols[Math.floor(Math.random() * symbols.length)];
                }
            }, 70);

            setTimeout(() => {
                clearInterval(interval);
                slot.textContent = final[i];
                slot.classList.remove('spinning');
                finished++;
                if (finished === 3) {
                    setTimeout(() => {
                        checkWin(final, bet);
                        isSpinning = false;
                        spinBtn.disabled = false;
                    }, 200);
                }
            }, 1100);
        }, i * 280);
    });
}

function checkWin(results, bet) {
    const [a, b, c] = results;
    let win = 0;
    let msg = '';
    let cls = 'lose';

    const r = Math.random();

    if (r > 0.11) {
        win = 0;
        msg = 'Повезёт в следующий раз';
    } else if (a === b && b === c) {
        if (a === '💎') { win = bet * 10; msg = '💎 ДЖЕКПОТ ×10'; cls = 'bigwin'; }
        else if (a === '7️⃣') { win = bet * 8; msg = '7️⃣ СЧАСТЛИВЧИК ×8'; cls = 'bigwin'; }
        else if (a === '⭐') { win = bet * 12; msg = '⭐ СУПЕР ×12'; cls = 'bigwin'; }
        else { win = bet * 4; msg = 'Три в ряд ×4'; cls = 'win'; }
    } else if (a === b || b === c || a === c) {
        if (Math.random() < 0.25) {
            win = Math.floor(bet * 1.5);
            msg = 'Пара ×1.5';
            cls = 'win';
        } else {
            msg = 'Почти...';
        }
    } else if ([a,b,c].includes('💎') && Math.random() < 0.12) {
        win = Math.floor(bet * 1.5);
        msg = '💎 Бриллиант ×1.5';
        cls = 'win';
    } else {
        msg = 'Повезёт в следующий раз';
    }

    const net = win - bet;
    balance += net;
    updateBalance(balance);

    if (net > 0) {
        [s1,s2,s3].forEach(s => s.classList.add('win'));
        setTimeout(() => [s1,s2,s3].forEach(s => s.classList.remove('win')), 700);
    }

    resultDiv.textContent = msg + (net !== 0 ? ` ${net > 0 ? '+' : ''}${net} ₴` : '');
    resultDiv.className = 'result ' + cls;

    const uid = getUserId();
    if (uid) {
        fetch('/game_result', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user_id: uid,
                bet: bet,
                win: net,
                symbols: results.join('')
            })
        }).catch(()=>{});
    }
}

function loadBalance() {
    const uid = getUserId();
    if (!uid) return;
    fetch('/get_balance?user_id=' + uid)
        .then(r => r.json())
        .then(d => { if (d.balance !== undefined) updateBalance(d.balance); })
        .catch(()=>{});
}

document.getElementById('betMinus').onclick = () => {
    let v = parseInt(betInput.value) || 25;
    betInput.value = Math.max(25, v - 25);
};

document.getElementById('betPlus').onclick = () => {
    let v = parseInt(betInput.value) || 25;
    betInput.value = Math.min(balance, v + 25);
};

betInput.onchange = () => {
    let v = parseInt(betInput.value) || 25;
    if (v < 25) v = 25;
    if (v % 25 !== 0) v = Math.round(v / 25) * 25;
    if (v > balance) v = balance;
    betInput.value = v;
};

spinBtn.onclick = spinSlots;
document.getElementById('closeBtn').onclick = () => tg.close();

loadBalance();
setInterval(loadBalance, 12000);
</script>
</body>
</html>'''

# ========== ROUTES ==========
@app.route('/')
def index():
    return HTML

@app.route('/get_balance')
def get_balance():
    user_id = request.args.get('user_id')
    if user_id:
        with app.app_context():
            user = User.query.filter_by(telegram_id=str(user_id)).first()
            if user:
                return jsonify({'balance': user.balance})
    return jsonify({'balance': 25})

@app.route('/game_result', methods=['POST'])
def game_result():
    data = request.json or {}
    user_id = str(data.get('user_id', ''))
    bet = int(data.get('bet', 0))
    win = int(data.get('win', 0))
    symbols = data.get('symbols', '')

    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        if user:
            user.balance += win
            user.games_played += 1
            if win > 0:
                user.total_won += win
            else:
                user.total_lost += abs(win)
            user.last_active = datetime.utcnow()
            db.session.add(GameHistory(user_id=user.id, bet=bet, win=win, symbols=symbols))
            db.session.commit()
    return jsonify({'status': 'ok'})

# ========== BOT ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        if not user:
            user = User(
                telegram_id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name or '',
                last_name=message.from_user.last_name or ''
            )
            db.session.add(user)
            db.session.commit()

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🎰 Играть", web_app=WebAppInfo(url=f"{WEBAPP_URL}?user_id={user_id}")),
        InlineKeyboardButton("💳 Пополнить", url=REFILL_LINK)
    )
    if user.is_admin:
        markup.row(InlineKeyboardButton("👑 Админ-панель", callback_data="admin_panel"))

    bot.send_message(
        message.chat.id,
        f"Добро пожаловать в <b>Casino Royale</b>, {message.from_user.first_name}!\n\n"
        f"Минимальная ставка — 25 ₴",
        reply_markup=markup
    )

@bot.message_handler(commands=['balance'])
def balance_cmd(message):
    user_id = str(message.from_user.id)
    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        if user:
            bot.reply_to(message,
                f"💰 Баланс: <b>{user.balance} ₴</b>\n"
                f"🏆 Выиграно: {user.total_won} ₴\n"
                f"💔 Проиграно: {user.total_lost} ₴\n"
                f"🎮 Игр: {user.games_played}"
            )
        else:
            bot.reply_to(message, "Напиши /start")

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    user_id = str(message.from_user.id)
    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        if user and user.is_admin:
            show_admin(message.chat.id)
        else:
            bot.reply_to(message, "Нет доступа")

# ========== АДМИНКА (полностью переписана, не виснет) ==========
def show_admin(chat_id):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📋 Список пользователей", callback_data="adm_users_0"),
        InlineKeyboardButton("🔍 Найти пользователя", callback_data="adm_find"),
        InlineKeyboardButton("« Закрыть", callback_data="adm_close")
    )
    bot.send_message(chat_id, "<b>Админ-панель</b>\nВыберите действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: True)
def all_callbacks(call):
    user_id = str(call.from_user.id)
    data = call.data

    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        if not user:
            bot.answer_callback_query(call.id, "Напиши /start")
            return

        # обычные кнопки
        if data == "admin_panel":
            if not user.is_admin:
                bot.answer_callback_query(call.id, "Нет прав", show_alert=True)
                return
            bot.answer_callback_query(call.id)
            show_admin(call.message.chat.id)
            return

        if not user.is_admin:
            bot.answer_callback_query(call.id, "Нет прав", show_alert=True)
            return

        bot.answer_callback_query(call.id)

        # список пользователей
        if data.startswith("adm_users_"):
            page = int(data.split("_")[-1])
            show_users(call.message, page)
            return

        if data == "adm_find":
            msg = bot.send_message(call.message.chat.id, "Введите ID пользователя или @username:")
            bot.register_next_step_handler(msg, process_find)
            return

        if data == "adm_close":
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            return

        # действия над пользователем
        if data.startswith("adm_act_"):
            parts = data.split("_")
            target_id = parts[2]
            action = parts[3]
            process_action(call.message, target_id, action)
            return

def show_users(message, page=0):
    with app.app_context():
        total = User.query.count()
        if total == 0:
            bot.edit_message_text("Пользователей пока нет", message.chat.id, message.message_id)
            return

        per_page = 6
        users = User.query.order_by(User.balance.desc()).offset(page * per_page).limit(per_page).all()
        total_pages = max(1, (total + per_page - 1) // per_page)

        text = f"<b>Пользователи</b> · стр. {page+1}/{total_pages}\n\n"
        for i, u in enumerate(users, start=page*per_page + 1):
            name = u.first_name or "—"
            uname = f"@{u.username}" if u.username else "нет"
            text += f"{i}. <b>{name}</b> ({uname})\n"
            text += f"   ID: <code>{u.telegram_id}</code> · {u.balance} ₴\n\n"

        markup = InlineKeyboardMarkup()
        row = []
        if page > 0:
            row.append(InlineKeyboardButton("‹ Назад", callback_data=f"adm_users_{page-1}"))
        if page + 1 < total_pages:
            row.append(InlineKeyboardButton("Вперёд ›", callback_data=f"adm_users_{page+1}"))
        if row:
            markup.row(*row)
        markup.row(InlineKeyboardButton("🔄 Обновить", callback_data=f"adm_users_{page}"))
        markup.row(InlineKeyboardButton("« В меню", callback_data="admin_panel"))

        try:
            bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=markup)
        except:
            bot.send_message(message.chat.id, text, reply_markup=markup)

def process_find(message):
    query = (message.text or "").strip()
    if not query:
        bot.send_message(message.chat.id, "Пустой запрос")
        return

    with app.app_context():
        if query.startswith("@"):
            user = User.query.filter_by(username=query[1:]).first()
        else:
            user = User.query.filter_by(telegram_id=query).first()

        if not user:
            bot.send_message(message.chat.id, "Пользователь не найден")
            return

        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("➕ Выдать", callback_data=f"adm_act_{user.telegram_id}_give"),
            InlineKeyboardButton("➖ Забрать", callback_data=f"adm_act_{user.telegram_id}_take"),
            InlineKeyboardButton("🗑 Удалить", callback_data=f"adm_act_{user.telegram_id}_del"),
            InlineKeyboardButton("👑 Админ", callback_data=f"adm_act_{user.telegram_id}_admin"),
        )
        markup.row(InlineKeyboardButton("« В меню", callback_data="admin_panel"))

        bot.send_message(
            message.chat.id,
            f"<b>{user.first_name or '—'}</b>\n"
            f"ID: <code>{user.telegram_id}</code>\n"
            f"Username: @{user.username or 'нет'}\n"
            f"Баланс: <b>{user.balance} ₴</b>\n"
            f"Игр: {user.games_played} · Выиграно: {user.total_won} · Проиграно: {user.total_lost}\n"
            f"Админ: {'да' if user.is_admin else 'нет'}",
            reply_markup=markup
        )

def process_action(message, target_id, action):
    with app.app_context():
        user = User.query.filter_by(telegram_id=target_id).first()
        if not user:
            bot.send_message(message.chat.id, "Пользователь не найден")
            return

        if action == "give":
            msg = bot.send_message(message.chat.id, f"Сумма для выдачи (кратно 25):")
            bot.register_next_step_handler(msg, lambda m: do_give(m, target_id))
        elif action == "take":
            msg = bot.send_message(message.chat.id, f"Сумма для забора (кратно 25):")
            bot.register_next_step_handler(msg, lambda m: do_take(m, target_id))
        elif action == "del":
            name = user.first_name
            db.session.delete(user)
            db.session.commit()
            bot.send_message(message.chat.id, f"Пользователь {name} удалён")
        elif action == "admin":
            user.is_admin = True
            db.session.commit()
            bot.send_message(message.chat.id, f"{user.first_name} теперь админ")

def do_give(message, target_id):
    try:
        amount = int(message.text.strip())
        if amount <= 0 or amount % 25 != 0:
            bot.send_message(message.chat.id, "Сумма должна быть положительной и кратной 25")
            return
        with app.app_context():
            user = User.query.filter_by(telegram_id=target_id).first()
            if user:
                user.balance += amount
                db.session.commit()
                bot.send_message(message.chat.id, f"Выдано {amount} ₴ → {user.first_name}")
            else:
                bot.send_message(message.chat.id, "Пользователь не найден")
    except:
        bot.send_message(message.chat.id, "Введите число")

def do_take(message, target_id):
    try:
        amount = int(message.text.strip())
        if amount <= 0 or amount % 25 != 0:
            bot.send_message(message.chat.id, "Сумма должна быть положительной и кратной 25")
            return
        with app.app_context():
            user = User.query.filter_by(telegram_id=target_id).first()
            if user:
                if user.balance < amount:
                    bot.send_message(message.chat.id, "Недостаточно средств")
                    return
                user.balance -= amount
                db.session.commit()
                bot.send_message(message.chat.id, f"Забрано {amount} ₴ у {user.first_name}")
            else:
                bot.send_message(message.chat.id, "Пользователь не найден")
    except:
        bot.send_message(message.chat.id, "Введите число")

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    def run_bot():
        while True:
            try:
                bot.polling(none_stop=True, interval=1, timeout=30)
            except Exception as e:
                print("Bot error:", e)
                import time
                time.sleep(5)
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=port, debug=False)
