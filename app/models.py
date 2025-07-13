from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    language = db.Column(db.String(5), default='zh')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # 关系
    files = db.relationship('File', backref='uploader', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class File(db.Model):
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)
    file_type = db.Column(db.String(100))
    mime_type = db.Column(db.String(100))
    description = db.Column(db.Text)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # 文件分类 (file, image, video) - 允许为空以兼容旧数据
    category = db.Column(db.String(20), default='file', index=True)
    
    # 通用字段（允许为空以兼容旧数据）
    project_number = db.Column(db.String(100), index=True)     # 项目号
    device_name = db.Column(db.String(200), index=True)        # 设备名称  
    content_language = db.Column(db.String(50))                # 语言
    security_level = db.Column(db.String(20), index=True)      # 保密等级
    remarks = db.Column(db.Text)                               # 备注
    
    # 图片和视频特有字段
    product_type = db.Column(db.String(100))        # 产品类型
    product_material = db.Column(db.String(100))    # 产品物料
    
    # 图片特有字段
    image_quality = db.Column(db.String(50))        # 图片质量
    image_number = db.Column(db.String(100))        # 图片编号
    
    # 视频特有字段
    video_quality = db.Column(db.String(50))        # 视频质量
    video_number = db.Column(db.String(100))        # 视频编号
    
    # 外键
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def format_file_size(self):
        """格式化文件大小显示"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"
    
    def get_category_display(self):
        """获取分类的中文显示名称"""
        category_map = {
            'file': '文件',
            'image': '图片', 
            'video': '视频'
        }
        return category_map.get(self.category or 'file', '文件')
    
    def get_security_level_display(self):
        """获取保密等级的显示名称"""
        level_map = {
            'public': '公开',
            'internal': '内部',
            'confidential': '机密',
            'secret': '秘密',
            'top_secret': '绝密'
        }
        return level_map.get(self.security_level, '未设置')
    
    @staticmethod
    def get_file_category_by_type(file_type):
        """根据文件类型判断分类"""
        image_types = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'}
        video_types = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm', '3gp'}
        
        if file_type.lower() in image_types:
            return 'image'
        elif file_type.lower() in video_types:
            return 'video'
        else:
            return 'file'
    
    def __repr__(self):
        return f'<File {self.filename}>' 