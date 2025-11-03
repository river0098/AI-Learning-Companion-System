"""
完整的认证服务
支持多种登录方式：微信、手机号、邮箱等
"""

import jwt
import requests
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from storage.auth_database import auth_db, User, AuthAccount, RefreshToken


# ==================== 配置 ====================

JWT_SECRET_KEY = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1小时
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30天

# 微信配置
WECHAT_H5_APPID = "your_h5_appid"
WECHAT_H5_SECRET = "your_h5_secret"
WECHAT_MINI_APPID = "your_mini_appid"
WECHAT_MINI_SECRET = "your_mini_secret"


# ==================== JWT Token管理 ====================

def create_access_token(user_id: int, user_uuid: str, user_type: str) -> str:
    """创建access token（短期）"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "user_id": user_id,
        "user_uuid": user_uuid,
        "user_type": user_type,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict:
    """解码access token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        if payload.get("type") != "access":
            raise ValueError("Invalid token type")

        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.JWTError:
        raise ValueError("Invalid token")


def create_token_pair(user: User, device_id: str = None, ip_address: str = None,
                     user_agent: str = None) -> Dict:
    """创建access token和refresh token对"""
    # 创建access token
    access_token = create_access_token(
        user_id=user.id,
        user_uuid=user.uuid,
        user_type=user.user_type
    )

    # 创建refresh token
    refresh_token = auth_db.create_refresh_token(
        user_id=user.id,
        device_id=device_id,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_days=REFRESH_TOKEN_EXPIRE_DAYS
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token.token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


def refresh_access_token(refresh_token_str: str, ip_address: str = None) -> Dict:
    """使用refresh token刷新access token"""
    # 获取refresh token
    refresh_token = auth_db.get_refresh_token(refresh_token_str)

    if not refresh_token:
        raise ValueError("Invalid refresh token")

    if not refresh_token.is_valid():
        raise ValueError("Refresh token expired or revoked")

    # 检查IP是否变化（可选的安全检查）
    if ip_address and refresh_token.ip_address != ip_address:
        # 记录可疑活动
        pass

    # 获取用户
    user = auth_db.get_user_by_id(refresh_token.user_id)
    if not user or not user.is_active:
        raise ValueError("User not found or inactive")

    # 创建新的access token
    access_token = create_access_token(
        user_id=user.id,
        user_uuid=user.uuid,
        user_type=user.user_type
    )

    # 更新refresh token的最后使用时间
    # 这里可以考虑是否要轮换refresh token

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


# ==================== 手机号+验证码登录 ====================

def send_sms_code(phone_number: str, purpose: str, ip_address: str = None) -> Dict:
    """
    发送短信验证码
    purpose: login, register, bind, reset_password
    """
    # TODO: 这里需要实现频率限制（使用Redis）
    # 例如：同一手机号1分钟内只能发送1次，1小时内最多5次

    # 生成验证码
    code = auth_db.create_sms_code(
        phone_number=phone_number,
        purpose=purpose,
        ip_address=ip_address,
        expires_minutes=5
    )

    # TODO: 调用短信服务商API发送验证码
    # 例如：阿里云、腾讯云等
    print(f"[SMS] 发送验证码到 {phone_number}: {code}")

    # 开发环境返回验证码，生产环境不应返回
    return {
        "success": True,
        "message": "验证码已发送",
        "code": code if True else None  # 仅开发环境
    }


def login_with_phone(phone_number: str, code: str, device_id: str = None,
                    ip_address: str = None, user_agent: str = None) -> Dict:
    """手机号+验证码登录"""
    # 验证验证码
    if not auth_db.verify_sms_code(phone_number, code, 'login'):
        raise ValueError("验证码错误或已过期")

    # 查找或创建认证账号
    auth_account = auth_db.get_auth_account('phone', phone_number)

    if auth_account:
        # 已存在，直接登录
        user = auth_db.get_user_by_id(auth_account.user_id)
    else:
        # 新用户，创建账号
        user = auth_db.create_user(
            nickname=f"手机用户{phone_number[-4:]}",
            user_type='student'
        )

        auth_account = auth_db.create_auth_account(
            user_id=user.id,
            auth_type='phone',
            auth_identifier=phone_number
        )

        # 验证账号
        auth_db.verify_auth_account(auth_account.id)

    # 检查用户状态
    if not user.is_active:
        raise ValueError("账号已被禁用")

    # 记录登录历史
    auth_db.record_login(
        user_id=user.id,
        auth_type='phone',
        ip_address=ip_address,
        user_agent=user_agent,
        device_id=device_id,
        is_success=True
    )

    # 创建token
    tokens = create_token_pair(user, device_id, ip_address, user_agent)

    return {
        "success": True,
        "user": {
            "id": user.id,
            "uuid": user.uuid,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "user_type": user.user_type,
            "membership_type": user.membership_type,
            "is_vip": user.is_vip()
        },
        "tokens": tokens
    }


# ==================== 邮箱+密码登录 ====================

def register_with_email(email: str, password: str, nickname: str = None,
                       user_type: str = 'student') -> Dict:
    """邮箱+密码注册"""
    # 检查邮箱是否已注册
    existing_account = auth_db.get_auth_account('email', email)
    if existing_account:
        raise ValueError("该邮箱已被注册")

    # 创建用户
    user = auth_db.create_user(
        nickname=nickname or f"用户{secrets.token_hex(4)}",
        user_type=user_type
    )

    # 创建邮箱认证账号
    auth_account = auth_db.create_auth_account(
        user_id=user.id,
        auth_type='email',
        auth_identifier=email,
        password=password
    )

    # TODO: 发送验证邮件

    return {
        "success": True,
        "message": "注册成功，请验证邮箱",
        "user_id": user.id
    }


def login_with_email(email: str, password: str, device_id: str = None,
                    ip_address: str = None, user_agent: str = None) -> Dict:
    """邮箱+密码登录"""
    # 查找认证账号
    auth_account = auth_db.get_auth_account('email', email)

    if not auth_account:
        raise ValueError("邮箱或密码错误")

    # 验证密码
    if not auth_account.check_password(password):
        # 记录失败的登录尝试
        auth_db.record_login(
            user_id=auth_account.user_id,
            auth_type='email',
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            is_success=False,
            failure_reason="密码错误"
        )
        raise ValueError("邮箱或密码错误")

    # 获取用户
    user = auth_db.get_user_by_id(auth_account.user_id)

    if not user or not user.is_active:
        raise ValueError("账号不存在或已被禁用")

    # 记录登录历史
    auth_db.record_login(
        user_id=user.id,
        auth_type='email',
        ip_address=ip_address,
        user_agent=user_agent,
        device_id=device_id,
        is_success=True
    )

    # 创建token
    tokens = create_token_pair(user, device_id, ip_address, user_agent)

    return {
        "success": True,
        "user": {
            "id": user.id,
            "uuid": user.uuid,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "user_type": user.user_type,
            "membership_type": user.membership_type,
            "is_vip": user.is_vip()
        },
        "tokens": tokens
    }


# ==================== 微信登录（H5网页授权） ====================

def get_wechat_h5_auth_url(redirect_uri: str, state: str = None) -> str:
    """获取微信H5授权URL"""
    if not state:
        state = secrets.token_urlsafe(16)

    base_url = "https://open.weixin.qq.com/connect/oauth2/authorize"
    params = {
        "appid": WECHAT_H5_APPID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "snsapi_userinfo",  # 或 snsapi_base（仅获取openid）
        "state": state
    }

    param_str = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{base_url}?{param_str}#wechat_redirect"


def login_with_wechat_h5(code: str, device_id: str = None,
                        ip_address: str = None, user_agent: str = None) -> Dict:
    """微信H5登录"""
    # 1. 使用code换取access_token和openid
    token_url = "https://api.weixin.qq.com/sns/oauth2/access_token"
    token_params = {
        "appid": WECHAT_H5_APPID,
        "secret": WECHAT_H5_SECRET,
        "code": code,
        "grant_type": "authorization_code"
    }

    token_response = requests.get(token_url, params=token_params)
    token_data = token_response.json()

    if "errcode" in token_data:
        raise ValueError(f"微信授权失败: {token_data.get('errmsg')}")

    openid = token_data.get("openid")
    access_token = token_data.get("access_token")
    unionid = token_data.get("unionid")  # 可能没有

    # 2. 获取用户信息
    user_info_url = "https://api.weixin.qq.com/sns/userinfo"
    user_info_params = {
        "access_token": access_token,
        "openid": openid,
        "lang": "zh_CN"
    }

    user_info_response = requests.get(user_info_url, params=user_info_params)
    user_info = user_info_response.json()

    nickname = user_info.get("nickname")
    avatar = user_info.get("headimgurl")

    # 3. 查找或创建认证账号
    # 优先使用unionid（跨应用唯一），否则使用openid
    auth_identifier = unionid if unionid else openid
    auth_type = 'wechat_h5'

    auth_account = auth_db.get_auth_account(auth_type, auth_identifier)

    if auth_account:
        # 已存在，直接登录
        user = auth_db.get_user_by_id(auth_account.user_id)

        # 更新用户信息
        session = auth_db.get_session()
        try:
            user.nickname = nickname
            user.avatar = avatar
            session.add(user)
            session.commit()
        finally:
            session.close()
    else:
        # 新用户，创建账号
        user = auth_db.create_user(
            nickname=nickname,
            avatar=avatar,
            user_type='student'
        )

        credential_data = {
            "openid": openid,
            "unionid": unionid,
            "nickname": nickname,
            "avatar": avatar
        }

        auth_account = auth_db.create_auth_account(
            user_id=user.id,
            auth_type=auth_type,
            auth_identifier=auth_identifier,
            credential_data=credential_data
        )

        # 自动验证微信账号
        auth_db.verify_auth_account(auth_account.id)

    # 4. 记录登录历史
    auth_db.record_login(
        user_id=user.id,
        auth_type=auth_type,
        ip_address=ip_address,
        user_agent=user_agent,
        device_id=device_id,
        is_success=True
    )

    # 5. 创建token
    tokens = create_token_pair(user, device_id, ip_address, user_agent)

    return {
        "success": True,
        "user": {
            "id": user.id,
            "uuid": user.uuid,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "user_type": user.user_type,
            "membership_type": user.membership_type,
            "is_vip": user.is_vip()
        },
        "tokens": tokens
    }


# ==================== 微信小程序登录 ====================

def login_with_wechat_mini(code: str, encrypted_data: str = None,
                          iv: str = None, device_id: str = None,
                          ip_address: str = None, user_agent: str = None) -> Dict:
    """微信小程序登录"""
    # 1. code换取session_key和openid
    auth_url = "https://api.weixin.qq.com/sns/jscode2session"
    auth_params = {
        "appid": WECHAT_MINI_APPID,
        "secret": WECHAT_MINI_SECRET,
        "js_code": code,
        "grant_type": "authorization_code"
    }

    auth_response = requests.get(auth_url, params=auth_params)
    auth_data = auth_response.json()

    if "errcode" in auth_data:
        raise ValueError(f"微信授权失败: {auth_data.get('errmsg')}")

    openid = auth_data.get("openid")
    session_key = auth_data.get("session_key")
    unionid = auth_data.get("unionid")  # 可能没有

    # 2. 如果有encrypted_data和iv，解密获取用户信息
    # TODO: 实现微信加密数据解密
    nickname = None
    avatar = None

    if encrypted_data and iv:
        # 解密用户信息
        # from wechat_decrypt import WXBizDataCrypt
        # user_info = WXBizDataCrypt(WECHAT_MINI_APPID, session_key).decrypt(encrypted_data, iv)
        # nickname = user_info.get('nickName')
        # avatar = user_info.get('avatarUrl')
        pass

    # 3. 查找或创建认证账号
    auth_identifier = unionid if unionid else openid
    auth_type = 'wechat_mini'

    auth_account = auth_db.get_auth_account(auth_type, auth_identifier)

    if auth_account:
        user = auth_db.get_user_by_id(auth_account.user_id)

        if nickname and avatar:
            session = auth_db.get_session()
            try:
                user.nickname = nickname
                user.avatar = avatar
                session.add(user)
                session.commit()
            finally:
                session.close()
    else:
        user = auth_db.create_user(
            nickname=nickname or f"小程序用户{secrets.token_hex(4)}",
            avatar=avatar,
            user_type='student'
        )

        credential_data = {
            "openid": openid,
            "unionid": unionid,
            "session_key": session_key
        }

        auth_account = auth_db.create_auth_account(
            user_id=user.id,
            auth_type=auth_type,
            auth_identifier=auth_identifier,
            credential_data=credential_data
        )

        auth_db.verify_auth_account(auth_account.id)

    # 4. 记录登录历史
    auth_db.record_login(
        user_id=user.id,
        auth_type=auth_type,
        ip_address=ip_address,
        user_agent=user_agent,
        device_id=device_id,
        is_success=True
    )

    # 5. 创建token
    tokens = create_token_pair(user, device_id, ip_address, user_agent)

    return {
        "success": True,
        "user": {
            "id": user.id,
            "uuid": user.uuid,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "user_type": user.user_type,
            "membership_type": user.membership_type,
            "is_vip": user.is_vip()
        },
        "tokens": tokens
    }


# ==================== 账号绑定/解绑 ====================

def bind_phone(user_id: int, phone_number: str, code: str) -> Dict:
    """绑定手机号"""
    # 验证验证码
    if not auth_db.verify_sms_code(phone_number, code, 'bind'):
        raise ValueError("验证码错误或已过期")

    # 检查手机号是否已被其他用户绑定
    existing_account = auth_db.get_auth_account('phone', phone_number)
    if existing_account and existing_account.user_id != user_id:
        raise ValueError("该手机号已被其他账号绑定")

    if existing_account:
        # 已经绑定
        return {"success": True, "message": "该手机号已绑定"}

    # 创建绑定
    auth_account = auth_db.create_auth_account(
        user_id=user_id,
        auth_type='phone',
        auth_identifier=phone_number
    )

    auth_db.verify_auth_account(auth_account.id)

    return {"success": True, "message": "绑定成功"}


def unbind_auth(user_id: int, auth_type: str) -> Dict:
    """解绑认证方式"""
    # 获取用户的所有认证方式
    auth_accounts = auth_db.get_user_auth_accounts(user_id)

    if len(auth_accounts) <= 1:
        raise ValueError("至少需要保留一种登录方式")

    # 查找要解绑的认证
    target_account = None
    for account in auth_accounts:
        if account.auth_type == auth_type:
            target_account = account
            break

    if not target_account:
        raise ValueError("未找到该认证方式")

    # 删除认证
    session = auth_db.get_session()
    try:
        session.delete(target_account)
        session.commit()
    finally:
        session.close()

    return {"success": True, "message": "解绑成功"}


if __name__ == "__main__":
    print("=" * 60)
    print("认证服务测试")
    print("=" * 60)

    # 测试手机号登录
    try:
        # 发送验证码
        result = send_sms_code("13800138000", "login", "127.0.0.1")
        print(f"✓ 发送验证码: {result}")

        # 登录
        # login_result = login_with_phone("13800138000", result['code'])
        # print(f"✓ 登录成功: {login_result['user']['nickname']}")
    except Exception as e:
        print(f"✗ 错误: {e}")

    print("\n认证服务就绪！")
