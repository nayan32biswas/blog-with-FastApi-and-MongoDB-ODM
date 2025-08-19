import typer
from mongodb_odm.utils.apply_indexes import async_apply_indexes

app = typer.Typer()


@app.command()
async def create_indexes() -> None:
    await async_apply_indexes()


@app.command()
async def populate_data(
    total_user: int = typer.Option(100),
    total_post: int = typer.Option(100),
) -> None:
    from cli.management_command.data_population import populate_dummy_data

    populate_dummy_data(total_user=total_user, total_post=total_post)


@app.command()
def delete_data() -> None:
    from cli.management_command.data_population import clean_data

    clean_data()
