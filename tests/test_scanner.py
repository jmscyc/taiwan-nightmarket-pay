import unittest
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))
from scan_and_notify import check_quota_status, SimpleHTMLTextExtractor

class TestQuotaChecker(unittest.TestCase):
    def test_active_promotion(self):
        promo = {
            "title": "測試夜市優惠",
            "end_date": "2099-12-31",
            "status": "ACTIVE"
        }
        status, note = check_quota_status(promo, "一般活動內容滿百送十")
        self.assertEqual(status, "ACTIVE")
        self.assertIn("尚有名額", note)

    def test_full_keyword_detection(self):
        promo = {
            "title": "測試夜市優惠",
            "end_date": "2099-12-31",
            "status": "ACTIVE"
        }
        status, note = check_quota_status(promo, "本活動回饋預算已用罄，感謝大家支持！")
        self.assertEqual(status, "FULL")
        self.assertIn("額滿", note)

    def test_expired_promotion(self):
        promo = {
            "title": "過期活動",
            "end_date": "2020-01-01",
            "status": "ACTIVE"
        }
        status, note = check_quota_status(promo, "")
        self.assertEqual(status, "EXPIRED")
        self.assertIn("自然截止", note)

    def test_html_parser(self):
        parser = SimpleHTMLTextExtractor()
        parser.feed("<div><h1>標題</h1><p>優惠內容<script>ignore me</script></p></div>")
        text = parser.get_text()
        self.assertIn("標題", text)
        self.assertIn("優惠內容", text)
        self.assertNotIn("ignore me", text)

if __name__ == '__main__':
    unittest.main()
