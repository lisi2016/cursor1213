# 作业管理系统

## 项目简介
这是一个基于Django和WebSocket的作业管理系统,主要用于教师分发作业和学生提交作业的场景。系统支持实时显示学生在线状态,作业分发,成绩评定等功能。

## 主要功能

### 1. 用户管理
- 教师和学生两种角色
- 支持批量导入学生信息
- 学生默认密码为学号

### 2. 实时监控
- 实时显示学生在线状态
- 显示学生登录IP和时间
- WebSocket实时更新连接状态

### 3. 作业管理
- 教师可以上传和分发作业
- 支持批量分发作业给在线学生
- 学生可以下载分配给自己的作业
- 教师可以删除已分发的作业

### 4. 成绩管理
- 教师可以对作业进行评分(A/B/C/D)
- 支持导出成绩统计表
- 可按班级筛选导出成绩

## 技术栈
- 后端: Django 4.x
- 前端: HTML5, CSS3, JavaScript
- WebSocket: Django Channels
- 数据库: SQLite
- UI框架: Bootstrap 5

## 系统要求
- Python 3.8+
- Django 4.x
- Channels 4.x
- Redis(可选,用于生产环境)

## 安装步骤
1. 克隆项目
git clone

2. 安装依赖
pip install -r requirements.txt
3. 配置数据库
python manage.py migrate
4. 运行开发服务器
python manage.py runserver
## 项目结构
omework_system/
├── core/ # 主应用
│ ├── consumers.py # WebSocket消费者
│ ├── models.py # 数据模型
│ ├── views.py # 视图函数
│ └── routing.py # WebSocket路由
├── static/ # 静态文件
│ └── core/
│ ├── css/ # 样式文件
│ └── js/ # JavaScript文件
├── templates/ # 模板文件
│ └── core/
│ ├── base.html # 基础模板
│ ├── login.html # 登录页面
│ └── teacher_dashboard.html # 教师仪表盘
└── manage.py

## 主要功能说明

### 教师端
1. 登录系统后可以看到在线学生列表
2. 可以上传作业文件并分发给选定的学生
3. 可以查看学生的作业完成情况
4. 可以对学生作业进行评分
5. 可以导出成绩统计表

### 学生端
1. 使用学号登录系统
2. 可以查看和下载分配给自己的作业
3. 可以查看自己的作业成绩

## 注意事项
1. 首次使用需要导入学生信息
2. 建议使用最新版本的Chrome或Firefox浏览器
3. 确保WebSocket连接正常
4. 定期备份数据库

## 开发者
- [开发者名字]

## 许可证
MIT License
