import jinja2


class SqlTemplate:
    """
    Convenience wrapper around SQL files
    This allows using Jinja templating inside those files.

    Be mindful of SQL injections though!

    Example usage:

    ```
    query = SqlTemplate("./my-query.sql")
    template_params = {"foo": "bar"}
    sql_params = {"baz": "qux"}

    with pg_session() as pg:
        formatted_query = query(template_params)
        results = pg.execute(formatted_query, sql_params)
    ```
    """

    def __init__(self, filename):
        self.filename = filename
        with open(filename, "r") as f:
            self.query = jinja2.Template(f.read())

    def __call__(self, **kwargs):
        return self.query.render(kwargs)


db_exists = SqlTemplate("src/sql/db_exists.sql")
list_migrations = SqlTemplate("src/sql/list_migrations.sql")
