# FMS 文件管理系统架构与代码分析

## 一、系统架构

### 1. 项目结构
- `run.py`：项目启动入口，负责创建应用、初始化数据库并运行服务。
- `config.py`：配置文件，存放数据库、密钥等配置信息。
- `app/`：主应用目录
  - `models.py`：定义数据库模型（如用户、文件等）。
  - `blueprints/`：功能模块目录，按功能拆分为多个蓝图（如认证、文件管理、主页等）。
    - `auth.py`：用户认证相关路由和逻辑。
    - `files.py`：文件上传、下载、删除等相关路由和逻辑。
    - `main.py`：主页、仪表板等通用页面逻辑。
  - `static/`：静态资源（如 CSS、JS、图片）。
  - `templates/`：前端模板文件（HTML），分模块存放。
- `instance/`：存放数据库文件等实例数据。
- `requirements.txt`：依赖包列表。
- `README.md`、`DASHBOARD_GUIDE.md`、`FILE_SAVE_GUIDE.md`：项目说明和使用文档。

### 2. 技术栈
- 后端：Python 3 + Flask
- 前端：Bootstrap 5、Bootstrap Icons、Chart.js
- 数据库：SQLite

---

## 二、主要代码分析

### 1. `run.py`
```python
from app import create_app, db
from app.models import User, File

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'File': File}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
```
- **导入应用工厂和数据库对象**：`create_app` 用于创建 Flask 应用，`db` 是数据库实例。
- **导入模型**：`User` 和 `File` 是数据库表的模型类。
- **shell 上下文**：方便在 Flask shell 中直接访问数据库和模型。
- **主程序入口**：
  - `db.create_all()`：在应用上下文中创建所有数据库表。
  - `app.run(...)`：启动 Flask 服务，监听所有 IP 的 5000 端口，调试模式开启。

### 2. `models.py`
- 定义了用户（User）、文件（File）等数据库模型，包含字段和关系，用于数据存储和查询。

### 3. `blueprints/`
- 按功能拆分路由和业务逻辑，便于维护和扩展。
  - `auth.py`：处理登录、注册、权限验证等。
  - `files.py`：处理文件的上传、下载、删除、元数据管理等。
  - `main.py`：仪表板、首页等通用页面。

### 4. `templates/`
- 使用 Jinja2 模板渲染 HTML 页面，支持响应式设计和数据可视化。

### 5. `static/`
- 存放前端静态资源，提升页面美观和交互体验。

---

## 三、学习建议

- **理解 Flask 应用工厂模式**：便于项目扩展和测试。
- **掌握蓝图（Blueprint）模块化开发**：提升代码可维护性。
- **熟悉 ORM 数据模型设计**：便于数据操作和迁移。
- **前后端分离与模板渲染**：学习如何将后端数据动态展示到前端页面。
- **安全与权限管理**：了解如何实现用户认证和文件权限控制。

---

如需更详细的代码解读或某个模块的具体说明，可以进一步查阅相关文件或提问。
