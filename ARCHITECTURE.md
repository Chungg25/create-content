# TÀI LIỆU KIẾN TRÚC HỆ THỐNG: DR. SMILE AUTO-CONTENT AGENT

## 1. MỤC TIÊU HỆ THỐNG (SYSTEM GOALS)
Hệ thống **Auto-Content Agent** được thiết kế nhằm tự động hóa 100% quy trình sản xuất nội dung Marketing cho Nha khoa Dr. Smile. 
Thay vì phải vận hành thủ công từng bước, hệ thống đóng vai trò như một **Chuyên viên Content Marketing 24/7**, có khả năng:
1. **Nghiên cứu thị trường:** Tự động tìm kiếm các bài viết đang Viral/Hot trend trên mạng xã hội.
2. **Sáng tạo nội dung:** Viết bài chuẩn SEO, chuẩn tone-giọng thương hiệu, tự động lồng ghép dịch vụ và bảng giá Dr. Smile một cách tinh tế.
3. **Chỉ đạo hình ảnh:** Tự động tư duy và sinh ra các câu lệnh (Prompt) thiết kế hình ảnh cao cấp cho đội ngũ Design (qua Leonardo.ai).
4. **Vận hành tự động:** Lên lịch xuất bản và tự động chạy ngầm theo thời gian thực mà không cần con người trực máy.

---

## 2. CẤU TRÚC AI AGENT (AGENT ARCHITECTURE)

Hệ thống được cấu thành từ 4 module chính, hoạt động liên kết chặt chẽ với nhau:

### 2.1. Khối Thu thập Dữ liệu (Crawler Module)
- **Công nghệ:** `crawl4ai` (Playwright) và Google Search.
- **Nhiệm vụ:** Khi nhận được một chủ đề (Topic), Crawler sẽ đóng vai trò như một người nghiên cứu, tự động lướt web và thu thập 5 bài viết Viral nhất trên Facebook về chủ đề đó. 
- **Cơ chế chống lỗi (Fail-safe):** Nếu bị Google chặn IP hoặc yêu cầu Captcha (thường gặp khi chạy trên Server), Crawler sẽ trả tín hiệu về cho AI để AI tự chuyển sang chế độ "Viết bài bằng kiến thức gốc" thay vì bị sập hệ thống.

### 2.2. Khối Trí tuệ Nhân tạo (The Brain - LLM Llama 3)
- **Công nghệ:** Llama-3 (thông qua API siêu tốc của Groq).
- **Cơ chế Prompt Engineering (Điều khiển Não bộ):**
  - **Brand Context:** AI được nạp sẵn toàn bộ tài liệu về Bảng giá, Chế độ bảo hành, Ưu điểm công nghệ của Dr. Smile (`doc/DrSmile.md`).
  - **Phân tích Ý định (Topic Intent):** AI tự nhận biết đây là bài *Chia sẻ kiến thức* (Cấm bán hàng, cấm nhắc giá) hay bài *So sánh/Bán dịch vụ* (Bắt buộc dò tìm trong bảng giá và báo giá thấp nhất để chốt sale).
  - **Image Prompting:** AI đọc hiểu bài đăng vừa viết để trích xuất ra câu lệnh tiếng Anh chuẩn xác cho Leonardo.ai, bắt buộc bao gồm yêu cầu chèn Text (Typography) giá tiền nếu bài viết có nhắc đến giá.

### 2.3. Khối Cơ sở Dữ liệu & Lên lịch (Database & Scheduler)
- **Công nghệ:** Google Sheets API (`gspread`) và `apscheduler`.
- **Nhiệm vụ:** 
  - Sử dụng Google Sheets làm bảng điều khiển trung tâm (CMS) giúp Sếp và nhân viên dễ dàng theo dõi trực quan trạng thái từng bài viết (Chờ xử lý ➡️ Đang tạo ➡️ Đã hoàn thành ➡️ Lỗi).
  - Khối Scheduler chạy ngầm 24/24, canh đúng đến phút người dùng đã hẹn để đánh thức AI dậy làm việc.

### 2.4. Khối Giao tiếp Con người (Human-in-the-loop UI)
- **Công nghệ:** `Gradio`.
- **Nhiệm vụ:** Tạo ra một trang web quản trị nội bộ trực quan. Cho phép nhân sự can thiệp vào giữa quá trình của AI (Chỉnh sửa nội dung AI vừa sinh ra, và yêu cầu AI tự động đọc lại bài đã sửa để sinh lại Lệnh ảnh tương ứng).

---

## 3. LUỒNG HOẠT ĐỘNG THỰC TẾ (WORKFLOW)

1. **Input:** Nhân viên nhập Chủ đề (VD: *Trồng răng Implant*) và Lịch hẹn (VD: *28/06/2026 21:00*).
2. **Database:** Nhiệm vụ được đẩy lên Google Sheets với trạng thái `Chờ xử lý`.
3. **Trigger:** Đúng 21:00, Background Worker tự động kích hoạt.
4. **Execution:**
   - Crawler đi cào 5 bài Viral nhất về Implant.
   - LLM Llama 3 đọc 5 bài Viral + Đọc bảng giá Dr.Smile ➡️ Viết ra bài Facebook Post hoàn chỉnh (có báo giá thấp nhất).
   - LLM Llama 3 đọc lại bài Facebook Post ➡️ Viết ra Lệnh tạo ảnh Leonardo (Yêu cầu có chữ 3D báo giá).
5. **Output:** Lưu bài viết và lệnh ảnh ngược lại lên Google Sheets, đổi trạng thái thành `Đã hoàn thành`.

---

## 4. TẦM NHÌN NÂNG CẤP: HỆ THỐNG TỰ HỌC PHONG CÁCH (STYLE LEARNING)

Để Agent không chỉ viết hay mà còn viết **"đúng gu của Sếp"**, hệ thống đã được vạch sẵn định hướng nâng cấp cơ chế **Tự học phong cách (Style Reference Mechanism)** trong Phase tiếp theo.

### Cơ chế hoạt động trong tương lai:
1. **File Lưu trữ Phong cách (`doc/style_reference.md`):**
   - Mỗi khi nhân sự đọc bài của AI và thấy không ưng ý, họ sẽ tự tay sửa lại văn phong (thêm bớt icon, sửa cách dùng từ xưng hô, đổi kiểu giật tít) qua tab Lịch sử trên web.
   - Khi nhân sự bấm "Lưu", hệ thống không chỉ lưu bài viết lên Google Sheets mà còn ngầm trích xuất những câu chữ nhân sự vừa sửa để ghi nhận vào file `style_reference.md` (giống như một cuốn sổ tay học việc của nhân viên).
2. **RAG (Retrieval-Augmented Generation) - Hấp thụ phong cách:**
   - Ở những lần tạo bài tiếp theo, trước khi viết, LLM bắt buộc phải đọc file `style_reference.md` này đầu tiên.
   - LLM sẽ tự động phân tích: *"À, hôm qua Sếp vừa sửa cụm từ 'Chi phí cực rẻ' thành 'Đầu tư xứng đáng', và Sếp thích dùng icon 🌟 thay vì 🔥"*.
   - Từ đó, LLM sẽ tự động uốn nắn Tone of Voice (Giọng điệu) của nó để bài viết sinh ra ngày càng giống hệt như một Copywriter ruột của công ty. Bạn dùng càng lâu, dạy nó sửa lỗi càng nhiều, con AI này sẽ càng trở nên thông minh và "hợp cạ" với bạn đến mức đáng kinh ngạc!
