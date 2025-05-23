import re, jwt, datetime, pymysql
from flask import request, jsonify, current_app, Blueprint, g
from werkzeug.security import generate_password_hash, check_password_hash
from database.mysql_client import get_db
from app.utils import error_response

auth_bp = Blueprint('auth', __name__)

# 辅助函数 - 验证令牌
def token_required(f):
    """用于保护需要认证的API端点的装饰器"""
    from functools import wraps
    
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头中获取token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            # if auth_header.startswith('Bearer '):
            # token = auth_header.split(' ')[1]
            token = auth_header
        
        if not token:
            return error_response(message='缺少认证令牌', http_status=401)
        print(token)
        try:
            # 验证令牌
            secret_key = current_app.config.get('SECRET_KEY', 'default_secret_key')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            # 这里可以从数据库中获取用户信息并附加到request中
            # 例如: request.current_user = get_user_by_id(current_user_id)
            g.current_user = {
                'user_id': payload['user_id'],
                'username': payload['username']
            }
        except jwt.ExpiredSignatureError:
            return error_response(message='令牌已过期', http_status=401)
        except jwt.InvalidTokenError:
            return error_response(message='无效的令牌', http_status=401)
        
        return f(*args, **kwargs)
    
    return decorated

# 邮箱格式验证正则表达式
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# 注册的用户 abcd 12345678
@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册接口"""
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    repassword = request.form.get('repassword')
    
    # 检查必要字段是否存在
    if not all([username, password, email, repassword]):
        return error_response(message='缺少必要的注册信息')
    
    # 输入验证
    if len(username) < 4 or len(username) > 50:
        return error_response(message='用户名长度应在4-50个字符之间')
    
    if len(password) < 6:
        return error_response(message='密码长度不能少于6个字符')
    
    if not EMAIL_REGEX.match(email):
        return error_response(message='邮箱格式不正确')
    
    if password != repassword:
        return error_response(message='两次输入的密码不一致')
    
    # 密码加密
    hashed_password = generate_password_hash(password)
    
    # 连接数据库
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # 检查用户名或邮箱是否已存在
            cursor.execute(
                "SELECT * FROM user WHERE username = %s OR email = %s", 
                (username, email)
            )
            if cursor.fetchone():
                return error_response(message='用户名或邮箱已被注册', http_status=409)
            
            # 插入新用户
            cursor.execute(
                "INSERT INTO user (username, password, email) VALUES (%s, %s, %s)",
                (username, hashed_password, email)
            )
        conn.commit()
        
        return jsonify({
            'code': 0,
            'message': '注册成功',
            'data': None
        }), 200
    
    except Exception as e:
        conn.rollback()
        return error_response(message=f'注册失败: {str(e)}', http_status=500)
    finally:
        conn.close()


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录接口"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    # 检查必要字段是否存在
    if not all([username, password]):
        return error_response(message='缺少必要的注册信息')
    
    # 连接数据库
    conn = get_db()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 查询用户信息（支持用户名或邮箱登录）
            cursor.execute(
                "SELECT * FROM user WHERE username = %s ",
                (username,)
            )
            user = cursor.fetchone()
            
            if not user or not check_password_hash(user['password'], password):
                return error_response(message='用户名或密码错误', http_status=401)
            
            # 生成JWT令牌
            payload = {
                'user_id': user['user_id'],
                'username': user['username'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)  # 令牌有效期1天
            }
            
            # 获取密钥 (理想情况下应该从配置中读取)
            secret_key = current_app.config.get('SECRET_KEY', 'default_secret_key')
            
            token = jwt.encode(payload, secret_key, algorithm='HS256')

            # 如果是 PyJWT 1.x 版本，结果是 bytes，要 decode
            if isinstance(token, bytes):
                token = token.decode('utf-8')
            
            return jsonify({
                'code': 0,
                'message': '登录成功',
                'data': token,
                # 'userId': user['user_id']
            }), 200
            
    except Exception as e:
        return error_response(message=f'登录失败: {str(e)}', http_status=500)
    finally:
        conn.close()

# 加一个获取用户信息的接口
@auth_bp.route('/getUserInfo', methods=['GET'])
@token_required
def get_user_info():
    return jsonify({
        'code': 0,
        'message': '获取用户信息成功',
        'data': {
            'userId': g.current_user['user_id'],
            'username': g.current_user['username'],
        }
    }), 200