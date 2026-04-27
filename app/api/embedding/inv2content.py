from app.db.models.inv.i_nvoice import InvoiceDB


def invoice_to_content(invoice: InvoiceDB) -> str:
    return f"""
        Company Name: {invoice.company_name}
        Symbol: {invoice.symbol}

        Dividend Ex-Date: {invoice.dividend_ex_date}
        Record Date: {invoice.record_date}
        Payment Date: {invoice.payment_date}
        Announcement Date: {invoice.announcement_date}

        Dividend Rate: {invoice.dividend_rate}
        Indicated Annual Dividend: {invoice.indicated_annual_dividend}
        Yield (%): {invoice.yield_percent}

        Latest Price: {invoice.latest_price}
        Market Cap: {invoice.market_cap}
        """.strip()
