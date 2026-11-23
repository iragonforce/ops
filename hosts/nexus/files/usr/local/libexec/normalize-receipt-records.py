#!/usr/bin/env python3

if __name__ == "__main__":
    import sys as _ops_sys
    if _ops_sys.argv[1:] == ["--help"]:
        print('Normalize existing receipt records for the maintained local ingestion workflow.\nUsage: normalize-receipt-records.py  [ARGUMENT ...]\n\nSource: hosts/nexus/files/usr/local/libexec/normalize-receipt-records.py in ~/ops\nSee man normalize-receipt-records.py for the existing call sites and argument handling.')
        raise SystemExit(0)
# Normalize existing receipt records for the maintained local ingestion workflow. See normalize-receipt-records.py(1) for source and integration details.
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])

expected = {
    "MERCHANT": 2,
    "DATE": 2,
    "CURRENCY": 2,
    "SUBTOTAL": 2,
    "TOTAL": 2,
    "TAX": 3,
    "DISCOUNT": 3,
    "ITEM": 6,
}

aliases = {
    "STORE": "MERCHANT",
    "STORE NAME": "MERCHANT",
    "MERCHANT NAME": "MERCHANT",
    "RETAILER": "MERCHANT",
}

normalized = []
skipped = 0

for line_number, original in enumerate(
    path.read_text(encoding="utf-8-sig").splitlines(), 1
):
    line = original.strip()

    if not line:
        continue

    fields = [field.strip() for field in line.split("|")]

    # Normalize Unicode formatting and invisible characters
    # in the record label without modifying field values.
    label = fields[0].upper()
    label = re.sub(r"[^A-Z]", "", label)

    label = {
        "STORE": "MERCHANT",
        "STORENAME": "MERCHANT",
        "MERCHANTNAME": "MERCHANT",
        "RETAILER": "MERCHANT",
    }.get(label, label)

    if label not in expected:
        if not normalized:
            skipped += 1
            continue

        raise SystemExit(
            f"Unrecognized record after receipt started "
            f"at line {line_number}: {label[:50]!r}"
        )

    if len(fields) != expected[label]:
        raise SystemExit(
            f"Line {line_number}: {label} has "
            f"{len(fields)} fields, expected {expected[label]}"
        )

    if not normalized and label != "MERCHANT":
        raise SystemExit(
            "First recognized record is "
            f"{label}, expected MERCHANT. "
            "Check the merchant label in the model output."
        )

    normalized.append("|".join([label, *fields[1:]]))

if not normalized:
    raise SystemExit("No valid receipt records found")

path.write_text("\n".join(normalized) + "\n")

print(
    f"Normalized {len(normalized)} records; "
    f"ignored {skipped} introductory lines",
    file=sys.stderr,
)
