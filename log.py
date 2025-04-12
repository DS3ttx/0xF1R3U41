import logging
from logging.handlers import RotatingFileHandler


# Configuração básica de logging
def log_setup():
    logger = logging.getLogger("bot_logger")
    logger.setLevel(logging.INFO)

    # Formato do log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Handler para salvar os logs em arquivo
    file_handler = RotatingFileHandler(
        "bot.log", maxBytes=5 * 1024 * 1024, backupCount=3
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler para imprimir os logs no console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
