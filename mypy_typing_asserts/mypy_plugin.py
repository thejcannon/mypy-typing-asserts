from typing import Callable, Optional, Type

import mypy.types
from mypy.plugin import FunctionContext, Plugin


def callback(ctx: FunctionContext) -> mypy.types.Type:
    deduced_return_type = ctx.default_return_type
    assert isinstance(deduced_return_type, mypy.types.Instance)
    expected_type = deduced_return_type.args[0]
    if isinstance(expected_type, mypy.types.UninhabitedType):
        ctx.api.fail("You must provide a type parameter to 'assert_type'", ctx.context)
        return ctx.default_return_type

    arg_types = ctx.arg_types[0]
    if arg_types:
        actual_type = arg_types[0]
        if expected_type != actual_type:
            ctx.api.fail(
                f"assert_type failed. expected: '{expected_type}', actual '{actual_type}'",
                ctx.context,
            )
        return actual_type
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
