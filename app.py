from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Разрешить запросы с других доменов

# Настройки для отправки email
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = 'your_email@gmail.com'  # Замените на ваш email
EMAIL_PASSWORD = 'your_app_password'  # Замените на пароль приложения

# Файл для хранения комментариев
COMMENTS_FILE = 'comments.json'

# Загрузка комментариев из файла
def load_comments():
    if os.path.exists(COMMENTS_FILE):
        with open(COMMENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Сохранение комментариев в файл
def save_comments(comments):
    with open(COMMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)

# Отправка email
def send_email(subject, body, to_email):
    try:
        # Создание сообщения
        msg = MimeMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Добавление текста сообщения
        msg.attach(MimeText(body, 'plain', 'utf-8'))
        
        # Отправка сообщения
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, to_email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Получение комментариев
@app.route('/get_comments', methods=['GET'])
def get_comments():
    comments = load_comments()
    return jsonify(comments)

# Добавление комментария
@app.route('/submit_comment', methods=['POST'])
def submit_comment():
    try:
        data = request.json
        name = data.get('name', 'Аноним')
        text = data.get('text', '')
        
        if not text:
            return jsonify({'success': False, 'error': 'Текст комментария не может быть пустым'})
        
        # Загрузка существующих комментариев
        comments = load_comments()
        
        # Добавление нового комментария
        new_comment = {
            'id': len(comments) + 1,
            'name': name,
            'text': text,
            'date': datetime.now().strftime('%d.%m.%Y %H:%M')
        }
        
        comments.append(new_comment)
        
        # Сохранение комментариев
        save_comments(comments)
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Error submitting comment: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Обработка заказа
@app.route('/submit_order', methods=['POST'])
def submit_order():
    try:
        data = request.json
        name = data.get('name', '')
        email = data.get('email', '')
        phone = data.get('phone', '')
        doll_type = data.get('dollType', '')
        description = data.get('description', '')
        
        # Проверка обязательных полей
        if not name or not email or not phone or not doll_type or not description:
            return jsonify({'success': False, 'error': 'Все поля обязательны для заполнения'})
        
        # Формирование текста заказа
        order_text = f"""
        Новый заказ куклы!
        
        Имя: {name}
        Email: {email}
        Телефон: {phone}
        Тип куклы: {doll_type}
        Описание: {description}
        
        Дата заказа: {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        # Отправка email с заказом
        email_sent = send_email(
            subject='Новый заказ куклы',
            body=order_text,
            to_email=EMAIL_USER  # Отправка на email владельца
        )
        
        # Также отправка подтверждения клиенту
        if email_sent:
            confirmation_text = f"""
            Уважаемый(ая) {name},
            
            Благодарим вас за заказ куклы в нашем магазине!
            
            Мы получили ваш заказ:
            Тип куклы: {doll_type}
            Описание: {description}
            
            В ближайшее время мы свяжемся с вами для уточнения деталей.
            
            С уважением,
            Команда "Авторские куклы на заказ"
            """
            
            send_email(
                subject='Подтверждение заказа куклы',
                body=confirmation_text,
                to_email=email
            )
        
        return jsonify({'success': True, 'email_sent': email_sent})
    
    except Exception as e:
        print(f"Error submitting order: {e}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Создание файла для комментариев, если его нет
    if not os.path.exists(COMMENTS_FILE):
        save_comments([])
    
    app.run(debug=True, host='0.0.0.0', port=5000)