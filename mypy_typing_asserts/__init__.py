from typing import Generic, TypeVar, cast

T = TypeVar("T")


class assert_type(Generic[T]):
    def __new__(self, expression) -> T:  # type: ignore
        return cast("T", expression)
