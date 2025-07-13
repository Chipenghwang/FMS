# FMS 文件管理系统

## 简介
FMS（File Management System）是一款基于 Flask 的现代化文件管理系统，支持多种文件类型的上传、分类、搜索、下载和删除，具备灵活的路径管理和丰富的元数据记录。

## 主要功能
- 🗂️ 多类型文件上传（文档、图片、视频）
- 📂 路径自定义与预设目录选择
- 📊 仪表板统计与数据可视化（文件类型分布、上传趋势等）
- 🔍 文件搜索与筛选（按类型、项目号、设备名等）
- 📝 完整元数据管理（项目号、设备名称、语言、保密等级等）
- ⚡ 快速操作面板
- 🌤️ 实时天气信息
- 🖥️ 响应式设计，适配多端设备
- 🛡️ 安全可靠，支持权限与物理文件同步删除

## 安装与运行
1. 克隆项目到本地：
   ```sh
   git clone https://github.com/your-repo/fms.git
   cd fms
   ```
2. 安装依赖：
   ```sh
   pip install -r requirements.txt
   ```
3. 配置环境变量（可选）：
   - 编辑 `.env` 文件，设置数据库路径等参数

4. 初始化数据库（如首次使用）：
   ```sh
   python run.py initdb
   ```

5. 启动服务：
   ```sh
   python run.py
   ```
   默认访问地址：[http://localhost:5000](http://localhost:5000)

## 使用说明
- 注册新账户或使用管理员账号（admin / 123456）登录
- 进入仪表板，浏览文件统计与天气信息
- 上传文件时可选择保存位置、填写详细属性
- 支持文件的下载、删除（含物理文件同步删除）
- 更多详细操作请参考 [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md) 和 [FILE_SAVE_GUIDE.md](FILE_SAVE_GUIDE.md)

## 目录结构
```
.env
config.py
run.py
app/
    models.py
    blueprints/
        auth.py
        files.py
        main.py
    static/
    templates/
        base.html
        dashboard.html
        files/
            upload.html
            upload_step1.html
            upload_step2.html
            upload_step3.html
            list.html
instance/
    fms.db
README.md
DASHBOARD_GUIDE.md
FILE_SAVE_GUIDE.md
requirements.txt
```

## 技术栈
- Python 3 / Flask
- Bootstrap 5 / Bootstrap Icons
- Chart.js
- SQLite

## 许可证
MIT License

---

如需帮助或反馈，请联系系统管理员或查阅相关指文档。