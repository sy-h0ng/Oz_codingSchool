import enum


class GenderEnum(str, enum.Enum):
    """성별"""

    M = "M"
    F = "F"


class RoleEnum(str, enum.Enum):
    """유저에게 부여된 역할 권한"""

    PENDING = "PENDING"  # 권한 부여 대기
    STAFF = "STAFF"  # 폐렴 추적 관련 데이터 CRUD 허용
    ADMIN = "ADMIN"  # 전체 데이터 CRUD 허용


class DepartmentEnum(str, enum.Enum):
    """유저 소속 부서"""

    MEDICAL = "MEDICAL"  # 의료진
    DEV = "DEV"  # 개발팀
    RESEARCH = "RESEARCH"  # 연구진
