import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from app.models import File
from app import db

files_bp = Blueprint('files', __name__)

def allowed_file(filename, category=None):
    """检查文件类型是否允许"""
    file_extensions = {
        'file': {'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', 'csv'},
        'image': {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'tiff'},
        'video': {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm', '3gp', 'mp3', 'wav'}
    }
    
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if category:
        return ext in file_extensions.get(category, set())
    else:
        # 如果没有指定分类，检查是否在所有允许的扩展名中
        all_extensions = set()
        for exts in file_extensions.values():
            all_extensions.update(exts)
        return ext in all_extensions

def generate_date_based_filename(original_filename, uploader_id):
    """生成基于日期和序号的文件名"""
    from datetime import datetime
    
    # 获取当前日期
    today = datetime.now()
    date_str = today.strftime('%Y%m%d')
    
    # 获取文件扩展名
    if '.' in original_filename:
        ext = '.' + original_filename.rsplit('.', 1)[1]
    else:
        ext = ''
    
    # 查询今天该用户已上传的文件数量
    today_start = datetime(today.year, today.month, today.day)
    today_end = datetime(today.year, today.month, today.day, 23, 59, 59)
    
    today_files_count = File.query.filter(
        File.uploader_id == uploader_id,
        File.upload_time >= today_start,
        File.upload_time <= today_end
    ).count()
    
    # 生成序号（从1开始）
    sequence_number = today_files_count + 1
    
    # 构建新文件名
    new_filename = f"{date_str}-{sequence_number:05d}{ext}"
    
    return new_filename

def get_file_absolute_path(file_obj, save_path, uploader_id):
    """根据用户指定的路径保存文件并返回绝对路径"""
    import tempfile
    import os
    
    # 确保保存目录存在
    if not os.path.exists(save_path):
        try:
            os.makedirs(save_path, exist_ok=True)
        except Exception as e:
            raise Exception(f"无法创建目录 {save_path}: {str(e)}")
    
    # 生成基于日期的文件名
    new_filename = generate_date_based_filename(file_obj.filename, uploader_id)
    file_path = os.path.join(save_path, new_filename)
    
    # 如果文件已存在（极少情况），添加额外序号
    if os.path.exists(file_path):
        name_without_ext, ext = os.path.splitext(new_filename)
        counter = 1
        while os.path.exists(file_path):
            new_filename_with_counter = f"{name_without_ext}_{counter}{ext}"
            file_path = os.path.join(save_path, new_filename_with_counter)
            counter += 1
        new_filename = new_filename_with_counter
    
    # 保存文件
    file_obj.save(file_path)
    
    # 返回绝对路径
    return os.path.abspath(file_path)

@files_bp.route('/')
@files_bp.route('/list')
@login_required
def list():
    """文件列表页面"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    category = request.args.get('category', '', type=str)
    per_page = 10
    
    query = File.query.filter_by(uploader_id=current_user.id)
    
    if search:
        query = query.filter(
            or_(
                File.original_filename.contains(search),
                File.description.contains(search),
                File.project_number.contains(search) if File.project_number else False,
                File.device_name.contains(search) if File.device_name else False
            )
        )
    
    if category:
        query = query.filter_by(category=category)
    
    files = query.order_by(File.upload_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('files/list.html', files=files, search=search, category=category)

@files_bp.route('/upload')
@login_required 
def upload():
    """文件上传 - 第一步：选择分类"""
    return render_template('files/upload_step1.html')

@files_bp.route('/upload/step2/<category>')
@login_required
def upload_step2(category):
    """文件上传 - 第二步：填写属性"""
    if category not in ['file', 'image', 'video']:
        flash('无效的文件类型', 'error')
        return redirect(url_for('files.upload'))
    
    # 定义选项数据
    form_data = {
        'languages': [
            ('zh-CN', '中文简体'),
            ('zh-TW', '中文繁体'),
            ('en-US', '英语'),
            ('ja-JP', '日语'),
            ('ko-KR', '韩语'),
            ('de-DE', '德语'),
            ('fr-FR', '法语'),
            ('es-ES', '西班牙语')
        ],
        'security_levels': [
            ('public', '公开'),
            ('internal', '内部'),
            ('confidential', '机密'),
            ('secret', '秘密'),
            ('top_secret', '绝密')
        ],
        'product_types': [
            ('hardware', '硬件产品'),
            ('software', '软件产品'),
            ('service', '服务产品'),
            ('solution', '解决方案'),
            ('component', '组件部件')
        ],
        'quality_options': [
            ('low', '低质量'),
            ('medium', '中等质量'),
            ('high', '高质量'),
            ('ultra', '超高质量'),
            ('raw', '原始质量')
        ]
    }
    
    return render_template('files/upload_step2.html', category=category, form_data=form_data)

@files_bp.route('/upload/step3', methods=['POST'])
@login_required
def upload_step3():
    """文件上传 - 第三步：上传文件"""
    # 获取表单数据
    category = request.form.get('category')
    if category not in ['file', 'image', 'video']:
        flash('无效的文件类型', 'error')
        return redirect(url_for('files.upload'))
    
    # 验证必要字段（但现在都允许为空）
    required_fields = ['project_number', 'device_name', 'content_language', 'security_level']
    
    if category in ['image', 'video']:
        required_fields.extend(['product_type', 'product_material'])
    
    if category == 'image':
        required_fields.extend(['image_quality', 'image_number'])
    elif category == 'video':
        required_fields.extend(['video_quality', 'video_number'])
    
    # 检查必要字段（但允许为空值）
    form_data = {}
    for field in required_fields:
        value = request.form.get(field, '').strip()
        if not value:
            flash(f'请填写必要字段：{field}', 'warning')
            return redirect(url_for('files.upload_step2', category=category))
        form_data[field] = value
    
    # 将表单数据存储到session中
    session['upload_data'] = {
        'category': category,
        'project_number': form_data.get('project_number', ''),
        'device_name': form_data.get('device_name', ''),
        'content_language': form_data.get('content_language', ''),
        'security_level': form_data.get('security_level', ''),
        'remarks': request.form.get('remarks', ''),
        'product_type': form_data.get('product_type', ''),
        'product_material': form_data.get('product_material', ''),
        'image_quality': form_data.get('image_quality', ''),
        'image_number': form_data.get('image_number', ''),
        'video_quality': form_data.get('video_quality', ''),
        'video_number': form_data.get('video_number', ''),
    }
    
    return render_template('files/upload_step3.html', category=category)

@files_bp.route('/upload/process', methods=['POST'])
@login_required
def upload_process():
    """处理文件上传"""
    # 获取session中的数据
    upload_data = session.get('upload_data')
    if not upload_data:
        flash('上传会话已过期，请重新开始', 'error')
        return redirect(url_for('files.upload'))
    
    category = upload_data['category']
    
    # 获取用户指定的保存路径
    save_path = request.form.get('save_path', '').strip()
    if not save_path:
        if request.is_json:
            return jsonify({'error': '请选择文件保存位置'}), 400
        flash('请选择文件保存位置', 'error')
        return render_template('files/upload_step3.html', category=category)
    
    # 检查是否有文件
    if 'file' not in request.files:
        if request.is_json:
            return jsonify({'error': '未选择文件'}), 400
        flash('未选择文件', 'error')
        return render_template('files/upload_step3.html', category=category)
    
    file = request.files['file']
    
    if file.filename == '':
        if request.is_json:
            return jsonify({'error': '未选择文件'}), 400
        flash('未选择文件', 'error')
        return render_template('files/upload_step3.html', category=category)
    
    if not allowed_file(file.filename, category):
        allowed_types = {
            'file': '文档文件 (txt, pdf, doc, docx, xls, xlsx, ppt, pptx, zip, rar, csv)',
            'image': '图片文件 (jpg, jpeg, png, gif, bmp, webp, svg, tiff)',
            'video': '视频文件 (mp4, avi, mov, wmv, flv, mkv, webm, 3gp, mp3, wav)'
        }
        error_msg = f'不支持的文件类型，请上传{allowed_types.get(category, "支持的文件")}'
        if request.is_json:
            return jsonify({'error': error_msg}), 400
        flash(error_msg, 'error')
        return render_template('files/upload_step3.html', category=category)
    
    try:
        # 将文件保存到用户指定的路径（使用日期ID命名）
        file_absolute_path = get_file_absolute_path(file, save_path, current_user.id)
        
        # 获取文件信息
        file_size = os.path.getsize(file_absolute_path)
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        # 自动判断分类（作为验证）
        auto_category = File.get_file_category_by_type(file_ext)
        if auto_category != category:
            # 如果自动判断的分类与用户选择不符，给出提示但继续上传
            flash(f'注意：根据文件类型自动判断为{auto_category}，但您选择的是{category}', 'warning')
        
        # 获取实际保存的文件名（不含路径）
        actual_filename = os.path.basename(file_absolute_path)
        
        # 保存到数据库（保存绝对路径）
        new_file = File(
            filename=actual_filename,  # 保存实际的文件名（日期ID格式）
            original_filename=file.filename,  # 保存原始文件名
            file_path=file_absolute_path,  # 保存绝对路径
            file_size=file_size,
            file_type=file_ext,
            mime_type=file.content_type,
            category=category,
            
            # 通用字段
            project_number=upload_data.get('project_number'),
            device_name=upload_data.get('device_name'),
            content_language=upload_data.get('content_language'),
            security_level=upload_data.get('security_level'),
            remarks=upload_data.get('remarks'),
            
            # 图片和视频字段
            product_type=upload_data.get('product_type'),
            product_material=upload_data.get('product_material'),
            
            # 图片字段
            image_quality=upload_data.get('image_quality'),
            image_number=upload_data.get('image_number'),
            
            # 视频字段
            video_quality=upload_data.get('video_quality'),
            video_number=upload_data.get('video_number'),
            
            uploader_id=current_user.id
        )
        
        db.session.add(new_file)
        db.session.commit()
        
        # 清除session数据
        session.pop('upload_data', None)
        
        success_msg = f'{new_file.get_category_display()}"{file.filename}"已保存为"{actual_filename}": {file_absolute_path}'
        
        if request.is_json:
            return jsonify({
                'message': success_msg,
                'file_id': new_file.id,
                'original_name': file.filename,
                'saved_name': actual_filename,
                'file_path': file_absolute_path,
                'redirect': url_for('files.list')
            }), 200
        
        flash(success_msg, 'success')
        return redirect(url_for('files.list'))
        
    except Exception as e:
        db.session.rollback()
        # 如果保存文件失败，尝试删除已创建的文件
        if 'file_absolute_path' in locals() and os.path.exists(file_absolute_path):
            try:
                os.remove(file_absolute_path)
            except:
                pass
        
        error_msg = f'文件保存失败: {str(e)}'
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        flash(error_msg, 'error')
        return render_template('files/upload_step3.html', category=category)

# 简化版本的上传处理，兼容旧的上传方式
@files_bp.route('/upload/simple', methods=['GET', 'POST'])
@login_required
def upload_simple():
    """简化版文件上传，兼容旧方式"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('未选择文件', 'error')
            return render_template('files/upload_simple.html')
        
        file = request.files['file']
        description = request.form.get('description', '')
        
        if file.filename == '':
            flash('未选择文件', 'error')
            return render_template('files/upload_simple.html')
        
        if not allowed_file(file.filename):
            flash('不支持的文件类型', 'error')
            return render_template('files/upload_simple.html')
        
        try:
            # 使用默认的下载文件夹
            import os
            default_save_path = os.path.join(os.path.expanduser("~"), "Downloads")
            
            # 将文件保存到默认路径（使用日期ID命名）
            file_absolute_path = get_file_absolute_path(file, default_save_path, current_user.id)
            
            # 获取文件信息
            file_size = os.path.getsize(file_absolute_path)
            file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            
            # 自动判断分类
            category = File.get_file_category_by_type(file_ext)
            
            # 获取实际保存的文件名
            actual_filename = os.path.basename(file_absolute_path)
            
            # 保存到数据库（使用默认值）
            new_file = File(
                filename=actual_filename,  # 保存实际的文件名（日期ID格式）
                original_filename=file.filename,  # 保存原始文件名
                file_path=file_absolute_path,  # 保存绝对路径
                file_size=file_size,
                file_type=file_ext,
                mime_type=file.content_type,
                description=description,
                category=category,
                uploader_id=current_user.id
            )
            
            db.session.add(new_file)
            db.session.commit()
            
            flash(f'文件"{file.filename}"已保存为"{actual_filename}": {file_absolute_path}', 'success')
            return redirect(url_for('files.list'))
            
        except Exception as e:
            db.session.rollback()
            if 'file_absolute_path' in locals() and os.path.exists(file_absolute_path):
                try:
                    os.remove(file_absolute_path)
                except:
                    pass
            flash(f'文件保存失败: {str(e)}', 'error')
    
    return render_template('files/upload_simple.html')

@files_bp.route('/download/<int:file_id>')
@login_required
def download(file_id):
    """文件下载"""
    file = File.query.filter_by(id=file_id, uploader_id=current_user.id).first()
    
    if not file:
        flash('文件不存在或无权限访问', 'error')
        return redirect(url_for('files.list'))
    
    # 检查文件路径是否存在
    if not os.path.exists(file.file_path):
        flash(f'文件路径不存在: {file.file_path}', 'error')
        return redirect(url_for('files.list'))
    
    try:
        return send_file(
            file.file_path,
            as_attachment=True,
            download_name=file.original_filename
        )
    except Exception as e:
        flash(f'文件下载失败: {str(e)}', 'error')
        return redirect(url_for('files.list'))

@files_bp.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete(file_id):
    """删除文件（默认同时删除物理文件）"""
    file = File.query.filter_by(id=file_id, uploader_id=current_user.id).first()
    
    if not file:
        if request.is_json:
            return jsonify({'error': '文件不存在或无权限访问'}), 404
        flash('文件不存在或无权限访问', 'error')
        return redirect(url_for('files.list'))
    
    try:
        # 默认删除物理文件，除非明确指定不删除
        delete_physical = request.form.get('delete_physical', 'true').lower() == 'true'
        
        physical_deleted = False
        physical_error = None
        
        if delete_physical and os.path.exists(file.file_path):
            try:
                os.remove(file.file_path)
                physical_deleted = True
            except Exception as e:
                physical_error = str(e)
        
        # 删除数据库记录
        db.session.delete(file)
        db.session.commit()
        
        # 准备成功消息
        if delete_physical:
            if physical_deleted:
                flash_msg = f'文件 "{file.original_filename}" 及其物理文件已删除'
            elif physical_error:
                flash_msg = f'文件记录已删除，但物理文件删除失败: {physical_error}'
            else:
                flash_msg = f'文件记录已删除（物理文件不存在）'
        else:
            flash_msg = f'文件记录已删除（物理文件保留）'
        
        if request.is_json:
            return jsonify({
                'message': flash_msg,
                'physical_deleted': physical_deleted,
                'physical_error': physical_error
            }), 200
        
        flash(flash_msg, 'success')
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'删除文件失败: {str(e)}'
        
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        flash(error_msg, 'error')
    
    return redirect(url_for('files.list'))

@files_bp.route('/api/search')
@login_required
def api_search():
    """API: 搜索文件"""
    search = request.args.get('q', '', type=str)
    category = request.args.get('category', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = File.query.filter_by(uploader_id=current_user.id)
    
    if search:
        query = query.filter(
            or_(
                File.original_filename.contains(search),
                File.description.contains(search),
                File.project_number.contains(search) if File.project_number else False,
                File.device_name.contains(search) if File.device_name else False
            )
        )
    
    if category:
        query = query.filter_by(category=category)
    
    files = query.order_by(File.upload_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'files': [{
            'id': f.id,
            'filename': f.original_filename,
            'size': f.format_file_size(),
            'type': f.file_type,
            'category': f.get_category_display(),
            'project_number': f.project_number or '',
            'device_name': f.device_name or '',
            'security_level': f.get_security_level_display(),
            'upload_time': f.upload_time.strftime('%Y-%m-%d %H:%M:%S'),
            'description': f.description or ''
        } for f in files.items],
        'total': files.total,
        'pages': files.pages,
        'current_page': files.page,
        'has_next': files.has_next,
        'has_prev': files.has_prev
    })

@files_bp.route('/api/file_info/<int:file_id>')
@login_required
def api_file_info(file_id):
    """获取文件详细信息"""
    file = File.query.filter_by(id=file_id, uploader_id=current_user.id).first()
    
    if not file:
        return jsonify({'error': '文件不存在或无权限访问'}), 404
    
    # 检查文件是否存在
    file_exists = os.path.exists(file.file_path)
    
    # 获取文件的创建时间和修改时间
    if file_exists:
        file_stat = os.stat(file.file_path)
        create_time = datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
        modify_time = datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    else:
        create_time = '文件不存在'
        modify_time = '文件不存在'
    
    # 构建文件信息
    file_info = {
        'id': file.id,
        'category': file.get_category_display(),
        'original_filename': file.original_filename,
        'system_filename': file.filename,
        'file_path': file.file_path,
        'file_size': file.format_file_size(),
        'file_type': file.file_type.upper() if file.file_type else '未知',
        'mime_type': file.mime_type or '未知',
        'upload_time': file.upload_time.strftime('%Y-%m-%d %H:%M:%S'),
        'create_time': create_time,
        'modify_time': modify_time,
        'file_exists': file_exists,
        
        # 基本属性
        'project_number': file.project_number,
        'device_name': file.device_name,
        'content_language': file.content_language,
        'security_level': file.get_security_level_display(),
        'remarks': file.remarks,
        
        # 产品信息（图片和视频）
        'product_type': file.get_product_type_display() if hasattr(file, 'get_product_type_display') else None,
        'product_material': file.product_material,
        
        # 图片特有属性
        'image_quality': file.get_image_quality_display() if hasattr(file, 'get_image_quality_display') else None,
        'image_number': file.image_number,
        
        # 视频特有属性
        'video_quality': file.get_video_quality_display() if hasattr(file, 'get_video_quality_display') else None,
        'video_number': file.video_number,
    }
    
    return jsonify(file_info) 