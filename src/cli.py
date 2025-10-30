import typer
from src.ingest.rss import ingest_rss
from src.ingest.jobs import ingest_jobs
from src.normalize.to_events import normalize_all
from src.features.extract import annotate_events
from src.score.rank import daily_scores
from src.rag.embed import ensure_index
from src.rag.retrieve import gather_context
from src.llm.draft import make_drafts
from src.delivery.approve import set_status
from src.delivery.send_email import send_batch

app = typer.Typer(help="Sales Intelligence Agent (Headless)")

@app.command()
def ingest(
    companies: str = typer.Option(
        "config/companies.yaml",
        "--companies",
        help="Path to companies YAML",
    ),
):
    """Fetch RSS, jobs, etc., and store as events."""
    ingest_rss(companies)
    ingest_jobs(companies)
    normalize_all()

@app.command()
def score(
    rules: str = typer.Option(
        "config/rules.yaml",
        "--rules",
        help="Path to scoring rules YAML",
    ),
):
    """Extract features and compute daily account scores."""
    annotate_events()
    daily_scores(rules)

@app.command()
def draft(
    top_n: int = typer.Option(
        10,
        "--top-n",
        help="How many top companies to draft for",
    ),
    variants: int = typer.Option(
        2,
        "--variants",
        help="How many variants per company",
    ),
):
    """Build index, gather context, and generate email drafts."""
    ensure_index()
    gather_context(top_n=top_n)
    make_drafts(top_n=top_n, variants=variants)

@app.command()
def approve(
    draft_id: str = typer.Argument(..., help="Draft ID"),
    status: str = typer.Option(
        "approved",
        "--status",
        help="queued / approved / rejected",
    ),
):
    """Mark a draft as approved/rejected/queued."""
    set_status(draft_id, status)

@app.command()
def send(
    provider: str = typer.Option(
        "dryrun",
        "--provider",
        help="dryrun / SendGrid / Gmail",
    ),
    # Keep as a regular option to avoid paired-flag quirks on older Click
    only_approved: bool = typer.Option(
        True,
        "--only-approved",
        help="Send only approved drafts (true/false)",
    ),
):
    """Send drafts via provider."""
    send_batch(provider=provider, only_approved=only_approved)

@app.command()
def report():
    """Generate CSV/Markdown report (stub for now)."""
    print("Report generation TODO (will compile CSV + REPORT.md)")

if __name__ == "__main__":
    app()
