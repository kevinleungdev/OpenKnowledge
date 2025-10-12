from typing import Any


class AppConfig:

    _config: dict[str, Any]

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        if config is None:
            self._config = {}
        super().__setattr__("_config", config)

    def __setattr__(self, key: str, value: Any) -> None:
        self._config[key] = value

    def __getattr__(self, key: str):
        try:
            return self._config[key]
        except KeyError:
            message = "'{}' object has no attribute '{}'"
            raise AttributeError(message.format(self.__class__.__name__, key))

    def __delattr__(self, key: str) -> None:
        del self._config[key]