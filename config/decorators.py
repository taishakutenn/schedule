import functools
from config.logging_config import configure_logging

logger = configure_logging()


def log_exceptions(func):
    """Decorator for logging exceptions"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        method_name = f"{func.__qualname__}"
        logger.info(f"→ Вызов: {method_name} с аргументами {kwargs}")
        try:
            result = await func(*args, **kwargs)
            logger.info(f"✓ {method_name} завершён успешно")
            return result
        except Exception as e:
            logger.exception(f"✗ Ошибка в {method_name}: {e}")
            raise

    return wrapper
