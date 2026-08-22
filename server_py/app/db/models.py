import json
import time
from sqlalchemy import Column, String, Integer, Boolean, Text, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(32), default="player")  # admin, moderator, player
    avatar_url = Column(String(255), nullable=True)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255), nullable=True)
    preferences = Column(Text, default="{}")
    created_at = Column(Integer, default=lambda: int(time.time()))
    updated_at = Column(Integer, default=lambda: int(time.time()))

    def to_dict(self):
        prefs = {}
        try:
            if self.preferences:
                prefs = json.loads(self.preferences)
        except Exception:
            pass
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "avatarUrl": self.avatar_url,
            "twoFactorEnabled": self.two_factor_enabled,
            "preferences": prefs,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

class ServerModel(Base):
    __tablename__ = "servers"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    owner_id = Column(String(64), nullable=True, index=True)
    loader = Column(String(32), default="vanilla")
    mc_version = Column(String(32), default="1.21.4")
    status = Column(String(32), default="offline")
    port = Column(Integer, default=25565)
    min_memory = Column(String(16), default="1G")
    max_memory = Column(String(16), default="4G")
    jvm_args = Column(Text, default="")
    java_path = Column(String(255), nullable=True)
    jar_file = Column(String(255), nullable=True)
    auto_start = Column(Boolean, default=False)
    created_at = Column(Integer, default=lambda: int(time.time()))
    updated_at = Column(Integer, default=lambda: int(time.time()))

    def to_dict(self):
        return {
            "id": self.id,
            "craftyServerId": self.id,
            "name": self.name,
            "ownerId": self.owner_id,
            "loader": self.loader,
            "mcVersion": self.mc_version,
            "status": self.status,
            "port": self.port,
            "minMemory": self.min_memory,
            "maxMemory": self.max_memory,
            "jvmArgs": self.jvm_args,
            "javaPath": self.java_path,
            "jarFile": self.jar_file,
            "autoStart": self.auto_start,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id = Column(String(64), primary_key=True, index=True)
    server_id = Column(String(64), nullable=True, index=True)
    name = Column(String(128), nullable=False)
    action = Column(String(64), nullable=False)  # backup, restart, command, stop, start
    payload = Column(Text, default="")
    cron_expression = Column(String(64), nullable=False)
    enabled = Column(Boolean, default=True)
    last_run = Column(Integer, nullable=True)
    next_run = Column(Integer, nullable=True)
    created_at = Column(Integer, default=lambda: int(time.time()))

    def to_dict(self):
        return {
            "id": self.id,
            "serverId": self.server_id,
            "name": self.name,
            "action": self.action,
            "payload": self.payload,
            "cronExpression": self.cron_expression,
            "enabled": self.enabled,
            "lastRun": self.last_run,
            "nextRun": self.next_run,
            "createdAt": self.created_at,
        }

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(128), primary_key=True, index=True)
    value = Column(Text, nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), nullable=True)
    username = Column(String(64), nullable=True)
    action = Column(String(64), nullable=False)
    target = Column(String(128), nullable=True)
    details = Column(Text, default="")
    timestamp = Column(Integer, default=lambda: int(time.time()))
