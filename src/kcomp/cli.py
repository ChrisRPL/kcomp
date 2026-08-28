import os

import janus_swi as janus
import typer
from rich.console import Console

from kcomp.analysis.analyzer import StaticAnalyzer
from kcomp.backends.prolog.compiler import PrologCompiler
from kcomp.runtime.case_parser import CaseParser
from kcomp.semantic.compiler import SemanticCompiler

app = typer.Typer(help="Knowledge Compiler (kc) CLI")
console = Console()


@app.command()
def analyze(policy_file: str):
    """
    Parse a policy document and run the static analyzer on the extracted IR.
    """
    console.print(f"[bold blue]Analyzing policy:[/] {policy_file}")
    with open(policy_file, "r") as f:
        content = f.read()

    compiler = SemanticCompiler()
    console.print("Extracting IR from document...")
    ir = compiler.compile(content, document_id=os.path.basename(policy_file))

    analyzer = StaticAnalyzer(ir)
    warnings = analyzer.analyze()

    if warnings:
        console.print("[bold yellow]Static Analysis Warnings:[/]")
        for w in warnings:
            console.print(f"  - {w}")
    else:
        console.print("[bold green]Static Analysis passed with no warnings.[/]")


@app.command()
def compile(policy_file: str, out_dir: str = "src/kcomp/prolog/generated"):
    """
    Compile a policy document into Prolog rules.
    """
    console.print(f"[bold blue]Compiling policy:[/] {policy_file}")
    with open(policy_file, "r") as f:
        content = f.read()

    compiler = SemanticCompiler()
    ir = compiler.compile(content, document_id=os.path.basename(policy_file))

    analyzer = StaticAnalyzer(ir)
    warnings = analyzer.analyze()
    if warnings:
        console.print("[bold yellow]Static Analysis Warnings:[/]")
        for w in warnings:
            console.print(f"  - {w}")

    prolog_compiler = PrologCompiler()
    pl_code = prolog_compiler.compile(ir)

    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"{ir.document_id}.pl")
    with open(out_file, "w") as f:
        f.write(pl_code)
    console.print(f"[bold green]Successfully compiled to:[/] {out_file}")


@app.command()
def reason(document_id: str, case_file: str, proposition: str):
    """
    Evaluate a runtime case against a compiled policy.
    Example proposition: 'permission(work_remotely(alice))'
    """
    console.print(
        f"[bold blue]Evaluating case:[/] {case_file} [bold blue]against policy:[/] {document_id}"
    )

    with open(case_file, "r") as f:
        case_content = f.read()

    parser = CaseParser()
    case_facts = parser.parse(case_content)

    janus.query_once("consult('src/kcomp/prolog/core.pl')")
    janus.query_once("consult('src/kcomp/prolog/truth_status.pl')")
    janus.query_once(f"consult('src/kcomp/prolog/generated/{document_id}.pl')")

    janus.query_once("retractall(fact(_))")
    for fact in case_facts:
        janus.query_once(f"assertz(fact({fact}))")

    query_str = f"truth_status({proposition}, Status, Trace)"
    try:
        result = janus.query_once(query_str)
        console.print("[bold green]Decision:[/]")
        console.print(f"  Status: {result['Status']}")
        console.print(f"  Trace:  {result['Trace']}")
    except Exception as e:
        console.print(f"[bold red]Error during reasoning:[/] {e}")


if __name__ == "__main__":
    app()
