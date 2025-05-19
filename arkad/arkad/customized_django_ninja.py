from typing import override, Any

import ninja
from ninja import Schema as NinjaSchema

from pydantic.alias_generators import to_camel


class Schema(NinjaSchema):
    class Config(NinjaSchema.Config):
        alias_generator = to_camel
        populate_by_name = True


class Router(ninja.Router):
    """
    Router that uses camelCase for all API operations.
    This is done by overriding default behaviour and forcing by_alias=True.
    """

    @override
    def add_api_operation(
        self, *args: Any, by_alias: bool = True, **kwargs: Any
    ) -> None:  # type: ignore[override]
        if "by_alias" in kwargs and not kwargs["by_alias"]:
            raise ValueError("By_alias should not be set in add_api_operation")
        kwargs["by_alias"] = True
        return super().add_api_operation(*args, **kwargs)
