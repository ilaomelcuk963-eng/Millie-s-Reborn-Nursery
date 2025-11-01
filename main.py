from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Настройки для отправки email
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = 'ilaomelcuk963@gmail.com'  # Замените на ваш email
EMAIL_PASSWORD = 'ilaomel2011'  # Замените на пароль приложения

# Файл для хранения данных
DATA_FILE = 'data.json'

def load_data():
    """Загрузка данных из JSON файла"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"comments": [], "orders": []}
    return {"comments": [], "orders": []}

def save_data(data):
    """Сохранение данных в JSON файл"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def send_email(subject, body, to_email):
    """Отправка email через Gmail"""
    try:
        msg = MimeMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MimeText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, to_email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_comments')
def get_comments():
    """Получение всех комментариев"""
    data = load_data()
    return jsonify(data.get("comments", []))

@app.route('/submit_comment', methods=['POST'])
def submit_comment():
    """Добавление нового комментария"""
    try:
        comment_data = request.json
        name = comment_data.get('name', 'Аноним').strip()
        text = comment_data.get('text', '').strip()
        
        if not text:
            return jsonify({'success': False, 'error': 'Текст комментария не может быть пустым'})
        
        data = load_data()
        comments = data.get("comments", [])
        
        new_comment = {
            'id': len(comments) + 1,
            'name': name,
            'text': text,
            'date': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'timestamp': datetime.now().isoformat()
        }
        
        comments.append(new_comment)
        data["comments"] = comments
        save_data(data)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Ошибка добавления комментария: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/submit_order', methods=['POST'])
def submit_order():
    """Обработка нового заказа"""
    try:
        order_data = request.json
        name = order_data.get('name', '').strip()
        email = order_data.get('email', '').strip()
        phone = order_data.get('phone', '').strip()
        doll_type = order_data.get('dollType', '').strip()
        description = order_data.get('description', '').strip()
        
        # Валидация данных
        if not all([name, email, phone, doll_type, description]):
            return jsonify({'success': False, 'error': 'Все поля обязательны для заполнения'})
        
        # Сохранение заказа в JSON
        data = load_data()
        orders = data.get("orders", [])
        
        new_order = {
            'id': len(orders) + 1,
            'name': name,
            'email': email,
            'phone': phone,
            'doll_type': doll_type,
            'description': description,
            'date': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'timestamp': datetime.now().isoformat(),
            'status': 'новый'
        }
        
        orders.append(new_order)
        data["orders"] = orders
        save_data(data)
        
        # Отправка email владельцу
        order_text = f"""
        НОВЫЙ ЗАКАЗ КУКЛЫ!
        
        Детали заказа:
        • Имя: {name}
        • Email: {email}
        • Телефон: {phone}
        • Тип куклы: {doll_type}
        • Описание: {description}
        
        Дата заказа: {datetime.now().strftime('%d.%m.%Y в %H:%M')}
        ID заказа: {new_order['id']}
        
        Не забудьте связаться с клиентом в ближайшее время!
        """
        
        owner_email_sent = send_email(
            subject=f'Новый заказ куклы №{new_order["id"]}',
            body=order_text,
            to_email=EMAIL_USER
        )
        
        # Отправка подтверждения клиенту
        confirmation_text = f"""
        Уважаемый(ая) {name}!
        
        Благодарим Вас за заказ авторской куклы в нашей мастерской!
        
        Мы получили Ваш заказ:
        • Тип куклы: {doll_type}
        • Ваши пожелания: {description}
        
        Номер Вашего заказа: {new_order['id']}
        
        В течение 24 часов мы свяжемся с Вами для уточнения деталей 
        и обсуждения сроков выполнения заказа.
        
        С уважением,
        Мастерская авторских кукол
        Телефон: +7 (999) 123-45-67
        Email: dolls@example.com
        """
        
        client_email_sent = send_email(
            subject='Подтверждение заказа авторской куклы',
            body=confirmation_text,
            to_email=email
        )
        
        return jsonify({
            'success': True, 
            'order_id': new_order['id'],
            'owner_email_sent': owner_email_sent,
            'client_email_sent': client_email_sent
        })
        
    except Exception as e:
        print(f"Ошибка обработки заказа: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_orders')
def get_orders():
    """Получение списка заказов (для админки)"""
    data = load_data()
    return jsonify(data.get("orders", []))

if __name__ == '__main__':
    # Создаем начальную структуру данных, если файла нет
    if not os.path.exists(DATA_FILE):
        save_data({"comments": [], "orders": []})
    
    print("Сервер запускается...")
    print("Доступные эндпоинты:")
    print("- GET  / - главная страница")
    print("- GET  /get_comments - получение комментариев")
    print("- POST /submit_comment - добавление комментария")
    print("- POST /submit_order - оформление заказа")
    print("- GET  /get_orders - получение заказов (админка)")
    
    app.run(debug=True, host='0.0.0.0', port=5000)  