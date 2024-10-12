import requests
from pathlib import Path


def download_to_local(url: str, out_path: Path, parent_mkdir: bool = True):

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
        print(f"Failed to download url {url} \n {e}")
        return False
