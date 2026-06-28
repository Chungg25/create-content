#!/usr/bin/env bash
# Tự động kết thúc nếu có lỗi
set -o errexit

# Cài đặt các thư viện Python
pip install -r requirements.txt

# Cài đặt trình duyệt Chromium (Yêu cầu bắt buộc của Crawl4AI / Playwright)
playwright install chromium
