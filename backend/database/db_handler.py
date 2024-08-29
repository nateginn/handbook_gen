from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get the database URL from environment variables
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("No DATABASE_URL environment variable has been set.")

Base = declarative_base()

class Topic(Base):
    __tablename__ = 'topics'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    files = relationship("File", back_populates="topic")
    handbooks = relationship("Handbook", back_populates="topic")

class File(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=False)
    name = Column(String(100), nullable=False)
    file_type = Column(String(20), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    topic = relationship("Topic", back_populates="files")
    processed_content = relationship("ProcessedContent", back_populates="file", uselist=False)
    
class ProcessedContent(Base):
    __tablename__ = 'processed_contents'
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=False)
    content = Column(Text, nullable=False)
    processing_date = Column(DateTime, default=datetime.utcnow)
    file = relationship("File", back_populates="processed_content")

class Transcription(Base):
    __tablename__ = 'transcriptions'
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=False)
    content = Column(Text, nullable=False)
    file = relationship("File", back_populates="transcriptions")
    summaries = relationship("Summary", back_populates="transcription")

class Summary(Base):
    __tablename__ = 'summaries'
    id = Column(Integer, primary_key=True)
    transcription_id = Column(Integer, ForeignKey('transcriptions.id'), nullable=False)
    content = Column(Text, nullable=False)
    transcription = relationship("Transcription", back_populates="summaries")
    handbooks = relationship("Handbook", back_populates="summary")

class Handbook(Base):
    __tablename__ = 'handbooks'
    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=False)
    content = Column(Text, nullable=False)
    creation_date = Column(DateTime, default=datetime.utcnow)
    topic = relationship("Topic", back_populates="handbooks")

class DatabaseHandler:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        
    def add_topic(self, topic_name):
        session = self.Session()
        try:
            new_topic = Topic(name=topic_name)
            session.add(new_topic)
            session.commit()
            return new_topic.id
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error adding topic: {str(e)}")
        finally:
            session.close()

    def get_topics(self):
        session = self.Session()
        try:
            return session.query(Topic).all()
        except SQLAlchemyError as e:
            logging.error(f"Error retrieving topics: {str(e)}")
        finally:
            session.close()

    def add_file_to_topic(self, topic_id, file_name, file_type, content):
        session = self.Session()
        try:
            new_file = File(name=file_name, type=file_type, content=content, topic_id=topic_id)
            session.add(new_file)
            session.commit()
            return new_file.id
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error adding file to topic: {str(e)}")
        finally:
            session.close()

    def get_files_for_topic(self, topic_id):
        session = self.Session()
        try:
            return session.query(File).filter(File.topic_id == topic_id).all()
        except SQLAlchemyError as e:
            logging.error(f"Error retrieving files for topic: {str(e)}")
        finally:
            session.close()

    def create_handbook_for_topic(self, topic_id, content):
        session = self.Session()
        try:
            new_handbook = Handbook(topic_id=topic_id, content=content)
            session.add(new_handbook)
            session.commit()
            return new_handbook.id
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error creating handbook for topic: {str(e)}")
        finally:
            session.close()
            
    def create_tables(self):
        try:
            Base.metadata.create_all(self.engine)
            logging.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logging.error(f"Error creating database tables: {str(e)}")

    def insert_data(self, table_name, data):
        session = self.Session()
        try:
            if table_name == "file":
                new_record = File(**data)
            elif table_name == "transcription":
                new_record = Transcription(**data)
            elif table_name == "summary":
                new_record = Summary(**data)
            elif table_name == "handbook":
                new_record = Handbook(**data)
            else:
                raise ValueError(f"Invalid table name: {table_name}")

            session.add(new_record)
            session.commit()
            logging.info(f"Data inserted successfully into {table_name}")
            return new_record.id
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error inserting data into {table_name}: {str(e)}")
            return None
        finally:
            session.close()

    def retrieve_data(self, table_name, record_id):
        session = self.Session()
        try:
            if table_name == "file":
                record = session.query(File).get(record_id)
            elif table_name == "transcription":
                record = session.query(Transcription).get(record_id)
            elif table_name == "summary":
                record = session.query(Summary).get(record_id)
            elif table_name == "handbook":
                record = session.query(Handbook).get(record_id)
            else:
                raise ValueError(f"Invalid table name: {table_name}")

            if record:
                return record
            else:
                logging.warning(f"No record found in {table_name} with id {record_id}")
                return None
        except SQLAlchemyError as e:
            logging.error(f"Error retrieving data from {table_name}: {str(e)}")
            return None
        finally:
            session.close()

    def update_data(self, table_name, record_id, data):
        session = self.Session()
        try:
            if table_name == "file":
                record = session.query(File).get(record_id)
            elif table_name == "transcription":
                record = session.query(Transcription).get(record_id)
            elif table_name == "summary":
                record = session.query(Summary).get(record_id)
            elif table_name == "handbook":
                record = session.query(Handbook).get(record_id)
            else:
                raise ValueError(f"Invalid table name: {table_name}")

            if record:
                for key, value in data.items():
                    setattr(record, key, value)
                session.commit()
                logging.info(f"Record updated successfully in {table_name}")
                return True
            else:
                logging.warning(f"No record found in {table_name} with id {record_id}")
                return False
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error updating data in {table_name}: {str(e)}")
            return False
        finally:
            session.close()

    def delete_data(self, table_name, record_id):
        session = self.Session()
        try:
            if table_name == "file":
                record = session.query(File).get(record_id)
            elif table_name == "transcription":
                record = session.query(Transcription).get(record_id)
            elif table_name == "summary":
                record = session.query(Summary).get(record_id)
            elif table_name == "handbook":
                record = session.query(Handbook).get(record_id)
            else:
                raise ValueError(f"Invalid table name: {table_name}")

            if record:
                session.delete(record)
                session.commit()
                logging.info(f"Record deleted successfully from {table_name}")
                return True
            else:
                logging.warning(f"No record found in {table_name} with id {record_id}")
                return False
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error deleting data from {table_name}: {str(e)}")
            return False
        finally:
            session.close()

    def clear_database(self):
        session = self.Session()
        try:
            for table in reversed(Base.metadata.sorted_tables):
                session.execute(table.delete())
            session.commit()
            logging.info("Database cleared successfully")
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error clearing database: {str(e)}")
        finally:
            session.close()

# Usage example
if __name__ == "__main__":
    db_handler = DatabaseHandler()
    db_handler.create_tables()