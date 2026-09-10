from sqlalchemy import (
    Column, Integer, BigInteger, VARCHAR, String, DateTime,
    Text, INTEGER, ForeignKey, Index, text, Boolean, false, DATETIME
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT, TEXT
from typing import Any

from core.utils.db_api.base import Base

from datetime import datetime


class BaseModel(Base):
    __abstract__ = True
    
    @property
    def to_dict(self) -> dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__}(' +
            ''.join([f'{i.name}={getattr(self, i.name)!r}, ' for i in self.__table__.columns]) +
            ')>'
        )

class User(BaseModel):
    __tablename__ = "Users"

    id = Column(BigInteger, primary_key=True, index=True)
    full_name = Column(String(128), nullable=False)
    username = Column(String(32))

    bag = relationship("UserBag", lazy="selectin", uselist=False)

    # lab = relationship("Lab", primaryjoin="User.id==Lab.lab_id", uselist=False)
    # bag = relationship("Bag", primaryjoin="User.id==Bag.id", uselist=False)
    # lab = relationship("Lab", foreign_keys=id, remote_side='Lab.lab_id')


class Victims(BaseModel):
    __tablename__ = 'Victims'
    
    id = Column(BigInteger, unique=True, autoincrement=True, nullable=False, primary_key=True)
    victims_owner_id = Column(ForeignKey(User.id), nullable=False, index=True)
    victim_id = Column(BigInteger, nullable=False, index=True)
    victim_expire = Column(BigInteger, nullable=False)
    infect_date = Column(BigInteger, nullable=False)
    victim_expire_kd = Column(BigInteger, nullable=False)
    victim_bio_resource_earn = Column(BigInteger, nullable=False)
    pathogen_name = Column(VARCHAR(48), nullable=False)
    ss_detect = Column(TINYINT, nullable=False)



class Chat(BaseModel):
    __tablename__ = "Chat"
    __table_args__ = (Index("chat_id", "chat_id", "user_id"),)

    id = Column(BigInteger, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    title = Column(String(128), nullable=False)
    user_id = Column(ForeignKey(User.id), nullable=False, index=True)
    is_private = Column(TINYINT(1), nullable=False, server_default=text("'0'"))

    # user = relationship("User")


class UserLab(BaseModel):  # сделано так потому что отсюда легче делать связи
    __tablename__ = "Lab"

    lab_id = Column(ForeignKey(User.id), ForeignKey(Chat.user_id), primary_key=True, index=True)
    lab_name = Column(String(128), nullable=False)
    customization_emoji = Column(String(20))
    pathogen_name = Column(String(48))
    pathogens = Column(Integer, nullable=False, server_default=text("'4'"))
    ready_pathogens = Column(Integer, nullable=False, server_default=text("'4'"))
    science = Column(TINYINT, nullable=False, server_default=text("'1'"))
    science_time = Column(BigInteger)
    infect = Column(Integer, nullable=False, server_default=text("'1'"))
    immunity = Column(Integer, nullable=False, server_default=text("'1'"))
    lethality = Column(Integer, nullable=False, server_default=text("'1'"))
    security_service = Column(Integer, nullable=False, server_default=text("'1'"))
    bio_experience = Column(BigInteger, nullable=False, server_default=text("'0'"))
    bio_resource = Column(BigInteger, nullable=False, server_default=text("'0'"))
    infected = Column(Integer, nullable=False, server_default=text("'0'"))
    illnesses = Column(Integer, nullable=False, server_default=text("'0'"))
    fever = Column(BigInteger)
    fever_pathogen_name = Column(String(42))
    victims_food = Column(BigInteger, nullable=False, server_default=text("'0'"))
    chat_setup_virus = Column(BigInteger)
    lab_dossier = Column(TINYINT(1), nullable=False, server_default=text("'1'"))

    # bag = relationship("UserBag", lazy='selectin')


class UserBag(BaseModel):
    __tablename__ = "Bag"

    id = Column(BigInteger, ForeignKey(User.id), primary_key=True)
    primogem = Column(BigInteger, nullable=False, server_default=text("'0'"))
    stellar_Jade = Column(BigInteger, nullable=False, server_default=text("'0'"))


class UserUserBot(BaseModel):
    __tablename__ = "UsersUserbots"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(ForeignKey(User.id), nullable=False)

    # ub_id = Column(Integer, nullable=False)  # позже будет создана таблица со списком юзерботов и будет фореджин кей
    status = Column(Boolean, server_default=false())

    data = relationship("UserUserBotData", lazy="selectin", uselist=False)


class UserUserBotData(BaseModel):
    __tablename__ = "UsersUserbotsData"
    id = Column(Integer, primary_key=True, index=True)

    ub_id = Column(ForeignKey(UserUserBot.id), nullable=False)

    api_id = Column(BigInteger, nullable=False)
    api_hash = Column(String(255), nullable=False)
    phone_number = Column(String(255), nullable=False)
    time_expire = Column(DateTime, default=datetime.utcnow(), nullable=False)


class UserbotUserSettings(BaseModel):
    __tablename__ = 'UserbotUserSettings'
    
    user_id = Column(BigInteger, primary_key=True, unique=True, index=True, nullable=False)
    
    prefix = Column(VARCHAR(1), nullable=False, default='а')

class UserbotTrustedUsers(BaseModel):
    __tablename__ = 'UserbotTrustedUsers'
    
    id = Column(BigInteger, unique=True, autoincrement=True, nullable=False, primary_key=True)
    user_id = Column(BigInteger, unique=False, index=True, nullable=False)
    trusted_user_id = Column(BigInteger, unique=False, nullable=False)
    
class UserbotVictims(BaseModel):
    __tablename__ = 'UserbotVictims'
    
    id = Column(BigInteger, unique=True, autoincrement=True, nullable=False, primary_key=True)
    infecter_id = Column(BigInteger, index=True, nullable=False)
    victimer_id = Column(BigInteger, nullable=False)
    victimer_name = Column(VARCHAR(128), nullable=False)
    victim_expire = Column(DateTime, default=datetime.utcnow(), nullable=False)
    bio_resource = Column(BigInteger, nullable=False)

