#!/usr/bin/env bash
# Tự động kết thúc nếu có lỗi
set -o errexit

# Cài đặt các thư viện Python
pip install -r requirements.txt

# Yêu cầu Playwright cài đặt trình duyệt vào thư mục cục bộ (tránh lỗi cache của Render)
export PLAYWRIGHT_BROWSERS_PATH=0
playwright install chromium
