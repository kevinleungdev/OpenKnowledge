import locale
import logging
import sys

from langchain_core.documents import Document

from open_knowledge.storage.provider import Storage
from open_knowledge.env import SRC_LOG_LEVELS, GLOBAL_LOG_LEVEL


logging.basicConfig(stream=sys.stdout, level=GLOBAL_LOG_LEVEL)
log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["RAG"])

known_source_ext = [
    "go",
    "py",
    "java",
    "sh",
    "bat",
    "ps1",
    "cmd",
    "js",
    "ts",
    "css",
    "cpp",
    "hpp",
    "h",
    "c",
    "cs",
    "sql",
    "log",
    "ini",
    "pl",
    "pm",
    "r",
    "dart",
    "dockerfile",
    "env",
    "php",
    "hs",
    "hsc",
    "lua",
    "nginxconf",
    "conf",
    "m",
    "mm",
    "plsql",
    "perl",
    "rb",
    "rs",
    "db2",
    "scala",
    "bash",
    "swift",
    "vue",
    "svelte",
    "ex",
    "exs",
    "erl",
    "tsx",
    "jsx",
    "hs",
    "lhs",
    "json",
]


def _read_text_file(path: str) -> str:
    """Read a text file as a string, tolerant of encodings.

    `open()` without an encoding uses the locale default (GBK/cp936 on
    Chinese Windows), which raises UnicodeDecodeError on files that aren't
    valid in that encoding - e.g. UTF-8 files, or Windows-1252 text with
    curly quotes (byte 0x94). Try UTF-8 first, then the locale default for
    legacy text, then latin-1 which decodes any byte stream without raising.
    """
    for enc in ("utf-8", locale.getpreferredencoding(False), "latin-1"):
        try:
            with open(path, encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    return ""  # unreachable: latin-1 never raises


class Loader:
    def __init__(self) -> None:
        pass

    def load(
        self, filename: str, file_content_type: str, file_path: str
    ) -> list[Document]:
        log.debug(f"Loader.load: {filename} {file_content_type} {file_path}")

        try:
            local_file_path = Storage.get_file(file_path)
            log.debug(f"Download file: {local_file_path}")

            content = _read_text_file(local_file_path)
            return [Document(page_content=content)]
        except Exception as e:
            log.exception(f"Error loading document {file_path}: {e}")
            return []

    def _is_text_file(self, file_ext: str, file_content_type: str) -> bool:
        return file_ext in known_source_ext or (
            file_content_type
            and file_content_type.find("text/") >= 0
            # Avoid text/html files being detected as text
            and not file_content_type.find("html") >= 0
        )

    def _get_loader(self, filename: str, file_content_type: str, file_path: str):
        # TODO
        pass
