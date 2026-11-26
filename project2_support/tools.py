"""
ابزارهای متخصص‌ها — اسلاید «داده و ابزارهای هر متخصص».

    پیگیری سفارش  ← track_order
    صورت‌حساب     ← get_invoice، request_refund (فقط با تأیید انسان)
    پشتیبانی فنی  ← search_knowledge (RAG)
    همه           ← create_ticket (ارجاع به کارشناس انسانی)
"""

import json

from kb_search import KnowledgeBase
from state_store import DATA, STATE, now, read_json, write_json

REFUNDS = STATE / "refunds.json"
FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
TICKETS = STATE / "tickets.json"
_kb = None


def track_order(order_id: str) -> str:
    """Return status, carrier and delivery date of an order."""
    orders = read_json(DATA / "orders.json", {})
    order_id = str(order_id).translate(FA_DIGITS).strip().lstrip("#")
    order = orders.get(order_id)
    if not order:
        return f"Error: order {order_id} not found. Ask the customer to check the number."
    safe = {k: v for k, v in order.items() if k != "customer"}   # دادهٔ شخصی لازم نیست
    return json.dumps({"order_id": order_id, **safe}, ensure_ascii=False)


def get_invoice(invoice_id: str) -> str:
    """Return invoice details and payment records."""
    invoices = read_json(DATA / "invoices.json", {})
    invoice_id = str(invoice_id).translate(FA_DIGITS).strip().upper()
    inv = invoices.get(invoice_id)
    if not inv:
        return f"Error: invoice {invoice_id} not found."
    return json.dumps({"invoice_id": invoice_id, **inv}, ensure_ascii=False)


def add_to_queue(invoice_id: str, reason: str) -> str:
    queue = read_json(REFUNDS, [])
    rid = f"R-{len(queue) + 1:04d}"
    queue.append({"id": rid, "invoice_id": invoice_id, "reason": reason,
                  "status": "pending", "created": now()})
    write_json(REFUNDS, queue)
    return rid


def request_refund(invoice_id: str, reason: str) -> str:
    """Create a refund request; a human must approve it (Human-in-the-Loop)."""
    if invoice_id.strip().upper() not in read_json(DATA / "invoices.json", {}):
        return f"Error: invoice {invoice_id} not found."
    rid = add_to_queue(invoice_id.strip().upper(), reason)
    return (f"Refund request {rid} saved and waiting for human approval. "
            "Do not promise the refund.")


def search_knowledge(query: str) -> str:
    """Search the product help center."""
    global _kb
    if _kb is None:
        _kb = KnowledgeBase()
    results = _kb.search(query)
    return "\n\n".join(results) if results else "No relevant article found."


def create_ticket(message: str, reason: str) -> str:
    """Create a ticket for a human agent and return its id."""
    tickets = read_json(TICKETS, [])
    tid = f"T-{len(tickets) + 1:04d}"
    tickets.append({"id": tid, "message": message, "reason": reason,
                    "status": "open", "created": now()})
    write_json(TICKETS, tickets)
    return tid


def _tool(name, description, props, required):
    return {"type": "function", "function": {"name": name, "description": description,
            "parameters": {"type": "object", "properties": props, "required": required}}}


TRACK_ORDER = _tool("track_order", "Get the status and delivery date of an order by its number.",
                    {"order_id": {"type": "string", "description": "e.g. 1042"}}, ["order_id"])
GET_INVOICE = _tool("get_invoice", "Get invoice details and payments by invoice id.",
                    {"invoice_id": {"type": "string", "description": "e.g. INV-77"}}, ["invoice_id"])
REQUEST_REFUND = _tool("request_refund",
                       "Create a refund request for an invoice. It needs human approval; it does not pay.",
                       {"invoice_id": {"type": "string"}, "reason": {"type": "string"}},
                       ["invoice_id", "reason"])
SEARCH_KB = _tool("search_knowledge",
                  "Search the product help center. Use it for any technical question before answering.",
                  {"query": {"type": "string"}}, ["query"])
