import asyncio
import concurrent.futures
from collections.abc import Coroutine
from typing import Any, TypeVar

import typer
from mongodb_odm.utils.apply_indexes import async_apply_indexes

app = typer.Typer()

T = TypeVar("T")


def run_async(func_call: Coroutine[Any, Any, T]) -> T:
    """
    Run an async function, handling both cases where an event loop
    is already running or not.
    """
    try:
        # Check if we're already in an event loop
        asyncio.get_running_loop()
        # If we are, run in a separate thread to avoid conflicts
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, func_call)
            return future.result()
    except RuntimeError:
        # No event loop running, safe to use asyncio.run()
        return asyncio.run(func_call)


@app.command()
def create_indexes() -> None:
    run_async(async_apply_indexes())


@app.command()
def populate_data(
    total_user: int = typer.Option(100),
    total_post: int = typer.Option(100),
) -> None:
    from cli.management_command.data_population import populate_dummy_data

    run_async(populate_dummy_data(total_user=total_user, total_post=total_post))


@app.command()
def delete_data() -> None:
    from cli.management_command.data_population import clean_data

    run_async(clean_data())
