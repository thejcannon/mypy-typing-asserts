from typing import Callable, Optional, Type

import mypy.types
from mypy.plugin import FunctionContext, Plugin


def _extract_type(type_: mypy.types.Type) -> mypy.types.Type:
    return getattr(type_, "type", type_)


def _typename(type_: mypy.types.Type) -> str:
    result = getattr(type_, "fullname", None)
    if result is None:
        return str(type_)
    if callable(result):
        return result()
    return result


def callback(ctx: FunctionContext) -> mypy.types.Type:
    deduced_return_type = ctx.default_return_type
    assert isinstance(deduced_return_type, mypy.types.Instance)
    return_type = deduced_return_type.args[0]
    if isinstance(return_type, mypy.types.UninhabitedType):
        ctx.api.fail("You must provide a type parameter to 'assert_type'", ctx.context)
        return ctx.default_return_type

    expected_type = _extract_type(return_type)
    arg_types = ctx.arg_types[0]
    if arg_types:
        arg_type = arg_types[0]
        actual_type = _extract_type(arg_types[0])
        if expected_type != actual_type:
            ctx.api.fail(
                f"assert_type failed. expected: '{_typename(expected_type)}', actual '{_typename(actual_type)}'",
                ctx.context,
            )
        return arg_type
    return ctx.default_return_type


class CustomPlugin(Plugin):
    def get_function_hook(
        self, fullname: str
    ) -> Optional[Callable[[FunctionContext], mypy.types.Type]]:
        if fullname == "mypy_typing_asserts.assert_type":
            return callback
        return None


def plugin(version: str) -> Type[Plugin]:
    return CustomPlugin
