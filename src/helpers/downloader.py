import requests
from pathlib import Path
from typing import Optional
import warnings
import logging

logger = logging.getLogger("myproject")


def download_to_local(
    url: str, out_path: Path, parent_mkdir: bool = True
) -> Optional[bool]:
    """

    Downloads a file from a given URL and saves it to a local path.

    Args:
        url (str): The URL of the file to be downloaded.
        out_path (Path): The local file path where the downloaded file will be saved.
        parent_mkdir (bool, optional): Whether to create parent directories for `out_path`
            if they don't already exist. Defaults to True.

    Returns:
        Optional[bool]: Returns `True` if the download is successful,
        `False` if the download fails. Returns `None` if an error occurs
        outside the download logic.

    Raises:
        ValueError: If `out_path` is not a valid `Path` object.
        RuntimeWarning: If the download fails due to a request error.
    """

    if not isinstance(out_path, Path):
        raise (ValueError(f"{out_path} is not a valid Path object"))
    if parent_mkdir:
        out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url)
        response.raise_for_status()

        # Write out the file in binary mode
        out_path.write_bytes(response.content)
        return True
    except requests.RequestException as e:
        msg = f"Failed to download url {url} \n {e}"
        logger.error(msg)
        warnings.warn(msg, RuntimeWarning)
        return False
