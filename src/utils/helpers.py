from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_verified_sources(filepath: str) -> List[str]:
    """Загружает список доверенных доменов/URL из файла."""
    domains = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sources = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        for source in sources:
            try:
                domain = source.split('//')[-1].split('/')[0].split(':')[0].lower()
                if domain and domain not in domains:
                    domains.append(domain)
            except Exception:
                logger.warning(f"Не удалось извлечь домен из источника: {source}", exc_info=False)
        logger.info(f"Загружено {len(domains)} доверенных доменов из {filepath}")
        return domains
    except FileNotFoundError:
        logger.warning(f"Файл доверенных источников не найден: {filepath}. Поиск НЕ будет ограничен.")
        return []
    except Exception as e:
        logger.error(f"Ошибка при загрузке доверенных источников из {filepath}", exc_info=True)
        return []