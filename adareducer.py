import click
from src import engine
import os

@click.command()
@click.argument("project_file")
@click.argument("main_file")
@click.argument("predicate")
def main(project_file, main_file, predicate):
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

    r = engine.Reducer(project_file, main_file, predicate)
    r.run()

if __name__ == '__main__':
    main()