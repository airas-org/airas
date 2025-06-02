import logging
import os
import shutil

logger = logging.getLogger(__name__)


def cleanup_tmp_dir(tmp_dir: str) -> bool:
    try:
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)
            logger.info(f"Removed temporary dir: {tmp_dir}")

        os.makedirs(tmp_dir, exist_ok=True)
        logger.info(f"Created temporary dir: {tmp_dir}")
        return True
    except Exception as e:
        logger.warning(f"Failed to remove {tmp_dir}: {e}")
        return False
    
if __name__== "__main__":
    result = cleanup_tmp_dir(
        tmp_dir="/workspaces/airas/tmp"
    )
    print(f"result: {result}")
