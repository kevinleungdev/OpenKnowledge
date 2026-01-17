from curses import meta
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

            with open(local_file_path) as f:
                doc = Document(
                    page_content=f.read(),
                )
            return [doc]
        except Exception as e:
            log.exception(f"Error loading document {file_path}: {e}")

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
