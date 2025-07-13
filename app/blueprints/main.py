from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from flask_login import current_user, login_required
from sqlalchemy import func
from datetime import datetime, timedelta
import requests
from app import db
import threading
import time

main_bp = Blueprint('main', __name__)

# 天气缓存
weather_cache = {
    'data': None,
    'timestamp': None,
    'cache_duration': 300  # 5分钟缓存
}

@main_bp.route('/')
def index():
    """首页"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """用户仪表板"""
    return render_template('dashboard.html')

@main_bp.route('/api/file_stats')
@login_required
def file_stats():
    """获取文件统计数据"""
    from app.models import File
    
    # 获取当前用户的文件统计
    total_files = File.query.filter_by(uploader_id=current_user.id).count()
    
    # 获取文件类型统计
    file_types = db.session.query(
        File.file_type,
        func.count(File.id).label('count')
    ).filter_by(uploader_id=current_user.id).group_by(File.file_type).all()
    
    # 获取总文件大小
    total_size = db.session.query(
        func.sum(File.file_size)
    ).filter_by(uploader_id=current_user.id).scalar() or 0
    
    # 获取最近7天的上传统计
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_uploads = db.session.query(
        func.date(File.upload_time).label('date'),
        func.count(File.id).label('count')
    ).filter(
        File.uploader_id == current_user.id,
        File.upload_time >= seven_days_ago
    ).group_by(func.date(File.upload_time)).all()
    
    # 格式化文件大小
    def format_size(bytes_size):
        if bytes_size < 1024:
            return f"{bytes_size} B"
        elif bytes_size < 1024 * 1024:
            return f"{bytes_size / 1024:.1f} KB"
        elif bytes_size < 1024 * 1024 * 1024:
            return f"{bytes_size / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_size / (1024 * 1024 * 1024):.1f} GB"
    
    return jsonify({
        'total_files': total_files,
        'total_size': format_size(total_size),
        'total_size_bytes': total_size,
        'file_types': [{'type': ft.file_type or 'unknown', 'count': ft.count} for ft in file_types],
        'daily_uploads': [{'date': str(du.date), 'count': du.count} for du in daily_uploads]
    })

def get_default_weather():
    """获取默认天气数据"""
    return {
        'success': True,
        'city': '北京',
        'temperature': '22',
        'description': '晴天',
        'humidity': '60',
        'wind_speed': '8',
        'feels_like': '24',
        'source': 'default'
    }

def fetch_weather_async(city):
    """异步获取天气数据"""
    try:
        # 使用更快的API和更短的超时时间
        weather_url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(weather_url, timeout=2)  # 减少到2秒超时
        
        if response.status_code == 200:
            data = response.json()
            current_condition = data['current_condition'][0]
            
            weather_data = {
                'success': True,
                'city': city,
                'temperature': current_condition['temp_C'],
                'description': current_condition['weatherDesc'][0]['value'],
                'humidity': current_condition['humidity'],
                'wind_speed': current_condition['windspeedKmph'],
                'feels_like': current_condition['FeelsLikeC'],
                'source': 'api'
            }
            
            # 更新缓存
            weather_cache['data'] = weather_data
            weather_cache['timestamp'] = time.time()
            
            return weather_data
        else:
            return None
            
    except Exception as e:
        print(f"Weather API error: {e}")
        return None

@main_bp.route('/api/weather')
@login_required
def weather():
    """获取天气信息 - 优化版本"""
    city = request.args.get('city', '北京')
    
    # 检查缓存
    current_time = time.time()
    if (weather_cache['data'] and 
        weather_cache['timestamp'] and 
        (current_time - weather_cache['timestamp']) < weather_cache['cache_duration']):
        return jsonify(weather_cache['data'])
    
    # 立即返回默认数据
    default_weather = get_default_weather()
    
    # 在后台异步获取真实天气数据
    def update_weather():
        real_weather = fetch_weather_async(city)
        if real_weather:
            weather_cache['data'] = real_weather
            weather_cache['timestamp'] = time.time()
    
    # 启动后台线程更新天气（不阻塞响应）
    weather_thread = threading.Thread(target=update_weather)
    weather_thread.daemon = True
    weather_thread.start()
    
    return jsonify(default_weather)

@main_bp.route('/api/weather/refresh')
@login_required
def weather_refresh():
    """强制刷新天气数据"""
    city = request.args.get('city', '北京')
    
    # 直接获取天气数据（同步）
    weather_data = fetch_weather_async(city)
    
    if weather_data:
        return jsonify(weather_data)
    else:
        # 如果失败，返回默认数据但标记为错误
        default_weather = get_default_weather()
        default_weather['success'] = False
        default_weather['error'] = '天气服务暂时不可用'
        return jsonify(default_weather)

@main_bp.route('/set_language/<language>')
def set_language(language=None):
    """设置语言"""
    if language in ['zh', 'en']:
        session['language'] = language
        if current_user.is_authenticated:
            current_user.language = language
            from app import db
            db.session.commit()
    
    # 返回到引用页面
    return redirect(request.referrer or url_for('main.index')) 