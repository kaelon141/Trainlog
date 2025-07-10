from src.sql import SqlTemplate

insert_denied_login = SqlTemplate("src/sql/suspicious_activity/insert_denied_login.sql")
list_denied_logins = SqlTemplate("src/sql/suspicious_activity/list_denied_logins.sql")

insert_suspicious_activity = SqlTemplate(
    "src/sql/suspicious_activity/insert_suspicious_activity.sql"
)
list_suspicious_activity = SqlTemplate(
    "src/sql/suspicious_activity/list_suspicious_activity.sql"
)
