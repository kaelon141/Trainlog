from enum import Enum


class Env(Enum):
    PROD = "production"
    DEV = "development"
    LOCAL = "local"


class DbNames(str, Enum):
    AUTH_DB = "databases/auth.db"
    PATH_DB = "databases/path.db"
    MAIN_DB = "databases/main.db"
