import unittest

from langchain_core.documents import Document

from app.rag_pipeline import (
    _detect_sources_mentioned_in_query,
    _extract_architecture_styles_from_text,
    _extract_en_numbered_exercises,
    _extract_vi_exercises,
    _is_exercise_content_query,
    _is_follow_up_query,
    _is_architecture_style_count_query,
    _slice_text_by_chapter,
    _build_context_for_scoring,
)


class TestDeterministicExtraction(unittest.TestCase):
    def test_extract_vi_exercises(self):
        text = """
        BAI TAP 1: Ve hinh
        Noi dung ...
        Bai tap 2: Truy xuat du lieu
        """
        exercises = _extract_vi_exercises(text)
        self.assertEqual(2, len(exercises))
        self.assertTrue(any("1" in item for item in exercises))
        self.assertTrue(any("2" in item for item in exercises))

    def test_extract_en_numbered_exercises(self):
        text = """
        1. Build API endpoint
        2. Add integration tests
        3. Document deployment steps
        """
        exercises = _extract_en_numbered_exercises(text)
        self.assertEqual(3, len(exercises))
        self.assertTrue(exercises[0].startswith("Bài 1:"))

    def test_slice_text_by_chapter(self):
        text = """
        Chapter 1
        Intro content
        1. Task A

        Chapter 2
        Deep content
        1. Task B

        Chapter 3
        Next section
        1. Task C
        """
        chapter_2_text = _slice_text_by_chapter(text, 2)
        self.assertIn("Deep content", chapter_2_text)
        self.assertIn("Task B", chapter_2_text)
        self.assertNotIn("Task C", chapter_2_text)

    def test_detect_sources_mentioned_in_query(self):
        sources = [
            "Bai_tap_123_-_Do_hoa_dinh_vi.pdf",
            "Bai_tap_123_-_Truy_xuat_phan_cung.pdf",
        ]
        query = "Cho toi dem bai tap trong file do hoa dinh vi"
        matched = _detect_sources_mentioned_in_query(query, sources)
        self.assertEqual(["Bai_tap_123_-_Do_hoa_dinh_vi.pdf"], matched)

    def test_scoring_context_is_limited(self):
        docs = [
            Document(
                page_content=("x" * 1200),
                metadata={"source": f"file_{i}.pdf", "page": i + 1},
            )
            for i in range(20)
        ]
        context = _build_context_for_scoring(docs)
        self.assertLessEqual(len(context), 3400)

    def test_architecture_style_count_query_detect(self):
        query = "Co bao nhieu phong cach kien truc trong tai lieu?"
        self.assertTrue(_is_architecture_style_count_query(query))

    def test_extract_architecture_styles_from_text(self):
        text = """
        Client/Server
        Component-Based
        Domain Driven Design
        Layered Architecture
        Message Bus
        N-Tier / 3-Tier
        Object-Oriented
        SOA
        """
        styles = _extract_architecture_styles_from_text(text)
        self.assertEqual(8, len(styles))
        self.assertIn("Client/Server", styles)
        self.assertIn("SOA", styles)

    def test_exercise_content_query_detects_bai_tap_pattern(self):
        query = "Bài tập 1 của đồ họa định vị có nội dung là gì?"
        self.assertEqual("1", _is_exercise_content_query(query))

    def test_follow_up_detection_not_triggered_for_standalone_query(self):
        query = "Bài tập 1 của đồ họa định vị có nội dung là gì?"
        self.assertFalse(_is_follow_up_query(query))

    def test_follow_up_detection_for_short_referential_query(self):
        query = "còn bài 2 thì sao?"
        self.assertTrue(_is_follow_up_query(query))


if __name__ == "__main__":
    unittest.main()
