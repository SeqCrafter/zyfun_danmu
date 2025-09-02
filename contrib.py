from __future__ import annotations

from collections.abc import Iterable
from types import ModuleType

from robyn import Robyn  # pylint: disable=E0401

from tortoise import Tortoise, connections
from tortoise.log import logger


def register_tortoise(
    app: Robyn,
    config: dict | None = None,
    config_file: str | None = None,
    db_url: str | None = None,
    modules: dict[str, Iterable[str | ModuleType]] | None = None,
    generate_schemas: bool = False,
) -> None:
    async def tortoise_init() -> None:
        await Tortoise.init(
            config=config, config_file=config_file, db_url=db_url, modules=modules
        )
        logger.info(
            "Tortoise-ORM started, %s, %s", connections._get_storage(), Tortoise.apps
        )  # pylint: disable=W0212

    @app.startup_handler
    async def init_orm():  # pylint: disable=W0612
        await tortoise_init()
        if generate_schemas:
            logger.info("Tortoise-ORM generating schema")
            await Tortoise.generate_schemas()

    @app.shutdown_handler
    async def close_orm():  # pylint: disable=W0612
        await connections.close_all()
        logger.info("Tortoise-ORM shutdown")
