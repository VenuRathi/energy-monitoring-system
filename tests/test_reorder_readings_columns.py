import unittest

from scripts.reorder_readings_columns import replacement_partition_name


class ReorderReadingsColumnsTests(unittest.TestCase):
    def test_replacement_partition_uses_runtime_partition_prefix(self) -> None:
        self.assertEqual(
            replacement_partition_name("readings_2026_08_19"),
            "readings_2026_08_19",
        )
        self.assertEqual(
            replacement_partition_name("readings_reordered_2026_08_19"),
            "readings_2026_08_19",
        )

    def test_replacement_partition_rejects_unexpected_names(self) -> None:
        with self.assertRaises(ValueError):
            replacement_partition_name("readings_backup_2026_08_19")


if __name__ == "__main__":
    unittest.main()
