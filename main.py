import os
import sys

# Nhận diện môi trường Cloud (Render) thông qua biến PORT
is_cloud = os.environ.get("PORT") is not None

# Nếu chạy trên Cloud (Render), yêu cầu Playwright dùng trình duyệt cục bộ tránh lỗi cache
if is_cloud:
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"

import asyncio
import gradio as gr
from crawl4ai import AsyncWebCrawler
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Fix lỗi UnicodeEncodeError khi in emoji ra console trên Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Đọc cấu hình từ file .env
load_dotenv()

# Cấu hình Client LLM
api_key = os.getenv("GROQ_API_KEY")
is_groq = True

if not api_key:
    api_key = os.getenv("OPENAI_API_KEY")
    is_groq = False

client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1" if is_groq else None
)

# Lựa chọn Model
MODEL_NAME = "llama-3.3-70b-versatile"

async def crawl_facebook_posts(topic):
    """Sử dụng crawl4ai để tìm kiếm qua Google"""
    search_query = f"site:facebook.com '{topic}' (viral OR hot OR xu hướng)"
    # Thêm &num=5 để chỉ lấy 5 kết quả (5 bài viral nhất)
    google_search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}&num=5"
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=google_search_url)
        return result.markdown

def read_brand_context():
    """Đọc thông tin phòng khám từ file doc/DrSmile.md"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "doc", "DrSmile.md")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def read_prompt_guidelines():
    """Đọc tài liệu hướng dẫn tạo prompt Leonardo.ai"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "doc", "leonardo_ai_prompt_guidelines.md")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

async def generate_fb_post_async(topic, scraped_data, brand_context):
    system_prompt = f"""Bạn là một Copywriter và Chuyên gia Marketing Đỉnh Cao cho Nha Khoa DR. SMILE.

Thông tin phòng khám DR. SMILE:
{brand_context}

Nhiệm vụ:
1. Đọc dữ liệu tham khảo (nếu có) và phân tích cực kỳ cẩn thận chủ đề: '{topic}'.
2. Viết NGAY 1 BÀI ĐĂNG FACEBOOK HOÀN CHỈNH, cực kỳ hấp dẫn, bắt trend và mang lại giá trị cao cho người đọc.

🎯 CHIẾN LƯỢC NỘI DUNG TÙY THEO CHỦ ĐỀ:
- Hãy xác định ý định của chủ đề (Topic Intent): Đây là bài So sánh? Giải đáp thắc mắc? Hay Giới thiệu dịch vụ?
- NẾU LÀ CHỦ ĐỀ SO SÁNH (ví dụ: Veneer vs Bọc sứ): Bắt buộc phải đưa ra ưu/nhược điểm hoặc trường hợp áp dụng của CẢ 2 PHƯƠNG PHÁP một cách khách quan, chuyên sâu. Tuyệt đối không được bỏ sót vế nào hoặc thiên vị chỉ nhắc đến một dịch vụ.
- NẾU LÀ CHỦ ĐỀ CHIA SẺ KIẾN THỨC: Phải giải quyết triệt để nỗi đau/thắc mắc của khách hàng trước bằng chuyên môn sâu, sau đó mới lồng ghép khéo léo giải pháp của DR. SMILE.

⚠️ YÊU CẦU BẮT BUỘC (CRITICAL RULE):
- BẠN CHỈ ĐƯỢC PHÉP TRẢ VỀ DUY NHẤT NỘI DUNG CỦA BÀI ĐĂNG FACEBOOK. 
- KHÔNG MỞ ĐẦU bằng các câu như "Dưới đây là...", "Bài viết của bạn đây...".
- KHÔNG KẾT THÚC bằng các câu giải thích, nhận xét hay phân tích.
- TUYỆT ĐỐI KHÔNG CHIA PHẦN BẰNG NHỮNG TỪ KHÔ KHAN (như "Tiêu đề:", "Thân bài:"). Trình bày ngắt dòng, liền mạch, tự nhiên như một bài post thực tế.
- Khéo léo nhắc đến các gói dịch vụ/công nghệ của DR. SMILE liên quan đến TẤT CẢ các khía cạnh trong chủ đề.
- TUYỆT ĐỐI KHÔNG ĐƯỢC ĐỀ CẬP ĐẾN GIÁ CẢ (KHÔNG báo giá, KHÔNG nói rẻ hay đắt, KHÔNG dùng từ "chi phí").
- Phần cuối bài BẮT BUỘC phải có đầy đủ thông tin liên hệ: Hotline, Website và Địa chỉ (Address) của DR. SMILE.
- Viết sẵn sàng để người dùng COPY & PASTE lên Facebook.
- Có đầy đủ emoji và hashtag chuẩn SEO liên quan đến TẤT CẢ từ khóa trong '{topic}'.
"""
    user_prompt = f"Dữ liệu cào được:\n{scraped_data[:8000]}" 

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Lỗi khi gọi API LLM (Post): {str(e)}"

async def generate_leonardo_prompt_async(topic, fb_post, guidelines):
    system_prompt = f"""Bạn là một AI chuyên viết Prompt hình ảnh cho Leonardo.ai theo chuẩn nhận diện thương hiệu.

Dưới đây là tài liệu hướng dẫn cực kỳ quan trọng về màu sắc, đối tượng và bố cục của DR. SMILE:
{guidelines}

Nhiệm vụ của bạn:
Dựa trên bài đăng Facebook vừa được tạo về chủ đề '{topic}', hãy viết một PROMPT TIẾNG ANH duy nhất cho Leonardo.ai để tạo ảnh minh họa cho bài viết đó.

YÊU CẦU ĐẶC BIỆT MỚI VỀ CẤU TRÚC ẢNH (Dựa trên thiết kế tham khảo):
- BẠN HÃY TỰ DO SÁNG TẠO bố cục, góc chụp, biểu cảm nhân vật sao cho PHÙ HỢP NHẤT với nội dung của bài đăng Facebook chứ không gò bó. (Tuy nhiên nếu có nhân vật thì BẮT BUỘC phải là người Châu Á / Asian).
- TRÊN ẢNH PHẢI CÓ CHỮ (TEXT) BẰNG TIẾNG VIỆT CÓ DẤU. BẮT BUỘC bạn phải yêu cầu công cụ AI sinh ảnh tạo ra text Tiếng Việt CÓ DẤU chuẩn xác phù hợp với thông điệp. Ví dụ: `with typography "NỤ CƯỜI HOÀN MỸ"`, `featuring bold text "RĂNG ĐẸP TỰ TIN"`.
- BẮT BUỘC PHẢI DÙNG LOGO GỐC: Trong câu lệnh prompt, bạn phải thêm hướng dẫn sử dụng hình ảnh Logo gốc của DR. SMILE và TUYỆT ĐỐI KHÔNG thêm ngoại cảnh (background/scenery) vào khu vực logo (Ví dụ: `Ensure to integrate the exact original DR. SMILE logo provided via Image Guidance, with strictly NO background or scenery added around the logo`).
- BẮT BUỘC phải thiết kế một khu vực nhỏ (như infographic đơn giản, bảng hướng dẫn, các icon có viền) để mô tả tóm tắt QUY TRÌNH hoặc ƯU ĐIỂM của dịch vụ đó.
- Đảm bảo tuân thủ TUYỆT ĐỐI các quy tắc về màu sắc (Xanh, Trắng) từ tài liệu hướng dẫn.
- BẠN CHỈ ĐƯỢC TRẢ VỀ CÂU LỆNH PROMPT BẰNG TIẾNG ANH, không có tiêu đề, không giải thích gì thêm.
- Bắt buộc phải có Hotline và câu "Liên hệ ngay để nhận tư vấn miễn phí"
"""
    user_prompt = f"Bài đăng Facebook:\n{fb_post}"

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1024
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Lỗi khi gọi API LLM (Prompt): {str(e)}"


async def generate_fb_post_only(topic):
    if not api_key:
        return "Lỗi: Bạn chưa cấu hình biến môi trường GROQ_API_KEY trên Render."
        
    try:
        scraped_data = await crawl_facebook_posts(topic)
        if not scraped_data:
            scraped_data = "Không thể tìm thấy bài viết nào trên Google để tham khảo."
    except Exception as e:
        return f"Lỗi cào dữ liệu (Khả năng cao do Render thiếu thư viện hệ thống của Chromium): {str(e)}"
        
    brand_context = read_brand_context()
    
    # 1. Tạo bài post Facebook
    fb_post = await generate_fb_post_async(topic, scraped_data, brand_context)
    return fb_post

def generate_post_ui_action(topic):
    if not topic.strip():
        return "Vui lòng nhập chủ đề."
    return asyncio.run(generate_fb_post_only(topic))

async def generate_leonardo_prompt_only(topic, fb_post):
    if not api_key:
        return "Lỗi: Bạn cần cung cấp API KEY trong file .env"
    
    guidelines = read_prompt_guidelines()
    # 2. Tạo prompt Leonardo.ai dựa trên fb_post đã chỉnh sửa
    image_prompt = await generate_leonardo_prompt_async(topic, fb_post, guidelines)
    return image_prompt

def generate_prompt_ui_action(topic, fb_post):
    if not fb_post.strip():
        return "Vui lòng tạo bài đăng Facebook trước khi sinh lệnh tạo ảnh."
    return asyncio.run(generate_leonardo_prompt_only(topic, fb_post))

# ==========================================
# CHỨC NĂNG LÊN LỊCH & GOOGLE SHEETS
# ==========================================
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

HEADERS = ["Thời gian tạo", "Thời gian đăng", "Chủ đề", "Nội dung", "Lệnh ảnh", "Trạng thái"]

def ensure_headers(sheet):
    try:
        records = sheet.get_all_values()
        # Nếu sheet rỗng hoàn toàn, thêm dòng đầu
        if not records:
            sheet.append_row(HEADERS, table_range="A1")
            return
        
        # Nếu dòng 1 không phải là header (dựa vào cột 1), ta chèn một dòng header lên trên cùng
        if len(records[0]) == 0 or records[0][0] != "Thời gian tạo":
            sheet.insert_row(HEADERS, index=1)
    except Exception as e:
        print(f"Lỗi kiểm tra header: {e}")

def init_gsheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if not os.path.exists("credentials.json"):
            return None, "Lỗi: Không tìm thấy file credentials.json. Bạn cần tạo Google Service Account."
        
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        
        sheet_name = os.getenv("GSHEET_NAME", "DrSmile_Content_Schedule")
        try:
            sheet = client.open(sheet_name).sheet1
            ensure_headers(sheet) # Tự động tạo hoặc chèn Header nếu thiếu
        except gspread.exceptions.SpreadsheetNotFound:
            return None, f"Lỗi: Không tìm thấy Google Sheet có tên '{sheet_name}'. Hãy tạo và share quyền Edit cho email Service Account!"
        return sheet, "Kết nối Google Sheets thành công!"
    except Exception as e:
        return None, f"Lỗi kết nối Google Sheets: {str(e)}"

def schedule_topic_only(topic, schedule_date, schedule_time):
    if not topic.strip() or not schedule_date.strip() or not schedule_time.strip():
        return "Vui lòng điền đủ Chủ đề, Ngày đăng và Giờ đăng!"
    
    sheet, msg = init_gsheet()
    if sheet is None:
        return msg
        
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    schedule_datetime = f"{schedule_date} {schedule_time}"
    
    row = [now, schedule_datetime, topic, "", "", "Chờ xử lý"]
    try:
        sheet.append_row(row, table_range="A1")
        return f"✅ Đã lên lịch tự động chạy vào lúc {schedule_datetime}!"
    except Exception as e:
        return f"❌ Lỗi khi lưu dữ liệu: {str(e)}"

def save_schedule(topic, fb_post, image_prompt, schedule_date, schedule_time):
    if not fb_post.strip() or not schedule_date.strip() or not schedule_time.strip():
        return "Vui lòng điền đủ Nội dung bài, Ngày đăng và Giờ đăng!"
    
    sheet, msg = init_gsheet()
    if sheet is None:
        return msg
        
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    schedule_datetime = f"{schedule_date} {schedule_time}"
    
    row = [now, schedule_datetime, topic, fb_post, image_prompt, "Chờ đăng"]
    try:
        sheet.append_row(row, table_range="A1")
        return f"✅ Đã lưu lịch trình thành công vào lúc {now}!"
    except Exception as e:
        return f"❌ Lỗi khi lưu dữ liệu: {str(e)}"

def load_history():
    sheet, msg = init_gsheet()
    empty_data = [["", "", "", "", "", ""]]
    if sheet is None:
        return empty_data
    try:
        records = sheet.get_all_values()
        if not records:
            return empty_data
        # Kiểm tra xem dòng 1 có phải là header không (dựa vào chữ "Trạng thái")
        if len(records[0]) >= 6 and records[0][5] == "Trạng thái":
            if len(records) <= 1:
                return empty_data
            return records[1:]
        return records
    except Exception as e:
        return empty_data

def update_history_record_ui(row_index_str, topic, new_fb_post):
    if not row_index_str:
        return "Vui lòng chọn một bài viết từ bảng phía trên!", ""
    if not new_fb_post.strip():
        return "Nội dung bài viết không được để trống!", ""
        
    try:
        row_idx = int(row_index_str)
        gsheet_row = row_idx + 2 # Vì dòng 1 là header, data bắt đầu từ dòng 2
        
        # 1. Sinh lệnh ảnh mới
        new_prompt = asyncio.run(generate_leonardo_prompt_only(topic, new_fb_post))
        
        # 2. Cập nhật Gsheet
        sheet, msg = init_gsheet()
        if sheet is None:
            return msg, ""
            
        # Update cột D (Nội dung) và E (Lệnh ảnh)
        sheet.update(f'D{gsheet_row}:E{gsheet_row}', [[new_fb_post, new_prompt]])
        return "✅ Đã lưu và AI đã tạo lệnh ảnh mới! Hãy bấm 'Tải lại dữ liệu'.", new_prompt
    except Exception as e:
        return f"❌ Lỗi khi cập nhật: {str(e)}", ""

def update_history_record_manual(row_index_str, new_fb_post, new_img_prompt):
    if not row_index_str:
        return "Vui lòng chọn một bài viết từ bảng phía trên!"
    
    try:
        row_idx = int(row_index_str)
        gsheet_row = row_idx + 2
        
        sheet, msg = init_gsheet()
        if sheet is None:
            return msg
            
        sheet.update(f'D{gsheet_row}:E{gsheet_row}', [[new_fb_post, new_img_prompt]])
        return "✅ Đã lưu chỉnh sửa của bạn thành công! Hãy bấm 'Tải lại dữ liệu'."
    except Exception as e:
        return f"❌ Lỗi khi lưu: {str(e)}"

def on_history_select(evt: gr.SelectData, df_data):
    try:
        row_idx = evt.index[0]
        # Xử lý an toàn cho mọi kiểu dữ liệu mà Gradio trả về
        if hasattr(df_data, "values"):
            # Nếu là pandas DataFrame, chuyển thành list để dễ lấy index
            row = df_data.values.tolist()[row_idx]
        elif isinstance(df_data, dict) and "data" in df_data:
            row = df_data["data"][row_idx]
        else:
            row = df_data[row_idx]
        
        # Trả về: (row_index, topic, fb_post, image_prompt)
        return str(row_idx), str(row[2]), str(row[3]), str(row[4])
    except Exception as e:
        print(f"Lỗi khi bấm vào bảng lịch sử: {repr(e)}")
        return "", "Lỗi đọc dữ liệu, vui lòng xem Terminal", "", ""

import time
from apscheduler.schedulers.background import BackgroundScheduler

def process_pending_jobs():
    sheet, msg = init_gsheet()
    if sheet is None: return
    try:
        records = sheet.get_all_values()
        if not records: return
            
        current_time = datetime.now()
        # Duyệt từ dòng 1 (phòng trường hợp user không có header)
        for i, row in enumerate(records, start=1):
            if len(row) >= 6 and row[5] == "Chờ xử lý":
                try:
                    sched_time = datetime.strptime(row[1], "%d/%m/%Y %H:%M")
                except ValueError:
                    continue # Bỏ qua nếu định dạng sai
                
                if current_time >= sched_time:
                    print(f"[*] Đang tự động tạo content cho chủ đề: {row[2]}")
                    sheet.update_cell(i, 6, "Đang tạo...")
                    
                    topic = row[2]
                    try:
                        fb_post = asyncio.run(generate_fb_post_only(topic))
                        image_prompt = asyncio.run(generate_leonardo_prompt_only(topic, fb_post))
                        
                        # Cập nhật nhiều ô cùng lúc tránh limit API
                        sheet.update(f'D{i}:F{i}', [[fb_post, image_prompt, "Đã hoàn thành"]])
                        print(f"[*] Hoàn thành tạo content: {topic}")
                    except Exception as task_error:
                        error_msg = str(task_error)
                        print(f"[!] Lỗi tạo content cho {topic}: {error_msg}")
                        # Ghi đè trạng thái thành Lỗi trên Sheet để user biết
                        sheet.update_cell(i, 6, f"Lỗi: {error_msg[:100]}")
                        
                    time.sleep(2)
    except Exception as e:
        print(f"Lỗi background job: {e}")

# Khởi động Bot ngầm chạy mỗi 1 phút
scheduler = BackgroundScheduler()
scheduler.add_job(process_pending_jobs, 'interval', minutes=1)
scheduler.start()

# ==========================================
# GIAO DIỆN NGƯỜI DÙNG BẰNG GRADIO
# ==========================================
with gr.Blocks(title="Dr. Smile - AI Content Generator") as demo:
    gr.Markdown("# 🤖 Tự Động Tạo Content Viral & Hình Ảnh - DR. SMILE")
    gr.Markdown("Công cụ tự động tìm bài hot trên Facebook, viết bài Marketing, tự động sinh Prompt ảnh và Lên lịch đăng bài.")
    
    with gr.Tabs():
        with gr.TabItem("1. Tạo & Lên Lịch Content"):
            with gr.Row():
                topic_input = gr.Textbox(
                    label="Chủ đề Nha Khoa", 
                    placeholder="Ví dụ: trồng răng implant, niềng răng trong suốt...", 
                    scale=4
                )
                generate_post_btn = gr.Button("1. Tạo Bài Đăng Facebook 📝", variant="primary", scale=1)
                
            with gr.Row():
                fb_output = gr.Textbox(
                    label="1. Bài đăng Facebook (Bạn có thể Đọc & Chỉnh Sửa tự do tại đây)", 
                    lines=10,
                    interactive=True
                )
                
            with gr.Row():
                generate_prompt_btn = gr.Button("2. Đã Chỉnh Sửa Xong? Bấm Để Tạo Lệnh Ảnh 🎨", variant="secondary")

            with gr.Row():
                img_prompt_output = gr.Textbox(
                    label="2. Lệnh tạo ảnh Leonardo.ai (Copy & Paste vào Leonardo)", 
                    lines=5,
                    interactive=True
                )
                
            gr.Markdown("---")
            gr.Markdown("### 🕒 Lên Lịch Tự Động (Auto-Scheduler)")
            gr.Markdown("*Nhập Ngày/Giờ. Bạn có thể bấm **Lưu bài đã viết** nếu đã tự tạo bài ở trên, HOẶC bấm **Chỉ lên lịch Chủ đề** để hệ thống ngầm tự động cào dữ liệu và viết bài vào đúng giờ đó.*")
            with gr.Row():
                schedule_date = gr.Textbox(label="Ngày đăng (VD: 15/10/2023)", placeholder="DD/MM/YYYY")
                schedule_time = gr.Textbox(label="Giờ đăng (VD: 09:00)", placeholder="HH:MM")
            
            with gr.Row():
                save_btn = gr.Button("💾 Lưu bài đã viết", variant="secondary")
                auto_sched_btn = gr.Button("🤖 Chỉ lên lịch Chủ đề (Auto Gen)", variant="primary")
                
            with gr.Row():
                save_status = gr.Textbox(label="Trạng thái", interactive=False)
            
            # Gán sự kiện
            generate_post_btn.click(fn=generate_post_ui_action, inputs=topic_input, outputs=fb_output)
            generate_prompt_btn.click(fn=generate_prompt_ui_action, inputs=[topic_input, fb_output], outputs=img_prompt_output)
            save_btn.click(fn=save_schedule, inputs=[topic_input, fb_output, img_prompt_output, schedule_date, schedule_time], outputs=save_status)
            auto_sched_btn.click(fn=schedule_topic_only, inputs=[topic_input, schedule_date, schedule_time], outputs=save_status)

        with gr.TabItem("2. Lịch Sử Đăng Bài"):
            gr.Markdown("### 📊 Lịch Sử Content từ Google Sheets")
            gr.Markdown("*Mẹo: Bấm vào bất kỳ dòng nào trong bảng để hiển thị nội dung và sửa chữa.*")
            refresh_btn = gr.Button("🔄 Tải lại dữ liệu")
            
            history_table = gr.Dataframe(
                headers=["Thời gian tạo", "Thời gian đăng", "Chủ đề", "Nội dung", "Lệnh ảnh", "Trạng thái"],
                datatype=["str", "str", "str", "str", "str", "str"],
                col_count=(6, "fixed"),
                interactive=False,
                wrap=True
            )
            
            gr.Markdown("---")
            gr.Markdown("### ✏️ Chỉnh Sửa Nội Dung Lịch Sử")
            selected_row_state = gr.State("") # Biến ẩn lưu số thứ tự dòng
            with gr.Row():
                hist_topic_input = gr.Textbox(label="Chủ đề", interactive=False, scale=1)
            with gr.Row():
                hist_fb_post_input = gr.Textbox(label="Nội dung Facebook (Có thể Sửa trực tiếp)", lines=8, interactive=True)
            with gr.Row():
                hist_img_prompt_input = gr.Textbox(label="Lệnh tạo ảnh (Có thể Sửa trực tiếp)", lines=5, interactive=True)
            with gr.Row():
                hist_update_ai_btn = gr.Button("🤖 Lưu Nội Dung & Nhờ AI Sinh Lệnh Ảnh Mới", variant="primary")
                hist_update_manual_btn = gr.Button("💾 Chỉ Lưu Thay Đổi (Thủ công)", variant="secondary")
            with gr.Row():
                hist_update_status = gr.Textbox(label="Trạng thái cập nhật", interactive=False)
            
            # Gán sự kiện cho Tab 2
            refresh_btn.click(fn=load_history, inputs=[], outputs=history_table)
            demo.load(fn=load_history, inputs=[], outputs=history_table)
            
            # Khi click vào bảng
            history_table.select(
                fn=on_history_select, 
                inputs=[history_table], 
                outputs=[selected_row_state, hist_topic_input, hist_fb_post_input, hist_img_prompt_input]
            )
            
            # Khi bấm nút Cập nhật bằng AI
            hist_update_ai_btn.click(
                fn=update_history_record_ui,
                inputs=[selected_row_state, hist_topic_input, hist_fb_post_input],
                outputs=[hist_update_status, hist_img_prompt_input]
            )
            
            # Khi bấm nút Cập nhật thủ công
            hist_update_manual_btn.click(
                fn=update_history_record_manual,
                inputs=[selected_row_state, hist_fb_post_input, hist_img_prompt_input],
                outputs=[hist_update_status]
            )

if __name__ == "__main__":
    print("[*] Đang khởi động giao diện người dùng (UI)...")
    
    # Render thường dùng cổng 10000, mặc định fallback về 7860 cho local
    port_env = os.environ.get("PORT")
    port = int(port_env) if port_env else 7860
    
    demo.launch(
        server_name="0.0.0.0" if is_cloud else "127.0.0.1",
        server_port=port,
        inbrowser=not is_cloud, 
        theme=gr.themes.Soft(primary_hue="blue")
    )
