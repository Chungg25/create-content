# SYSTEM ARCHITECTURE DOCUMENT: DR. SMILE AUTO-CONTENT AGENT

## 1. SYSTEM GOALS
The **Auto-Content Agent** system is designed to 100% automate the Marketing content production process for Dr. Smile Dental Clinic.
Instead of operating each step manually, the system acts as a **24/7 Content Marketing Specialist**, capable of:
1. **Market Research:** Automatically searching for Viral/Hot trending posts on social networks.
2. **Content Creation:** Writing SEO-standard posts, adhering to the brand's tone of voice, and seamlessly integrating Dr. Smile's services and pricing.
3. **Image Direction:** Automatically conceptualizing and generating high-quality Image Prompts for the Design team (via Leonardo.ai).
4. **Automated Operations:** Scheduling publications and running continuously in the background in real-time without human intervention.

---

## 2. AGENT ARCHITECTURE

The system is composed of 4 main modules that work closely together:

### 2.1. Data Collection Module (Crawler Module)
- **Technologies:** `crawl4ai` (Playwright) and Google Search.
- **Mission:** Upon receiving a Topic, the Crawler acts as a researcher, automatically browsing the web to collect the top 5 most Viral Facebook posts about that topic.
- **Fail-safe Mechanism:** If blocked by Google IP bans or Captcha requests (common when running on a Server), the Crawler will send a signal to the AI. The AI will then automatically switch to "Knowledge-based Writing" mode to prevent system crashes.

### 2.2. Artificial Intelligence Module (The Brain - LLM Llama 3)
- **Technologies:** Llama-3 (powered by Groq's ultra-fast API).
- **Prompt Engineering Mechanism (Brain Control):**
  - **Brand Context:** The AI is pre-loaded with comprehensive documentation regarding Dr. Smile's Price list, Warranty policies, and Technological advantages (`doc/DrSmile.md`).
  - **Topic Intent Analysis:** The AI autonomously identifies whether the topic is for *Knowledge Sharing* (Strictly no sales, no pricing mentioned) or *Service Comparison/Sales* (Mandatory scanning of the price list to quote the lowest price for lead generation).
  - **Image Prompting:** The AI comprehends the newly written post to extract an accurate English prompt for Leonardo.ai, mandatorily including a requirement for 3D Typography text if the post mentions a specific price.

### 2.3. Database & Scheduling Module (Database & Scheduler)
- **Technologies:** Google Sheets API (`gspread`) and `apscheduler`.
- **Mission:** 
  - Utilizing Google Sheets as a central dashboard (CMS) to help managers and staff visually track the status of each post (Pending ➡️ Generating ➡️ Completed ➡️ Error).
  - The Scheduler runs in the background 24/7, triggering the AI to work at the exact scheduled minute specified by the user.

### 2.4. Human Interaction Module (Human-in-the-loop UI)
- **Technologies:** `Gradio`.
- **Mission:** Creating an intuitive internal web administration portal. It allows staff to intervene in the middle of the AI's process (e.g., editing the AI-generated content manually and requesting the AI to re-read the edited post to regenerate the corresponding Image Prompt).

---

## 3. ACTUAL WORKFLOW

1. **Input:** Staff enters a Topic (e.g., *Implant Dentistry*) and a Scheduled Time (e.g., *28/06/2026 21:00*).
2. **Database:** The task is pushed to Google Sheets with a `Pending` status.
3. **Trigger:** At exactly 21:00, the Background Worker automatically activates.
4. **Execution:**
   - The Crawler scrapes the top 5 Viral posts regarding Implants.
   - LLM Llama 3 reads the 5 Viral posts + Reads Dr. Smile's price list ➡️ Writes a complete Facebook Post (including the lowest quoted price).
   - LLM Llama 3 re-reads the Facebook Post ➡️ Writes a Leonardo Image Prompt (Requesting 3D text for the price).
5. **Output:** Saves the post and image prompt back to Google Sheets, updating the status to `Completed`.

---

## 4. UPGRADE VISION: STYLE LEARNING MECHANISM

To ensure the Agent not only writes well but also writes **"exactly to the Boss's taste"**, the system has a pre-defined roadmap to upgrade with a **Style Reference Mechanism** in the upcoming phase.

### Future Operational Mechanism:
1. **Style Storage File (`doc/style_reference.md`):**
   - Whenever staff reads an AI-generated post and feels dissatisfied, they can manually edit the writing style (adding/removing emojis, changing pronouns, altering headline styles) via the web's History tab.
   - When the user clicks "Save", the system will not only save the post to Google Sheets but also implicitly extract the exact phrasing changes to log into `style_reference.md` (acting as the AI's learning notebook).
2. **RAG (Retrieval-Augmented Generation) - Style Absorption:**
   - During subsequent generation tasks, before writing, the LLM is mandated to read this `style_reference.md` file first.
   - The LLM will autonomously analyze: *"Ah, yesterday the Boss changed 'Extremely cheap cost' to 'Worthy investment', and preferred using the 🌟 emoji instead of 🔥"*.
   - Consequently, the LLM will automatically adjust its Tone of Voice so that generated posts increasingly resemble the company's in-house Copywriter. The longer it is used and corrected, the smarter and more "in sync" the AI will become with your specific preferences!
