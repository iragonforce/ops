#!/usr/bin/env python3

if __name__ == "__main__":
    import sys as _ops_sys
    if _ops_sys.argv[1:] == ["--help"]:
        print('Check the existing receipt deduplication policy.\nUsage: receipt-dedup-guard.py  [ARGUMENT ...]\nraise ValueError("Usage: --check normalized.json")\nSource: hosts/nexus/files/usr/local/libexec/receipt-dedup-guard.py in ~/ops\nSee man receipt-dedup-guard.py for the existing call sites and argument handling.')
        raise SystemExit(0)
# Check the existing receipt deduplication policy. See receipt-dedup-guard.py(1) for source and integration details.
import json
import re
import subprocess
import sys
import unicodedata
from datetime import date
from decimal import Decimal
from difflib import SequenceMatcher
from pathlib import Path

def normalized(value):
    value = unicodedata.normalize("NFKD", str(value or "")).casefold()
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", value))

def cents(value):
    amount = Decimal(str(value).replace("$", "").replace(",", ""))
    if not amount.is_finite():
        raise ValueError("Invalid amount")
    return amount.quantize(Decimal("0.01"))

def records(where):
    query = f"""
    SELECT json_build_object(
        'id', r.id,
        'merchant', r.name,
        'date', to_char(r.date AT TIME ZONE 'UTC', 'YYYY-MM-DD'),
        'total', r.amount::text,
        'items', COALESCE((
            SELECT json_agg(
                json_build_object('name', i.name, 'amount', i.amount)
                ORDER BY i.id
            )
            FROM public.items i
            WHERE i.receipt_id = r.id
        ), '[]'::json)
    )::text
    FROM public.receipts r
    WHERE {where}
    ORDER BY r.id ASC
    """

    result = subprocess.run(
        [
            "docker", "exec", "receipt-wrangler-db-1",
            "psql", "-X", "-A", "-t",
            "-v", "ON_ERROR_STOP=1",
            "-U", "wrangler", "-d", "wrangler",
            "-c", query
        ],
        capture_output=True,
        text=True,
        timeout=20
    )

    if result.returncode:
        raise RuntimeError("Receipt database query failed")

    return [
        json.loads(line)
        for line in result.stdout.splitlines()
        if line.strip()
    ]

def merchant_match(a, b):
    a = normalized(a)
    b = normalized(b)
    return bool(
        a and b and (
            a == b
            or (len(a) >= 5 and b.startswith(a + " "))
            or (len(b) >= 5 and a.startswith(b + " "))
        )
    )

def matching_items(source, target):
    remaining = list(target)
    matches = 0

    for item in source:
        best_index = -1
        best_score = 0

        for index, existing in enumerate(remaining):
            try:
                if cents(item.get("totalPrice", item.get("amount"))) != cents(existing["amount"]):
                    continue
            except (ValueError, KeyError):
                continue

            a = normalized(item.get("name"))
            b = normalized(existing.get("name"))

            score = SequenceMatcher(None, a, b).ratio()

            if score >= 0.73 and score > best_score:
                best_score = score
                best_index = index

        if best_index >= 0:
            remaining.pop(best_index)
            matches += 1

    return matches

def classify(new, old):
    if date.fromisoformat(new["date"][:10]) != date.fromisoformat(old["date"][:10]):
        return "CLEAR"

    if cents(new["total"]) != cents(old["total"]):
        return "CLEAR"

    a = new.get("items") or []
    b = old.get("items") or []

    matches = matching_items(a, b)

    strong_items = (
        len(a) >= 2
        and len(b) >= 2
        and matches >= 2
        and matches / len(a) >= 0.80
        and matches / len(b) >= 0.80
    )

    same_merchant = merchant_match(new["merchant"], old["merchant"])

    if strong_items and same_merchant:
        return "MATCH"

    if same_merchant or strong_items:
        return "REVIEW"

    return "CLEAR"

def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--audit-pair":
        a_id, b_id = map(int, sys.argv[2:])

        if min(a_id, b_id) <= 0:
            raise ValueError("Invalid receipt IDs")

        rows = records(f"r.id IN ({a_id}, {b_id})")

        if len(rows) != 2:
            raise ValueError("Expected two existing receipt records")

        a, b = rows

        incoming = {
            "merchant": a["merchant"],
            "date": a["date"],
            "total": a["total"],
            "items": [
                {"name": i["name"], "totalPrice": i["amount"]}
                for i in a["items"]
            ]
        }

        status = classify(incoming, b)
        print(f"Receipt IDs {a_id}/{b_id}: {status}")

        if status == "CLEAR":
            raise ValueError("Known duplicate not detected")

        return

    if len(sys.argv) != 3 or sys.argv[1] != "--check":
        raise ValueError("Usage: --check normalized.json")

    receipt = json.loads(Path(sys.argv[2]).read_text())

    day = date.fromisoformat(receipt["date"]).isoformat()
    total = cents(receipt["total"])

    candidates = records(
        "r.group_id = 1 AND "
        f"(r.date AT TIME ZONE 'UTC')::date = DATE '{day}' "
        f"AND r.amount = {total}"
    )

    results = [
        (classify(receipt, existing), existing["id"])
        for existing in candidates
    ]

    for desired, code in (("MATCH", 10), ("REVIEW", 11)):
        matches = [
            receipt_id
            for status, receipt_id in results
            if status == desired
        ]

        if matches:
            if desired == "MATCH":
                print(f"Receipt already submitted: ID={matches[0]}")
            else:
                print(
                    f"Possible duplicate: ID={matches[0]}. "
                    "Manual review required."
                )
            sys.exit(code)

    print("No matching receipt")

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(
            f"Duplicate guard error: {type(error).__name__}: {error}",
            file=sys.stderr
        )
        sys.exit(2)
