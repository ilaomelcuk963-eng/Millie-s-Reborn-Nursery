from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # Добавляем CORS поддержку

# Конфигурация Яндекс.Диска
YANDEX_DISK_TOKEN = "y0__xDK_b6HCBjblgMg-t6diRWhjiVtinXJTPA2alYj4QGwhdV5kg"
YANDEX_API_URL = "https://cloud-api.yandex.net/v1/disk/resources"
DATA_FILE_PATH = "data.json"

class YandexDiskManager:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://cloud-api.yandex.net/v1/disk/resources"
    
    def _make_request(self, url, method='GET', data=None):
        headers = {'Authorization': f'OAuth {self.token}'}
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'PUT':
                if isinstance(data, (dict, list)):
                    response = requests.put(url, headers=headers, json=data)
                else:
                    response = requests.put(url, headers=headers, data=data)
            return response
        except Exception as e:
            print(f"Ошибка запроса к Яндекс.Диску: {e}")
            return None
    
    def save_data(self, data):
        """Сохраняет данные на Яндекс.Диск"""
        try:
            # Получаем ссылку для загрузки
            upload_url = f"{self.base_url}/upload?path={DATA_FILE_PATH}&overwrite=true"
            response = self._make_request(upload_url, 'GET')
            
            if response and response.status_code == 200:
                upload_href = response.json().get('href')
                if upload_href:
                    # Загружаем данные
                    put_response = requests.put(upload_href, 
                                              json=data,
                                              headers={'Content-Type': 'application/json'})
                    return put_response.status_code == 201
            return False
        except Exception as e:
            print(f"Ошибка сохранения на Яндекс.Диск: {e}")
            return False
    
    def load_data(self):
        """Загружает данные с Яндекс.Диска"""
        try:
            # Получаем ссылку для скачивания
            download_url = f"{self.base_url}/download?path={DATA_FILE_PATH}"
            response = self._make_request(download_url, 'GET')
            
            if response and response.status_code == 200:
                download_href = response.json().get('href')
                if download_href:
                    # Скачиваем данные
                    data_response = requests.get(download_href)
                    if data_response.status_code == 200:
                        return data_response.json()
            
            # Если файла нет, возвращаем структуру по умолчанию
            return {"orders": [], "comments": []}
        except Exception as e:
            print(f"Ошибка загрузки с Яндекс.Диска: {e}")
            return {"orders": [], "comments": []}

# Инициализация менеджера Яндекс.Диска
yandex_disk = YandexDiskManager(YANDEX_DISK_TOKEN)

def get_local_data():
    """Получает данные из локального файла"""
    try:
        if os.path.exists('data.json'):
            with open('data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Ошибка чтения локального файла: {e}")
    return {"orders": [], "comments": []}

def save_local_data(data):
    """Сохраняет данные в локальный файл"""
    try:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка сохранения локального файла: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/orders', methods=['POST', 'OPTIONS'])
def create_order():
    """Создание нового заказа"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        order_data = request.json
        if not order_data:
            return jsonify({"success": False, "error": "No data provided"}), 400
            
        order_data["id"] = int(datetime.now().timestamp() * 1000)
        order_data["timestamp"] = order_data["id"]
        order_data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Загружаем текущие данные
        data = get_local_data()
        data["orders"].append(order_data)
        
        # Сохраняем обновленные данные
        save_local_data(data)
        yandex_disk.save_data(data)
        
        return jsonify({"success": True, "order_id": order_data["id"]})
    except Exception as e:
        print(f"Ошибка создания заказа: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/comments', methods=['POST', 'OPTIONS'])
def create_comment():
    """Создание нового комментария"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        comment_data = request.json
        if not comment_data:
            return jsonify({"success": False, "error": "No data provided"}), 400
            
        comment_data["id"] = int(datetime.now().timestamp() * 1000)
        comment_data["timestamp"] = comment_data["id"]
        comment_data["date"] = datetime.now().isoformat()
        
        # Загружаем текущие данные
        data = get_local_data()
        data["comments"].append(comment_data)
        
        # Сохраняем обновленные данные
        save_local_data(data)
        yandex_disk.save_data(data)
        
        return jsonify({"success": True, "comment_id": comment_data["id"]})
    except Exception as e:
        print(f"Ошибка создания комментария: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Получение списка заказов"""
    try:
        data = get_local_data()
        return jsonify(data.get("orders", []))
    except Exception as e:
        print(f"Ошибка получения заказов: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/comments', methods=['GET'])
def get_comments():
    """Получение списка комментариев"""
    try:
        data = get_local_data()
        return jsonify(data.get("comments", []))
    except Exception as e:
        print(f"Ошибка получения комментариев: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/sync', methods=['POST', 'OPTIONS'])
def sync():
    """Принудительная синхронизация данных"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        local_data = get_local_data()
        yandex_data = yandex_disk.load_data()
        
        # Объединяем данные
        merged_data = {
            "orders": local_data.get("orders", []) + yandex_data.get("orders", []),
            "comments": local_data.get("comments", []) + yandex_data.get("comments", [])
        }
        
        # Убираем дубликаты по ID
        def remove_duplicates(items):
            seen = set()
            unique = []
            for item in items:
                if item["id"] not in seen:
                    seen.add(item["id"])
                    unique.append(item)
            return unique
            
        merged_data["orders"] = remove_duplicates(merged_data["orders"])
        merged_data["comments"] = remove_duplicates(merged_data["comments"])
        
        # Сохраняем объединенные данные
        save_local_data(merged_data)
        yandex_disk.save_data(merged_data)
        
        return jsonify({
            "success": True, 
            "orders_count": len(merged_data["orders"]),
            "comments_count": len(merged_data["comments"])
        })
    except Exception as e:
        print(f"Ошибка синхронизации: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    # Создаем папки если их нет
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # Проверяем подключение к Яндекс.Диску
    print("Проверка подключения к Яндекс.Диску...")
    try:
        test_data = yandex_disk.load_data()
        print("✅ Подключение к Яндекс.Диску успешно")
    except Exception as e:
        print(f"❌ Ошибка подключения к Яндекс.Диску: {e}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
