from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from ..core.config import settings

Base = declarative_base()

class AISRecord(Base):
    """AIS position record"""
    __tablename__ = "ais_records"

    id = Column(Integer, primary_key=True, index=True)
    mmsi = Column(Integer, index=True)
    timestamp = Column(DateTime, index=True)
    lat = Column(Float)
    lon = Column(Float)
    speed = Column(Float, nullable=True)
    course = Column(Float, nullable=True)
    vessel_name = Column(String, nullable=True)
    vessel_type = Column(String, nullable=True)
    distance_from_shore = Column(Float, nullable=True)
    distance_from_port = Column(Float, nullable=True)
    is_fishing = Column(Boolean, nullable=True)
    source = Column(String, nullable=True)

class DarkPeriodRecord(Base):
    """Detected dark period"""
    __tablename__ = "dark_periods"

    id = Column(Integer, primary_key=True, index=True)
    mmsi = Column(Integer, index=True)
    start_time = Column(DateTime, index=True)
    end_time = Column(DateTime)
    duration_hours = Column(Float)
    start_lat = Column(Float)
    start_lon = Column(Float)
    end_lat = Column(Float)
    end_lon = Column(Float)
    distance_km = Column(Float)
    risk_score = Column(Float, index=True)
    in_mpa = Column(Boolean, default=False)
    in_eez = Column(String, nullable=True)
    is_nighttime = Column(Boolean, default=False)
    detection_date = Column(DateTime, default=datetime.utcnow)

class MPARecord(Base):
    """Marine Protected Area"""
    __tablename__ = "mpas"

    id = Column(Integer, primary_key=True, index=True)
    wdpa_id = Column(Integer, unique=True)
    name = Column(String)
    desig_eng = Column(String, nullable=True)
    iucn_cat = Column(String, nullable=True)
    marine = Column(Integer)
    no_take = Column(String, nullable=True)
    status = Column(String, nullable=True)
    geometry = Column(Text)  # Store as WKT or GeoJSON

# Database setup
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
