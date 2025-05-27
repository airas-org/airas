import logging
import os
import shutil

logger = logging.getLogger(__name__)


def cleanup_tmp_dir(tmp_dir: str) -> bool:
    if not os.path.isdir(tmp_dir):
        logger.debug(f"Temporary dir does not exist: {tmp_dir}")
        return False

    try:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        logger.info(f"Removed temporary dir: {tmp_dir}")
        return True
    except Exception as e:
        logger.warning(f"Failed to remove {tmp_dir}: {e}")
        return False
    

if __name__== "__main__":
    result = cleanup_tmp_dir(
        tmp_dir="/workspaces/airas/tmp"
    )
    print(f"result: {result}")
