"""Interface for ModelDictHandler"""
from abc import ABC, abstractmethod


class DataStoreInterface(ABC):
    @abstractmethod
    def load_data(self) -> dict:
        pass

    @abstractmethod
    def save_data(self, data: dict) -> None:
        pass