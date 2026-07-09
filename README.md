# SmartClass - 智能讲义生成系统

> 基于计算机视觉与OCR技术的智能课堂讲义生成平台，自动从教学视频中提取关键内容并生成结构化讲义。
> 项目演示视频：【网课智能讲义生成系统】 https://www.bilibili.com/video/BV1shMp6fEMe/?share_source=copy_web&vd_source=3c36984389e93926780c19850f1f7a6a

---

## 项目简介

SmartClass 是一个面向教育场景的智能讲义生成系统，通过视频帧提取、OCR文字识别、黑板区域检测等技术，自动将教学视频转换为结构化的电子讲义，支持PDF导出和分类管理。

## 核心功能

| 功能模块 | 描述 |
| :--- | :--- |
| **视频上传与处理** | 支持教学视频上传，自动进行帧提取和内容分析 |
| **智能帧提取** | 基于内容变化检测，自动提取关键帧 |
| **OCR文字识别** | 集成 PaddleOCR，支持中英文混合识别 |
| **黑板区域检测** | 基于HSV颜色空间的智能黑板/板书区域检测 |
| **讲义自动生成** | 将识别内容整理为Markdown格式讲义 |
| **PDF导出** | 支持将讲义导出为PDF文件 |
| **讲义管理** | 支持讲义分类、标签、搜索和统计 |
| **用户认证** | 完整的注册、登录、Token认证机制 |
| **语音识别** | 集成 OpenAI Whisper，支持教学视频语音转文字 |

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (Vue 3)                        │
│  Vue Router  │  Pinia  │  Element Plus  │  Axios  │  Vite   │
└─────────────────────────────────────────────────────────────┘
                              │ API
┌─────────────────────────────────────────────────────────────┐
│                      后端层 (Django)                         │
│  Django REST Framework  │  Token Authentication  │  CORS    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    数据处理层                                │
│  OpenCV (帧提取)  │  PaddleOCR (文字识别)  │  Whisper (语音)  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                        数据层                                │
│                    MySQL + File Storage                      │
└─────────────────────────────────────────────────────────────┘
```

## 技术栈

### 前端
- **框架**: Vue 3.5+
- **路由**: Vue Router 4.5+
- **状态管理**: Pinia 3.0+
- **UI组件**: Element Plus 2.9+
- **构建工具**: Vite 6.3+
- **HTTP客户端**: Axios 1.9+

### 后端
- **框架**: Django 4.2+
- **API**: Django REST Framework
- **认证**: Token Authentication
- **数据库**: MySQL 8.0+
- **图像处理**: OpenCV, PaddleOCR
- **视频处理**: ffmpeg-python
- **语音识别**: OpenAI Whisper

## 项目结构

```
smart_class/
├── django1/                    # 主后端服务
│   ├── app/                    # 应用模块
│   │   ├── models.py           # 数据模型
│   │   ├── views.py            # 业务逻辑（视频处理/OCR）
│   │   ├── auth_views.py       # 用户认证视图
│   │   ├── urls.py             # 路由配置
│   │   └── migrations/         # 数据库迁移
│   ├── douxing/                # 项目配置
│   │   ├── settings.py         # Django配置
│   │   └── urls.py             # 根路由
│   └── manage.py               # Django管理脚本
├── django2/                    # 音频处理服务（Whisper语音识别）
│   ├── app/
│   │   ├── views.py            # 语音识别逻辑
│   │   └── urls.py             # 音频处理路由
│   └── audioprocess/           # 项目配置
├── vue/                        # 前端项目
│   ├── src/
│   │   ├── views/              # 页面组件
│   │   │   ├── Home.vue        # 首页
│   │   │   ├── Annotation.vue  # 视频标注
│   │   │   ├── Generating.vue  # 生成过程
│   │   │   ├── Result.vue      # 结果展示
│   │   │   ├── LectureList.vue # 讲义列表
│   │   │   ├── PersonalCenter.vue # 个人中心
│   │   │   └── Login/Register.vue # 认证页面
│   │   ├── components/         # 公共组件
│   │   ├── stores/             # Pinia状态管理
│   │   ├── router/             # 路由配置
│   │   └── main.js             # 入口文件
│   ├── index.html              # HTML模板
│   ├── package.json            # 依赖配置
│   └── vite.config.js          # Vite配置
└── README.md                   # 项目说明
```

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 18+
- MySQL 8.0+
- ffmpeg

### 后端安装

```bash
# 进入后端目录
cd django1

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 数据库配置
# 修改 douxing/settings.py 中的数据库连接信息

# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动服务
python manage.py runserver 0.0.0.0:8000
```

### 音频处理服务（可选）

```bash
# 进入音频服务目录
cd django2

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
# 参考 .env.example 创建 .env 文件

# 启动服务（默认端口8001）
python manage.py runserver 0.0.0.0:8001
```

### 前端安装

```bash
# 进入前端目录
cd vue

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

## API接口

### 用户认证
| 接口 | 方法 | 描述 |
| :--- | :--- | :--- |
| `/api/auth/register/` | POST | 用户注册 |
| `/api/auth/login/` | POST | 用户登录 |
| `/api/auth/user_info/` | GET | 获取用户信息 |
| `/api/auth/logout/` | POST | 用户登出 |

### 讲义管理
| 接口 | 方法 | 描述 |
| :--- | :--- | :--- |
| `/api/lectures/` | GET/POST | 获取/创建讲义列表 |
| `/api/lectures/<id>/` | GET/PUT/DELETE | 获取/更新/删除讲义 |
| `/api/categories/` | GET/POST | 获取/创建分类 |
| `/api/lectures/statistics/` | GET | 获取统计信息 |

### 视频处理
| 接口 | 方法 | 描述 |
| :--- | :--- | :--- |
| `/api/video_upload/` | POST | 上传视频文件 |
| `/api/execute/` | GET | 执行OCR处理 |
| `/api/get_progress/` | GET | 获取处理进度 |
| `/api/get_ocr_summary/` | GET | 获取识别结果 |

## 核心算法

### 黑板区域检测
```
1. HSV颜色空间转换，提取深绿色/青绿色黑板区域
2. 形态学处理（闭运算+开运算）连接区域
3. 轮廓检测与过滤，合并相邻黑板区域
4. 输出外接矩形框坐标
```

### 帧提取策略
```
1. 计算帧间差异，检测内容变化
2. 跳过内容变化较小的连续帧
3. 按时间间隔采样作为补充
4. 保存帧元数据（索引、时间戳）
```

## 项目特点

- **模块化设计**: 前后端分离，服务解耦
- **异步处理**: 视频处理支持进度跟踪
- **图像优化**: 帧图片压缩存储，减少存储空间
- **安全认证**: Token-based认证，权限控制
- **响应式UI**: 现代前端框架，良好用户体验

## 安全注意事项

- **环境变量配置**: 敏感配置（SECRET_KEY、数据库密码等）应通过环境变量设置，参考 `.env.example` 文件
- **Token认证**: 使用Token Authentication替代Session，增强API安全性
- **文件上传**: 限制上传文件大小和类型，防止恶意文件上传
- **权限控制**: 敏感接口添加 `IsAuthenticated` 权限校验
- **CORS配置**: 生产环境应限制允许的源，避免 `CORS_ALLOW_ALL_ORIGINS=True`

### 环境变量配置

在 `django1/` 和 `django2/` 目录下创建 `.env` 文件：

```bash
# django1/.env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DB_NAME=smart_class
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306
```
