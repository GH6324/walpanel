from sqlalchemy.orm import Session
from app.schema._input import CreatePanelInput, CreateNews
from app.db.models import Panel, News
from fastapi.exceptions import HTTPException
from fastapi import status
from app.admin_services.api import PanelAPI
from app.log.logger_config import logger


class PanelOperations:

    def create_panel(self, db: Session, request: CreatePanelInput):
        panel_exception = db.query(Panel).filter(Panel.url == request.url).first()

        if panel_exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Panel with this URL already exists.",
            )

        if not PanelAPI(request.url, request.username, request.password).login_test():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Login failed.",
            )
        try:
            new_panel = Panel(
                name=request.name,
                url=request.url,
                sub=request.sub,
                username=request.username,
                password=request.password,
            )
            db.add(new_panel)
            db.commit()
            db.refresh(new_panel)
            return new_panel
        except Exception as e:
            db.rollback()
            logger.error(f"Error while creating panel")
            return None

    def edit_panel(self, db: Session, request: CreatePanelInput, id: int):
        panel = db.query(Panel).filter(Panel.id == id).first()
        if not panel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Panel with this id not exist",
            )
        try:
            panel.name = request.name
            panel.url = request.url
            panel.sub = request.sub
            panel.username = request.username
            panel.password = request.password
            db.commit()
            db.refresh(panel)
            return panel
        except Exception as e:
            db.rollback()
            logger.exception("Error while editing panel")
            return None

    def delete_panel(self, db: Session, id: int):
        panel = db.query(Panel).filter(Panel.id == id).first()
        if not panel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Panel with this name not exist",
            )
        db.query(Panel).filter(Panel.id == id).delete()
        db.commit()
        return {"messsage": "successful"}

    def get_panels(self, db: Session):
        panels = db.query(Panel).all()
        return panels

    async def get_panel_status(self, db: Session):
        panels = db.query(Panel).all()
        statuses = []
        if panels:
            for panel in panels:
                panel_status = PanelAPI(
                    panel.url, panel.username, panel.password
                ).server_status()
                statuses.append({"panel_id": panel.id, "status": panel_status})
        return statuses

    def panel_data(self, db: Session, id: int):
        panel = db.query(Panel).filter(Panel.id == id).first()
        if not panel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Panel with this name"
            )
        return panel

    async def create_news(self, db: Session, request: CreateNews):
        try:
            new_news = News(message=request.message)
            db.add(new_news)
            db.commit()
            db.refresh(new_news)
            return new_news
        except Exception as e:
            logger.exception(f"Error while creating a new news => {e}")

    async def get_news(self, db: Session):
        try:
            news = db.query(News).all()
            return news
        except Exception as e:
            logger.exception(f"Error while get news => {e}")

    async def delete_news(self, db: Session, id: int):
        try:
            news = db.query(News).filter(News.id == id).first()
            if not news:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="News with this name not exist",
                )
            db.query(News).filter(News.id == id).delete()
            db.commit()
            return {"messsage": "successful"}
        except Exception as e:
            logger.exception(f"Error while deleting a news => {e}")


panel_operations = PanelOperations()
