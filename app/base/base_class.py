from typing import Self


class StaticBase:
    def __new__(cls, *args, **kwargs):  # type: ignore
        raise TypeError(
            f"Cannot instantiate '{cls.__name__}'. Use static or class methods only."
        )


class SingletonBase:
    _instances: dict[type[Self], Self] = {}

    def __init__(self) -> None:
        raise TypeError(
            f'Cannot instantiate "{self.__class__.__name__}" directly. \
                Use get_instance() instead.'
        )

    @classmethod
    def get_instance(cls) -> Self:
        if cls not in cls._instances:
            instance = cls.__new__(cls)
            instance.class_initialized()
            cls._instances[cls] = instance

        return cls._instances[cls]  # type: ignore

    def class_initialized(self) -> None:
        """Method to initialize the singleton instance"""
        pass


class ServiceBase:
    pass
