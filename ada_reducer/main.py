#!/usr/bin/env python3

import argparse
from ada_reducer import engine
from ada_reducer import gui
import os


def _main(single_file, follow_closure, project_file, predicate):
    # sanity check
    if not os.path.exists(project_file):
        print(f"project {project_file} not found")
        return

    if not os.path.exists(predicate):
        print(f"predicate script {predicate} not found")
        return

    r = engine.Reducer(project_file, predicate, single_file, follow_closure)
    gui.GUI.run(r)


args_parser = argparse.ArgumentParser(description="""
    Reduces the closure of the given main file in the
    given project as long as predicate returns 0.

    For instance:    adareducer.py sdc.gpr main.adb check.sh

     Where check.sh is a script which checks for the property
     that we want and returns 0 if we do have it.
""")
args_parser.add_argument(
    "--single-file", help="Reduce only this file."
)
args_parser.add_argument(
    "--follow-closure",
    action="store_true",
    help="Allow reducing with'ed units when using --single-file.",
)
args_parser.add_argument("project_file")
args_parser.add_argument("predicate")


def main():
    args = args_parser.parse_args()
    _main(
        args.single_file,
        args.follow_closure,
        args.project_file,
        args.predicate,
    )


if __name__ == "__main__":
    main()
