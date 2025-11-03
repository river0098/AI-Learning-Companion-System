"""
增强版认证服务 - 包含完整的安全措施和账号合并功能
"""

import secrets
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import requests

from storage.auth_database import auth_db
from services.redis_service import redis_service

# ==================== 配置 ====================

# 微信H5配置
WECHAT_H5_APPID = "your_h5_appid"
WECHAT_H5_SECRET = "your_h5_secret"
WECHAT_H5_REDIRECT_URI = "http://yourdomain.com/api/auth/wechat/callback"

# 微信小程序配置
WECHAT_MINI_APPID = "your_mini_appid"
WECHAT_MINI_SECRET = "your_mini_secret"

# JWT配置
JWT_SECRET = "your-secret-key-change-this-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 1
REFRESH_TOKEN_EXPIRE_DAYS = 30

# 短信配置
SMS_API_KEY = "your_sms_api_key"
SMS_PROVIDER = "aliyun"  # aliyun, tencent, etc.


# ==================== 短信服务（增强版） ====================

def send_sms_code(
    phone_number: str,
    purpose: str = "login",
    ip_address: str = None,
    captcha_token: str = None
) -> Dict:
    """
    发送短信验证码（增强版，带限频和CAPTCHA）

    :param phone_number: 手机号
    :param purpose: 用途（login, bind, reset）
    :param ip_address: IP地址
    :param captcha_token: CAPTCHA验证token（可选）
    :return: {"success": bool, "error": str, "code": str (仅测试环境)}
    """
    # 1. 验证手机号格式
    if not _validate_phone_number(phone_number):
        return {"success": False, "error": "手机号格式不正确"}

    # 2. 检查IP频率限制
    if ip_address:
        ip_allowed, ip_error = redis_service.check_ip_rate_limit(ip_address, 'sms')
        if not ip_allowed:
            # IP请求过多，需要CAPTCHA
            if not captcha_token or not redis_service.verify_captcha_token(captcha_token):
                return {
                    "success": False,
                    "error": ip_error,
                    "require_captcha": True
                }

    # 3. 检查手机号频率限制
    phone_allowed, phone_error = redis_service.check_sms_rate_limit(phone_number)
    if not phone_allowed:
        return {"success": False, "error": phone_error}

    # 4. 生成验证码
    code = _generate_sms_code()

    # 5. 保存到Redis（5分钟有效期）
    redis_service.save_sms_code(phone_number, code, purpose, ttl=300)

    # 6. 发送短信
    sms_sent = _send_sms_via_provider(phone_number, code, purpose)

    if sms_sent:
        # 生产环境不返回code
        result = {"success": True, "message": "验证码已发送"}
        # 测试环境返回code方便调试
        if _is_test_mode():
            result["code"] = code
        return result
    else:
        return {"success": False, "error": "短信发送失败，请稍后重试"}


def _generate_sms_code(length: int = 6) -> str:
    """生成随机验证码"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])


def _validate_phone_number(phone: str) -> bool:
    """验证手机号格式（中国大陆）"""
    import re
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))


def _send_sms_via_provider(phone_number: str, code: str, purpose: str) -> bool:
    """
    通过短信服务商发送验证码

    TODO: 集成真实短信服务
    - 阿里云短信: https://help.aliyun.com/document_detail/101414.html
    - 腾讯云短信: https://cloud.tencent.com/document/product/382
    """
    # 测试模式：打印到控制台
    print(f"📱 [SMS] 发送验证码到 {phone_number}: {code} (用途: {purpose})")

    # 生产环境示例代码：
    # if SMS_PROVIDER == 'aliyun':
    #     from aliyunsdkcore.client import AcsClient
    #     from aliyunsdkcore.request import CommonRequest
    #
    #     client = AcsClient('<accessKeyId>', '<accessSecret>', 'cn-hangzhou')
    #     request = CommonRequest()
    #     request.set_domain('dysmsapi.aliyuncs.com')
    #     request.set_method('POST')
    #     request.set_version('2017-05-25')
    #     request.set_action_name('SendSms')
    #     request.add_query_param('PhoneNumbers', phone_number)
    #     request.add_query_param('SignName', '您的签名')
    #     request.add_query_param('TemplateCode', 'SMS_123456789')
    #     request.add_query_param('TemplateParam', json.dumps({'code': code}))
    #
    #     response = client.do_action_with_exception(request)
    #     return json.loads(response)['Code'] == 'OK'

    return True


def _is_test_mode() -> bool:
    """检查是否为测试模式"""
    import os
    return os.getenv('ENVIRONMENT', 'development') != 'production'


# ==================== 手机号登录（增强版） ====================

def login_with_phone_enhanced(
    phone_number: str,
    code: str,
    device_id: str = None,
    ip_address: str = None,
    user_agent: str = None,
    location: str = None
) -> Dict:
    """
    手机号+验证码登录（增强版，包含异常检测）

    :return: {
        "success": bool,
        "user": {...},
        "tokens": {...},
        "is_new_user": bool,
        "warning": str (可选，异常登录警告)
    }
    """
    # 1. 验证验证码
    success, error = redis_service.verify_sms_code(phone_number, code, 'login')
    if not success:
        return {"success": False, "error": error}

    # 2. 查找或创建用户
    auth_account = auth_db.get_auth_account('phone', phone_number)

    if auth_account:
        # 已有账号
        user = auth_db.get_user_by_id(auth_account.user_id)
        is_new_user = False
    else:
        # 首次登录，自动注册
        user = auth_db.create_user(
            nickname=f"用户{phone_number[-4:]}",
            user_type='student'
        )
        auth_account = auth_db.create_auth_account(
            user_id=user.id,
            auth_type='phone',
            auth_identifier=phone_number,
            is_verified=True
        )
        is_new_user = True

    # 3. 异常登录检测
    warning = None
    if not is_new_user:
        is_anomaly, anomaly_reason = redis_service.check_login_anomaly(
            user.id, ip_address, location
        )
        if is_anomaly:
            warning = anomaly_reason
            # TODO: 发送异常登录通知（短信/微信）
            _send_anomaly_notification(user.id, phone_number, anomaly_reason)

    # 4. 记录登录信息
    redis_service.record_login(user.id, ip_address, location, device_id)
    auth_db.record_login(user.id, 'phone', ip_address, user_agent, device_id, success=True)

    # 5. 保存设备信息
    if device_id:
        device_info = {
            'user_agent': user_agent,
            'ip': ip_address,
            'first_seen': datetime.now().isoformat()
        }
        redis_service.save_device_info(user.id, device_id, device_info)

    # 6. 生成Token
    tokens = create_token_pair(user, device_id, ip_address, user_agent)

    return {
        "success": True,
        "user": {
            "id": user.id,
            "uuid": user.uuid,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "user_type": user.user_type,
            "membership_type": user.membership_type
        },
        "tokens": tokens,
        "is_new_user": is_new_user,
        "warning": warning
    }


def _send_anomaly_notification(user_id: int, phone_number: str, reason: str):
    """发送异常登录通知"""
    print(f"🔔 [异常登录通知] 用户{user_id}: {reason}")
    # TODO: 集成短信/微信通知
    # send_sms_notification(phone_number, f"检测到异常登录：{reason}，如非本人操作请立即修改密码")


# ==================== 账号绑定（增强版，带冲突处理） ====================

def bind_phone_enhanced(
    user_id: int,
    phone_number: str,
    code: str
) -> Dict:
    """
    绑定手机号（增强版，处理冲突）

    :return: {
        "success": bool,
        "conflict": bool (可选，是否存在冲突),
        "conflict_user_id": int (可选，冲突的用户ID),
        "merge_token": str (可选，用于账号合并的token)
    }
    """
    # 1. 验证验证码
    success, error = redis_service.verify_sms_code(phone_number, code, 'bind')
    if not success:
        return {"success": False, "error": error}

    # 2. 检查当前用户是否已绑定手机号
    existing_phone = auth_db.get_auth_account_by_user('phone', user_id)
    if existing_phone:
        return {"success": False, "error": "您已绑定手机号，请先解绑"}

    # 3. 检查手机号是否已被其他用户绑定
    existing_account = auth_db.get_auth_account('phone', phone_number)

    if existing_account and existing_account.user_id != user_id:
        # 冲突：手机号已被另一个用户绑定
        # 生成合并token
        merge_token = _generate_merge_token(user_id, existing_account.user_id, 'phone', phone_number)

        return {
            "success": False,
            "conflict": True,
            "error": "该手机号已被其他账号使用",
            "conflict_user_id": existing_account.user_id,
            "merge_token": merge_token,
            "message": "检测到您可能拥有多个账号，是否合并账号？"
        }

    # 4. 无冲突，直接绑定
    auth_db.create_auth_account(
        user_id=user_id,
        auth_type='phone',
        auth_identifier=phone_number,
        is_verified=True
    )

    return {
        "success": True,
        "message": "手机号绑定成功",
        "auth_account": {
            "auth_type": "phone",
            "auth_identifier": phone_number,
            "is_verified": True
        }
    }


def _generate_merge_token(from_user_id: int, to_user_id: int, auth_type: str, identifier: str) -> str:
    """
    生成账号合并token
    """
    token = secrets.token_urlsafe(32)
    merge_data = {
        'from_user_id': from_user_id,
        'to_user_id': to_user_id,
        'auth_type': auth_type,
        'identifier': identifier,
        'created_at': datetime.now().isoformat()
    }

    # 保存到Redis，15分钟有效
    import json
    if redis_service.enabled:
        redis_service.redis.setex(f"merge:token:{token}", 900, json.dumps(merge_data))
    else:
        redis_service._memory_cache[f"merge:token:{token}"] = {
            'data': merge_data,
            'expires_at': datetime.now() + timedelta(seconds=900)
        }

    return token


# ==================== 账号合并 ====================

def merge_accounts(merge_token: str, confirmation_code: str = None) -> Dict:
    """
    合并账号

    :param merge_token: 合并token
    :param confirmation_code: 确认码（短信验证码）
    :return: {"success": bool, "merged_user": {...}}
    """
    import json

    # 1. 获取合并信息
    key = f"merge:token:{merge_token}"

    if redis_service.enabled:
        data = redis_service.redis.get(key)
        if not data:
            return {"success": False, "error": "合并请求已过期，请重新操作"}
        merge_data = json.loads(data)
    else:
        cache_item = redis_service._memory_cache.get(key)
        if not cache_item or datetime.now() >= cache_item['expires_at']:
            return {"success": False, "error": "合并请求已过期，请重新操作"}
        merge_data = cache_item['data']

    from_user_id = merge_data['from_user_id']
    to_user_id = merge_data['to_user_id']
    auth_type = merge_data['auth_type']
    identifier = merge_data['identifier']

    # 2. 验证确认码（可选，增强安全性）
    if confirmation_code:
        success, error = redis_service.verify_sms_code(identifier, confirmation_code, 'merge')
        if not success:
            return {"success": False, "error": "验证码错误"}

    # 3. 执行合并
    try:
        # 将from_user的所有auth_accounts转移到to_user
        from_accounts = auth_db.session.query(auth_db.AuthAccount).filter(
            auth_db.AuthAccount.user_id == from_user_id
        ).all()

        for account in from_accounts:
            # 检查to_user是否已有相同类型的认证
            existing = auth_db.get_auth_account_by_user(account.auth_type, to_user_id)
            if not existing:
                account.user_id = to_user_id
            # 如果已存在，保留to_user的，删除from_user的
            else:
                auth_db.session.delete(account)

        # 转移refresh_tokens
        from_tokens = auth_db.session.query(auth_db.RefreshToken).filter(
            auth_db.RefreshToken.user_id == from_user_id,
            auth_db.RefreshToken.is_revoked == False
        ).all()

        for token in from_tokens:
            token.user_id = to_user_id

        # 记录合并日志
        _log_account_merge(from_user_id, to_user_id, auth_type, identifier)

        # 标记from_user为已合并（不删除，保留审计记录）
        from_user = auth_db.get_user_by_id(from_user_id)
        from_user.is_active = False
        from_user.nickname = f"[已合并]{from_user.nickname}"

        auth_db.session.commit()

        # 删除merge token
        if redis_service.enabled:
            redis_service.redis.delete(key)
        else:
            redis_service._memory_cache.pop(key, None)

        # 返回合并后的用户信息
        merged_user = auth_db.get_user_by_id(to_user_id)

        return {
            "success": True,
            "message": "账号合并成功",
            "merged_user": {
                "id": merged_user.id,
                "uuid": merged_user.uuid,
                "nickname": merged_user.nickname,
                "user_type": merged_user.user_type
            }
        }

    except Exception as e:
        auth_db.session.rollback()
        print(f"❌ 账号合并失败: {e}")
        return {"success": False, "error": "账号合并失败，请联系客服"}


def _log_account_merge(from_user_id: int, to_user_id: int, auth_type: str, identifier: str):
    """记录账号合并日志"""
    # TODO: 保存到专门的审计表
    print(f"📝 [账号合并] 用户{from_user_id} → 用户{to_user_id} (通过{auth_type}: {identifier})")


# ==================== Token管理（增强版） ====================

def create_token_pair(
    user,
    device_id: str = None,
    ip_address: str = None,
    user_agent: str = None
) -> Dict:
    """
    创建Access Token和Refresh Token
    """
    import jwt

    # Access Token（短期，1小时）
    access_payload = {
        "user_id": user.id,
        "username": user.username if hasattr(user, 'username') else user.nickname,
        "user_type": user.user_type,
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    }
    access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # Refresh Token（长期，30天）
    refresh_token_str = secrets.token_urlsafe(32)

    # 保存Refresh Token到数据库
    refresh_token = auth_db.create_refresh_token(
        user_id=user.id,
        token=refresh_token_str,
        device_id=device_id,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_HOURS * 3600
    }


def refresh_access_token_enhanced(refresh_token: str, ip_address: str = None) -> Dict:
    """
    刷新Access Token（增强版，检查黑名单）
    """
    # 1. 检查refresh token是否在黑名单
    if redis_service.is_token_blacklisted(refresh_token):
        return {"success": False, "error": "Token已失效，请重新登录"}

    # 2. 验证refresh token
    token_record = auth_db.get_refresh_token(refresh_token)

    if not token_record:
        return {"success": False, "error": "Invalid refresh token"}

    if token_record.is_revoked:
        return {"success": False, "error": "Token已被撤销"}

    if datetime.now() > token_record.expires_at:
        return {"success": False, "error": "Token已过期"}

    # 3. 检查IP是否一致（可选，严格模式）
    # if ip_address and token_record.ip_address != ip_address:
    #     return {"success": False, "error": "IP地址不匹配"}

    # 4. 获取用户信息
    user = auth_db.get_user_by_id(token_record.user_id)

    if not user or not user.is_active:
        return {"success": False, "error": "用户不存在或已禁用"}

    # 5. 生成新的Access Token
    import jwt

    access_payload = {
        "user_id": user.id,
        "username": user.username if hasattr(user, 'username') else user.nickname,
        "user_type": user.user_type,
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    }
    access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # 6. 更新last_used时间
    token_record.last_used = datetime.now()
    auth_db.session.commit()

    return {
        "success": True,
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_HOURS * 3600
    }


def logout_enhanced(refresh_token: str):
    """
    登出（增强版，撤销token并加入黑名单）
    """
    # 1. 撤销refresh token
    auth_db.revoke_refresh_token(refresh_token)

    # 2. 将refresh token加入黑名单（防止在过期前被使用）
    redis_service.add_token_to_blacklist(
        refresh_token,
        expires_in=REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )

    return {"success": True, "message": "登出成功"}


def logout_all_devices(user_id: int):
    """
    登出所有设备
    """
    # 撤销用户所有refresh tokens
    tokens = auth_db.session.query(auth_db.RefreshToken).filter(
        auth_db.RefreshToken.user_id == user_id,
        auth_db.RefreshToken.is_revoked == False
    ).all()

    for token in tokens:
        token.is_revoked = True
        token.revoked_at = datetime.now()

        # 加入黑名单
        redis_service.add_token_to_blacklist(
            token.token,
            expires_in=REFRESH_TOKEN_EXPIRE_DAYS * 86400
        )

    auth_db.session.commit()

    return {"success": True, "message": f"已登出{len(tokens)}个设备"}


# ==================== 其他增强功能 ====================

def get_user_auth_accounts_enhanced(user_id: int) -> List[Dict]:
    """
    获取用户所有认证账号（增强版，包含安全信息）
    """
    accounts = auth_db.get_user_auth_accounts(user_id)

    result = []
    for acc in accounts:
        # 脱敏处理
        masked_identifier = _mask_sensitive_data(acc.auth_identifier, acc.auth_type)

        result.append({
            "auth_type": acc.auth_type,
            "auth_identifier": masked_identifier,
            "is_verified": acc.is_verified,
            "is_primary": False,  # TODO: 实现主认证方式标记
            "bound_at": acc.created_at.isoformat() if acc.created_at else None,
            "last_used": None  # TODO: 从login_history获取
        })

    return result


def _mask_sensitive_data(data: str, data_type: str) -> str:
    """脱敏处理"""
    if data_type == 'phone':
        if len(data) == 11:
            return f"{data[:3]}****{data[-4:]}"
        return data
    elif data_type == 'email':
        if '@' in data:
            name, domain = data.split('@')
            if len(name) > 3:
                return f"{name[:3]}***@{domain}"
        return data
    else:
        return "***" + data[-4:] if len(data) > 4 else "***"


def check_user_security_status(user_id: int) -> Dict:
    """
    检查用户账号安全状态

    :return: {
        "security_score": int,  # 0-100
        "has_phone": bool,
        "has_email": bool,
        "has_password": bool,
        "linked_accounts_count": int,
        "recommendations": List[str]
    }
    """
    accounts = auth_db.get_user_auth_accounts(user_id)

    has_phone = any(a.auth_type == 'phone' for a in accounts)
    has_email = any(a.auth_type == 'email' for a in accounts)
    has_password = any(a.auth_type == 'email' and a.password_hash for a in accounts)

    # 计算安全分数
    score = 0
    if has_phone:
        score += 30
    if has_email:
        score += 20
    if has_password:
        score += 20
    if len(accounts) >= 2:
        score += 20
    if len(accounts) >= 3:
        score += 10

    # 安全建议
    recommendations = []
    if not has_phone:
        recommendations.append("绑定手机号以提升账号安全性")
    if not has_email:
        recommendations.append("绑定邮箱以便找回密码")
    if len(accounts) < 2:
        recommendations.append("建议至少绑定两种登录方式")

    return {
        "security_score": min(score, 100),
        "has_phone": has_phone,
        "has_email": has_email,
        "has_password": has_password,
        "linked_accounts_count": len(accounts),
        "recommendations": recommendations
    }
