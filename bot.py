import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, MenuButtonWebApp
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
    balance = db.Column(db.Integer, default=0)
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

# ========== HTML ==========
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
    background: #08080d;
    min-height: 100vh;
    color: #fff;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 10px;
}

.container {
    width: 100%;
    max-width: 390px;
    background: linear-gradient(165deg, #12121c 0%, #0b0b12 100%);
    border-radius: 22px;
    border: 1px solid rgba(255,255,255,0.07);
    overflow: hidden;
    box-shadow: 0 30px 60px -15px rgba(0,0,0,0.85);
}

.header {
    padding: 16px 18px 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}

.logo {
    font-size: 17px;
    font-weight: 800;
    letter-spacing: 0.6px;
}

.logo span {
    background: linear-gradient(90deg, #fcd34d, #f59e0b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.live {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 10px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 1.1px;
}

.live-dot {
    width: 6px;
    height: 6px;
    background: #22c55e;
    border-radius: 50%;
    box-shadow: 0 0 10px #22c55e;
    animation: pulse 1.6s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.45; transform: scale(0.85); }
}

.balance-section {
    padding: 16px 16px 8px;
}

.balance-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 14px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.balance-label {
    font-size: 11px;
    font-weight: 600;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.9px;
}

.balance-value {
    font-size: 24px;
    font-weight: 800;
    color: #fbbf24;
    letter-spacing: -0.4px;
}

.balance-value small {
    font-size: 13px;
    font-weight: 600;
    color: #9ca3af;
}

.refill-btn {
    display: block;
    margin: 10px 16px 0;
    padding: 12px;
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    color: #fff;
    text-align: center;
    text-decoration: none;
    font-size: 13px;
    font-weight: 700;
    border-radius: 11px;
    letter-spacing: 0.3px;
    transition: all 0.15s;
    box-shadow: 0 4px 15px rgba(59,130,246,0.25);
}

.refill-btn:active {
    transform: scale(0.98);
    box-shadow: none;
}

.slots-wrap {
    margin: 14px 12px;
    background: #07070c;
    border-radius: 16px;
    padding: 20px 12px;
    border: 1px solid rgba(255,255,255,0.04);
    position: relative;
}

.slots {
    display: flex;
    justify-content: center;
    gap: 9px;
}

.slot-box {
    flex: 1;
    max-width: 92px;
    background: #101018;
    border-radius: 13px;
    padding: 5px;
    border: 1px solid rgba(255,255,255,0.05);
    transition: border-color 0.3s, box-shadow 0.3s;
}

.slot-box.active {
    border-color: rgba(251,191,36,0.4);
    box-shadow: 0 0 22px rgba(251,191,36,0.18);
}

.slot {
    width: 100%;
    aspect-ratio: 1;
    background: #0c0c14;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 42px;
    transition: transform 0.15s;
    will-change: transform;
}

.slot.spinning {
    animation: slotBlur 0.06s linear infinite;
}

@keyframes slotBlur {
    0% { transform: translateY(-3px); filter: blur(0.8px); }
    50% { transform: translateY(3px); filter: blur(1.2px); }
    100% { transform: translateY(-3px); filter: blur(0.8px); }
}

.slot.win {
    animation: winPulse 0.65s ease;
}

@keyframes winPulse {
    0% { transform: scale(1); }
    40% { transform: scale(1.15); }
    100% { transform: scale(1); }
}

.controls {
    padding: 0 16px 6px;
}

.bet-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 9px 12px;
    margin-bottom: 11px;
}

.bet-label {
    font-size: 11px;
    font-weight: 600;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.7px;
}

.bet-controls {
    display: flex;
    align-items: center;
    gap: 7px;
}

.bet-btn {
    width: 32px;
    height: 32px;
    border: none;
    background: rgba(255,255,255,0.07);
    color: #fff;
    font-size: 18px;
    font-weight: 600;
    border-radius: 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.12s;
}

.bet-btn:active {
    background: rgba(255,255,255,0.14);
}

.bet-input {
    width: 64px;
    height: 32px;
    background: #08080e;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    color: #fff;
    font-size: 15px;
    font-weight: 700;
    text-align: center;
    outline: none;
}

.bet-input:focus {
    border-color: #fbbf24;
}

.spin-btn {
    width: 100%;
    padding: 15px;
    background: linear-gradient(135deg, #fbbf24 0%, #d97706 100%);
    color: #111;
    border: none;
    border-radius: 13px;
    font-size: 16px;
    font-weight: 800;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.15s;
    box-shadow: 0 6px 20px rgba(251,191,36,0.3);
}

.spin-btn:active:not(:disabled) {
    transform: scale(0.97);
    box-shadow: 0 2px 10px rgba(251,191,36,0.2);
}

.spin-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
    box-shadow: none;
}

.result {
    margin: 12px 16px 0;
    min-height: 46px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 11px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 600;
    color: #d1d5db;
    text-align: center;
    padding: 0 10px;
    transition: all 0.25s;
}

.result.win {
    color: #4ade80;
    border-color: rgba(74,222,128,0.25);
    background: rgba(74,222,128,0.06);
}

.result.lose {
    color: #f87171;
    border-color: rgba(248,113,113,0.18);
}

.result.bigwin {
    color: #fbbf24;
    border-color: rgba(251,191,36,0.35);
    background: rgba(251,191,36,0.08);
    font-size: 15px;
}

.close-btn {
    display: block;
    width: calc(100% - 32px);
    margin: 14px 16px 18px;
    padding: 12px;
    background: transparent;
    border: 1px solid rgba(255,255,255,0.07);
    color: #6b7280;
    font-size: 12px;
    font-weight: 600;
    border-radius: 11px;
    cursor: pointer;
    text-transform: uppercase;
    letter-spacing: 0.9px;
    transition: all 0.15s;
}

.close-btn:active {
    background: rgba(255,255,255,0.04);
    color: #9ca3af;
}

.footer {
    text-align: center;
    padding-bottom: 14px;
    font-size: 9px;
    color: #4b5563;
    letter-spacing: 1.3px;
    text-transform: uppercase;
}

@media (max-width: 360px) {
    .slot { font-size: 36px; }
    .balance-value { font-size: 21px; }
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
            <div class="balance-value" id="balance">0 <small>₴</small></div>
        </div>
    </div>

    <a href="https://t.me/Qwile_Games" class="refill-btn" target="_blank">Пополнить баланс</a>

    <div class="slots-wrap">
        <div class="slots">
            <div class="slot-box" id="box1"><div class="slot" id="slot1">🍒</div></div>
            <div class="slot-box" id="box2"><div class="slot" id="slot2">🍋</div></div>
            <div class="slot-box" id="box3"><div class="slot" id="slot3">🍇</div></div>
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

    <div class="result" id="result">Пополни баланс и крути</div>

    <button class="close-btn" id="closeBtn">Закрыть</button>
    <div class="footer">18+ · Играй ответственно</div>
</div>

<script>
const tg = window.Telegram.WebApp;
tg.expand();
tg.setHeaderColor('#08080d');
tg.setBackgroundColor('#08080d');

let balance = 0;
let isSpinning = false;
let isSyncing = false;
const symbols = ['🍒','🍋','🍊','🍇','💎','7️⃣','⭐','🍉'];

const s1 = document.getElementById('slot1');
const s2 = document.getElementById('slot2');
const s3 = document.getElementById('slot3');
const box1 = document.getElementById('box1');
const box2 = document.getElementById('box2');
const box3 = document.getElementById('box3');
const spinBtn = document.getElementById('spinBtn');
const betInput = document.getElementById('betAmount');
const resultDiv = document.getElementById('result');
const balanceEl = document.getElementById('balance');

function getUserId() {
    return new URLSearchParams(window.location.search).get('user_id') || '';
}

function updateBalance(val) {
    balance = Math.max(0, Math.floor(val));
    balanceEl.innerHTML = balance + ' <small>₴</small>';
}

function getWinChance(bet) {
    if (bet <= 50) return 0.23;
    if (bet <= 100) return 0.19;
    if (bet <= 200) return 0.15;
    if (bet <= 400) return 0.11;
    return 0.09;
}

function loadBalance(force = false) {
    if (isSpinning && !force) return;
    if (isSyncing) return;

    const uid = getUserId();
    if (!uid) return;

    isSyncing = true;
    fetch('/get_balance?user_id=' + uid)
        .then(r => r.json())
        .then(d => {
            if (d.balance !== undefined) {
                updateBalance(d.balance);
            }
        })
        .catch(() => {})
        .finally(() => {
            isSyncing = false;
        });
}

function spinSlots() {
    if (isSpinning) return;

    let bet = parseInt(betInput.value) || 25;
    if (bet < 25) bet = 25;

    if (balance < 25) {
        resultDiv.textContent = 'Пополни баланс (мин. 25 ₴)';
        resultDiv.className = 'result lose';
        return;
    }
    if (bet > balance) {
        resultDiv.textContent = 'Недостаточно средств';
        resultDiv.className = 'result lose';
        return;
    }

    isSpinning = true;
    spinBtn.disabled = true;
    resultDiv.textContent = 'Крутим...';
    resultDiv.className = 'result';

    const prevBalance = balance;
    updateBalance(balance - bet);

    const slots = [s1, s2, s3];
    const boxes = [box1, box2, box3];
    const final = [];
    let finished = 0;

    const chance = getWinChance(bet);
    const willWin = Math.random() < chance;

    if (willWin) {
        const roll = Math.random();
        if (roll < 0.10) {
            const sym = symbols[Math.floor(Math.random() * symbols.length)];
            final.push(sym, sym, sym);
        } else if (roll < 0.55) {
            const sym = symbols[Math.floor(Math.random() * symbols.length)];
            const pos = Math.floor(Math.random() * 3);
            final[0] = symbols[Math.floor(Math.random() * symbols.length)];
            final[1] = symbols[Math.floor(Math.random() * symbols.length)];
            final[2] = symbols[Math.floor(Math.random() * symbols.length)];
            if (pos === 0) { final[0] = final[1] = sym; }
            else if (pos === 1) { final[1] = final[2] = sym; }
            else { final[0] = final[2] = sym; }
        } else {
            final[0] = symbols[Math.floor(Math.random() * symbols.length)];
            final[1] = symbols[Math.floor(Math.random() * symbols.length)];
            final[2] = symbols[Math.floor(Math.random() * symbols.length)];
            final[Math.floor(Math.random() * 3)] = '💎';
        }
    } else {
        do {
            final[0] = symbols[Math.floor(Math.random() * symbols.length)];
            final[1] = symbols[Math.floor(Math.random() * symbols.length)];
            final[2] = symbols[Math.floor(Math.random() * symbols.length)];
        } while (final[0] === final[1] || final[1] === final[2] || final[0] === final[2]);
    }

    // Быстрое вращение + медленная поочерёдная остановка
    slots.forEach((slot, i) => {
        boxes[i].classList.add('active');
        slot.classList.add('spinning');

        // Очень быстрая смена символов
        const interval = setInterval(() => {
            if (slot.classList.contains('spinning')) {
                slot.textContent = symbols[Math.floor(Math.random() * symbols.length)];
            }
        }, 45);

        // Остановка: 1-й ~1.3с, 2-й ~2.2с, 3-й ~3.2с
        const stopDelay = 1300 + i * 950;

        setTimeout(() => {
            clearInterval(interval);
            slot.classList.remove('spinning');
            slot.textContent = final[i];
            boxes[i].classList.remove('active');

            finished++;
            if (finished === 3) {
                setTimeout(() => {
                    checkWin(final, bet, prevBalance);
                }, 250);
            }
        }, stopDelay);
    });
}

function checkWin(results, bet, prevBalance) {
    const [a, b, c] = results;
    let winAmount = 0;
    let msg = '';
    let cls = 'lose';

    if (a === b && b === c) {
        if (a === '💎' || a === '⭐') {
            winAmount = Math.floor(bet * 4);
            msg = a === '💎' ? '💎 ДЖЕКПОТ ×4' : '⭐ СУПЕР ×4';
            cls = 'bigwin';
        } else if (a === '7️⃣') {
            winAmount = Math.floor(bet * 3);
            msg = '7️⃣ СЧАСТЛИВЧИК ×3';
            cls = 'bigwin';
        } else {
            winAmount = Math.floor(bet * 2.5);
            msg = 'Три в ряд ×2.5';
            cls = 'win';
        }
    }
    else if (a === b || b === c || a === c) {
        winAmount = Math.floor(bet * 1.3);
        msg = 'Пара ×1.3';
        cls = 'win';
    }
    else if ([a,b,c].includes('💎')) {
        winAmount = Math.floor(bet * 1.2);
        msg = '💎 Бриллиант ×1.2';
        cls = 'win';
    }
    else {
        msg = 'Повезёт в следующий раз';
        cls = 'lose';
    }

    updateBalance(prevBalance - bet + winAmount);

    if (winAmount > 0) {
        [s1,s2,s3].forEach(s => s.classList.add('win'));
        setTimeout(() => [s1,s2,s3].forEach(s => s.classList.remove('win')), 700);
    }

    resultDiv.textContent = msg + (winAmount > 0 ? ` +${winAmount} ₴` : '');
    resultDiv.className = 'result ' + cls;

    const uid = getUserId();
    if (uid) {
        fetch('/game_result', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user_id: uid,
                bet: bet,
                win: winAmount - bet,
                symbols: results.join('')
            })
        })
        .then(r => r.json())
        .then(d => {
            if (d.balance !== undefined) {
                updateBalance(d.balance);
            } else {
                loadBalance(true);
            }
        })
        .catch(() => {
            loadBalance(true);
        })
        .finally(() => {
            isSpinning = false;
            spinBtn.disabled = false;
        });
    } else {
        isSpinning = false;
        spinBtn.disabled = false;
    }
}

document.getElementById('betMinus').onclick = () => {
    let v = parseInt(betInput.value) || 25;
    betInput.value = Math.max(25, v - 25);
};

document.getElementById('betPlus').onclick = () => {
    let v = parseInt(betInput.value) || 25;
    betInput.value = Math.min(balance || 25, v + 25);
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

loadBalance(true);

setInterval(() => {
    if (!isSpinning) loadBalance();
}, 12000);
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
                return jsonify({'balance': max(0, user.balance)})
    return jsonify({'balance': 0})

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
            user.balance = max(0, user.balance + win)
            user.games_played += 1
            if win > 0:
                user.total_won += win
            else:
                user.total_lost += abs(win)
            user.last_active = datetime.utcnow()
            db.session.add(GameHistory(user_id=user.id, bet=bet, win=win, symbols=symbols))
            db.session.commit()
            return jsonify({'status': 'ok', 'balance': user.balance})
    return jsonify({'status': 'error', 'balance': 0})

# ========== BOT ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name or 'Игрок'

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🎰 Играть", web_app=WebAppInfo(url=f"{WEBAPP_URL}?user_id={user_id}")),
        InlineKeyboardButton("💳 Пополнить", url=REFILL_LINK)
    )

    bot.send_message(
        message.chat.id,
        f"Добро пожаловать в <b>Casino Royale</b>, {first_name}!\n\n"
        f"Баланс: <b>0 ₴</b>\n"
        f"Минимальная ставка — 25 ₴\n\n"
        f"Пополни баланс и начинай крутить!",
        reply_markup=markup
    )

    try:
        with app.app_context():
            user = User.query.filter_by(telegram_id=user_id).first()
            if not user:
                user = User(
                    telegram_id=user_id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name or '',
                    last_name=message.from_user.last_name or '',
                    balance=0
                )
                db.session.add(user)
                db.session.commit()

            if user.is_admin:
                markup_admin = InlineKeyboardMarkup()
                markup_admin.row(
                    InlineKeyboardButton("🎰 Играть", web_app=WebAppInfo(url=f"{WEBAPP_URL}?user_id={user_id}")),
                    InlineKeyboardButton("💳 Пополнить", url=REFILL_LINK)
                )
                markup_admin.row(InlineKeyboardButton("👑 Админ-панель", callback_data="admin_panel"))
                try:
                    bot.edit_message_reply_markup(message.chat.id, message.message_id + 1, reply_markup=markup_admin)
                except:
                    pass
    except Exception as e:
        print("DB error:", e)

    # Кнопка Open
    try:
        bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=MenuButtonWebApp(
                text="Open",
                web_app=WebAppInfo(url=f"{WEBAPP_URL}?user_id={user_id}")
            )
        )
    except Exception as e:
        print("Menu button error:", e)

@bot.message_handler(commands=['balance'])
def balance_cmd(message):
 mon = str(message.from_user.id)
    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        if user:
            bot.reply_to(message,
                f"💰 Баланс: <b>{max(0, user.balance)} ₴</b>\n"
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

# ========== АДМИНКА ==========
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
            text += f"   ID: <code>{u.telegram_id}</code> · {max(0, u.balance)} ₴\n\n"

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
            f"Баланс: <b>{max(0, user.balance)} ₴</b>\n"
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
                user.balance = max(0, user.balance - amount)
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
