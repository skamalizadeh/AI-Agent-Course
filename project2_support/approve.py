"""
صف تأیید بازپرداخت، از دید کارشناس انسانی (Human-in-the-Loop).

اجرا:
    python approve.py          # نمایش و تأیید یا رد درخواست‌های در انتظار
    python approve.py --list   # فقط نمایش
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from state_store import DATA, now, read_json, write_json
from tools import REFUNDS, TICKETS


def main() -> None:
    queue = read_json(REFUNDS, [])
    invoices = read_json(DATA / "invoices.json", {})
    pending = [r for r in queue if r["status"] == "pending"]
    tickets = [t for t in read_json(TICKETS, []) if t["status"] == "open"]
    print(f"Open tickets: {len(tickets)}")
    for t in tickets:
        print(f"  {t['id']} | {t['reason']} | {t['message'][:60]}")
    print(f"\nPending refunds: {len(pending)}")
    if not pending:
        return
    for r in pending:
        inv = invoices.get(r["invoice_id"], {})
        print(f"\n{r['id']} | invoice {r['invoice_id']} | amount {inv.get('amount')} {inv.get('currency', '')}")
        print(f"  reason : {r['reason']}")
        print(f"  note   : {inv.get('note', '')}")
        print(f"  payments: {len(inv.get('payments', []))}")
        if "--list" in sys.argv:
            continue
        choice = input("Approve? [y]es / [n]o / [s]kip: ").strip().lower()
        if choice in ("y", "n"):
            r["status"] = "approved" if choice == "y" else "rejected"
            r["decided"] = now()
            print(f"  -> {r['status']}")
    write_json(REFUNDS, queue)


if __name__ == "__main__":
    main()
