def test_create_transaction_and_list(client):
    resp = client.post(
        "/api/finance/transactions",
        json={"type": "income", "category": "Ürün satışı", "amount": "1500.00"},
    )
    assert resp.status_code == 201

    resp = client.get("/api/finance/transactions")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_summary_computes_income_expense_net(client):
    client.post("/api/finance/transactions", json={"type": "income", "amount": "1000.00"})
    client.post("/api/finance/transactions", json={"type": "income", "amount": "500.00"})
    client.post("/api/finance/transactions", json={"type": "expense", "amount": "300.00"})

    resp = client.get("/api/finance/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert float(body["total_income"]) == 1500.0
    assert float(body["total_expense"]) == 300.0
    assert float(body["net_profit"]) == 1200.0


def test_summary_with_no_transactions_is_zero(client):
    resp = client.get("/api/finance/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert float(body["total_income"]) == 0.0
    assert float(body["total_expense"]) == 0.0
    assert float(body["net_profit"]) == 0.0
