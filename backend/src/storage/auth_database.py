"""
多凭证认证系统数据库模型
支持微信、手机号、邮箱等多种登录方式
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import hashlib
import secrets
import uuid

Base = declarative_base()


class User(Base):
    """主用户表 - 一个用户可以有多个登录凭证"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    # 基本信息
    nickname = Column(String(100))
    avatar = Column(String(500))
    user_type = Column(String(20), default='student')  # student, parent, teacher

    # 会员信息
    membership_type = Column(String(20), default='free')  # free, vip
    membership_expires = Column(DateTime)

    # 状态
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # 是否已验证（手机号或邮箱）

    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_login = Column(DateTime)

    # 关联
    auth_accounts = relationship('AuthAccount', back_populates='user', cascade='all, delete-orphan')
    refresh_tokens = relationship('RefreshToken', back_populates='user', cascade='all, delete-orphan')
    login_history = relationship('LoginHistory', back_populates='user', cascade='all, delete-orphan')

    def is_vip(self) -> bool:
        """检查是否为VIP会员"""
        if self.membership_type == 'vip':
            if self.membership_expires:
                return datetime.now() < self.membership_expires
            return True
        return False

    def get_daily_limit(self) -> int:
        """获取每日使用时长限制（秒）"""
        if self.is_vip():
            return -1  # 无限制
        return 30 * 60  # 普通会员30分钟


class AuthAccount(Base):
    """认证账号表 - 存储各种登录凭证"""
    __tablename__ = 'auth_accounts'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # 认证类型：wechat_h5, wechat_mini, phone, email, apple, google, guest
    auth_type = Column(String(20), nullable=False)

    # 认证标识（openid, unionid, phone, email等）
    auth_identifier = Column(String(200), nullable=False)

    # 凭证数据（JSON格式存储额外信息）
    # 微信：openid, unionid, session_key
    # 手机：phone_number
    # 邮箱：email, password_hash
    credential_data = Column(Text)

    # 密码（仅用于邮箱登录）
    password_hash = Column(String(256))
    salt = Column(String(64))

    # 验证状态
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime)

    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    user = relationship('User', back_populates='auth_accounts')

    # 索引
    __table_args__ = (
        Index('idx_auth_type_identifier', 'auth_type', 'auth_identifier', unique=True),
    )

    def set_password(self, password: str):
        """设置密码（仅用于邮箱登录）"""
        self.salt = secrets.token_hex(32)
        self.password_hash = self._hash_password(password, self.salt)

    def check_password(self, password: str) -> bool:
        """验证密码"""
        if not self.password_hash or not self.salt:
            return False
        return self.password_hash == self._hash_password(password, self.salt)

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """密码哈希"""
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


class RefreshToken(Base):
    """Refresh Token表 - 用于刷新access token"""
    __tablename__ = 'refresh_tokens'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Token
    token = Column(String(256), unique=True, nullable=False)

    # 设备信息
    device_id = Column(String(100))
    device_name = Column(String(200))
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    # 过期时间
    expires_at = Column(DateTime, nullable=False)

    # 是否已撤销
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime)

    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    last_used = Column(DateTime, default=datetime.now)

    # 关联
    user = relationship('User', back_populates='refresh_tokens')

    # 索引
    __table_args__ = (
        Index('idx_token', 'token'),
        Index('idx_user_device', 'user_id', 'device_id'),
    )

    def is_valid(self) -> bool:
        """检查token是否有效"""
        if self.is_revoked:
            return False
        if datetime.now() > self.expires_at:
            return False
        return True


class LoginHistory(Base):
    """登录历史表"""
    __tablename__ = 'login_history'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # 登录信息
    auth_type = Column(String(20))  # 登录方式
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    device_id = Column(String(100))

    # 地理位置（可选）
    location = Column(String(200))

    # 登录状态
    is_success = Column(Boolean, default=True)
    failure_reason = Column(String(200))

    # 时间戳
    created_at = Column(DateTime, default=datetime.now)

    # 关联
    user = relationship('User', back_populates='login_history')

    # 索引
    __table_args__ = (
        Index('idx_user_time', 'user_id', 'created_at'),
        Index('idx_ip_time', 'ip_address', 'created_at'),
    )


class SMSVerification(Base):
    """短信验证码表（建议迁移到Redis）"""
    __tablename__ = 'sms_verifications'

    id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), nullable=False)
    code = Column(String(6), nullable=False)

    # 用途：login, register, bind, reset_password
    purpose = Column(String(20), nullable=False)

    # 验证状态
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime)

    # IP限制
    ip_address = Column(String(45))

    # 过期时间
    expires_at = Column(DateTime, nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.now)

    # 索引
    __table_args__ = (
        Index('idx_phone_purpose', 'phone_number', 'purpose'),
        Index('idx_expires', 'expires_at'),
    )

    def is_valid(self) -> bool:
        """检查验证码是否有效"""
        if self.is_used:
            return False
        if datetime.now() > self.expires_at:
            return False
        return True


# ==================== 数据库管理器 ====================

class AuthDatabaseManager:
    """认证数据库管理器"""

    def __init__(self, db_path: str = "../../data/auth.db"):
        """初始化数据库连接"""
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()

    # ==================== 用户管理 ====================

    def create_user(self, nickname: str = None, avatar: str = None,
                   user_type: str = 'student') -> User:
        """创建新用户"""
        session = self.get_session()
        try:
            user = User(
                nickname=nickname or f"用户{secrets.token_hex(4)}",
                avatar=avatar,
                user_type=user_type
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()

    def get_user_by_id(self, user_id: int) -> User:
        """通过ID获取用户"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.id == user_id).first()
        finally:
            session.close()

    def get_user_by_uuid(self, user_uuid: str) -> User:
        """通过UUID获取用户"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.uuid == user_uuid).first()
        finally:
            session.close()

    # ==================== 认证账号管理 ====================

    def create_auth_account(self, user_id: int, auth_type: str,
                          auth_identifier: str, credential_data: dict = None,
                          password: str = None) -> AuthAccount:
        """创建认证账号"""
        session = self.get_session()
        try:
            account = AuthAccount(
                user_id=user_id,
                auth_type=auth_type,
                auth_identifier=auth_identifier,
                credential_data=str(credential_data) if credential_data else None
            )

            if password and auth_type == 'email':
                account.set_password(password)

            session.add(account)
            session.commit()
            session.refresh(account)
            return account
        finally:
            session.close()

    def get_auth_account(self, auth_type: str, auth_identifier: str) -> AuthAccount:
        """获取认证账号"""
        session = self.get_session()
        try:
            return session.query(AuthAccount).filter(
                AuthAccount.auth_type == auth_type,
                AuthAccount.auth_identifier == auth_identifier
            ).first()
        finally:
            session.close()

    def get_user_auth_accounts(self, user_id: int) -> list:
        """获取用户的所有认证账号"""
        session = self.get_session()
        try:
            return session.query(AuthAccount).filter(
                AuthAccount.user_id == user_id
            ).all()
        finally:
            session.close()

    def verify_auth_account(self, account_id: int):
        """验证认证账号"""
        session = self.get_session()
        try:
            account = session.query(AuthAccount).filter(
                AuthAccount.id == account_id
            ).first()
            if account:
                account.is_verified = True
                account.verified_at = datetime.now()

                # 同时验证用户
                user = session.query(User).filter(User.id == account.user_id).first()
                if user:
                    user.is_verified = True

                session.commit()
        finally:
            session.close()

    # ==================== Refresh Token管理 ====================

    def create_refresh_token(self, user_id: int, device_id: str = None,
                           device_name: str = None, ip_address: str = None,
                           user_agent: str = None, expires_days: int = 30) -> RefreshToken:
        """创建refresh token"""
        session = self.get_session()
        try:
            token = RefreshToken(
                user_id=user_id,
                token=secrets.token_urlsafe(32),
                device_id=device_id,
                device_name=device_name,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=datetime.now() + timedelta(days=expires_days)
            )
            session.add(token)
            session.commit()
            session.refresh(token)
            return token
        finally:
            session.close()

    def get_refresh_token(self, token_str: str) -> RefreshToken:
        """获取refresh token"""
        session = self.get_session()
        try:
            return session.query(RefreshToken).filter(
                RefreshToken.token == token_str
            ).first()
        finally:
            session.close()

    def revoke_refresh_token(self, token_str: str):
        """撤销refresh token"""
        session = self.get_session()
        try:
            token = session.query(RefreshToken).filter(
                RefreshToken.token == token_str
            ).first()
            if token:
                token.is_revoked = True
                token.revoked_at = datetime.now()
                session.commit()
        finally:
            session.close()

    def revoke_user_tokens(self, user_id: int, except_token: str = None):
        """撤销用户的所有token（除了指定的）"""
        session = self.get_session()
        try:
            query = session.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False
            )

            if except_token:
                query = query.filter(RefreshToken.token != except_token)

            tokens = query.all()
            for token in tokens:
                token.is_revoked = True
                token.revoked_at = datetime.now()

            session.commit()
        finally:
            session.close()

    # ==================== 登录历史 ====================

    def record_login(self, user_id: int, auth_type: str, ip_address: str = None,
                    user_agent: str = None, device_id: str = None,
                    is_success: bool = True, failure_reason: str = None):
        """记录登录历史"""
        session = self.get_session()
        try:
            history = LoginHistory(
                user_id=user_id,
                auth_type=auth_type,
                ip_address=ip_address,
                user_agent=user_agent,
                device_id=device_id,
                is_success=is_success,
                failure_reason=failure_reason
            )
            session.add(history)

            # 更新用户最后登录时间
            if is_success:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    user.last_login = datetime.now()

            session.commit()
        finally:
            session.close()

    # ==================== 短信验证码 ====================

    def create_sms_code(self, phone_number: str, purpose: str,
                       ip_address: str = None, expires_minutes: int = 5) -> str:
        """创建短信验证码"""
        session = self.get_session()
        try:
            # 生成6位验证码
            code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])

            verification = SMSVerification(
                phone_number=phone_number,
                code=code,
                purpose=purpose,
                ip_address=ip_address,
                expires_at=datetime.now() + timedelta(minutes=expires_minutes)
            )
            session.add(verification)
            session.commit()

            return code
        finally:
            session.close()

    def verify_sms_code(self, phone_number: str, code: str, purpose: str) -> bool:
        """验证短信验证码"""
        session = self.get_session()
        try:
            verification = session.query(SMSVerification).filter(
                SMSVerification.phone_number == phone_number,
                SMSVerification.code == code,
                SMSVerification.purpose == purpose,
                SMSVerification.is_used == False
            ).order_by(SMSVerification.created_at.desc()).first()

            if not verification:
                return False

            if not verification.is_valid():
                return False

            # 标记为已使用
            verification.is_used = True
            verification.used_at = datetime.now()
            session.commit()

            return True
        finally:
            session.close()


# 创建全局实例
auth_db = AuthDatabaseManager()


if __name__ == "__main__":
    print("=" * 60)
    print("认证数据库初始化")
    print("=" * 60)

    # 测试创建用户和认证账号
    user = auth_db.create_user(nickname="测试用户", user_type="student")
    print(f"✓ 创建用户: {user.nickname} (UUID: {user.uuid})")

    # 创建手机号认证
    auth_account = auth_db.create_auth_account(
        user_id=user.id,
        auth_type='phone',
        auth_identifier='13800138000'
    )
    print(f"✓ 创建手机号认证: {auth_account.auth_identifier}")

    # 创建refresh token
    refresh_token = auth_db.create_refresh_token(
        user_id=user.id,
        device_id='test_device',
        ip_address='127.0.0.1'
    )
    print(f"✓ 创建refresh token: {refresh_token.token[:20]}...")

    print("\n认证数据库初始化完成！")
