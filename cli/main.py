import typer
from mongodb_odm import apply_indexes

app = typer.Typer()


@app.command()
def create_indexes() -> None:
    apply_indexes()


@app.command()
def populate_data(
    total_user: int = typer.Option(100),
    total_post: int = typer.Option(100),
) -> None:
    from cli.management_command.data_population import populate_dummy_data

    populate_dummy_data(total_user=total_user, total_post=total_post)


@app.command()
def delete_data() -> None:
    from cli.management_command.data_population import clean_data

    clean_data()
