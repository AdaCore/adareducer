#!/usr/bin/env python3

import click
from ada_reducer import engine
from ada_reducer import gui
import os


@click.command()
@click.option("--single-file", is_flag=False, help="Reduce only this file.")
@click.option(
    "--follow-closure",
    is_flag=True,
    help="Allow reducing with'ed units when using --single-file.",
)
@click.argument("project_file")
@click.argument("predicate")
def main(single_file, follow_closure, project_file, predicate):
    """Reduces the closure of the given main file in the
    given project as long as predicate returns 0.

    For instance:    adareducer.py sdc.gpr main.adb check.sh

     Where check.sh is a script which checks for the property
     that we want and returns 0 if we do have it.
    """

    # sanity check
    if not os.path.exists(project_file):
        print(f"project {project_file} not found")
        return

    if not os.path.exists(predicate):
        print(f"predicate script {predicate} not found")
        return

    r = engine.Reducer(project_file, predicate, single_file, follow_closure)
    gui.GUI.run(r)


if __name__ == "__main__":
    main()
