from database import Database


class FireuaiDB(Database):
    def __init__(self, user, password, database):
        super().__init__("localhost", user, password, database)

    def user_exists(self, user_id: str) -> bool:
        """
        Verifica se um usuário existe.

        @type user_id: string
        @param user_id: Id do discord a ser buscado no bd.
        @rtype: bool
        """

        query_sql = "SELECT 1 FROM users WHERE id = %(user_id)s LIMIT 1"
        result = self._execute(query_sql, {"user_id": user_id})

        return bool(result)

    def user_is_admin(self, user_id) -> bool:
        """
        Verifica se um usuário é administrador.

        @type user_id: string
        @param user_id: Id do discord a ser buscado no bd.
        @rtype: bool
        """

        query_sql = "SELECT 1 FROM users WHERE id = %(user_id)s AND permission = 1 LIMIT 1"
        result = self._execute(query_sql, {"user_id": user_id})

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

        query_sql = "INSERT INTO `users` (id, nickname) VALUES (%s, %s);"

        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query_sql, (user_id, nickname))
            except Exception as err:
                connection.rollback()
                cursor.close()
                raise err
            else:
                connection.commit()
                cursor.close()

    def make_admin(self, nickname: str):
        """
        Transforma um usuário em administrador.

        @type nickname: string
        @param nickname: Nickname do discord do user a ser promovido.
        @rtype: None
        """

        query_sql = "UPDATE users SET permission = 1 WHERE nickname = %(nickname)s;"

        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query_sql, {"nickname": nickname})
            except Exception as err:
                connection.rollback()
                cursor.close()
                raise err
            else:
                connection.commit()
                cursor.close()

    def get_user_points(self, user_id: str) -> int:
        """
        Obtém a quantidade de pontos obtidos pelo usuário.

        @type user_id: string
        @param user_id: Id do discord a ser buscado no bd.
        @rtype: int
        """

        query_sql = "SELECT points FROM users WHERE id = %(user_id)s;"
        result = self._execute(query_sql, {"user_id": user_id})

        return result[0][0]

    def get_user_coins(self, user_id: str) -> int:
        """
        Obtém a quantidade de moedas atuais do usuário.

        @type user_id: string
        @param user_id: Id do discord a ser buscado no bd.
        @rtype: int
        """

        query_sql = "SELECT coins FROM users WHERE id = %(user_id)s;"
        result = self._execute(query_sql, {"user_id": user_id})

        return result[0][0]

    def create_event(self, name: str) -> int | None:
        """
        Cria um evento.

        @type name: string
        @param name: Nome do evento a ser criado.
        @rtype: Int ou None
        @return: O Id do evento ou None caso já exista
        """

        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("INSERT IGNORE INTO event (name) VALUES (%s);", (name,))
            except Exception as err:
                connection.rollback()
                cursor.close()
                raise err
            else:
                event_id = cursor.lastrowid
                connection.commit()
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

        query_sql = "SELECT id FROM event WHERE name = %(name)s;"
        result = self._execute(query_sql, {"name": event_name})

        return result[0][0] if result else None

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

        # Inserir a flag com os IDs obtidos
        query_sql = """
            INSERT IGNORE INTO flags (flag, event_id, points, name, creator)
            VALUES (%s, %s, %s, %s, %s);
        """

        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query_sql, (flag, event_id, points, name, creator_id))
            except Exception as err:
                connection.rollback()
                cursor.close()
                raise err
            else:
                flag_id = cursor.lastrowid
                connection.commit()
                cursor.close()

                # lastrowid será 0 se o INSERT IGNORE não inseriu (porque já existia)
                return flag_id if flag_id != 0 else None

    def search_flag(self, flag: str) -> tuple | None:
        """
        Procura o Id, pontos e nome de um desafio com base na string da flag.

        @type flag: string
        @param flag: String da flag a ser procurada.

        @rtype: Tupla ou None
        @return: Uma tripla com Id, pontos e nome do desafio da flag ou None caso não exista
        """

        query_sql = "SELECT id, points, name FROM flags WHERE flag = %(flag)s;"
        search_result = self._execute(query_sql, {"flag": flag})

        return search_result[0] if search_result else None

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

            with self.get_connection() as connection:
                cursor = connection.cursor()

                try:
                    # Verificar resgate anterior
                    query_sql = "SELECT 1 FROM rewards WHERE user_id = %s AND flag_id = %s;"
                    cursor.execute(query_sql, (user_id, search_flag[0]))
                    result = cursor.fetchone()
                    print(result)
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

                except Exception as err:
                    connection.rollback()
                    cursor.close()
                    raise err

                else:
                    connection.commit()
                    cursor.close()
                    return f"Você concluiu com sucesso o desafio: {search_flag[2]}"

    def get_flags(self) -> list[dict]:
        """
        Retorna todas as flags ativas e a data de validade

        @rtype: Lista de Dicionários
        @return: Nome da Flag, Pontos e Validade
        """

        query_sql = """
            SELECT 
                f.name AS Desafio,
                f.points AS Pontos,
                e.name AS Evento,
                f.expiration AS Validade
            FROM flags f
            INNER JOIN event e
                ON f.event_id = e.id
            WHERE f.expiration > NOW()
            ORDER BY 
                f.points ASC,
                f.name ASC;
        """

        flags = self._execute(query_sql, _dict=True)
        return flags

    def get_remaining_flags(self, user_id) -> list[dict]:
        """
        Retorna todas as flags ativas que o usuário ainda não completou e a data de validade

        @rtype: Lista de Dicionários
        @return: Nome da Flag, Pontos e Validade
        """

        query_sql = """
            SELECT DISTINCT
                f.name AS Desafio,
                f.points AS Pontos,
                e.name AS Evento,
                f.expiration AS Validade
            FROM flags f
            INNER JOIN rewards r
                ON r.flag_id = f.id
            INNER JOIN event e
                ON f.event_id = e.id
            WHERE f.id NOT IN (
                SELECT
                    id
                FROM flags f2
                INNER JOIN rewards r2
                    ON f2.id = r2.flag_id
                WHERE r2.user_id = %s
            )
                AND f.expiration > NOW()
            ORDER BY 
                f.points ASC,
                f.name ASC;
        """

        flags = self._execute(query_sql, (user_id,), _dict=True)
        return flags

    def ranking_by_points(self) -> list[dict]:
        """
        Retorna um Ranking com os 20 melhores colocados com base nos pontos

        @rtype: Lista de Dicionários
        @return: Nomes e pontos
        """

        query_sql = """
            SELECT nickname, points
            FROM users
            WHERE permission != 1
            ORDER BY points DESC
            LIMIT 20;
        """

        ranking = self._execute(query_sql, _dict=True)
        return ranking

    def ranking_by_event(self, event_name: str) -> list[dict]:
        """
        Retorna um Ranking dos 20 melhores colocados dentro de um evento.

        @type event_name: string
        @param event_name: Nome do evento a ser buscado para ranking.

        @rtype: Lista de Dicionários
        @return: Nome e pontos
        """

        query_sql = """
            SELECT 
                u.nickname,
                SUM(f.points) AS total_points
            FROM rewards r
            INNER JOIN flags f ON r.flag_id = f.id
            INNER JOIN users u ON r.user_id = u.id
            INNER JOIN event e ON f.event_id = e.id
            WHERE e.name = %s AND permission != 1
            GROUP BY u.id
            ORDER BY total_points DESC
            LIMIT 20;
        """

        ranking = self._execute(query_sql, (event_name,), _dict=True)
        return ranking

    def get_rewards_number_flag(self, challenge_name: str) -> int:
        """
        Procura quantos resgates ocorreram com sucesso para um desafio.

        @type challenge_name: string
        @param challenge_name: Nome do desafio a ser buscado.

        @rtype: A quantidade resgates bem-sucedidos.
        """

        query_sql = """
            SELECT COUNT(*) 
            FROM rewards r
            INNER JOIN flags f ON r.flag_id = f.id
            WHERE f.name = %s
        """

        result = self._execute(query_sql, (challenge_name,))

        return result[0][0] if result else 0

    def get_blooded_flag(self, challenge_name: str) -> dict | None:
        """
        Obtém o id da primeira pessoa que resolveu o desafio.

        @type challenge_name: string
        @param challenge_name: Nome do desafio a ser procurado.

        @rtype: Dicionário
        @return: O id de quem resolveu e quando.
        """

        query_sql = """
            SELECT 
                u.id,
                r.detetime AS solved_at
            FROM rewards r
            INNER JOIN flags f ON r.flag_id = f.id
            INNER JOIN users u ON r.user_id = u.id
            WHERE f.name = %s AND u.permission != 1
            ORDER BY r.detetime ASC
            LIMIT 1
        """

        result = self._execute(query_sql, (challenge_name,), _dict=True)

        return result[0]

    def exists_hint_flag(self, challenge_name: str) -> tuple[bool, bool]:
        """
        Verifica se existe dicas para um desafio

        @type challenge_name: string
        @param challenge_name: Nome do desafio.

        @rtype: Tupla
        @return: Uma tupla (bool, bool) informando se existe uma dica normal e uma dica plus.
        """

        query_sql = """
            SELECT t.plus, 1
            FROM flags f
            INNER JOIN hints t ON f.id = t.flag_id
            WHERE f.name = %s;
        """

        result = self._execute(query_sql, (challenge_name,))

        if len(result) == 1:
            if result[0][0] == 1:
                return False, True
            return True, False

        elif len(result) == 2:
            return True, True

        return False, False

    def get_hint_flag(self, challenge_name: str, is_plus: bool) -> str:
        """
       Obtém uma dica

        @type challenge_name: string
        @param challenge_name: Nome do desafio a ser procurado.
        @type is_plus: bool
        @param is_plus: Indica se a dica procurada é plus ou comum.

        @rtype: string
        @return: A dica procurada
        """

        query_sql = """
            SELECT t.text
            FROM flags f
            INNER JOIN hints t ON f.id = t.flag_id
            WHERE f.name = %s AND t.plus = %s;
        """

        result = self._execute(query_sql, (challenge_name, is_plus))

        return result[0][0]

    def create_hint(self, challenge_name: str, is_plus: bool, text: str):
        """
       Cria uma dica

        @type challenge_name: string
        @param challenge_name: Nome do desafio a ser procurado.
        @type is_plus: bool
        @param is_plus: Indica se a dica procurada é plus ou comum.
        @type text: str
        @param text: O texto a ser informado como dica
        """

        query_sql = """
            INSERT INTO hints (flag_id, plus, text)
            SELECT f.id, %(plus)s, %(text)s
            FROM flags f
            WHERE f.name = %(flag_name)s;
        """

        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                self._execute(query_sql, {"plus": is_plus, "flag_name": challenge_name, "text": text})
            except Exception as e:
                raise e
            finally:
                cursor.close()

    def subtract_user_coins(self, user_id: str, amount: int):
        """
        Troca coins por uma dica

        @type user_id: string
        @param user_id: Id do usuário que irá perder coins.
        @type amount: int
        @param amount: Quantidade de moedas a serem retiradas.

        @rtype: None
        """

        query_sql = "UPDATE users SET coins = coins - %s WHERE id = %s;"

        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query_sql, (amount, user_id))
            except Exception as err:
                connection.rollback()
                cursor.close()
                raise err
            else:
                connection.commit()
                cursor.close()
