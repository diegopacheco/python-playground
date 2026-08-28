import json

from django.test import AsyncClient, TestCase


class ApiTest(TestCase):
    def setUp(self):
        self.client = AsyncClient()

    async def post(self, path, payload):
        response = await self.client.post(
            path, data=json.dumps(payload), content_type="application/json"
        )
        return response.status_code, json.loads(response.content)

    async def get(self, path):
        response = await self.client.get(path)
        return response.status_code, json.loads(response.content)

    async def open_account(self, name, email):
        _, profile = await self.post(
            "/api/profiles/", {"full_name": name, "email": email}
        )
        return profile["account"]["id"]

    async def test_creating_a_profile_returns_the_account_it_opened(self):
        status, body = await self.post(
            "/api/profiles/", {"full_name": "Ada Lovelace", "email": "ada@bank.dev"}
        )
        self.assertEqual(status, 201)
        self.assertEqual(body["email"], "ada@bank.dev")
        self.assertEqual(body["account"]["balance"], "0.00")

    async def test_missing_fields_are_reported_before_touching_the_database(self):
        status, body = await self.post("/api/profiles/", {"full_name": "Ada"})
        self.assertEqual(status, 422)
        self.assertIn("email", body["error"])

    async def test_deposit_then_withdraw_reports_running_balances(self):
        account = await self.open_account("Ada Lovelace", "ada@bank.dev")
        _, deposited = await self.post(f"/api/accounts/{account}/deposit/", {"amount": "100"})
        self.assertEqual(deposited["balance_after"], "100.00")
        _, withdrawn = await self.post(f"/api/accounts/{account}/withdraw/", {"amount": "25.50"})
        self.assertEqual(withdrawn["balance_after"], "74.50")

    async def test_overdraft_is_rejected_with_conflict_not_a_server_error(self):
        account = await self.open_account("Ada Lovelace", "ada@bank.dev")
        status, body = await self.post(f"/api/accounts/{account}/withdraw/", {"amount": "1"})
        self.assertEqual(status, 409)
        self.assertIn("cannot withdraw", body["error"])

    async def test_transfer_reports_both_sides_of_the_movement(self):
        source = await self.open_account("Ada Lovelace", "ada@bank.dev")
        target = await self.open_account("Alan Turing", "alan@bank.dev")
        await self.post(f"/api/accounts/{source}/deposit/", {"amount": "80"})
        status, body = await self.post(
            "/api/transfers/",
            {"source_account_id": source, "target_account_id": target, "amount": "30"},
        )
        self.assertEqual(status, 201)
        self.assertEqual(body["sent"]["balance_after"], "50.00")
        self.assertEqual(body["received"]["balance_after"], "30.00")
        self.assertEqual(body["sent"]["counterparty"], "Alan Turing")

    async def test_statement_lists_every_movement_newest_first(self):
        account = await self.open_account("Ada Lovelace", "ada@bank.dev")
        await self.post(f"/api/accounts/{account}/deposit/", {"amount": "10"})
        await self.post(f"/api/accounts/{account}/deposit/", {"amount": "20"})
        status, body = await self.get(f"/api/accounts/{account}/transactions/")
        self.assertEqual(status, 200)
        self.assertEqual([t["amount"] for t in body["transactions"]], ["20.00", "10.00"])

    async def test_unknown_account_returns_404(self):
        status, _ = await self.get("/api/accounts/999/")
        self.assertEqual(status, 404)

    async def test_wrong_method_is_rejected_so_reads_cannot_move_money(self):
        account = await self.open_account("Ada Lovelace", "ada@bank.dev")
        response = await self.client.get(f"/api/accounts/{account}/deposit/")
        self.assertEqual(response.status_code, 405)

    async def test_malformed_json_is_reported_as_a_client_error(self):
        account = await self.open_account("Ada Lovelace", "ada@bank.dev")
        response = await self.client.post(
            f"/api/accounts/{account}/deposit/",
            data="{not json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 422)

    async def test_index_page_serves_the_single_page_ui(self):
        response = await self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Async Bank")
