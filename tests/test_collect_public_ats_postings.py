import unittest

from ingestion import collect_public_ats_postings as collector


class CollectPublicAtsPostingsTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
