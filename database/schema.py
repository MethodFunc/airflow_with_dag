from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

BASE = declarative_base()


#################### 방재기상관측(AWS) 스키마 ####################
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
    # 매분 자료
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
    # 운고 운량
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
    # 초상 온도
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
    # 시정 자료
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
    # 현천 자료
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


#################### 종관기상관측(ASOS) 스키마 ####################
class AsosStnInfo(BASE):
    __tablename__ = 'ASOS_STN_INFO'
    STN_ID = Column(Integer, primary_key=True)
    LON = Column(Float(12, 9))
    LAT = Column(Float(10, 8))
    STN_SP = Column(Float(11, 8))
    HT = Column(Float(6, 2))
    HT_PA = Column(Float(5, 2))
    HT_TA = Column(Float(5, 2))
    HT_WD = Column(Float(5, 2))
    HT_RN = Column(Float(5, 2))
    STN_CD = Column(Float(3, 2))
    STN_KO = Column(String(10))
    STN_EN = Column(String(20))
    STN_AD = Column(Integer)
    FCT_ID = Column(String(8))
    LAW_ID = Column(String(12))
    BASIN = Column(String(10))

    asos_data = relationship('AsosData', back_populates='asos_stn_info', cascade='all, delete')


class AsosData(BASE):
    __tablename__ = 'ASOS_DATA'
    ID = Column(Integer, primary_key=True)
    CR_YMD = Column(DateTime)
    STN_ID = Column(Integer, ForeignKey('ASOS_STN_INFO.STN_ID', ondelete="CASCADE"))
    WD = Column(Integer)
    WS = Column(Float(3, 1))
    GST_WD = Column(Integer)
    GST_WS = Column(Float(3, 1))
    GST_TM = Column(Float(3, 1))
    PA = Column(Float(5, 1))
    PS = Column(Float(5, 1))
    PT = Column(Integer)
    PR = Column(Float(3, 1))
    TA = Column(Float(3, 1))
    TD = Column(Float(3, 1))
    HM = Column(Float(4, 1))
    PV = Column(Float(3, 1))
    RN = Column(Float(4, 1))
    RN_DAY = Column(Float(4, 1))
    RN_JUN = Column(Float(4, 1))
    RN_INT = Column(Float(4, 1))
    SD_HR3 = Column(Float(4, 1))
    SD_DAY = Column(Float(4, 1))
    SD_TOT = Column(Float(4, 1))
    WC = Column(Integer)
    WP = Column(Integer)
    WW = Column(String(22))
    CA_TOT = Column(Integer)
    CA_MID = Column(Integer)
    CH_MIN = Column(Integer)
    CT = Column(String(8))
    CT_TOP = Column(Integer)
    CT_MID = Column(Integer)
    CT_LOW = Column(Integer)
    VS = Column(Integer)
    SS = Column(Float(3, 1))
    SI = Column(Float(4, 2))
    ST_GD = Column(Integer)
    TS = Column(Float(3, 1))
    TE_005 = Column(Float(3, 1))
    TE_01 = Column(Float(3, 1))
    TE_02 = Column(Float(3, 1))
    TE_03 = Column(Float(3, 1))
    ST_SEA = Column(Integer)
    WH = Column(Float(3, 1))
    BF = Column(Integer)
    IR = Column(Integer)
    IX = Column(Integer)

    asos_stn_info = relationship('AsosStnInfo', back_populates='asos_data')
