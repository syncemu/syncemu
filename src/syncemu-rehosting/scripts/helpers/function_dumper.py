#!/usr/bin/python3
import ghidra_bridge
import json
import click


@click.command()
@click.option("--file", default="symbols.json", type=click.Path(exists=False))
def main(file):
    print(file)
    b = ghidra_bridge.GhidraBridge(namespace=globals())
    functions = b.remote_eval(
        "{int(f.getEntryPoint().toString(),16):f.getName() for f  in currentProgram.getFunctionManager().getFunctions(True)}"
    )
    for k, v in functions.items():
        print(f"key:{k}, value:{v}")
    with open(file, "w") as f:
        data = json.dumps(functions)
        f.write(data)


if __name__ == "__main__":
    main()
