import unittest
from urllib.error import URLError

from ingestion import collect_public_ats_postings as collector


class CollectPublicAtsPostingsTests(unittest.TestCase):
    def record(self, posting_id):
        return {
            "source_platform": "greenhouse",
            "source_posting_id": posting_id,
            "title": "Engineer",
        }

    def test_greenhouse_record_is_filtered_and_normalized(self):
        record = collector.greenhouse_record(
            {
                "id": 7,
                "title": "Data Engineer",
                "absolute_url": "https://example.test/jobs/7",
                "location": {"name": "Tokyo"},
                "departments": [{"name": "Engineering"}],
                "content": "Build data pipelines.",
            },
            "Example",
        )

        self.assertEqual(record["source_platform"], "greenhouse")
        self.assertEqual(record["source_posting_id"], "7")
        self.assertEqual(record["company_name"], "Example")
        self.assertTrue(collector.is_it_record(record))

    def test_ashby_record_is_filtered_and_normalized(self):
        record = collector.ashby_record(
            {
                "id": "job-8",
                "title": "Platform Engineer",
                "jobUrl": "https://jobs.ashbyhq.com/example/job-8",
                "location": "Tokyo",
                "department": "Engineering",
                "descriptionHtml": "<p>Operate cloud platforms.</p>",
            },
            "Example",
        )

        self.assertEqual(record["source_platform"], "ashby")
        self.assertEqual(record["source_posting_id"], "job-8")
        self.assertTrue(collector.is_it_record(record))

    def test_prepare_records_deduplicates_and_applies_seeded_cap(self):
        output = collector.prepare_records(
            [self.record("1"), self.record("1"), self.record("2"), self.record("3")],
            limit=2,
            seed=9,
        )

        self.assertEqual(len(output), 2)
        self.assertEqual(len({row["source_posting_id"] for row in output}), 2)

    def test_collect_board_records_captures_a_source_failure(self):
        rows, failure = collector.collect_board_records(
            {"ats": "greenhouse", "board": "bad", "company": "Example"},
            fetch_json=lambda _: (_ for _ in ()).throw(URLError("offline")),
        )

        self.assertEqual(rows, [])
        self.assertIn("offline", failure)

    def test_catalog_boards_selects_supported_unique_companies(self):
        boards = collector.catalog_boards(
            [
                {"platform": "greenhouse", "slug": "stripe", "name": "Stripe"},
                {"platform": "ashby", "slug": "openai", "name": "OpenAI"},
                {"platform": "lever", "slug": "skip", "name": "Skip"},
                {"platform": "greenhouse", "slug": "stripe", "name": "Stripe"},
            ],
            limit=2,
        )

        self.assertEqual(
            boards,
            [
                {"ats": "greenhouse", "board": "stripe", "company": "Stripe"},
                {"ats": "ashby", "board": "openai", "company": "OpenAI"},
            ],
        )

    def test_default_paths_partition_by_run_date(self):
        output, manifest = collector.default_paths("2026-08-25")

        self.assertTrue(str(output).endswith("dt=2026-08-25/postings.csv"))
        self.assertTrue(str(manifest).endswith("dt=2026-08-25/manifest.json"))

    def test_select_companies_keeps_all_records_for_the_first_companies(self):
        rows = [
            {"company_name": "A", "source_posting_id": "1"},
            {"company_name": "A", "source_posting_id": "2"},
            {"company_name": "B", "source_posting_id": "3"},
            {"company_name": "C", "source_posting_id": "4"},
        ]

        self.assertEqual(
            collector.select_companies(rows, target=2),
            rows[:3],
        )


if __name__ == "__main__":
    unittest.main()
