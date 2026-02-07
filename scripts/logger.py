import logging
import sys
import os

def setup_logger(name: str = "biodiversidade", level: int = logging.INFO, log_file: str = "logs/app.log") -> logging.Logger:
    """
    Configura e retorna um logger padronizado para o projeto.
    Salva logs em arquivo e exibe no console.
    
    Args:
        name (str): Nome do logger.
        level (int): Nível de log (default: logging.INFO).
        log_file (str): Caminho do arquivo de log (default: "logs/app.log").
        
    Returns:
        logging.Logger: Instância configurada do logger.
    """
    logger = logging.getLogger(name)
    
    # Evita duplicidade de handlers se o logger já estiver configurado
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(level)
    
    # Cria o diretório de logs se não existir
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Formato: [2026-02-07 10:00:00] [INFO] Mensagem
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 1. Handler para stdout (Console)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. Handler para arquivo
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
