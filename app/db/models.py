from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.db.engine import Base


class Panel(Base):
    __tablename__ = "panels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    sub = Column(String, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)

    admins = relationship("Admin", back_populates="panel")


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, nullable=True)
    username = Column(String, unique=True)
    password = Column(String, nullable=False)
    panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    inbound_id = Column(Integer, default=1)
    inbound_flow = Column(String, nullable=True)
    traffic = Column(Integer, default=0)
    expiry_time = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)

    panel = relationship("Panel", back_populates="admins")


class Plans(Base):
    __tablename__ = "plans"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    traffic = Column("traffic", Integer)
    price = Column("price", Integer)
    days = Column("days", Integer)


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    language = Column(String, default="en")
    card_payment_enabled = Column(Boolean, default=True)
    Intermediary_payment_gateway = Column(Boolean, default=False)


class News(Base):
    __tablename__ = "News"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message = Column(String, nullable=False)


class CardNumber(Base):
    __tablename__ = "card_number"

    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(String, nullable=False)


class PaymentGatewaykeys(Base):
    __tablename__ = "Payment_gateway_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    Intermediary_gateway_key = Column(String, nullable=True)


class PurchaseHistory(Base):
    __tablename__ = "purchase_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Integer, nullable=False)
    payer = Column(String, nullable=False)
    purchase_date = Column(Date, nullable=False)
    status = Column(String, nullable=False, default="pending")
