from typing import Generic, TypeVar


T = TypeVar("T")


class assert_type(Generic[T]):
    def __init__(self, expression) -> T:  # type: ignore
        pass
