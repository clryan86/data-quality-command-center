from __future__ import annotations

import argparse
import json
from pathlib import Path

from .services.io import read_dataset
from .services.profiling import numeric_anomalies, profile_dataframe
from .services.quality import evaluate_rules


def main() -> None:
    parser = argparse.ArgumentParser(prog="dqcc", description="Profile and validate datasets from the command line.")
    sub = parser.add_subparsers(dest="command", required=True)
    profile = sub.add_parser("profile")
    profile.add_argument("file")
    validate = sub.add_parser("validate")
    validate.add_argument("file")
    validate.add_argument("rules")
    args = parser.parse_args()
    path = Path(args.file)
    df = read_dataset(path.name, path.read_bytes())
    if args.command == "profile":
        output = {"profile": profile_dataframe(df), "anomalies": numeric_anomalies(df)}
    else:
        rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))
        output = evaluate_rules(df, rules)
    print(json.dumps(output, indent=2, default=str))


if __name__ == "__main__":
    main()
