from fastapi.exceptions import HTTPException
from fastapi import status
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session, joinedload
from decimal import Decimal

from app.schema._input import CreateAdminInput, UpdateAdminInput
from app.db.models import Admin, Plans
from app.db.engine import get_db
from app.log.logger_config import logger
from app.oprations.utility import purchase_hisory


class AdminOperations:

    def create_admin(self, db: Session, request: CreateAdminInput):
        existing_admin = (
            db.query(Admin).filter(Admin.username == request.username).first()
        )

        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin with this username already exists.",
            )

        try:
            expiry_datetime = date.today() + timedelta(days=request.days_remaining)
            admin = Admin(
                username=request.username,
                password=request.password,
                panel_id=request.panel_id,
                inbound_id=request.inbound_id,
                inbound_flow=request.inbound_flow,
                traffic=request.traffic,
                expiry_time=expiry_datetime,
                is_active=request.is_active,
                is_banned=request.is_banned,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            return admin
        except Exception as e:
            db.rollback()
            logger.exception(f"Error while creating admin: {e}")
            return None

    def delete_admin(self, db: Session, id: int):
        admin = db.query(Admin).filter(Admin.id == id).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin with this email not exist",
            )
        db.query(Admin).filter(Admin.id == id).delete()
        db.commit()
        return {"message": "successful"}

    async def get_all_admins(self, db: Session):
        from app.admin_services.task import admin_task

        admins = db.query(Admin).options(joinedload(Admin.panel)).all()
        result = []

        for admin in admins:
            try:
                get_clients = await admin_task.total_users_in_inbound(
                    db, admin.username
                )
            except:
                get_clients = 0
            admin_data = {
                "id": admin.id,
                "username": admin.username,
                "panel": {
                    "id": admin.panel_id,
                    "name": admin.panel.name if admin.panel else None,
                },
                "inbound_id": admin.inbound_id,
                "traffic": admin.traffic,
                "expiry_time": (
                    max((admin.expiry_time - date.today()).days, 0)
                    if admin.expiry_time
                    else 0
                ),
                "is_active": admin.is_active,
                "is_banned": admin.is_banned,
                "total_clients": get_clients,
            }
            result.append(admin_data)

        return result

    def edit_admin(self, db: Session, request: UpdateAdminInput):
        admin = db.query(Admin).filter(Admin.id == request.id).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not exist",
            )
        try:
            expiry_datetime = date.today() + timedelta(days=request.days_remaining)

            admin.panel_id = request.panel_id
            admin.inbound_id = request.inbound_id
            admin.inbound_flow = request.inbound_flow
            admin.traffic = request.traffic
            admin.expiry_time = expiry_datetime
            admin.is_active = request.is_active
            admin.is_banned = request.is_banned
            db.commit()
            db.refresh(admin)
            return admin
        except Exception as e:
            db.rollback()
            logger.exception(f"Error while editing admin: {e}")
            return None

    def login_admin(self, db: Session, username, password):
        admin = db.query(Admin).filter(Admin.username == username).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="username or password is incorrect",
            )
        admin_password = admin.password
        if admin_password != password:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="username or password is incorrect",
            )
        if not admin.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is disabled.",
            )
        return {"message": "Login successful"}

    def get_admin_data(self, db: Session, username: str):
        admin = db.query(Admin).filter(Admin.username == username).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin with this username not exist",
            )
        return admin

    def reduce_traffic(self, db: Session, username: str, traffic_gb: float):
        admin = db.query(Admin).filter(Admin.username == username).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Admin with this username"
            )

        current_traffic = Decimal(str(admin.traffic))
        reduction = Decimal(str(traffic_gb))
        admin.traffic = float(current_traffic - reduction)

        db.commit()
        db.refresh(admin)
        return admin

    def Increased_traffic(self, db: Session, username: str, traffic: float):
        try:
            admin = db.query(Admin).filter(Admin.username == username).first()

            current_traffic = Decimal(str(admin.traffic))
            increase = Decimal(str(traffic))
            admin.traffic = float(current_traffic + increase)

            db.commit()
            db.refresh(admin)
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error in Increased_traffic: {e}")
            return None

    def pre_opration_check(self, db: Session, username: str):
        admin = db.query(Admin).filter(Admin.username == username).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin with this username not exist",
            )
        elif (admin.expiry_time - date.today()).days <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your subscription has expired",
            )
        elif admin.traffic == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your traffic is over",
            )

        return True

    async def aproval_payment_(
        self, db: Session, dealer_name: str, plan_id: int, price: int, purchase_date
    ):
        admin = db.query(Admin).filter(Admin.username == dealer_name).first()
        plan = db.query(Plans).filter(Plans.id == plan_id).first()

        try:
            if admin:
                base_date = (
                    max(admin.expiry_time, date.today())
                    if admin.expiry_time
                    else date.today()
                )
                admin.expiry_time = base_date + timedelta(days=plan.days)
                admin.traffic += plan.traffic
                db.commit()
                db.refresh(admin)

                await purchase_hisory(db, price, purchase_date, dealer_name, "done")
                return True
            else:
                return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error in aproval_payment_: {e}")
            return None


admin_operations = AdminOperations()
