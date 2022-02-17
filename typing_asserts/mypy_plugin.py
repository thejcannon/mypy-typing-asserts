from mypy.plugin import Plugin
from mypy.types import Type

from typing import Optional


def callback(ctx) -> Type:
    expected_type: Type = ctx.default_return_type.args[0]
    actual_type: Type = ctx.arg_types[0][0]
    if expected_type != actual_type:
        ctx.api.fail(
            f"assert_type failed. expected: '{expected_type}', actual '{actual_type}'",
            ctx.context,
        )
    return ctx.default_return_type


class CustomPlugin(Plugin):
    def get_function_hook(self, fullname: str):
        if fullname == "typing_asserts.assert_type":
            return callback


def plugin(version: str) -> Optional[CustomPlugin]:
    if not version.startswith("0.9"):
        return None
    return CustomPlugin
