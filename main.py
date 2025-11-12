from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

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

def sync_data():
    """Синхронизирует данные между локальным файлом и Яндекс.Диском"""
    try:
        # Загружаем с Яндекс.Диска
        yandex_data = yandex_disk.load_data()
        
        # Загружаем локальные данные
        local_data = get_local_data()
        
        # Объединяем данные (приоритет у более новых записей)
        merged_data = merge_data(local_data, yandex_data)
        
        # Сохраняем объединенные данные
        save_local_data(merged_data)
        yandex_disk.save_data(merged_data)
        
        return merged_data
    except Exception as e:
        print(f"Ошибка синхронизации: {e}")
        return get_local_data()

def merge_data(local_data, yandex_data):
    """Объединяет данные из двух источников"""
    merged = {"orders": [], "comments": []}
    
    # Объединяем заказы
    all_orders = {}
    for order in local_data.get("orders", []):
        all_orders[order.get("id")] = order
    for order in yandex_data.get("orders", []):
        existing = all_orders.get(order.get("id"))
        if not existing or (order.get("timestamp", 0) > existing.get("timestamp", 0)):
            all_orders[order.get("id")] = order
    
    # Объединяем комментарии
    all_comments = {}
    for comment in local_data.get("comments", []):
        all_comments[comment.get("id")] = comment
    for comment in yandex_data.get("comments", []):
        existing = all_comments.get(comment.get("id"))
        if not existing or (comment.get("timestamp", 0) > existing.get("timestamp", 0)):
            all_comments[comment.get("id")] = comment
    
    merged["orders"] = list(all_orders.values())
    merged["comments"] = list(all_comments.values())
    
    # Сортируем по дате (новые first)
    merged["orders"].sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    merged["comments"].sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    
    return merged

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Создание нового заказа"""
    try:
        order_data = request.json
        order_data["id"] = int(datetime.now().timestamp() * 1000)
        order_data["timestamp"] = order_data["id"]
        order_data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Загружаем текущие данные
        data = sync_data()
        data["orders"].append(order_data)
        
        # Сохраняем обновленные данные
        save_local_data(data)
        yandex_disk.save_data(data)
        
        return jsonify({"success": True, "order_id": order_data["id"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/comments', methods=['POST'])
def create_comment():
    """Создание нового комментария"""
    try:
        comment_data = request.json
        comment_data["id"] = int(datetime.now().timestamp() * 1000)
        comment_data["timestamp"] = comment_data["id"]
        comment_data["date"] = datetime.now().isoformat()
        
        # Загружаем текущие данные
        data = sync_data()
        data["comments"].append(comment_data)
        
        # Сохраняем обновленные данные
        save_local_data(data)
        yandex_disk.save_data(data)
        
        return jsonify({"success": True, "comment_id": comment_data["id"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Получение списка заказов"""
    try:
        data = sync_data()
        return jsonify(data["orders"])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/comments', methods=['GET'])
def get_comments():
    """Получение списка комментариев"""
    try:
        data = sync_data()
        return jsonify(data["comments"])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sync', methods=['POST'])
def sync():
    """Принудительная синхронизация данных"""
    try:
        data = sync_data()
        return jsonify({
            "success": True, 
            "orders_count": len(data["orders"]),
            "comments_count": len(data["comments"])
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    # Создаем папку для статических файлов если её нет
    os.makedirs('static', exist_ok=True)
    
    # Первоначальная синхронизация при запуске
    print("Синхронизация данных с Яндекс.Диском...")
    sync_data()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
