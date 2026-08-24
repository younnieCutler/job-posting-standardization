import unittest

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

    def test_prepare_records_deduplicates_and_applies_seeded_cap(self):
        output = collector.prepare_records(
            [self.record("1"), self.record("1"), self.record("2"), self.record("3")],
            limit=2,
            seed=9,
        )

        self.assertEqual(len(output), 2)
        self.assertEqual(len({row["source_posting_id"] for row in output}), 2)


if __name__ == "__main__":
    unittest.main()
