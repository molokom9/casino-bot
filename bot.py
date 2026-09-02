import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import threading
import os
import json
import sys
import traceback

# ========== ЛОГИРОВАНИЕ ОШИБОК ==========
def log_error(e):
    print("=" * 60)
    print("ОШИБКА:")
    print(str(e))
    print("Трассировка:")
    traceback.print_exc()
    print("=" * 60)
    sys.stdout.flush()

try:
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

    # Создаем таблицы и админа
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
    <title>🎰 CASINO</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{background:radial-gradient(#0a0015,#1a0030);min-height:100vh;display:flex;justify-content:center;align-items:center;padding:12px}
    .container{background:linear-gradient(145deg,rgba(20,0,40,0.97),rgba(10,0,20,0.99));border-radius:32px;padding:24px 20px;max-width:420px;width:100%;border:1px solid rgba(255,215,0,0.15);box-shadow:0 20px 60px rgba(0,0,0,0.8)}
    .header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
    .logo-text{font-size:24px;font-weight:900;background:linear-gradient(135deg,#ffd700,#ff6b00);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
    .status-dot{width:8px;height:8px;background:#00ff88;border-radius:50%;display:inline-block;animation:blink 1.5s infinite}
    @keyframes blink{0%,100%{opacity:1}50%{opacity:0.3}}
    .balance-card{background:rgba(255,215,0,0.05);border:1px solid rgba(255,215,0,0.1);border-radius:16px;padding:14px 20px;margin-bottom:18px;display:flex;justify-content:space-between}
    .balance-label{color:rgba(255,215,0,0.6);font-size:12px;text-transform:uppercase;letter-spacing:2px}
    .balance-value{font-size:28px;font-weight:900;color:#ffd700}
    .slots-container{background:rgba(0,0,0,0.5);border-radius:20px;padding:20px;margin-bottom:18px}
    .slots{display:flex;justify-content:space-around}
    .slot{width:80px;height:80px;background:linear-gradient(145deg,#1a0030,#0a0015);border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:44px;border:2px solid rgba(255,215,0,0.1);transition:all 0.3s}
    .slot.spinning{animation:spin 0.6s;border-color:#ffd700}
    @keyframes spin{0%{transform:rotateX(0)}50%{transform:rotateX(180deg)}100%{transform:rotateX(360deg)}}
    .slot.win{border-color:#00ff88;box-shadow:0 0 40px rgba(0,255,136,0.3)}
    .bet-control{display:flex;align-items:center;justify-content:center;gap:12px;margin-bottom:12px}
    .bet-control label{color:rgba(255,215,0,0.5);font-size:12px;text-transform:uppercase;letter-spacing:1px}
    .bet-input{background:rgba(0,0,0,0.4);border:1px solid rgba(255,215,0,0.1);border-radius:10px;color:#ffd700;font-size:18px;font-weight:700;text-align:center;width:80px;padding:8px;outline:none}
    .btn-spin{background:linear-gradient(135deg,#ffd700,#f7971e);color:#0a0015;border:none;padding:16px;font-size:20px;font-weight:900;border-radius:16px;cursor:pointer;width:100%;transition:0.3s;text-transform:uppercase;letter-spacing:2px}
    .btn-spin:hover:not(:disabled){transform:scale(1.02);box-shadow:0 8px 40px rgba(255,215,0,0.3)}
    .btn-spin:disabled{opacity:0.5;cursor:not-allowed}
    .result{text-align:center;font-size:18px;font-weight:700;min-height:44px;padding:10px;border-radius:12px;margin-bottom:14px;background:rgba(0,0,0,0.3)}
    .result.win{color:#00ff88;border:1px solid rgba(0,255,136,0.2)}
    .result.lose{color:#ff2d55;border:1px solid rgba(255,45,85,0.2)}
    .result.bigwin{color:#ffd700;border:1px solid rgba(255,215,0,0.3);animation:big 0.8s}
    @keyframes big{0%{transform:scale(0.8)}50%{transform:scale(1.1)}100%{transform:scale(1)}}
    .history-section{margin-top:8px;padding-top:14px;border-top:1px solid rgba(255,215,0,0.06)}
    #historyList{max-height:130px;overflow-y:auto}
    .history-item{padding:6px 12px;background:rgba(255,255,255,0.02);border-radius:8px;display:flex;justify-content:space-between;margin:4px 0;font-size:13px}
    .history-item .positive{color:#00ff88}
    .history-item .negative{color:#ff2d55}
    .btn-close{width:100%;padding:12px;background:rgba(255,255,255,0.03);color:rgba(255,255,255,0.3);border:1px solid rgba(255,255,255,0.05);border-radius:12px;cursor:pointer;margin-top:14px;transition:0.3s}
    .btn-close:hover{background:rgba(255,255,255,0.05)}
    .footer{text-align:center;margin-top:10px;font-size:9px;color:rgba(255,215,0,0.1);letter-spacing:2px}
    @media(max-width:420px){.slot{width:65px;height:65px;font-size:36px}}
    </style>
    </head>
    <body>
    <div class="container">
    <div class="header"><span class="logo-text">🎰 CASINO</span><span><span class="status-dot"></span> LIVE</span></div>
    <div class="balance-card"><span class="balance-label">💰 Баланс</span><span class="balance-value" id="balance">1000</span></div>
    <div class="slots-container"><div class="slots"><div class="slot" id="slot1">🍒</div><div class="slot" id="slot2">🍋</div><div class="slot" id="slot3">🍒</div></div></div>
    <div class="bet-control"><label>Ставка</label><input type="number" class="bet-input" id="betAmount" value="10" min="1"></div>
    <button class="btn-spin" id="spinBtn">🎰 SPIN</button>
    <div id="result" class="result">Нажми SPIN</div>
    <div class="history-section"><div id="historyList"></div></div>
    <button class="btn-close" id="closeBtn">✖ Закрыть</button>
    <div class="footer">18+ · Играй ответственно</div>
    </div>
    <script>
    const tg=window.Telegram.WebApp;tg.expand();
    let balance=1000,isSpinning=false;
    const symbols=['🍒','🍋','🍊','🍇','💎','7️⃣','⭐'];
    const s1=document.getElementById('slot1'),s2=document.getElementById('slot2'),s3=document.getElementById('slot3');
    const spinBtn=document.getElementById('spinBtn'),betInput=document.getElementById('betAmount');
    const resultDiv=document.getElementById('result'),balanceSpan=document.getElementById('balance');
    const historyList=document.getElementById('historyList');
    
    function getUserId(){const p=new URLSearchParams(window.location.search);return p.get('user_id')||'';}
    function updateBalance(b){balance=b;balanceSpan.textContent=balance;}
    
    function addHistory(s,a){const d=document.createElement('div');d.className='history-item';const sign=a>=0?'+':'';const cls=a>=0?'positive':'negative';d.innerHTML='<span>'+s+'</span><span class="'+cls+'">'+sign+a+'</span>';historyList.prepend(d);if(historyList.children.length>15)historyList.removeChild(historyList.lastChild);}
    
    function spinSlots(){
    if(isSpinning)return;
    const bet=parseInt(betInput.value)||0;
    if(bet<=0||bet>balance){resultDiv.textContent='❌ Неверная ставка!';resultDiv.className='result lose';return;}
    isSpinning=true;spinBtn.disabled=true;resultDiv.textContent='🌀 SPIN...';resultDiv.className='result';
    const slots=[s1,s2,s3];slots.forEach(s=>s.classList.add('spinning'));
    const r=slots.map(()=>symbols[Math.floor(Math.random()*symbols.length)]);
    setTimeout(()=>{
    slots.forEach((s,i)=>{s.textContent=r[i];s.classList.remove('spinning');});
    const[r1,r2,r3]=r;let win=0,msg='',cls='lose',big=false;
    if(r1===r2&&r2===r3){
    if(r1==='💎'){win=bet*15;msg='💎 ДЖЕКПОТ! x15';cls='bigwin';big=true;}
    else if(r1==='7️⃣'){win=bet*10;msg='7️⃣ СЧАСТЛИВЧИК! x10';cls='bigwin';big=true;}
    else if(r1==='⭐'){win=bet*20;msg='⭐ СУПЕР! x20';cls='bigwin';big=true;}
    else{win=bet*5;msg='🎉 ТРИ '+r1+'! x5';cls='win';}
    }else if(r1===r2||r2===r3||r1===r3){win=bet*2;msg='✨ ПАРА! x2';cls='win';}
    else if(r1==='💎'||r2==='💎'||r3==='💎'){win=bet*1.5;msg='💎 БРИЛЛИАНТ!';cls='win';}
    else if(r1==='⭐'||r2==='⭐'||r3==='⭐'){win=bet*3;msg='⭐ ЗВЕЗДА! x3';cls='win';}
    else{win=0;msg='😔 Повезет в следующий раз';cls='lose';}
    const net=win-bet;balance+=net;updateBalance(balance);
    if(net>0){slots.forEach(s=>s.classList.add('win'));setTimeout(()=>slots.forEach(s=>s.classList.remove('win')),800);}
    resultDiv.textContent=msg+' '+(net>0?'+':'')+net;resultDiv.className='result '+cls;
    addHistory(r.join(' '),net);
    fetch('/game_result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:getUserId(),bet,win:net,symbols:r.join('')})});
    isSpinning=false;spinBtn.disabled=false;
    },600);}
    
    function loadBalance(){const id=getUserId();if(id){fetch('/get_balance?user_id='+id).then(r=>r.json()).then(d=>{if(d.balance!==undefined)updateBalance(d.balance);}).catch(()=>{});}}
    setInterval(loadBalance,10000);
    spinBtn.addEventListener('click',spinSlots);
    document.getElementById('closeBtn').addEventListener('click',()=>tg.close());
    betInput.addEventListener('change',()=>{let v=parseInt(betInput.value)||10;if(v<1)v=1;if(v>balance)v=balance;betInput.value=v;});
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
            f"🎲 Добро пожаловать в Casino, {message.from_user.first_name}!\n\n"
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
                    f"💰 Баланс: {user.balance}\n"
                    f"🏆 Выиграно: {user.total_won}\n"
                    f"💔 Проиграно: {user.total_lost}\n"
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
            "👑 Админ-панель\nВыберите действие:",
            reply_markup=markup
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
                bot.send_message(call.message.chat.id, "Введите ID и сумму: `123456789 100`", parse_mode='Markdown')
                bot.register_next_step_handler(call.message, admin_give_currency)
            
            elif call.data == "admin_take":
                bot.send_message(call.message.chat.id, "Введите ID и сумму: `123456789 50`", parse_mode='Markdown')
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
                    bot.send_message(message.chat.id, f"✅ Выдано {amount} пользователю {user.first_name}")
                else:
                    bot.send_message(message.chat.id, "❌ Пользователь не найден")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

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
                        bot.send_message(message.chat.id, f"✅ Забрано {amount} у {user.first_name}")
                    else:
                        bot.send_message(message.chat.id, "❌ Недостаточно средств")
                else:
                    bot.send_message(message.chat.id, "❌ Пользователь не найден")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

    def admin_get_user_info(message):
        try:
            user_id = message.text.strip()
            with app.app_context():
                user = User.query.filter_by(telegram_id=user_id).first()
                if user:
                    bot.send_message(
                        message.chat.id,
                        f"👤 Информация\n"
                        f"ID: {user.telegram_id}\n"
                        f"Имя: {user.first_name}\n"
                        f"💰 Баланс: {user.balance}\n"
                        f"🎮 Игр: {user.games_played}\n"
                        f"🏆 Выиграно: {user.total_won}\n"
                        f"💔 Проиграно: {user.total_lost}"
                    )
                else:
                    bot.send_message(message.chat.id, "❌ Пользователь не найден")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

    def show_top_players(message):
        with app.app_context():
            top = User.query.order_by(User.balance.desc()).limit(10).all()
            text = "🏆 Топ игроков\n\n"
            for i, user in enumerate(top, 1):
                text += f"{i}. {user.first_name} — {user.balance}💰\n"
            bot.send_message(message.chat.id, text)

    @bot.message_handler(commands=['balance'])
    def balance_command(message):
        user_id = str(message.from_user.id)
        with app.app_context():
            user = User.query.filter_by(telegram_id=user_id).first()
            if user:
                bot.send_message(
                    message.chat.id,
                    f"💰 Баланс: {user.balance}\n"
                    f"🏆 Выиграно: {user.total_won}\n"
                    f"💔 Проиграно: {user.total_lost}\n"
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

except Exception as e:
    log_error(e)
    raise
