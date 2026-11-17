"""
CLI Interface for HDFC Bank Daily Price Predictor & Backtesting System.
"""
import argparse
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from hdfc_predictor.signal_generator import SignalGenerator
from hdfc_predictor.backtester import Backtester
from hdfc_predictor.learner import FeedbackLearner
from hdfc_predictor.scheduler import SchedulerManager, LAUNCHD_PLIST_PATH
from hdfc_predictor.dashboard import launch_dashboard
from hdfc_predictor.config import settings

console = Console()


def cmd_signal(args):
    """Executes the daily 2:00 PM signal engine."""
    console.print("\n[bold cyan]⚡ Running HDFC Bank Daily 2:00 PM Decision Engine...[/bold cyan]")
    generator = SignalGenerator()
    result = generator.run_daily_signal(force=True)
    generator.print_signal_console(result)
    console.print(f"[dim]Daily report saved to: {settings.daily_report_path}[/dim]\n")


def cmd_backtest(args):
    """Runs historical strategy backtest."""
    period = args.period or "2y"
    console.print(f"\n[bold cyan]📊 Running Backtest on {settings.symbol} ({period})...[/bold cyan]")
    bt = Backtester()
    res = bt.run_backtest(period=period)

    table = Table(title=f"HDFC Bank Backtest Results ({res.start_date} to {res.end_date})")
    table.add_column("Quantitative Metric", style="cyan")
    table.add_column("AI Strategy", style="green bold")
    table.add_column("Buy & Hold Benchmark", style="white")

    strat_color = "green" if res.strategy_return_pct >= 0 else "red"
    bench_color = "green" if res.benchmark_return_pct >= 0 else "red"

    table.add_row("Total Return", f"[{strat_color}]{res.strategy_return_pct:+.2f}%[/{strat_color}]", f"[{bench_color}]{res.benchmark_return_pct:+.2f}%[/{bench_color}]")
    table.add_row("CAGR (Annualized)", f"{res.cagr_pct:+.2f}%", "--")
    table.add_row("Sharpe Ratio (Rf=6.5%)", f"{res.sharpe_ratio:.2f}", "--")
    table.add_row("Sortino Ratio", f"{res.sortino_ratio:.2f}", "--")
    table.add_row("Max Drawdown", f"[red]{res.max_drawdown_pct:.2f}%[/red]", "--")
    table.add_row("Total Trades Taken", str(res.total_trades), "1")
    table.add_row("Win Rate %", f"{res.win_rate_pct:.1f}%", "--")
    table.add_row("Profit Factor", f"{res.profit_factor:.2f}", "--")
    table.add_row("Avg Trade P&L", f"{res.avg_trade_pnl_pct:+.2f}%", "--")
    table.add_row("Max Consecutive Wins/Losses", f"{res.max_consecutive_wins} wins / {res.max_consecutive_losses} losses", "--")

    console.print(table)

    # News sensitivity breakdown
    reg_table = Table(title="News Sentiment Regime Performance")
    reg_table.add_column("News Regime", style="cyan")
    reg_table.add_column("Trades", style="white")
    reg_table.add_column("Win Rate %", style="green")
    reg_table.add_column("Avg P&L %", style="yellow")

    for reg_name, stats in res.news_regime_performance.items():
        clean_name = reg_name.replace("_", " ").title()
        reg_table.add_row(clean_name, str(stats["trades"]), f"{stats['win_rate']:.1f}%", f"{stats['avg_pnl']:+.2f}%")

    console.print(reg_table)
    console.print()


def cmd_learn(args):
    """Reconciles pending predictions and prints feedback loop progression."""
    console.print("\n[bold cyan]🧠 Running Self-Improving Feedback Loop Reconciliation...[/bold cyan]")
    learner = FeedbackLearner()
    
    if getattr(args, "seed", False):
        console.print("[cyan]Seeding verified 14-day history for baseline calibration...[/cyan]")
        learner.seed_recent_verified_history(days=14)

    reconciled = learner.reconcile_pending_predictions()

    if reconciled:
        console.print(f"[green]Reconciled {len(reconciled)} past predictions against verified market outcomes![/green]")
    else:
        console.print("[dim]No pending unverified predictions found (awaiting next market close).[/dim]")

    stats = learner.update_model_and_recalibrate()
    table = Table(title="Self-Improving Brain Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta bold")

    table.add_row("Total Verified Outcomes", str(stats.get("total_samples", 0)))
    table.add_row("Overall Model Accuracy", f"{stats.get('overall_accuracy', 0.0):.1f}%")
    table.add_row("Rolling 7-Day Accuracy", f"{stats.get('rolling_7d_accuracy', 0.0):.1f}%")
    table.add_row("Rolling 30-Day Accuracy", f"{stats.get('rolling_30d_accuracy', 0.0):.1f}%")
    table.add_row("Simulated Strategy P&L", f"{stats.get('total_pnl_pct', 0.0):+.2f}%")
    table.add_row("Profit Factor", f"{stats.get('profit_factor', 1.0):.2f}")
    table.add_row("Calibrated Buy Threshold", f"{stats.get('calibrated_buy_threshold', 0.55):.3f}")
    table.add_row("Calibrated Sell Threshold", f"{stats.get('calibrated_sell_threshold', 0.45):.3f}")
    table.add_row("Operational Notes", stats.get("notes", "Normal"))

    console.print(table)
    console.print()


def cmd_schedule(args):
    """Manages automation scheduling."""
    if args.install_launchd:
        msg = SchedulerManager.install_macos_launchagent()
        console.print(f"[green]{msg}[/green]")
    elif args.uninstall_launchd:
        msg = SchedulerManager.uninstall_macos_launchagent()
        console.print(f"[yellow]{msg}[/yellow]")
    elif args.daemon:
        console.print("[cyan]Starting foreground daemon scheduler... Press Ctrl+C to exit.[/cyan]")
        SchedulerManager.run_daemon_loop()
    else:
        is_installed = LAUNCHD_PLIST_PATH.exists()
        status_txt = "[green]Active & Scheduled (Mon-Fri 14:00 IST)[/green]" if is_installed else "[yellow]Not Installed[/yellow]"
        console.print(Panel(f"macOS Background Schedule (LaunchAgent): {status_txt}\n\nTo install automated 2:00 PM schedule:\n  python -m hdfc_predictor schedule --install-launchd\n\nTo remove:\n  python -m hdfc_predictor schedule --uninstall-launchd", title="HDFC Predictor Automation Status"))


def cmd_dashboard(args):
    """Launches local web dashboard."""
    port = args.port or 8501
    launch_dashboard(port=port)


def main():
    parser = argparse.ArgumentParser(description="HDFC Bank Daily AI Predictor & Backtesting Engine")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # signal
    p_signal = subparsers.add_parser("signal", help="Run 2:00 PM signal now")

    # backtest
    p_bt = subparsers.add_parser("backtest", help="Run historical backtest")
    p_bt.add_argument("--period", default="2y", choices=["1y", "2y", "3y", "5y"], help="Historical backtest period")

    # learn
    p_learn = subparsers.add_parser("learn", help="Reconcile outcomes and update self-improving brain")
    p_learn.add_argument("--seed", action="store_true", help="Seed past 14 days of verified history for immediate baseline")

    # schedule
    p_sched = subparsers.add_parser("schedule", help="Manage 2:00 PM automated schedule")
    p_sched.add_argument("--install-launchd", action="store_true", help="Install macOS launchd agent (runs 2:00 PM Mon-Fri)")
    p_sched.add_argument("--uninstall-launchd", action="store_true", help="Uninstall macOS launchd agent")
    p_sched.add_argument("--daemon", action="store_true", help="Run continuous foreground daemon loop")

    # dashboard
    p_dash = subparsers.add_parser("dashboard", help="Launch interactive web dashboard")
    p_dash.add_argument("--port", type=int, default=8501, help="Port to bind dashboard")

    args = parser.parse_args()

    if args.command == "signal":
        cmd_signal(args)
    elif args.command == "backtest":
        cmd_backtest(args)
    elif args.command == "learn":
        cmd_learn(args)
    elif args.command == "schedule":
        cmd_schedule(args)
    elif args.command == "dashboard":
        cmd_dashboard(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
