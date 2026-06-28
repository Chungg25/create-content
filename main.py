import os
import sys
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
    google_search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
    
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
1. Đọc dữ liệu cào được từ các bài đăng viral về '{topic}'.
2. Viết NGAY 1 BÀI ĐĂNG FACEBOOK HOÀN CHỈNH, cực kỳ hấp dẫn, bắt trend và lồng ghép khéo léo dịch vụ của DR. SMILE.

⚠️ YÊU CẦU BẮT BUỘC (CRITICAL RULE):
- BẠN CHỈ ĐƯỢC PHÉP TRẢ VỀ DUY NHẤT NỘI DUNG CỦA BÀI ĐĂNG FACEBOOK. 
- KHÔNG MỞ ĐẦU bằng các câu như "Dưới đây là...", "Bài viết của bạn đây...".
- KHÔNG KẾT THÚC bằng các câu giải thích, nhận xét hay phân tích.
- TUYỆT ĐỐI KHÔNG CHIA PHẦN (ví dụ không ghi "Tiêu đề:", "Thân bài:"). Viết liền mạch như một bài post thực tế.
- BẮT BUỘC liệt kê một vài DỊCH VỤ CON hoặc gói dịch vụ cụ thể của DR. SMILE CÓ LIÊN QUAN TRỰC TIẾP đến chủ đề '{topic}'. (KHÔNG liệt kê lan man các dịch vụ không liên quan).
- TUYỆT ĐỐI KHÔNG ĐƯỢC ĐỀ CẬP ĐẾN GIÁ CẢ (KHÔNG báo giá, KHÔNG nói rẻ hay đắt, KHÔNG dùng từ "chi phí").
- Phần cuối bài BẮT BUỘC phải có đầy đủ thông tin liên hệ: Hotline, Website và Địa chỉ (Address) của DR. SMILE.
- Viết sẵn sàng để người dùng COPY & PASTE lên Facebook.
- Có đầy đủ emoji và hashtag chuẩn SEO.
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
        return "Lỗi: Bạn cần cung cấp API KEY trong file .env"
        
    scraped_data = await crawl_facebook_posts(topic)
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
# GIAO DIỆN NGƯỜI DÙNG BẰNG GRADIO
# ==========================================
with gr.Blocks(title="Dr. Smile - AI Content Generator") as demo:
    gr.Markdown("# 🤖 Tự Động Tạo Content Viral & Hình Ảnh - DR. SMILE")
    gr.Markdown("Công cụ tự động tìm bài hot trên Facebook, viết bài Marketing và tự động sinh Prompt tạo ảnh cho Leonardo.ai.")
    
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
            lines=15,
            interactive=True
        )
        
    with gr.Row():
        generate_prompt_btn = gr.Button("2. Đã Chỉnh Sửa Xong? Bấm Để Tạo Lệnh Ảnh 🎨", variant="secondary")

    with gr.Row():
        img_prompt_output = gr.Textbox(
            label="2. Lệnh tạo ảnh Leonardo.ai (Bạn có thể Đọc & Chỉnh Sửa tự do tại đây trước khi copy)", 
            lines=10,
            interactive=True
        )
    
    # Bước 1: Tạo Post
    generate_post_btn.click(
        fn=generate_post_ui_action, 
        inputs=topic_input, 
        outputs=fb_output
    )
    
    # Bước 2: Tạo Prompt ảnh từ Post đã tạo (hoặc user đã sửa)
    generate_prompt_btn.click(
        fn=generate_prompt_ui_action,
        inputs=[topic_input, fb_output],
        outputs=img_prompt_output
    )

if __name__ == "__main__":
    print("[*] Đang khởi động giao diện người dùng (UI)...")
    
    # Render thường dùng cổng 10000, mặc định fallback về 7860
    port = int(os.environ.get("PORT", 10000))
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        inbrowser=False, 
        theme=gr.themes.Soft(primary_hue="blue")
    )
