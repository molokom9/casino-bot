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
ADMIN_ID = '8663798936'

# ========== БОТ ==========
bot = telebot.TeleBot(BOT_TOKEN)

# ========== ВЕБ-СЕРВЕР ==========
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///casino.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
init_db(app)

# ========== HTML СТРАНИЦА ==========
HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>🎰 CASINO ROYALE</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
        body{font-family:Arial,sans-serif;background:radial-gradient(ellipse at center,#0a0015 0%,#1a0030 50%,#0a0015 100%);min-height:100vh;display:flex;justify-content:center;align-items:center;padding:12px;overflow:hidden}
        .container{background:linear-gradient(145deg,rgba(20,0,40,0.97),rgba(10,0,20,0.99));border-radius:32px;padding:24px 20px 20px;max-width:420px;width:100%;border:1px solid rgba(255,215,0,0.15);box-shadow:0 0 80px rgba(255,215,0,0.05),inset 0 0 80px rgba(255,215,0,0.03),0 20px 60px rgba(0,0,0,0.8);position:relative;z-index:1}
        .container::before{content:'';position:absolute;top:-2px;left:-2px;right:-2px;bottom:-2px;background:conic-gradient(from 0deg,transparent,rgba(255,215,0,0.3),rgba(255,215,0,0.6),rgba(255,215,0,0.3),transparent);border-radius:34px;z-index:-1;animation:borderRotate 4s linear infinite}
        @keyframes borderRotate{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
        .header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
        .logo{display:flex;align-items:center;gap:8px}
        .logo-icon{font-size:28px;animation:pulse 2s ease-in-out infinite}
        @keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.1)}}
        .logo-text{font-size:20px;font-weight:900;background:linear-gradient(135deg,#ffd700,#ff6b00);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:2px}
        .status-dot{width:8px;height:8px;background:#00ff88;border-radius:50%;display:inline-block;animation:blink 1.5s ease-in-out infinite;box-shadow:0 0 10px rgba(0,255,136,0.5)}
        @keyframes blink{0%,100%{opacity:1}50%{opacity:0.3}}
        .balance-card{background:linear-gradient(135deg,rgba(255,215,0,0.08),rgba(255,215,0,0.02));border:1px solid rgba(255,215,0,0.12);border-radius:16px;padding:14px 20px;margin-bottom:18px;display:flex;justify-content:space-between;align-items:center;position:relative;overflow:hidden}
        .balance-card::before{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle,rgba(255,215,0,0.03) 0%,transparent 70%);animation:shimmer 3s ease-in-out infinite}
        @keyframes shimmer{0%{transform:translateX(-100%) translateY(-100%)}100%{transform:translateX(100%) translateY(100%)}}
        .balance-label{color:rgba(255,215,0,0.6);font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:2px;position:relative;z-index:1}
        .balance-value{font-size:26px;font-weight:900;color:#ffd700;text-shadow:0 0 30px rgba(255,215,0,0.2);position:relative;z-index:1}
        .balance-value .currency{font-size:16px;opacity:0.7}
        .slots-container{background:rgba(0,0,0,0.5);border-radius:20px;padding:20px;margin-bottom:18px;border:1px solid rgba(255,215,0,0.06)}
        .slots{display:flex;justify-content:space-around;align-items:center;gap:10px}
        .slot-wrapper{flex:1;display:flex;justify-content:center}
        .slot{width:80px;height:80px;background:linear-gradient(145deg,#1a0030,#0a0015);border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:44px;border:2px solid rgba(255,215,0,0.1);box-shadow:inset 0 0 30px rgba(255,215,0,0.03),0 4px 20px rgba(0,0,0,0.5);transition:all 0.3s cubic-bezier(0.4,0,0.2,1);user-select:none}
        .slot::after{content:'';position:absolute;inset:2px;border-radius:14px;background:linear-gradient(135deg,rgba(255,215,0,0.05),transparent);pointer-events:none}
        .slot.spinning{animation:slotSpin 0.6s cubic-bezier(0.4,0,0.2,1);border-color:#ffd700;box-shadow:0 0 50px rgba(255,215,0,0.3),inset 0 0 50px rgba(255,215,0,0.05)}
        @keyframes slotSpin{0%{transform:rotateX(0deg) scale(1)}20%{transform:rotateX(180deg) scale(1.1)}40%{transform:rotateX(360deg) scale(1)}60%{transform:rotateX(540deg) scale(1.1)}80%{transform:rotateX(720deg) scale(1)}100%{transform:rotateX(720deg) scale(1)}}
        .slot.win-highlight{border-color:#00ff88;box-shadow:0 0 40px rgba(0,255,136,0.3);animation:winGlow 0.8s ease}
        @keyframes winGlow{0%,100%{box-shadow:0 0 40px rgba(0,255,136,0.3)}50%{box-shadow:0 0 80px rgba(0,255,136,0.6)}}
        .controls{margin-bottom:16px}
        .bet-control{display:flex;align-items:center;justify-content:center;gap:12px;margin-bottom:12px}
        .bet-control label{color:rgba(255,215,0,0.5);font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:1.5px}
        .bet-input-group{display:flex;align-items:center;gap:6px;background:rgba(0,0,0,0.4);border-radius:12px;padding:4px;border:1px solid rgba(255,215,0,0.08)}
        .bet-btn{background:rgba(255,215,0,0.08);border:none;color:#ffd700;width:32px;height:32px;border-radius:8px;font-size:18px;font-weight:700;cursor:pointer;transition:all 0.2s}
        .bet-btn:hover{background:rgba(255,215,0,0.15)}
        .bet-btn:active{transform:scale(0.9)}
        .bet-input{background:transparent;border:none;color:#ffd700;font-size:16px;font-weight:700;text-align:center;width:70px;padding:6px 0;outline:none}
        .bet-input::-webkit-inner-spin-button{-webkit-appearance:none}
        .bet-input::-webkit-outer-spin-button{-webkit-appearance:none}
        .bet-input[type=number]{-moz-appearance:textfield}
        .btn-spin{background:linear-gradient(135deg,#ffd700,#f7971e);color:#0a0015;border:none;padding:16px 24px;font-size:20px;font-weight:900;border-radius:16px;cursor:pointer;width:100%;transition:all 0.3s cubic-bezier(0.4,0,0.2,1);text-transform:uppercase;letter-spacing:2px;position:relative;overflow:hidden}
        .btn-spin::before{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle,rgba(255,255,255,0.2) 0%,transparent 60%);animation:spinShimmer 3s ease-in-out infinite}
        @keyframes spinShimmer{0%{transform:translateX(-100%) translateY(-100%)}100%{transform:translateX(100%) translateY(100%)}}
        .btn-spin:hover:not(:disabled){transform:translateY(-2px) scale(1.02);box-shadow:0 8px 40px rgba(255,215,0,0.3)}
        .btn-spin:active:not(:disabled){transform:scale(0.97)}
        .btn-spin:disabled{opacity:0.5;cursor:not-allowed;transform:none}
        .result{text-align:center;font-size:18px;font-weight:700;min-height:44px;padding:10px 16px;border-radius:12px;margin-bottom:14px;background:rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;gap:8px;transition:all 0.3s}
        .result.win{color:#00ff88;background:rgba(0,255,136,0.06);border:1px solid rgba(0,255,136,0.15);animation:resultWin 0.6s ease}
        .result.lose{color:#ff2d55;background:rgba(255,45,85,0.06);border:1px solid rgba(255,45,85,0.15)}
        .result.bigwin{color:#ffd700;background:rgba(255,215,0,0.08);border:1px solid rgba(255,215,0,0.2);animation:resultBigWin 1s ease}
        @keyframes resultWin{0%{transform:scale(0.8);opacity:0}50%{transform:scale(1.05)}100%{transform:scale(1);opacity:1}}
        @keyframes resultBigWin{0%{transform:scale(0.7) rotate(-5deg);opacity:0}30%{transform:scale(1.2) rotate(3deg)}60%{transform:scale(0.95) rotate(-2deg)}100%{transform:scale(1) rotate(0deg);opacity:1}}
        .history-section{margin-top:8px;padding-top:14px;border-top:1px solid rgba(255,215,0,0.06)}
        .history-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
        .history-header h3{color:rgba(255,215,0,0.4);font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:2px}
        .history-header span{color:rgba(255,215,0,0.2);font-size:10px}
        #historyList{max-height:130px;overflow-y:auto;display:flex;flex-direction:column;gap:4px}
        #historyList::-webkit-scrollbar{width:3px}
        #historyList::-webkit-scrollbar-track{background:rgba(255,215,0,0.03);border-radius:2px}
        #historyList::-webkit-scrollbar-thumb{background:rgba(255,215,0,0.15);border-radius:2px}
        .history-item{padding:6px 12px;background:rgba(255,255,255,0.02);border-radius:8px;display:flex;justify-content:space-between;align-items:center;font-size:13px;border-left:2px solid rgba(255,215,0,0.1);animation:slideIn 0.3s ease}
        @keyframes slideIn{0%{transform:translateX(-20px);opacity:0}100%{transform:translateX(0);opacity:1}}
        .history-item .symbols{color:rgba(255,255,255,0.6);font-size:16px;letter-spacing:2px}
        .history-item .amount{font-weight:700;font-size:14px}
        .history-item .amount.positive{color:#00ff88}
        .history-item .amount.negative{color:#ff2d55}
        .btn-close{width:100%;padding:12px;background:rgba(255,255,255,0.03);color:rgba(255,255,255,0.2);border:1px solid rgba(255,255,255,0.05);border-radius:12px;font-size:13px;font-weight:600;cursor:pointer;margin-top:14px;transition:all 0.3s;text-transform:uppercase;letter-spacing:2px}
        .btn-close:hover{background:rgba(255,255,255,0.05);color:rgba(255,255,255,0.4)}
        .btn-close:active{transform:scale(0.97)}
        .footer{text-align:center;margin-top:10px;font-size:9px;color:rgba(255,215,0,0.12);letter-spacing:2px;text-transform:uppercase}
        .confetti-container{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:1000;overflow:hidden}
        .confetti{position:absolute;width:10px;height:10px;animation:confettiFall linear forwards}
        @keyframes confettiFall{0%{transform:translateY(-10vh) rotate(0deg);opacity:1}100%{transform:translateY(110vh) rotate(720deg);opacity:0}}
        @media(max-width:420px){.container{padding:16px 14px 14px;border-radius:24px}.slot{width:65px;height:65px;font-size:36px}.balance-value{font-size:22px}.btn-spin{font-size:17px;padding:14px 20px}}
        @media(max-width:360px){.slot{width:55px;height:55px;font-size:30px}.bet-input{width:55px;font-size:14px}}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="logo"><span class="logo-icon">🎰</span><span class="logo-text">CASINO</span></div>
        <div style="display:flex;align-items:center;gap:8px;"><span class="status-dot"></span><span style="color:rgba(255,255,255,0.15);font-size:9px;letter-spacing:1px;">LIVE</span></div>
    </div>
    <div class="balance-card">
        <span class="balance-label">💰 Баланс</span>
        <span class="balance-value" id="balance">1000 <span class="currency">₽</span></span>
    </div>
    <div class="slots-container">
        <div class="slots">
            <div class="slot-wrapper"><div class="slot" id="slot1">🍒</div></div>
            <div class="slot-wrapper"><div class="slot" id="slot2">🍋</div></div>
            <div class="slot-wrapper"><div class="slot" id="slot3">🍒</div></div>
        </div>
    </div>
    <div class="controls">
        <div class="bet-control">
            <label>Ставка</label>
            <div class="bet-input-group">
                <button class="bet-btn" id="betHalf">½</button>
                <input type="number" class="bet-input" id="betAmount" value="10" min="1" max="10000">
                <button class="bet-btn" id="betDouble">2×</button>
            </div>
        </div>
        <button class="btn-spin" id="spinBtn">🎰 SPIN</button>
    </div>
    <div id="result" class="result">🎲 Нажми SPIN чтобы начать</div>
    <div class="history-section">
        <div class="history-header"><h3>📜 История</h3><span id="historyCount">0</span></div>
        <div id="historyList"></div>
    </div>
    <button class="btn-close" id="closeBtn">✖ Закрыть</button>
    <div class="footer">18+ · Играй ответственно · Только развлечение</div>
</div>
<script>
const tg=window.Telegram.WebApp;tg.expand();
let balance=1000,isSpinning=false;
const symbols=['🍒','🍋','🍊','🍇','💎','7️⃣','⭐','🎰'];
const slot1=document.getElementById('slot1'),slot2=document.getElementById('slot2'),slot3=document.getElementById('slot3');
const spinBtn=document.getElementById('spinBtn'),betInput=document.getElementById('betAmount');
const betHalf=document.getElementById('betHalf'),betDouble=document.getElementById('betDouble');
const resultDiv=document.getElementById('result'),balanceSpan=document.getElementById('balance');
const historyList=document.getElementById('historyList'),historyCount=document.getElementById('historyCount');

function getRandomSymbol(){return symbols[Math.floor(Math.random()*symbols.length)];}
function getUserId(){const p=new URLSearchParams(window.location.search);return p.get('user_id')||'';}
function updateBalance(b){balance=b;balanceSpan.textContent=balance+' ₽';}
function addHistoryItem(s,a){const i=document.createElement('div');i.className='history-item';const sign=a>=0?'+':'';const cn=a>=0?'positive':'negative';i.innerHTML='<span class="symbols">'+s+'</span><span class="amount '+cn+'">'+sign+a+' ₽</span>';historyList.prepend(i);while(historyList.children.length>20)historyList.removeChild(historyList.lastChild);historyCount.textContent=historyList.children.length;}
function showConfetti(){const c=['#ffd700','#ff2d55','#00d4ff','#00ff88','#ff6b00','#a855f7'];const container=document.createElement('div');container.className='confetti-container';document.body.appendChild(container);for(let i=0;i<100;i++){const confetti=document.createElement('div');confetti.className='confetti';confetti.style.left=Math.random()*100+'%';confetti.style.background=c[Math.floor(Math.random()*c.length)];confetti.style.width=(Math.random()*8+4)+'px';confetti.style.height=(Math.random()*8+4)+'px';confetti.style.borderRadius=Math.random()>0.5?'50%':'2px';confetti.style.animationDuration=(Math.random()*2+2)+'s';confetti.style.animationDelay=(Math.random()*1.5)+'s';container.appendChild(confetti);}setTimeout(()=>{container.remove();},4000);}

function spinSlots(){if(isSpinning)return;const bet=parseInt(betInput.value)||0;if(bet<=0||bet>balance){resultDiv.textContent='❌ Неверная ставка!';resultDiv.className='result lose';return;}
isSpinning=true;spinBtn.disabled=true;resultDiv.textContent='🌀 SPIN...';resultDiv.className='result';
const slots=[slot1,slot2,slot3];slots.forEach(s=>s.classList.add('spinning'));
const results=slots.map(()=>getRandomSymbol());
setTimeout(()=>{slots.forEach((s,i)=>{s.textContent=results[i];s.classList.remove('spinning');});
const[r1,r2,r3]=results;let win=0,msg='',className='lose',isBigWin=false;
if(r1===r2&&r2===r3){if(r1==='💎'){win=bet*15;msg='💎💎💎 ДЖЕКПОТ! x15!';className='bigwin';isBigWin=true;}else if(r1==='7️⃣'){win=bet*10;msg='7️⃣7️⃣7️⃣ СЧАСТЛИВЧИК! x10!';className='bigwin';isBigWin=true;}else if(r1==='⭐'){win=bet*20;msg='⭐⭐⭐ СУПЕР ДЖЕКПОТ! x20!';className='bigwin';isBigWin=true;}else if(r1==='🎰'){win=bet*30;msg='🎰🎰🎰 МЕГА ДЖЕКПОТ! x30!';className='bigwin';isBigWin=true;}else{win=bet*5;msg='🎉 ТРИ '+r1+'! x5!';className='win';}}else if(r1===r2||r2===r3||r1===r3){win=bet*2;msg='✨ ПАРА! x2!';className='win';}else if(r1==='💎'||r2==='💎'||r3==='💎'){win=bet*1.5;msg='💎 БРИЛЛИАНТ! x1.5!';className='win';}else if(r1==='⭐'||r2==='⭐'||r3==='⭐'){win=bet*3;msg='⭐ ЗВЕЗДА! x3!';className='win';}else if(r1==='🎰'||r2==='🎰'||r3==='🎰'){win=bet*5;msg='🎰 СЛОТ! x5!';className='win';}else{win=0;msg='😔 Повезет в следующий раз!';className='lose';}
const net=win-bet;balance+=net;updateBalance(balance);
if(net>0){slots.forEach(s=>s.classList.add('win-highlight'));setTimeout(()=>{slots.forEach(s=>s.classList.remove('win-highlight'));},800);}
if(isBigWin)showConfetti();
const sign=net>0?'+':'';resultDiv.textContent=msg+' '+sign+net+' ₽';resultDiv.className='result '+className;
addHistoryItem(results.join(' '),net);
const userId=getUserId();if(userId){fetch('/game_result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:userId,bet:bet,win:net,symbols:results.join('')})});}
isSpinning=false;spinBtn.disabled=false;},700);}

function loadBalance(){const userId=getUserId();if(userId){fetch('/get_balance?user_id='+userId).then(res=>res.json()).then(data=>{if(data.balance!==undefined)updateBalance(data.balance);}).catch(()=>{});}}
setInterval(loadBalance,10000);

spinBtn.addEventListener('click',spinSlots);
betHalf.addEventListener('click',()=>{let val=parseInt(betInput.value)||10;val=Math.floor(val/2);if(val<1)val=1;betInput.value=val;});
betDouble.addEventListener('click',()=>{let val=parseInt(betInput.value)||10;val=Math.min(val*2,balance);if(val<1)val=1;betInput.value=val;});
betInput.addEventListener('change',()=>{let val=parseInt(betInput.value)||10;if(val<1)val=1;if(val>balance)val=balance;betInput.value=val;});
document.getElementById('closeBtn').addEventListener('click',()=>tg.close());
loadBalance();
</script>
</body>
</html>
'''

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
        InlineKeyboardButton("🔙 Назад", callback_data="back")
    )
    
    bot.send_message(
        message.chat.id,
        "👑 **Админ-панель**\n\nВыберите действие:",
        reply_markup=markup,
        parse_mode='Markdown'
    )

def handle_admin_action(call, admin):
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
                bot.send_message(message.chat.id, "❌ Пользова
