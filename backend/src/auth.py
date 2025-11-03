"""
用户认证模块
使用JWT（JSON Web Token）进行身份验证
"""

from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# JWT配置
SECRET_KEY = "your-secret-key-change-this-in-production"  # 生产环境请更改
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

security = HTTPBearer()


class TokenData(BaseModel):
    """Token数据模型"""
    user_id: int
    username: str
    user_type: str


def create_access_token(user_id: int, username: str, user_type: str) -> str:
    """创建访问令牌"""
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "user_id": user_id,
        "username": username,
        "user_type": user_type,
        "exp": expire
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """解码访问令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(
            user_id=payload.get("user_id"),
            username=payload.get("username"),
            user_type=payload.get("user_type")
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="令牌已过期")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="无效的令牌")


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> TokenData:
    """获取当前登录用户"""
    token = credentials.credentials
    return decode_access_token(token)


def require_student(current_user: TokenData = Security(get_current_user)) -> TokenData:
    """要求学生权限"""
    if current_user.user_type not in ["student", "admin"]:
        raise HTTPException(status_code=403, detail="需要学生权限")
    return current_user


def require_parent(current_user: TokenData = Security(get_current_user)) -> TokenData:
    """要求家长权限"""
    if current_user.user_type not in ["parent", "admin"]:
        raise HTTPException(status_code=403, detail="需要家长权限")
    return current_user
