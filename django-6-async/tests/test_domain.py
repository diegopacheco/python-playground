from decimal import Decimal

from django.test import SimpleTestCase

from bank.domain.errors import ValidationError
from bank.domain.identity import parse_email, parse_name
from bank.domain.money import format_amount, parse_amount


class ParseAmountTest(SimpleTestCase):
    def test_rounds_to_cents_so_the_ledger_never_stores_sub_cent_dust(self):
        self.assertEqual(parse_amount("10.005"), Decimal("10.00"))
        self.assertEqual(parse_amount("10.006"), Decimal("10.01"))

    def test_rejects_zero_and_negative_so_a_deposit_cannot_drain_an_account(self):
        for value in ["0", "0.00", "-1", "-0.01"]:
            with self.assertRaises(ValidationError):
                parse_amount(value)

    def test_rejects_non_numeric_input_instead_of_crashing_the_request(self):
        for value in ["abc", "", None, "1,00"]:
            with self.assertRaises(ValidationError):
                parse_amount(value)

    def test_caps_amount_so_a_typo_cannot_mint_unbounded_money(self):
        with self.assertRaises(ValidationError):
            parse_amount("1000000.01")

    def test_formats_with_two_decimals_so_the_ui_never_shows_a_bare_integer(self):
        self.assertEqual(format_amount(Decimal("5")), "5.00")


class IdentityTest(SimpleTestCase):
    def test_normalises_email_so_the_same_person_cannot_register_twice(self):
        self.assertEqual(parse_email("  Ada@Bank.DEV "), "ada@bank.dev")

    def test_rejects_malformed_email(self):
        for value in ["ada", "ada@bank", "@bank.dev", ""]:
            with self.assertRaises(ValidationError):
                parse_email(value)

    def test_trims_name_and_requires_content(self):
        self.assertEqual(parse_name("  Ada Lovelace  "), "Ada Lovelace")
        with self.assertRaises(ValidationError):
            parse_name(" A ")
