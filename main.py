from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import json
import os
from datetime import datetime
from mega import Mega

app = Flask(__name__)
CORS(app)

# Настройки для отправки email
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = 'ilaomelcuk963@gmail.com'
EMAIL_PASSWORD = 'ilaomel2011'

# Настройки Mega - ВАШИ ДАННЫЕ
MEGA_EMAIL = 'asuhop666@gmail.com'
MEGA_PASSWORD = 'millie_13Dark20'

# Локальный файл для кеширования
LOCAL_DATA_FILE = 'data.json'

class MegaStorage:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.mega = Mega()
        self.remote_filename = 'dolls_website_data.json'
        
    def login(self):
        """Авторизация в Mega"""
        try:
            self.m = self.mega.login(self.email, self.password)
            print("✅ Успешная авторизация в Mega")
            return True
        except Exception as e:
            print(f"❌ Ошибка авторизации в Mega: {e}")
            return False
    
    def upload_data(self, data):
        """Загрузка данных в Mega"""
        try:
            # Сохраняем данные во временный файл
            with open(LOCAL_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Загружаем файл в Mega
            file = self.m.upload(LOCAL_DATA_FILE)
            
            # Переименовываем файл в Mega
            if file:
                self.m.rename(file, self.remote_filename)
            
            print("✅ Данные успешно загружены в Mega")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки в Mega: {e}")
            return False
    
    def download_data(self):
        """Скачивание данных из Mega"""
        try:
            # Ищем файл в Mega
            files = self.m.find(self.remote_filename)
            if files:
                self.m.download(files, LOCAL_DATA_FILE)
                print("✅ Данные успешно скачаны из Mega")
                return True
            else:
                print("📝 Файл не найден в Mega, создаем новый")
                return False
        except Exception as e:
            print(f"❌ Ошибка скачивания из Mega: {e}")
            return False

# Инициализация Mega
print("🔄 Подключение к Mega...")
mega_storage = MegaStorage(MEGA_EMAIL, MEGA_PASSWORD)
mega_connected = mega_storage.login()

def load_data():
    """Загрузка данных из Mega или локального файла"""
    try:
        # Пытаемся скачать из Mega если подключены
        if mega_connected:
            if mega_storage.download_data():
                # Если скачали успешно, читаем локальный файл
                with open(LOCAL_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"📊 Загружено из Mega: {len(data.get('comments', []))} комментариев, {len(data.get('orders', []))} заказов")
                    return data
            else:
                # Если файла нет в Mega, создаем структуру по умолчанию
                print("📝 Создаем новую структуру данных в Mega")
                default_data = {
                    "comments": [
                        {
                            "id": 1,
                            "name": "Мария",
                            "text": "Заказывала куклу для дочки, остались очень довольны! Качество превосходное, дочка в восторге.",
                            "date": "15.11.2023 14:30",
                            "timestamp": "2023-11-15T14:30:00"
                        },
                        {
                            "id": 2,
                            "name": "Анна", 
                            "text": "Прекрасная работа! Кукла выполнена очень аккуратно, все детали проработаны. Спасибо большое!",
                            "date": "20.11.2023 10:15",
                            "timestamp": "2023-11-20T10:15:00"
                        }
                    ],
                    "orders": []
                }
                mega_storage.upload_data(default_data)
                return default_data
        else:
            # Если Mega не доступен, используем локальный файл
            if os.path.exists(LOCAL_DATA_FILE):
                with open(LOCAL_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"📊 Загружено локально: {len(data.get('comments', []))} комментариев, {len(data.get('orders', []))} заказов")
                    return data
            else:
                print("📝 Создаем новую локальную структуру данных")
                return {"comments": [], "orders": []}
                
    except Exception as e:
        print(f"❌ Ошибка загрузки данных: {e}")
        return {"comments": [], "orders": []}

def save_data(data):
    """Сохранение данных в Mega и локальный файл"""
    try:
        # Всегда сохраняем локально
        with open(LOCAL_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Пытаемся загрузить в Mega если подключены
        if mega_connected:
            success = mega_storage.upload_data(data)
            if success:
                print("✅ Данные синхронизированы с Mega")
            else:
                print("⚠️ Данные сохранены локально, но не синхронизированы с Mega")
        else:
            print("💾 Данные сохранены локально (Mega не доступен)")
            
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения данных: {e}")
        return False

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
        
        print(f"📧 Email отправлен на {to_email}")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки email: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_comments')
def get_comments():
    """Получение всех комментариев"""
    try:
        data = load_data()
        return jsonify(data.get("comments", []))
    except Exception as e:
        print(f"❌ Ошибка получения комментариев: {e}")
        return jsonify([])

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
        
        if save_data(data):
            print(f"💬 Добавлен новый комментарий от {name}")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Ошибка сохранения данных'})

    except Exception as e:
        print(f"❌ Ошибка добавления комментария: {e}")
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

        # Сохранение заказа
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
        
        if not save_data(data):
            return jsonify({'success': False, 'error': 'Ошибка сохранения заказа'})

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

Благодарим Вас за заказ авторской куклы в Millie's Reborn Nursery!

Мы получили Ваш заказ:
• Тип куклы: {doll_type}
• Ваши пожелания: {description}

Номер Вашего заказа: {new_order['id']}

В течение 24 часов мы свяжемся с Вами для уточнения деталей 
и обсуждения сроков выполнения заказа.

С уважением,
Millie's Reborn Nursery
Телефон: +380977057272
Instagram: @millie_reborn_ua
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
            'client_email_sent': client_email_sent,
            'mega_sync': mega_connected
        })

    except Exception as e:
        print(f"❌ Ошибка обработки заказа: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_orders')
def get_orders():
    """Получение списка заказов"""
    try:
        data = load_data()
        return jsonify(data.get("orders", []))
    except Exception as e:
        print(f"❌ Ошибка получения заказов: {e}")
        return jsonify([])

@app.route('/delete_comment', methods=['POST'])
def delete_comment():
    """Удаление комментария"""
    try:
        comment_data = request.json
        comment_id = comment_data.get('id')
        
        if not comment_id:
            return jsonify({'success': False, 'error': 'ID комментария не указан'})

        data = load_data()
        comments = data.get("comments", [])
        
        # Фильтруем комментарии, удаляя указанный
        initial_count = len(comments)
        comments = [c for c in comments if c['id'] != comment_id]
        
        if len(comments) == initial_count:
            return jsonify({'success': False, 'error': 'Комментарий не найден'})
            
        data["comments"] = comments
        
        if save_data(data):
            print(f"🗑️ Удален комментарий ID: {comment_id}")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Ошибка сохранения данных'})
            
    except Exception as e:
        print(f"❌ Ошибка удаления комментария: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/sync_data')
def sync_data():
    """Принудительная синхронизация с Mega"""
    try:
        if mega_connected:
            data = load_data()
            success = mega_storage.upload_data(data)
            return jsonify({'success': success, 'message': 'Данные синхронизированы с Mega'})
        else:
            return jsonify({'success': False, 'message': 'Mega не доступен'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка синхронизации: {str(e)}'})

@app.route('/status')
def status():
    """Статус системы"""
    data = load_data()
    return jsonify({
        'mega_connected': mega_connected,
        'comments_count': len(data.get('comments', [])),
        'orders_count': len(data.get('orders', [])),
        'local_file_exists': os.path.exists(LOCAL_DATA_FILE)
    })

if __name__ == '__main__':
    # Инициализация данных при первом запуске
    data = load_data()
    
    print("\n" + "="*50)
    print("🌟 Millie's Reborn Nursery Server")
    print("="*50)
    print(f"📊 Загружено данных:")
    print(f"   • Комментарии: {len(data.get('comments', []))}")
    print(f"   • Заказы: {len(data.get('orders', []))}")
    print(f"🔗 Mega подключение: {'✅ Да' if mega_connected else '❌ Нет'}")
    print(f"💾 Локальный файл: {'✅ Существует' if os.path.exists(LOCAL_DATA_FILE) else '❌ Отсутствует'}")
    print("="*50)

    print("\n🚀 Сервер запускается...")
    print("🌐 Доступные эндпоинты:")
    print("   - GET  / - главная страница")
    print("   - GET  /get_comments - получение комментариев")
    print("   - POST /submit_comment - добавление комментария") 
    print("   - POST /submit_order - оформление заказа")
    print("   - GET  /get_orders - получение заказов")
    print("   - POST /delete_comment - удаление комментария")
    print("   - GET  /sync_data - принудительная синхронизация с Mega")
    print("   - GET  /status - статус системы")
    print(f"\n📱 Откройте в браузере: http://localhost:5000")
    print("⏹️  Для остановки сервера нажмите Ctrl+C")
    print("="*50)

    app.run(debug=True, host='0.0.0.0', port=5000)
