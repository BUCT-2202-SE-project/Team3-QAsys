import pymysql
from flask import current_app, g
import logging
import os
def get_db():
    """获取数据库连接，使用环境变量而非硬编码"""
    try:
        # 使用的数据在.env文件中
        # 使用 current_app.config 而非硬编码值
        # conn = pymysql.connect(
        #     host=current_app.config['MYSQL_HOST'],
        #     user=current_app.config['MYSQL_USER'],
        #     password=current_app.config['MYSQL_PASSWORD'],
        #     database=current_app.config['MYSQL_DATABASE'],
        #     charset=current_app.config.get('MYSQL_CHARSET', 'utf8mb4')  # 默认 utf8mb4
        # )
        conn = pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),  # 确保密码被正确读取
            database=os.getenv('MYSQL_DATABASE', 'museum'),
            charset=os.getenv('MYSQL_CHARSET', 'utf8mb4')
           )

        return conn
    except pymysql.MySQLError as e:
        logging.error(f"数据库连接失败: {e}")
        raise

def test_connection():
    """测试数据库连接是否成功"""
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        conn.close()
        return True, "数据库连接成功"
    except Exception as e:
        return False, f"数据库连接失败: {str(e)}"

def init_db(app):
    with app.app_context():
        pass  # 这里可以添加数据库初始化逻辑

if __name__ == "__main__":
    # 测试数据库连接
    success, message = test_connection()
    if success:
        print(message)
    else:
        print(message)