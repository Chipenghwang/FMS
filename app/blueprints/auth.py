from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app.models import User
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('files.list'))
        
    if request.method == 'POST':
        if request.is_json:
            # API请求
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            # 表单请求
            username = request.form.get('username')
            password = request.form.get('password')
        
        if not username or not password:
            if request.is_json:
                return jsonify({'error': '用户名和密码不能为空'}), 400
            flash('用户名和密码不能为空', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            if request.is_json:
                return jsonify({'message': '登录成功', 'redirect': url_for('files.list')}), 200
            flash('登录成功！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('files.list'))
        else:
            if request.is_json:
                return jsonify({'error': '用户名或密码错误'}), 401
            flash('用户名或密码错误', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('files.list'))
        
    if request.method == 'POST':
        if request.is_json:
            # API请求
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            confirm_password = data.get('confirm_password')
        else:
            # 表单请求
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
        
        # 验证输入
        if not all([username, email, password, confirm_password]):
            error = '所有字段都必须填写'
            if request.is_json:
                return jsonify({'error': error}), 400
            flash(error, 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            error = '两次输入的密码不一致'
            if request.is_json:
                return jsonify({'error': error}), 400
            flash(error, 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            error = '密码长度至少6位'
            if request.is_json:
                return jsonify({'error': error}), 400
            flash(error, 'error')
            return render_template('auth/register.html')
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            error = '用户名已存在'
            if request.is_json:
                return jsonify({'error': error}), 400
            flash(error, 'error')
            return render_template('auth/register.html')
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            error = '邮箱已被注册'
            if request.is_json:
                return jsonify({'error': error}), 400
            flash(error, 'error')
            return render_template('auth/register.html')
        
        try:
            # 创建新用户
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            if request.is_json:
                return jsonify({'message': '注册成功', 'redirect': url_for('auth.login')}), 201
            flash('注册成功！请登录', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            error = '注册失败，请稍后重试'
            if request.is_json:
                return jsonify({'error': error}), 500
            flash(error, 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('您已成功登出', 'info')
    return redirect(url_for('main.index')) 