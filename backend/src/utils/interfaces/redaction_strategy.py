from abc import ABC, abstractmethod


class RedactionStrategy(ABC):

    @abstractmethod
    def is_sensitive_key(self):
        raise NotImplementedError("Method must be redefined")