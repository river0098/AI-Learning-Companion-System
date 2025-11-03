"""
Redis服务 - 用于验证码、限频、黑名单等
"""

import redis
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import os

class RedisService:
    """Redis服务类"""

    def __init__(self):
        """初始化Redis连接"""
        # 从环境变量读取Redis配置
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_DB', 0))
        redis_password = os.getenv('REDIS_PASSWORD', None)

        try:
            self.redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 测试连接
            self.redis.ping()
            self.enabled = True
            print(f"✅ Redis连接成功: {redis_host}:{redis_port}")
        except Exception as e:
            print(f"⚠️  Redis连接失败，使用内存模拟模式: {e}")
            self.redis = None
            self.enabled = False
            self._memory_cache = {}  # 内存模拟

    # ==================== 验证码相关 ====================

    def save_sms_code(self, phone_number: str, code: str, purpose: str = 'login', ttl: int = 300) -> bool:
        """
        保存短信验证码
        :param phone_number: 手机号
        :param code: 验证码
        :param purpose: 用途（login, bind, reset等）
        :param ttl: 有效期（秒），默认5分钟
        """
        key = f"sms:code:{purpose}:{phone_number}"
        data = {
            'code': code,
            'created_at': datetime.now().isoformat(),
            'attempts': 0  # 验证失败次数
        }

        if self.enabled:
            return self.redis.setex(key, ttl, json.dumps(data))
        else:
            # 内存模拟
            self._memory_cache[key] = {
                'data': data,
                'expires_at': datetime.now() + timedelta(seconds=ttl)
            }
            return True

    def get_sms_code(self, phone_number: str, purpose: str = 'login') -> Optional[Dict[str, Any]]:
        """
        获取短信验证码
        """
        key = f"sms:code:{purpose}:{phone_number}"

        if self.enabled:
            data = self.redis.get(key)
            return json.loads(data) if data else None
        else:
            # 内存模拟
            cache_item = self._memory_cache.get(key)
            if cache_item and datetime.now() < cache_item['expires_at']:
                return cache_item['data']
            return None

    def verify_sms_code(self, phone_number: str, code: str, purpose: str = 'login') -> tuple[bool, str]:
        """
        验证短信验证码
        :return: (是否成功, 错误信息)
        """
        key = f"sms:code:{purpose}:{phone_number}"

        # 检查是否被锁定
        if self.is_phone_locked(phone_number, purpose):
            return False, "验证码错误次数过多，已锁定30分钟"

        data = self.get_sms_code(phone_number, purpose)

        if not data:
            return False, "验证码不存在或已过期"

        if data['code'] != code:
            # 增加失败次数
            data['attempts'] = data.get('attempts', 0) + 1

            if self.enabled:
                ttl = self.redis.ttl(key)
                if ttl > 0:
                    self.redis.setex(key, ttl, json.dumps(data))
            else:
                # 内存模拟
                if key in self._memory_cache:
                    self._memory_cache[key]['data'] = data

            # 失败5次后锁定
            if data['attempts'] >= 5:
                self.lock_phone(phone_number, purpose, 1800)  # 锁定30分钟
                return False, "验证码错误次数过多，已锁定30分钟"

            return False, f"验证码错误，剩余{5 - data['attempts']}次机会"

        # 验证成功，删除验证码
        self.delete_sms_code(phone_number, purpose)
        return True, "验证成功"

    def delete_sms_code(self, phone_number: str, purpose: str = 'login') -> bool:
        """删除验证码"""
        key = f"sms:code:{purpose}:{phone_number}"

        if self.enabled:
            return self.redis.delete(key) > 0
        else:
            return self._memory_cache.pop(key, None) is not None

    # ==================== 频率限制 ====================

    def check_sms_rate_limit(self, phone_number: str) -> tuple[bool, str]:
        """
        检查短信发送频率限制
        - 同一手机号1分钟内最多1条
        - 同一手机号1小时内最多5条
        - 同一手机号1天内最多10条
        :return: (是否允许, 错误信息)
        """
        # 1分钟限制
        key_1min = f"sms:limit:1min:{phone_number}"
        if self._check_limit(key_1min, 1, 60):
            return False, "发送过于频繁，请1分钟后再试"

        # 1小时限制
        key_1hour = f"sms:limit:1hour:{phone_number}"
        if self._check_limit(key_1hour, 5, 3600):
            return False, "发送次数过多，请1小时后再试"

        # 1天限制
        key_1day = f"sms:limit:1day:{phone_number}"
        if self._check_limit(key_1day, 10, 86400):
            return False, "今日发送次数已达上限"

        # 增加计数
        self._increment_limit(key_1min, 60)
        self._increment_limit(key_1hour, 3600)
        self._increment_limit(key_1day, 86400)

        return True, ""

    def check_ip_rate_limit(self, ip_address: str, action: str = 'sms') -> tuple[bool, str]:
        """
        检查IP频率限制
        - 同一IP 1分钟内最多3次短信请求
        - 同一IP 1小时内最多10次短信请求
        :param action: 动作类型（sms, login, register等）
        """
        # 1分钟限制
        key_1min = f"ip:limit:{action}:1min:{ip_address}"
        if self._check_limit(key_1min, 3, 60):
            return False, "请求过于频繁，请稍后再试"

        # 1小时限制
        key_1hour = f"ip:limit:{action}:1hour:{ip_address}"
        if self._check_limit(key_1hour, 10, 3600):
            return False, "请求次数过多，请稍后再试"

        # 增加计数
        self._increment_limit(key_1min, 60)
        self._increment_limit(key_1hour, 3600)

        return True, ""

    def _check_limit(self, key: str, max_count: int, ttl: int) -> bool:
        """
        检查是否超过限制
        :return: True表示已超限
        """
        if self.enabled:
            count = self.redis.get(key)
            return int(count) >= max_count if count else False
        else:
            # 内存模拟
            cache_item = self._memory_cache.get(key)
            if cache_item and datetime.now() < cache_item['expires_at']:
                return cache_item['count'] >= max_count
            return False

    def _increment_limit(self, key: str, ttl: int) -> int:
        """增加计数"""
        if self.enabled:
            count = self.redis.incr(key)
            if count == 1:
                self.redis.expire(key, ttl)
            return count
        else:
            # 内存模拟
            cache_item = self._memory_cache.get(key)
            if cache_item and datetime.now() < cache_item['expires_at']:
                cache_item['count'] += 1
                return cache_item['count']
            else:
                self._memory_cache[key] = {
                    'count': 1,
                    'expires_at': datetime.now() + timedelta(seconds=ttl)
                }
                return 1

    # ==================== 手机号锁定 ====================

    def lock_phone(self, phone_number: str, purpose: str, duration: int = 1800):
        """
        锁定手机号（验证码错误过多）
        :param duration: 锁定时长（秒），默认30分钟
        """
        key = f"phone:locked:{purpose}:{phone_number}"

        if self.enabled:
            self.redis.setex(key, duration, '1')
        else:
            self._memory_cache[key] = {
                'locked': True,
                'expires_at': datetime.now() + timedelta(seconds=duration)
            }

    def is_phone_locked(self, phone_number: str, purpose: str) -> bool:
        """检查手机号是否被锁定"""
        key = f"phone:locked:{purpose}:{phone_number}"

        if self.enabled:
            return self.redis.exists(key) > 0
        else:
            cache_item = self._memory_cache.get(key)
            return cache_item and datetime.now() < cache_item['expires_at']

    # ==================== Token黑名单 ====================

    def add_token_to_blacklist(self, token: str, expires_in: int):
        """
        将token加入黑名单
        :param token: Token字符串
        :param expires_in: 过期时间（秒）
        """
        key = f"token:blacklist:{token}"

        if self.enabled:
            self.redis.setex(key, expires_in, '1')
        else:
            self._memory_cache[key] = {
                'blacklisted': True,
                'expires_at': datetime.now() + timedelta(seconds=expires_in)
            }

    def is_token_blacklisted(self, token: str) -> bool:
        """检查token是否在黑名单中"""
        key = f"token:blacklist:{token}"

        if self.enabled:
            return self.redis.exists(key) > 0
        else:
            cache_item = self._memory_cache.get(key)
            return cache_item and datetime.now() < cache_item['expires_at']

    # ==================== 登录异常检测 ====================

    def record_login(self, user_id: int, ip_address: str, location: str = None, device_id: str = None):
        """
        记录登录信息（用于异常检测）
        """
        key = f"user:login:{user_id}"
        login_info = {
            'ip': ip_address,
            'location': location,
            'device_id': device_id,
            'timestamp': datetime.now().isoformat()
        }

        if self.enabled:
            # 保存最近10次登录
            self.redis.lpush(key, json.dumps(login_info))
            self.redis.ltrim(key, 0, 9)
            self.redis.expire(key, 86400 * 30)  # 保留30天
        else:
            if key not in self._memory_cache:
                self._memory_cache[key] = []
            self._memory_cache[key].insert(0, login_info)
            self._memory_cache[key] = self._memory_cache[key][:10]

    def check_login_anomaly(self, user_id: int, current_ip: str, current_location: str = None) -> tuple[bool, str]:
        """
        检查登录是否异常
        :return: (是否异常, 异常原因)
        """
        key = f"user:login:{user_id}"

        if self.enabled:
            recent_logins = self.redis.lrange(key, 0, 9)
            login_records = [json.loads(r) for r in recent_logins]
        else:
            login_records = self._memory_cache.get(key, [])

        if not login_records:
            return False, ""

        # 检查是否在短时间内从不同IP登录
        recent_ips = set()
        now = datetime.now()

        for record in login_records:
            record_time = datetime.fromisoformat(record['timestamp'])
            if (now - record_time).seconds < 3600:  # 1小时内
                recent_ips.add(record['ip'])

        if len(recent_ips) >= 3:
            return True, "检测到异常登录：1小时内有3个不同IP登录"

        # 检查地理位置变化（如果有）
        if current_location and login_records:
            last_location = login_records[0].get('location')
            if last_location and last_location != current_location:
                last_time = datetime.fromisoformat(login_records[0]['timestamp'])
                if (now - last_time).seconds < 600:  # 10分钟内
                    return True, f"检测到异常登录：短时间内从 {last_location} 切换到 {current_location}"

        return False, ""

    # ==================== CAPTCHA支持 ====================

    def save_captcha_token(self, token: str, valid: bool = True, ttl: int = 300):
        """
        保存CAPTCHA验证结果
        :param token: CAPTCHA token
        :param valid: 是否通过验证
        :param ttl: 有效期（秒）
        """
        key = f"captcha:token:{token}"

        if self.enabled:
            self.redis.setex(key, ttl, '1' if valid else '0')
        else:
            self._memory_cache[key] = {
                'valid': valid,
                'expires_at': datetime.now() + timedelta(seconds=ttl)
            }

    def verify_captcha_token(self, token: str) -> bool:
        """验证CAPTCHA token"""
        if not token:
            return False

        key = f"captcha:token:{token}"

        if self.enabled:
            result = self.redis.get(key)
            if result:
                self.redis.delete(key)  # 一次性使用
                return result == '1'
            return False
        else:
            cache_item = self._memory_cache.pop(key, None)
            if cache_item and datetime.now() < cache_item['expires_at']:
                return cache_item['valid']
            return False

    # ==================== 设备指纹 ====================

    def save_device_info(self, user_id: int, device_id: str, device_info: Dict[str, Any]):
        """
        保存设备信息
        """
        key = f"user:device:{user_id}:{device_id}"

        if self.enabled:
            self.redis.setex(key, 86400 * 90, json.dumps(device_info))  # 保留90天
        else:
            self._memory_cache[key] = {
                'info': device_info,
                'expires_at': datetime.now() + timedelta(days=90)
            }

    def is_device_trusted(self, user_id: int, device_id: str) -> bool:
        """检查设备是否受信任"""
        key = f"user:device:{user_id}:{device_id}"

        if self.enabled:
            return self.redis.exists(key) > 0
        else:
            cache_item = self._memory_cache.get(key)
            return cache_item and datetime.now() < cache_item['expires_at']


# 全局Redis服务实例
redis_service = RedisService()
