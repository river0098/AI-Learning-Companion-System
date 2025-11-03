"""
数据库模型和管理
使用SQLite存储用户信息和学习数据
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import hashlib
import secrets

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    salt = Column(String(64), nullable=False)
    full_name = Column(String(100))
    user_type = Column(String(20), default='student')  # student, parent, teacher
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)

    def set_password(self, password: str):
        """设置密码（加盐哈希）"""
        self.salt = secrets.token_hex(32)
        self.password_hash = self._hash_password(password, self.salt)

    def check_password(self, password: str) -> bool:
        """验证密码"""
        return self.password_hash == self._hash_password(password, self.salt)

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """密码哈希"""
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


class StudentProfile(Base):
    """学生档案"""
    __tablename__ = 'student_profiles'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    grade = Column(String(20))
    school = Column(String(100))
    parent_id = Column(Integer)  # 关联的家长ID
    learning_goal = Column(Text)
    preferences = Column(Text)  # JSON格式存储偏好设置
    created_at = Column(DateTime, default=datetime.now)


class LearningSession(Base):
    """学习会话记录"""
    __tablename__ = 'learning_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    session_id = Column(String(100), unique=True)
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime)
    total_time = Column(Integer)  # 秒
    focused_time = Column(Integer)  # 秒
    idle_time = Column(Integer)  # 秒
    distraction_count = Column(Integer, default=0)
    productivity_score = Column(Float)
    detected_topics = Column(Text)  # JSON格式
    emotion_summary = Column(Text)  # JSON格式
    ai_interactions = Column(Integer, default=0)
    achievements = Column(Text)  # JSON格式


class KnowledgeProgress(Base):
    """知识掌握进度"""
    __tablename__ = 'knowledge_progress'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    concept_id = Column(String(100), nullable=False)
    mastery_level = Column(Float, default=0.0)  # 0-1
    exercises_completed = Column(Integer, default=0)
    exercises_correct = Column(Integer, default=0)
    total_time_spent = Column(Integer, default=0)  # 秒
    last_practiced = Column(DateTime, default=datetime.now)
    first_learned = Column(DateTime, default=datetime.now)


class AIInteraction(Base):
    """AI对话记录"""
    __tablename__ = 'ai_interactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    session_id = Column(String(100))
    timestamp = Column(DateTime, default=datetime.now)
    mode = Column(String(20))  # guide, coach, friend
    student_message = Column(Text)
    ai_response = Column(Text)
    intent = Column(String(50))
    helpful = Column(Boolean)  # 用户反馈


# 数据库管理类
class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = "../../data/companion.db"):
        """初始化数据库连接"""
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()

    def create_user(self, username: str, email: str, password: str,
                   full_name: str = None, user_type: str = 'student') -> User:
        """创建新用户"""
        session = self.get_session()
        try:
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                user_type=user_type
            )
            user.set_password(password)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()

    def get_user_by_username(self, username: str) -> User:
        """通过用户名获取用户"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.username == username).first()
        finally:
            session.close()

    def get_user_by_email(self, email: str) -> User:
        """通过邮箱获取用户"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.email == email).first()
        finally:
            session.close()

    def authenticate_user(self, username: str, password: str) -> User:
        """验证用户"""
        user = self.get_user_by_username(username)
        if user and user.check_password(password):
            # 更新最后登录时间
            session = self.get_session()
            try:
                user.last_login = datetime.now()
                session.add(user)
                session.commit()
            finally:
                session.close()
            return user
        return None

    def create_session_record(self, user_id: int, session_id: str) -> LearningSession:
        """创建学习会话记录"""
        session = self.get_session()
        try:
            record = LearningSession(
                user_id=user_id,
                session_id=session_id
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        finally:
            session.close()

    def update_session_record(self, session_id: str, **kwargs):
        """更新学习会话记录"""
        session = self.get_session()
        try:
            record = session.query(LearningSession).filter(
                LearningSession.session_id == session_id
            ).first()

            if record:
                for key, value in kwargs.items():
                    setattr(record, key, value)
                session.commit()
        finally:
            session.close()

    def save_ai_interaction(self, user_id: int, session_id: str,
                           mode: str, student_msg: str, ai_response: str, intent: str):
        """保存AI对话记录"""
        session = self.get_session()
        try:
            interaction = AIInteraction(
                user_id=user_id,
                session_id=session_id,
                mode=mode,
                student_message=student_msg,
                ai_response=ai_response,
                intent=intent
            )
            session.add(interaction)
            session.commit()
        finally:
            session.close()

    def update_knowledge_progress(self, user_id: int, concept_id: str,
                                 correct: bool, time_spent: int):
        """更新知识掌握进度"""
        session = self.get_session()
        try:
            progress = session.query(KnowledgeProgress).filter(
                KnowledgeProgress.user_id == user_id,
                KnowledgeProgress.concept_id == concept_id
            ).first()

            if not progress:
                progress = KnowledgeProgress(
                    user_id=user_id,
                    concept_id=concept_id
                )
                session.add(progress)

            progress.exercises_completed += 1
            if correct:
                progress.exercises_correct += 1
            progress.total_time_spent += time_spent
            progress.last_practiced = datetime.now()

            # 计算掌握度
            accuracy = progress.exercises_correct / progress.exercises_completed
            experience = min(progress.exercises_completed / 20, 1.0)
            progress.mastery_level = 0.7 * accuracy + 0.3 * experience

            session.commit()
        finally:
            session.close()

    def get_user_sessions(self, user_id: int, limit: int = 10):
        """获取用户的学习会话历史"""
        session = self.get_session()
        try:
            return session.query(LearningSession).filter(
                LearningSession.user_id == user_id
            ).order_by(LearningSession.start_time.desc()).limit(limit).all()
        finally:
            session.close()

    def get_user_knowledge_map(self, user_id: int):
        """获取用户的知识图谱"""
        session = self.get_session()
        try:
            return session.query(KnowledgeProgress).filter(
                KnowledgeProgress.user_id == user_id
            ).all()
        finally:
            session.close()


# 创建全局数据库实例
db = DatabaseManager()


if __name__ == "__main__":
    print("=" * 60)
    print("数据库初始化")
    print("=" * 60)

    # 测试创建用户
    try:
        user = db.create_user(
            username="test_student",
            email="student@example.com",
            password="password123",
            full_name="测试学生",
            user_type="student"
        )
        print(f"✓ 创建用户成功: {user.username}")
    except Exception as e:
        print(f"用户可能已存在: {e}")

    # 测试验证
    user = db.authenticate_user("test_student", "password123")
    if user:
        print(f"✓ 用户验证成功: {user.full_name}")
    else:
        print("✗ 验证失败")

    print("\n数据库初始化完成！")
