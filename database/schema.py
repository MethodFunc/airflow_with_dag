from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

BASE = declarative_base()


# AWS 지점 정보 테이블
class AwsStnInfo(BASE):
    __tablename__ = 'AWS_STN_INFO'

    STN_ID = Column(Integer, primary_key=True)
    LON = Column(Float(12, 9))
    LAT = Column(Float(10, 8))
    STN_SP = Column(String(8))
    HT = Column(Float(6, 2))
    HT_WD = Column(Float(5, 2))
    LAU_ID = Column(Integer)
    STN_AD = Column(Integer)
    STN_KO = Column(String(10))
    STN_EN = Column(String(20))
    FCT_ID = Column(String(8))
    LAW_ID = Column(String(12))
    BASIN = Column(String(10))

    aws_data = relationship('AwsData', back_populates='stn_info', cascade='all, delete')
    temperature_data = relationship('TemperatureData', back_populates='stn_info', cascade='all, delete')
    visible_data = relationship('VisibleData', back_populates='stn_info', cascade='all, delete')
    cloud_data = relationship('CloudData', back_populates='stn_info', cascade='all, delete')
    ww_data = relationship('WwData', back_populates='stn_info', cascade='all, delete')


class AwsData(BASE):
    __tablename__ = 'AWS_DATA'
    ID = Column(Integer, primary_key=True)
    CR_YMD = Column(DateTime)
    STN_ID = Column(Integer, ForeignKey('AWS_STN_INFO.STN_ID', ondelete="CASCADE"))
    WD1 = Column(Float)
    WS1 = Column(Float)
    WDS = Column(Float)
    WSS = Column(Float)
    WD10 = Column(Float)
    WS10 = Column(Float)
    TA = Column(Float)
    RE = Column(Float)
    RN_15m = Column(Float)
    RN_60m = Column(Float)
    RN_12H = Column(Float)
    RN_DAY = Column(Float)
    HM = Column(Float)
    PA = Column(Float)
    PS = Column(Float)
    TD = Column(Float)

    stn_info = relationship('AwsStnInfo', back_populates='aws_data')


class CloudData(BASE):
    __tablename__ = 'AWS_CLOUD_DATA'
    ID = Column(Integer, primary_key=True)
    CR_YMD = Column(DateTime)
    STN_ID = Column(Integer, ForeignKey('AWS_STN_INFO.STN_ID', ondelete="CASCADE"))
    LON = Column(Float(12, 9))
    LAT = Column(Float(10, 8))
    CH_LOW = Column(Integer)
    CH_MID = Column(Integer)
    CH_TOP = Column(Integer)
    CA_TOT = Column(Float(5, 2))

    stn_info = relationship('AwsStnInfo', back_populates='cloud_data')


class TemperatureData(BASE):
    __tablename__ = 'AWS_TEMPERATURE_DATA'
    ID = Column(Integer, primary_key=True)
    CR_YMD = Column(DateTime)
    STN_ID = Column(Integer, ForeignKey('AWS_STN_INFO.STN_ID', ondelete="CASCADE"))
    TA = Column(Float(3, 1))
    HM = Column(Float(4, 1))
    TD = Column(Float(3, 1))
    TG = Column(Float(3, 1))
    TS = Column(Float(3, 1))
    TE005 = Column(Float(3, 1))
    TE01 = Column(Float(3, 1))
    TE02 = Column(Float(3, 1))
    TE03 = Column(Float(3, 1))
    TE05 = Column(Float(3, 1))
    TE10 = Column(Float(3, 1))
    TE15 = Column(Float(3, 1))
    TE30 = Column(Float(3, 1))
    TE50 = Column(Float(3, 1))
    PA = Column(Float(5, 1))
    PS = Column(Float(5, 1))

    stn_info = relationship('AwsStnInfo', back_populates='temperature_data')


class VisibleData(BASE):
    __tablename__ = 'AWS_VISIBLE_DATA'
    ID = Column(Integer, primary_key=True)
    CR_YMD = Column(DateTime)
    STN_ID = Column(Integer, ForeignKey('AWS_STN_INFO.STN_ID', ondelete="CASCADE"))
    LON = Column(Float(12, 9))
    LAT = Column(Float(10, 8))
    S = Column(Integer)
    VIS1 = Column(Integer)
    VIS10 = Column(Integer)
    WW1 = Column(Integer)
    WW15 = Column(Integer)

    stn_info = relationship('AwsStnInfo', back_populates='visible_data')


class WwData(BASE):
    __tablename__ = 'AWS_WW_DATA'
    ID = Column(Integer, primary_key=True)
    CR_YMD = Column(DateTime)
    STN_ID = Column(Integer, ForeignKey('AWS_STN_INFO.STN_ID', ondelete="CASCADE"))
    LON = Column(Float(12, 9))
    LAT = Column(Float(10, 8))
    S = Column(Integer)
    N = Column(Integer)
    WW1 = Column(Integer)
    NN1 = Column(Integer)

    stn_info = relationship('AwsStnInfo', back_populates='ww_data')

