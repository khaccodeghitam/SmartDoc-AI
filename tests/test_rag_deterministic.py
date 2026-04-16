import unittest

from langchain_core.documents import Document

from src.utils import (
    detect_unknown_source_reference as _detect_unknown_source_reference,
    detect_source_filter_conflict as _detect_source_filter_conflict,
    detect_sources_mentioned_in_query as _detect_sources_mentioned_in_query,
    extract_explicit_source_reference as _extract_explicit_source_reference,
    resolve_effective_source_filter as _resolve_effective_source_filter,
)
from src.application.rag_chain_manager import (
    _extract_chapter_title_keyword,
    _extract_architecture_styles_from_text,
    _extract_en_numbered_exercises,
    _extract_vi_exercises,
    _is_exercise_count_query,
    _is_exercise_content_query,
    _is_architecture_style_count_query,
    _slice_text_by_chapter,
    _slice_text_by_chapter_title,
    _is_beginner_recommendation_query,
    _is_technology_suggestion_query,
)
from src.application.query_rewriter import (
    is_follow_up_query as _is_follow_up_query,
    should_include_history_in_prompt as _should_include_history_in_prompt,
)
from src.application.prompt_engineering import (
    is_probably_english_query as _is_probably_english_query,
)
from src.model_layer.ollama_inference_engine import (
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

    def test_extract_vi_exercises_keeps_same_number_across_sections(self):
        text = """
        RESTFUL API
        BÀI TẬP 1: GET API users

        TRUY XUẤT PHẦN CỨNG
        BÀI TẬP 1: Chụp ảnh bằng Camera
        """
        exercises = _extract_vi_exercises(text)
        self.assertEqual(2, len(exercises))
        self.assertTrue(any("RESTFUL API" in item for item in exercises))
        self.assertTrue(any("TRUY XUẤT PHẦN CỨNG" in item for item in exercises))

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

    def test_extract_chapter_title_keyword(self):
        query = "Chương RESTFUL API có bao nhiêu bài tập?"
        keyword = _extract_chapter_title_keyword(query)
        self.assertEqual("restful api", keyword)

    def test_slice_text_by_chapter_title(self):
        text = """
        LẬP TRÌNH MẠNG
        BÀI TẬP 1: Task A

        RESTFUL API
        BÀI TẬP 1: Task B
        BÀI TẬP 2: Task C

        TRUY XUẤT PHẦN CỨNG
        BÀI TẬP 1: Task D
        """
        sliced = _slice_text_by_chapter_title(text, "restful api")
        self.assertIn("Task B", sliced)
        self.assertIn("Task C", sliced)
        self.assertNotIn("Task D", sliced)

    def test_slice_text_by_chapter_title_not_cut_by_page_markers(self):
        text = """
        RESTFUL API
        BÀI TẬP 4: Task Weather
        [PAGE 2]
        BÀI TẬP 5: Task Currency

        LẬP TRÌNH MẠNG
        BÀI TẬP 1: Task Network
        """
        sliced = _slice_text_by_chapter_title(text, "restful api")
        self.assertIn("Task Weather", sliced)
        self.assertIn("Task Currency", sliced)
        self.assertNotIn("Task Network", sliced)

    def test_detect_sources_mentioned_in_query(self):
        sources = [
            "Bai_tap_123_-_Do_hoa_dinh_vi.pdf",
            "Bai_tap_123_-_Truy_xuat_phan_cung.pdf",
        ]
        query = "Cho toi dem bai tap trong file do hoa dinh vi"
        matched = _detect_sources_mentioned_in_query(query, sources)
        self.assertEqual(["Bai_tap_123_-_Do_hoa_dinh_vi.pdf"], matched)

    def test_detect_sources_mentioned_in_query_compact_filename(self):
        sources = ["DanhSachBT.docx", "Truy_xuat_phan_cung.pdf"]
        query = "Dem so bai tap trong danh sach bt"
        matched = _detect_sources_mentioned_in_query(query, sources)
        self.assertEqual(["DanhSachBT.docx"], matched)

    def test_resolve_effective_source_filter_prefers_query_mentioned_source(self):
        docs = [
            Document(page_content="A", metadata={"source": "Bai_tap_123_-_Do_hoa_dinh_vi.pdf"}),
            Document(page_content="B", metadata={"source": "Bai_tap_123_-_Truy_xuat_phan_cung.pdf"}),
            Document(page_content="C", metadata={"source": "DanhSachBT.docx"}),
        ]
        selected = ["Bai_tap_123_-_Do_hoa_dinh_vi.pdf", "Bai_tap_123_-_Truy_xuat_phan_cung.pdf"]
        query = "Cho toi dem bai tap trong file truy xuat phan cung"
        resolved = _resolve_effective_source_filter(query=query, source_filter=selected, all_docs=docs)
        self.assertEqual(["Bai_tap_123_-_Truy_xuat_phan_cung.pdf"], resolved)

    def test_resolve_effective_source_filter_keeps_selected_filter_when_query_mentions_other_file(self):
        docs = [
            Document(page_content="A", metadata={"source": "Bai_tap_123_-_Do_hoa_dinh_vi.pdf"}),
            Document(page_content="B", metadata={"source": "Bai_tap_123_-_Truy_xuat_phan_cung.pdf"}),
            Document(page_content="C", metadata={"source": "DanhSachBT.docx"}),
        ]
        selected = ["Bai_tap_123_-_Do_hoa_dinh_vi.pdf"]
        query = "Cho toi dem bai tap trong file DanhSachBT"
        resolved = _resolve_effective_source_filter(query=query, source_filter=selected, all_docs=docs)
        self.assertEqual(["Bai_tap_123_-_Do_hoa_dinh_vi.pdf"], resolved)

    def test_detect_source_filter_conflict_when_query_mentions_unselected_source(self):
        docs = [
            Document(page_content="A", metadata={"source": "Bai_tap_123_-_Do_hoa_dinh_vi.pdf"}),
            Document(page_content="B", metadata={"source": "Bai_tap_123_-_Truy_xuat_phan_cung.pdf"}),
        ]
        selected = ["Bai_tap_123_-_Do_hoa_dinh_vi.pdf"]
        query = "Noi dung bai tap trong file truy xuat phan cung"
        has_conflict, mentioned = _detect_source_filter_conflict(query=query, source_filter=selected, all_docs=docs)
        self.assertTrue(has_conflict)
        self.assertEqual(["Bai_tap_123_-_Truy_xuat_phan_cung.pdf"], mentioned)

    def test_extract_explicit_source_reference_from_query(self):
        query = "So luong bai tap cua tai lieu truy xuat phan cung co bao nhieu"
        self.assertEqual("truy xuat phan cung", _extract_explicit_source_reference(query))

    def test_extract_explicit_source_reference_ignores_generic_tai_lieu_question(self):
        query = "Tai lieu nao phu hop de hoc truoc cho nguoi moi, va vi sao?"
        self.assertIsNone(_extract_explicit_source_reference(query))

    def test_extract_explicit_source_reference_ignores_contextual_tai_lieu_phrase(self):
        query = "Trong tai lieu co goi y cong nghe hay thu vien nao dang chu y?"
        self.assertIsNone(_extract_explicit_source_reference(query))

    def test_detect_unknown_source_reference_ignores_generic_tai_lieu_clauses(self):
        docs = [
            Document(page_content="A", metadata={"source": "Bai_tap_123_-_Do_hoa_dinh_vi.pdf"}),
            Document(page_content="B", metadata={"source": "Bai_tap_123_-_Truy_xuat_phan_cung.pdf"}),
        ]

        query_1 = "Tu tai lieu hien co, rut ra tieu chi danh gia bai lam tot"
        has_unknown_1, hint_1 = _detect_unknown_source_reference(query=query_1, all_docs=docs)
        self.assertFalse(has_unknown_1)
        self.assertEqual("", hint_1)

        query_2 = "Diem giao nhau ve kien thuc giua hai tai lieu dang loc la gi?"
        has_unknown_2, hint_2 = _detect_unknown_source_reference(query=query_2, all_docs=docs)
        self.assertFalse(has_unknown_2)
        self.assertEqual("", hint_2)

    def test_detect_unknown_source_reference_when_target_not_found(self):
        docs = [
            Document(page_content="A", metadata={"source": "Bai_tap_123_-_Do_hoa_dinh_vi.pdf"}),
            Document(page_content="B", metadata={"source": "Bai_tap_123_-_Truy_xuat_phan_cung.pdf"}),
        ]
        query = "So luong bai tap cua tai lieu ftgyhujnc"
        has_unknown, hint = _detect_unknown_source_reference(query=query, all_docs=docs)
        self.assertTrue(has_unknown)
        self.assertEqual("ftgyhujnc", hint)

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

    def test_exercise_count_query_detects_so_luong_phrase(self):
        query = "Số lượng bài tập của Truy xuất phần cứng ?"
        self.assertTrue(_is_exercise_count_query(query))

    def test_probably_english_query(self):
        self.assertTrue(_is_probably_english_query("How many exercises in chapter 3?"))
        self.assertFalse(_is_probably_english_query("RESTFUL API"))

    def test_prompt_history_inclusion_for_standalone_query(self):
        query = "Tai lieu nao phu hop de hoc truoc cho nguoi moi, va vi sao?"
        self.assertFalse(_should_include_history_in_prompt(query=query, used_rewrite=False))

    def test_prompt_history_inclusion_for_follow_up_query(self):
        query = "Con bai 2 thi sao?"
        self.assertTrue(_should_include_history_in_prompt(query=query, used_rewrite=False))

    def test_prompt_history_inclusion_when_query_rewritten(self):
        query = "Tai lieu nao phu hop de hoc truoc cho nguoi moi, va vi sao?"
        self.assertTrue(_should_include_history_in_prompt(query=query, used_rewrite=True))

    def test_beginner_recommendation_query_detect(self):
        query = "Tai lieu nao phu hop de hoc truoc cho nguoi moi, va vi sao?"
        self.assertTrue(_is_beginner_recommendation_query(query))

    def test_technology_suggestion_query_detect(self):
        query = "Trong tai lieu co goi y cong nghe hay thu vien nao dang chu y?"
        self.assertTrue(_is_technology_suggestion_query(query))


if __name__ == "__main__":
    unittest.main()
