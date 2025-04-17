from abc import ABC
from mariadb import ConnectionPool


class Database(ABC):
    def __init__(self, host: str, user: str, password: str, database: str):
        self.__pool = ConnectionPool(
            pool_name="fireuai_pool",
            pool_size=10,
            host=host,
            user=user,
            password=password,
            database=database
        )

    def get_connection(self):
        return self.__pool.get_connection()

    def _execute(self, sql: str, params: dict | tuple | None = (None,), _dict: bool = False):
        with self.get_connection() as connection:
            cursor = connection.cursor(dictionary=_dict)
            try:
                cursor.execute(sql, params)
                result = cursor.fetchall()
            except Exception as e:
                raise e
            finally:
                cursor.close()
            return result
