from __future__ import annotations

import json
import unittest
from datetime import date, datetime
from unittest.mock import patch

from _sync_operator import (
    extract_pacotes,
    extract_pvoo_payload,
    fetch_text,
    filter_promo_voos,
    filter_pacotes,
    has_minimum_flight_sale_lead,
    has_publishable_destination,
    is_internal_package,
)


PACKAGE = {
    "nome": "Roteiro de teste",
    "destino": "Destino de teste",
    "slug": "roteiro-de-teste",
    "origens": [{"iata": "GIG", "cidade": "Rio de Janeiro", "data": "10/11/2027"}],
}


class SyncSourceExtractionTests(unittest.TestCase):
    def test_extracts_legacy_inline_array(self) -> None:
        source = f"<script>const PACOTES = {json.dumps([PACKAGE])};</script>"
        self.assertEqual(extract_pacotes(source), [PACKAGE])

    def test_extracts_array_from_same_origin_script(self) -> None:
        source = '<script src="/_s/pacotes.js?p=1&amp;n=3"></script>'
        script = f"(function(){{ const PACOTES = {json.dumps([PACKAGE])}; }})();"
        requested: list[str] = []

        def fetcher(url: str) -> str:
            requested.append(url)
            return script

        self.assertEqual(extract_pacotes(source, fetcher), [PACKAGE])
        self.assertEqual(requested, ["https://viajandocomdesconto.com/_s/pacotes.js?p=1&n=3"])

    def test_ignores_external_scripts(self) -> None:
        source = '<script src="https://cdn.example.invalid/pacotes.js"></script>'

        def fetcher(_: str) -> str:
            raise AssertionError("script externo não deveria ser consultado")

        with self.assertRaisesRegex(RuntimeError, "PACOTES não encontrado"):
            extract_pacotes(source, fetcher)

    def test_rejects_invalid_package_assignment(self) -> None:
        source = '<script src="/_s/pacotes.js"></script>'

        with self.assertRaisesRegex(RuntimeError, "PACOTES não encontrado"):
            extract_pacotes(source, lambda _: "const PACOTES = não-json;")

    def test_extracts_flight_payload_from_same_origin_script(self) -> None:
        source = '<script src="/_s/voos.js"></script>'
        payload = {"blob": "GIG|FOR|271110|271115|5|1|1000", "mapa": {}}
        script = f"window.__PVOO_PAYLOAD = {json.dumps(payload)};"

        self.assertEqual(extract_pvoo_payload(source, lambda _: script), payload)

    def test_requires_48_hours_before_flight_departure(self) -> None:
        now = datetime(2099, 1, 1, 12, 0)
        departure = date(2099, 1, 3)

        self.assertTrue(has_minimum_flight_sale_lead(departure, "12:00", now=now))
        self.assertFalse(has_minimum_flight_sale_lead(departure, "11:59", now=now))
        self.assertFalse(has_minimum_flight_sale_lead(departure, None, now=now))

    def test_filters_flights_with_insufficient_sale_lead_time(self) -> None:
        def row(departure_time: str) -> str:
            return "|".join([
                "GIG", "FOR", "990103", "990104", "1", "1", "1000", "0", "", departure_time,
                "", "1200", "", "0", "1", "Companhia",
            ])

        selected, stats = filter_promo_voos(
            {"blob": "\n".join([row("1200"), row("1159")]), "mapa": {}},
            now=datetime(2099, 1, 1, 12, 0),
        )

        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["departure_time"], "12:00")
        self.assertEqual(stats["ignored_insufficient_lead_time"], 1)

    def test_blocks_external_redirects(self) -> None:
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def geturl(self):
                return "https://cdn.example.invalid/pacotes.js"

            def read(self):
                raise AssertionError("resposta redirecionada não deveria ser lida")

        with patch("_sync_operator.urllib.request.urlopen", return_value=Response()):
            with self.assertRaisesRegex(RuntimeError, "origem externa bloqueado"):
                fetch_text("https://viajandocomdesconto.com/_s/pacotes.js")

    def test_rejects_internal_and_incomplete_packages(self) -> None:
        internal = {"nome": "Pacote Especial para a Cativa Operadora", "destino": "RECEPÇÃO"}
        self.assertTrue(is_internal_package(internal))
        self.assertFalse(has_publishable_destination(internal))
        self.assertFalse(has_publishable_destination({"destino": "Os"}))
        self.assertFalse(has_publishable_destination({"destino": "Buenos"}))
        self.assertFalse(has_publishable_destination({"destino": ""}))
        self.assertTrue(has_publishable_destination({"destino": "Islândia"}))

    def test_filter_reports_and_ignores_invalid_source_records(self) -> None:
        base = {
            "slug": "pacote-valido",
            "nome": "Roteiro válido",
            "destino": "Islândia",
            "capa": "img/islandia.png",
            "origens": [{
                "iata": "",
                "cidade": "",
                "data": "10/01/2027 a 14/01/2027",
                "inclui": [],
                "hoteis": [{"nome": "Hotel", "preco": "R$ 1.000,00", "parcela": "10x de R$ 100"}],
            }],
        }
        records = [
            base,
            {**base, "slug": "interno", "nome": "Pacote Especial para a Cativa Operadora"},
            {**base, "slug": "truncado", "destino": "Buenos"},
        ]

        selected, stats = filter_pacotes(records)

        self.assertEqual(len(selected), 1)
        self.assertEqual(stats["ignored_internal"], 1)
        self.assertEqual(stats["ignored_destination"], 1)

    def test_ignores_packages_without_image_or_reuses_destination_image(self) -> None:
        no_image = {
            "slug": "sem-imagem",
            "nome": "Roteiro sem imagem",
            "destino": "Bangkok",
            "origens": [],
        }
        selected, stats = filter_pacotes([no_image])
        self.assertEqual(selected, [])
        self.assertEqual(stats["ignored_image"], 1)

        sibling = {
            **no_image,
            "slug": "com-imagem",
            "capa": "img/bangkok.png",
        }
        selected, stats = filter_pacotes([no_image, sibling])
        self.assertEqual(len(selected), 2)
        self.assertEqual({offer["capa"] for offer in selected}, {"img/bangkok.png"})
        self.assertEqual(stats["ignored_image"], 0)


if __name__ == "__main__":
    unittest.main()
