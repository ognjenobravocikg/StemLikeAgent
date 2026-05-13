from loguru import logger

logger.add("stem_agent.log",rotation="1 MB",level="INFO")