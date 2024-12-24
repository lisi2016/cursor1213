# 添加或确认以下设置
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# 文件编码设置
DEFAULT_CHARSET = 'utf-8'
FILE_CHARSET = 'utf-8'

# 数据库编码设置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'charset': 'utf8mb4',
        }
    }
}

# 中间件设置，确保编码中间件在正确位置
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # 添加这行
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'corsheaders',
    'core',  # 确保这行存在
    # ...其他应用...
]

ASGI_APPLICATION = 'homework_system.asgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    },
}

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# 如果你使用 collectstatic
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 安全设置
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'SAMEORIGIN'
CSRF_COOKIE_SECURE = False  # 开发环境设为 False
SESSION_COOKIE_SECURE = False  # 开发环境设为 False

# 允许的主机
ALLOWED_HOSTS = ['*']  # 开发环境可以使用 '*'

# CORS 设置
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://192.168.3.20:9000",
    "http://192.168.3.20:8000",
    "http://localhost:9000",
    "http://localhost:8000",
]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://\d+\.\d+\.\d+\.\d+:9000$",
    r"^http://\d+\.\d+\.\d+\.\d+:8000$",
]

# 允许所有请求头
CORS_ALLOW_HEADERS = ['*']

# 添加日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'channels': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# 添加 MIME 类型
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 静态文件处理
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# 开发环境下使用 WhiteNoise 处理静态文件
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# 添加自定义用户模型设置
AUTH_USER_MODEL = 'core.User'