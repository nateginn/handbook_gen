# db_handler

from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError
import os
from datetime import datetime
from config import Config
from logger import logger
from utils import validate_string, validate_int

Base = declarative_base()

class Topic(Base):
    __tablename__ = 'topics'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    sources = relationship("Source", back_populates="topic")

class Source(Base):
    __tablename__ = 'sources'
    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=False)
    type = Column(String(50), nullable=False)
    origin = Column(String(255))
    timestamp = Column(DateTime, default=datetime.utcnow)
    topic = relationship("Topic", back_populates="sources")
    contents = relationship("Content", back_populates="source")

class Content(Base):
    __tablename__ = 'contents'
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('sources.id'), nullable=False)
    content_type = Column(String(50), nullable=False)
    content = Column(Text)
    file_content = Column(LargeBinary, nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    source = relationship("Source", back_populates="contents")

class DatabaseHandler:
    def __init__(self):
        self.engine = create_engine(Config.DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def add_topic(self, name, description=""):
        session = self.Session()
        try:
            name = validate_string(name, max_length=100)
            description = validate_string(description, allow_empty=True)
            new_topic = Topic(name=name, description=description)
            session.add(new_topic)
            session.commit()
            logger.info(f"Added new topic: {name}")
            return new_topic.id
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error adding topic: {str(e)}")
            raise
        finally:
            session.close()

    def add_source(self, topic_id, source_type, origin):
        session = self.Session()
        try:
            topic_id = validate_int(topic_id)
            source_type = validate_string(source_type, max_length=50)
            origin = validate_string(origin, max_length=255)
            new_source = Source(topic_id=topic_id, type=source_type, origin=origin)
            session.add(new_source)
            session.commit()
            logger.info(f"Added new source: {source_type} for topic {topic_id}")
            return new_source.id
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error adding source: {str(e)}")
            raise
        finally:
            session.close()

    def add_content(self, source_id, content_type, content, file_content=None):
        session = self.Session()
        try:
            source_id = validate_int(source_id)
            content_type = validate_string(content_type, max_length=50)
            content = validate_string(content, allow_empty=True)
            new_content = Content(source_id=source_id, content_type=content_type, 
                                  content=content, file_content=file_content)
            session.add(new_content)
            session.commit()
            logger.info(f"Added new content for source {source_id}")
            return new_content.id
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error adding content: {str(e)}")
            raise
        finally:
            session.close()

    def get_topic_content(self, topic_id):
        session = self.Session()
        try:
            topic_id = validate_int(topic_id)
            topic = session.query(Topic).get(topic_id)
            if not topic:
                logger.warning(f"Topic not found: {topic_id}")
                return None
            content = []
            for source in topic.sources:
                for content_item in source.contents:
                    content.append({
                        'source_type': source.type,
                        'origin': source.origin,
                        'content_type': content_item.content_type,
                        'content': content_item.content,
                        'version': content_item.version,
                        'created_at': content_item.created_at
                    })
            logger.info(f"Retrieved content for topic {topic_id}")
            return content
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving topic content: {str(e)}")
            raise
        finally:
            session.close()

    def update_content(self, content_id, new_content):
        session = self.Session()
        try:
            content_id = validate_int(content_id)
            new_content = validate_string(new_content)
            content_item = session.query(Content).get(content_id)
            if not content_item:
                logger.warning(f"Content not found: {content_id}")
                raise ValueError("Content not found")
            content_item.version += 1
            content_item.content = new_content
            content_item.created_at = datetime.utcnow()
            session.commit()
            logger.info(f"Updated content {content_id}")
            return content_item.version
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating content: {str(e)}")
            raise
        finally:
            session.close()

    def get_topics(self):
        session = self.Session()
        try:
            topics = session.query(Topic).all()
            logger.info("Retrieved all topics")
            return topics
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving topics: {str(e)}")
            raise
        finally:
            session.close()

db_handler = DatabaseHandler()

if __name__ == "__main__":
    db_handler.create_tables()