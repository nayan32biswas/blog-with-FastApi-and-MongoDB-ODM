import typer

cli_app = typer.Typer()


@cli_app.command()
def applyindexes():
    from mongodb_odm import apply_indexes

    apply_indexes()
