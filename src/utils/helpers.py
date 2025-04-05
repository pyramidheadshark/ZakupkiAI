import logging
import sys
from typing import List, Optional
from urllib.parse import urlparse


logger = logging.getLogger(__name__)


def load_verified_sources(filepath: str) -> List[str]:
    """
    Загружает список доверенных доменов из файла.
    Извлекает только доменное имя (например, 'consultant.ru') и убирает 'www.'.
    """
    domains: List[str] = []
    logger.debug(f"HELPERS: Загрузка доверенных источников из: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:

            sources = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        for source in sources:
            try:

                parsed_uri = urlparse(source)
                domain = parsed_uri.netloc.split(':')[0].lower()


                if not domain and '.' in source and '/' not in source:
                    domain = source.lower().split(':')[0]


                if domain.startswith('www.'):
                    domain = domain[4:]


                if domain and '.' in domain and domain not in domains:
                    domains.append(domain)
                    logger.debug(f"HELPERS: Добавлен доверенный домен: {domain}")

            except Exception:
                logger.warning(f"HELPERS: Не удалось извлечь домен из источника: {source}", exc_info=False)

        logger.info(f"HELPERS: Загружено {len(domains)} уникальных доверенных доменов из {filepath}")
        if not domains:
            logger.warning("HELPERS: Список доверенных доменов пуст!")
        return domains
    except FileNotFoundError:
        logger.error(f"HELPERS: Файл доверенных источников не найден: {filepath}")
        return []
    except Exception as e:
        logger.error(f"HELPERS: Ошибка при загрузке доверенных источников из {filepath}", exc_info=True)
        return []

def get_domain_from_url(url: str) -> Optional[str]:
    """Извлекает доменное имя из URL и убирает 'www.'."""
    if not url or not isinstance(url, str):
        return None
    try:
        domain = urlparse(url).netloc.split(':')[0].lower()
        if domain.startswith('www.'):
            domain = domain[4:]

        return domain if '.' in domain else None
    except Exception as e:
        logger.warning(f"HELPERS: Не удалось извлечь домен из URL '{url}': {e}")
        return None