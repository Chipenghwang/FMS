from app import create_app, db
from app.models import User, File

app = create_app() # 创建Flask应用实例

# NOTE # 装饰器
##############################################
# @app.shell_context_processor
# 作用：嵌套在 Flask 应用上下文中的函数
##############################################

@app.shell_context_processor
def make_shell_context():
    # db为数据库实例
    return {'db': db, 'User': User, 'File': File}

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # 在应用上下文中创建数据库表
    app.run(debug=True, host='0.0.0.0', port=5000) # 启动Flask服务，并设置端口为5000