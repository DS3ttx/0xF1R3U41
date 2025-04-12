import os
import mariadb


class FireUAIDB:
    def __init__(self, user, password, database):
        self._mydb = mariadb.connect(
            host="localhost",
            user=user,
            password=password,
            database=database
        )

    def __del__(self):
        self._mydb.close()

    def user_exists(self, user_id: str) -> bool:
        """
        Verifica se um usuário existe.

        @type user_id: string
        @param user_id: Id do discord a ser buscado no bd.
        @rtype: bool
        """
        cursor = self._mydb.cursor()
        query_sql = "SELECT 1 FROM users WHERE id = %(user_id)s LIMIT 1"
        cursor.execute(query_sql, {"user_id": user_id})
        result = cursor.fetchone()
        cursor.close()

        return result is not None

    def user_is_admin(self, user_id) -> bool:
        """
        Verifica se um usuário é administrador.

        @type user_id: string
        @param user_id: Id do discord a ser buscado no bd.
        @rtype: bool
        """
        cursor = self._mydb.cursor()
        query_sql = "SELECT 1 FROM users WHERE id = %(user_id)s AND permission = 1 LIMIT 1"
        cursor.execute(query_sql, {"user_id": user_id})
        result = cursor.fetchone()
        cursor.close()

        return result is not None

    def user_register(self, user_id: str, nickname: str):
        """
        Registra um usuário no bd com permissões de usuário.

        @type user_id: string
        @param user_id: Id do discord a ser registrado no bd.
        @type nickname: string
        @param nickname: Nick do discord a ser registrado no bd.
        @rtype: None
        """

        cursor = self._mydb.cursor()
        query_sql = "INSERT INTO `users` (id, nickname) VALUES (%s, %s);"
        cursor.execute(query_sql, (user_id, nickname))
        self._mydb.commit()
        cursor.close()

    def make_admin(self, user_id: str):
        """
        Transforma um usuário em administrador.

        @type user_id: string
        @param user_id: Id do discord a ser promovido.
        @rtype: None
        """

        cursor = self._mydb.cursor()
        query_sql = "UPDATE users SET permission = 1 WHERE nickname = %(nickname)s;"
        cursor.execute(query_sql, {"user_id": user_id})
        self._mydb.commit()
        cursor.close()

    def get_user_points(self, user_id: str) -> int:
        """
        Obtém a quantidade de pontos obtidos pelo usuário.

        @type user_id: string
        @param user_id: Id do discord a ser buscado no bd.
        @rtype: int
        """
        cursor = self._mydb.cursor()
        query_sql = "SELECT points FROM users WHERE id = %(user_id)s;"
        cursor.execute(query_sql, {"user_id": user_id})
        result = cursor.fetchone()
        cursor.close()

        return result[0]

    def get_user_coints(self, user_id: str) -> int:
        """
        Obtém a quantidade de moedas atuais do usuário.

        @type user_id: string
        @param user_id: Id do discord a ser buscado no bd.
        @rtype: int
        """
        cursor = self._mydb.cursor()
        query_sql = "SELECT coints FROM users WHERE id = %(user_id)s;"
        cursor.execute(query_sql, {"user_id": user_id})
        result = cursor.fetchone()
        cursor.close()

        return result[0]

    def create_event(self, name: str) -> int | None:
        """
        Cria um evento.

        @type name: string
        @param name: Nome do evento a ser criado.
        @rtype: Int ou None
        @return: O Id do evento ou None caso já exista
        """

        cursor = self._mydb.cursor()
        query_sql = "INSERT IGNORE INTO event (name) VALUES %(name)s;"
        cursor.execute(query_sql, {"name": name})
        self._mydb.commit()
        event_id = cursor.lastrowid
        cursor.close()

        # lastrowid será 0 se o INSERT IGNORE não inseriu (porque já existia)
        return event_id if event_id != 0 else None

    def get_event_id(self, event_name) -> int | None:
        """
        Obtém o Id um evento.

        @type event_name: string
        @param event_name: Nome do evento a ser buscado.
        @rtype: Int ou None
        @return: O Id do evento ou None caso não exista
        """

        cursor = self._mydb.cursor()
        query_sql = "SELECT id FROM event WHERE name = %(name)s;"
        cursor.execute(query_sql, {"name": event_name})
        create_result = cursor.fetchone()
        cursor.close()

        return create_result[0] if create_result else None

    def create_flag(self, name: str, flag: str, points: int, event_name: str | None, creator_id: str) -> int | None:
        """
        Cria uma flag. Caso o evento não exista, será criado.

        @type name: string
        @param name: Nome do desafio a ser criado.
        @type flag: string
        @param flag: String da flag a ser encontrada dentro do desafio.
        @type points: int
        @param points: Quantos pontos serão ofertados ao obter a flag.
        @type event_name: string
        @param event_name: Nome do evento a ser associado.
        @type creator_id: str
        @param creator_id: Id do criador do desafio.

        @rtype: Int ou None
        @return: O Id da flag ou None caso já exista
        """

        event_id = None

        if event_name:
            search_event_id = self.get_event_id(event_name)
            if search_event_id:
                event_id = search_event_id
            else:
                event_id = self.create_event(event_name)

        cursor = self._mydb.cursor()

        # Inserir a flag com os IDs obtidos
        query_sql = """
            INSERT IGNORE INTO flags (flag, event_id, points, name, creator)
            VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(query_sql, (flag, event_id, points, name, creator_id))
        self._mydb.commit()

        flag_id = cursor.lastrowid
        cursor.close()

        return flag_id if flag_id != 0 else None

    def search_flag(self, flag: str) -> tuple | None:
        """
        Procura o Id, pontos e nome de um desafio com base na string da flag.

        @type flag: string
        @param flag: String da flag a ser procurada.

        @rtype: Tupla ou None
        @return: Uma tripla com Id, pontos e nome do desafio da flag ou None caso não exista
        """

        cursor = self._mydb.cursor()
        query_sql = "SELECT id, points, name FROM flags WHERE flag = %(flag)s;"
        cursor.execute(query_sql, {"flag": flag})
        create_result = cursor.fetchone()
        cursor.close()

        return create_result[0] if create_result else None

    def reward_flag(self, user_id: str, flag: str) -> str | None:
        """
        Resgata uma flag.

        @type user_id: string
        @param user_id: Id do usuario do discord.
        @type flag: string
        @param flag: String da flag a ser resgatada.

        @rtype: String ou None
        @return: Uma mensagem de sucesso ou None caso de flag não encontrada
        """

        search_flag = self.search_flag(flag)
        if search_flag:
            cursor = self._mydb.cursor()

            # Verificar resgate
            query_sql = "SELECT 1 FROM rewards WHERE user_id = %s AND flag_id = %s;"
            cursor.execute(query_sql, (user_id, search_flag[0]))
            result = cursor.fetchone()

            if result is not None:
                raise AssertionError("Você já resgatou esta flag!")

            # Inserir Resgate
            query_sql = "INSERT INTO rewards (user_id, flag_id) VALUES (%s, %s);"
            cursor.execute(query_sql, (user_id, search_flag[0]))

            # Inserir Pontos e Moedas
            query_sql = """
                UPDATE users 
                SET points = points + %(points)s, coins = coins + %(points)s
                WHERE id = %(user_id)s;
            """
            cursor.execute(query_sql, {"points": search_flag[1], "user_id": user_id})

            self._mydb.commit()
            cursor.close()
            return f"Você concluiu com sucesso o desafio: {search_flag[2]}"

    def ranking_by_points(self) -> list[dict]:
        """
        Retorna um Ranking com os 20 melhores colocados com base nos pontos

        @rtype: Lista de Dicionários
        @return: Nomes e pontos
        """

        cursor = self._mydb.cursor(dictionary=True)
        query_sql = """
            SELECT nickname, points
            FROM users
            ORDER BY points DESC
            LIMIT 20;
        """
        cursor.execute(query_sql)
        ranking = cursor.fetchall()
        cursor.close()
        return ranking

    def ranking_by_event(self, event_name: str) -> list[dict]:
        """
        Retorna um Ranking dos 20 melhores colocados dentro de um evento.

        @type event_name: string
        @param event_name: Nome do evento a ser buscado para ranking.

        @rtype: Lista de Dicionários
        @return: Nome e pontos
        """

        cursor = self._mydb.cursor(dictionary=True)

        query_sql = """
            SELECT 
                u.nickname,
                SUM(f.points) AS total_points
            FROM rewards r
            INNER JOIN flags f ON r.flag_id = f.id
            INNER JOIN users u ON r.user_id = u.id
            INNER JOIN event e ON f.event_id = e.id
            WHERE e.name = %s
            GROUP BY u.id
            ORDER BY total_points DESC
            LIMIT 20;
        """

        cursor.execute(query_sql, (event_name,))
        ranking = cursor.fetchall()
        cursor.close()
        return ranking

    def get_rewards_number_flag(self, challenge_name: str) -> int:
        """
        Procura quantos resgates ocorreram com sucesso para um desafio.

        @type challenge_name: string
        @param challenge_name: Nome do desafio a ser buscado.

        @rtype: A quantidade resgates bem-sucedidos.
        """

        cursor = self._mydb.cursor()

        query_sql = """
            SELECT COUNT(*) 
            FROM rewards r
            INNER JOIN flags f ON r.flag_id = f.id
            WHERE f.name = %s
        """

        cursor.execute(query_sql, (challenge_name,))
        result = cursor.fetchone()
        cursor.close()

        return result[0] if result else 0

    def get_blooded_flag(self, challenge_name: str) -> dict | None:
        """
        Obtém o nick da primeira pessoa que resolveu o desafio.

        @type challenge_name: string
        @param challenge_name: Nome do desafio a ser procurado.

        @rtype: Dicionário
        @return: O nome de quem resolveu e quando.
        """

        cursor = self._mydb.cursor(dictionary=True)

        query_sql = """
            SELECT 
                u.nickname,
                r.detetime AS solved_at
            FROM rewards r
            INNER JOIN flags f ON r.flag_id = f.id
            INNER JOIN users u ON r.user_id = u.id
            WHERE f.name = %s
            ORDER BY r.detetime ASC
            LIMIT 1
        """

        cursor.execute(query_sql, (challenge_name,))
        result = cursor.fetchone()
        cursor.close()

        return result

