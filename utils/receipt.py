import os
from datetime import datetime
from config import RECEIPTS_DIR, APP_NAME


def generate_receipt(sale_data, items):
    sale = sale_data["sale"]
    receipt_lines = []
    w = 42

    receipt_lines.append("=" * w)
    receipt_lines.append(APP_NAME.upper().center(w))
    receipt_lines.append("=".center(w))
    receipt_lines.append(f"Receipt #{sale['id']}".center(w))
    receipt_lines.append(f"Date: {sale['created_at']}")
    receipt_lines.append(f"Attendant: {sale['attendant']}")
    receipt_lines.append("-" * w)
    receipt_lines.append(f"{'Item':<20}{'Qty':>4} {'Price':>8} {'Total':>8}")
    receipt_lines.append("-" * w)

    for item in items:
        name = item["product_name"][:18]
        receipt_lines.append(f"{name:<20}{item['qty']:>4} ${item['unit_price']:>7.2f} ${item['subtotal']:>7.2f}")

    receipt_lines.append("-" * w)
    if sale["discount_amount"] > 0:
        receipt_lines.append(f"{'Subtotal:':<30} ${sale['total'] + sale['discount_amount']:>8.2f}")
        receipt_lines.append(f"{'Discount:':<30} -${sale['discount_amount']:>7.2f}")
    receipt_lines.append(f"{'TOTAL:':<30} ${sale['total']:>8.2f}")
    receipt_lines.append(f"{'Payment:':<30} {sale['payment_method']:>8}")
    receipt_lines.append("=" * w)
    receipt_lines.append("Thank you for visiting!".center(w))
    receipt_lines.append(APP_NAME.center(w))
    receipt_lines.append("=".center(w))

    receipt_text = "\n".join(receipt_lines)
    filename = f"receipt_{sale['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = os.path.join(RECEIPTS_DIR, filename)
    with open(filepath, "w") as f:
        f.write(receipt_text)
    return filepath, receipt_text
