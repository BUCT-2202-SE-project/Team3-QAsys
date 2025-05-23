import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Config:
    API_KEY = os.getenv('API_KEY')
    # JWT密钥，实际项目中应该使用环境变量设置复杂的随机字符串
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key_change_in_production')
    # MySQL 数据库配置
    MYSQL_HOST = os.getenv('MYSQL_HOST')                    # MySQL 服务器地址
    MYSQL_USER = os.getenv('MYSQL_USER')                    # MySQL 用户名
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')            # MySQL 密码
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')            # MySQL 数据库名称
    MYSQL_CHARSET = os.getenv('MYSQL_CHARSET')              # MySQL 字符集

print(Config.API_KEY)