import json
import asyncio
from datetime import datetime
import streamlit as st
from google import genai
from google.genai import types
from telegram import Bot
from prompts import SYSTEM_PROMPT, SUMMARY_PROMPT, WELCOME_MESSAGE_TEMPLATE
MODEL_NAME = "gemini-3.5-flash"
st.set_page_config(
    page_title="Deadline Tracker",
    page_icon="📅",
    layout="centered",
)
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)
gemini_client = get_gemini_client()
def extract_deadlines(parts):
    """Send the uploaded syllabus/timetable/assignment sheet to Gemini."""
    try:
        response = gemini_client.models.generate_content(
            model=MODEL_NAME,
            contents=parts,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )
        return response.text
    except Exception as error:
        return json.dumps({
            "deadlines": [],
            "warnings": [f"Gemini error: {error}"]
        })

def parse_deadlines(raw_text):
    """Safely parse Gemini's JSON response."""
    try:
        data = json.loads(raw_text)
        if isinstance(data, dict) and isinstance(data.get("deadlines"), list):
            return data
    except json.JSONDecodeError:
        pass

    return {
        "deadlines": [],
        "warnings": [
            "The AI response could not be read as structured deadline data."
        ],
    }

def format_deadlines(deadlines):
    if not deadlines:
        return "No deadlines were confidently detected."

    lines = []
    for item in deadlines:
        title = item.get("title", "Untitled")
        date = item.get("date", "Date not found")
        time = item.get("time", "")
        course = item.get("course", "")
        confidence = item.get("confidence", "unknown")

        line = f"• {date}"
        if time:
            line += f" {time}"
        line += f" — {title}"
        if course:
            line += f" ({course})"
        line += f" [confidence: {confidence}]"
        lines.append(line)

    return "\n".join(lines)


def make_telegram_digest(deadlines, source_name):
    today = datetime.now().strftime("%d %b %Y")
    body = format_deadlines(deadlines)

    return (
        "📅 DEADLINE TRACKER\n\n"
        f"Source: {source_name}\n"
        f"Generated: {today}\n\n"
        "Upcoming / detected deadlines:\n"
        f"{body}\n\n"
        "⚠️ Please verify important dates against the original document."
    )


def send_telegram(chat_id, text):
    async def _send():
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=chat_id, text=text)

    try:
        asyncio.run(_send())
        return True, "Telegram message sent successfully."
    except Exception as error:
        return False, str(error)



if "onboarded" not in st.session_state:
    st.title("📅 Deadline Tracker")
    st.caption("Upload a syllabus, timetable, or assignment sheet and let AI find the deadlines.")

    with st.form("onboarding_form"):
        name = st.text_input("Your name", placeholder="Your name")
        chat_id = st.text_input(
            "Telegram Chat ID",
            placeholder="e.g. 123456789",
            help=(
                "First open your Telegram bot and send it any message. "
                "Then obtain your chat_id using Telegram's getUpdates API."
            ),
        )

        submitted = st.form_submit_button("Start Tracking 🚀")

        if submitted:
            if not name.strip() or not chat_id.strip():
                st.warning("Please enter both your name and Telegram Chat ID.")
            else:
                st.session_state.name = name.strip()
                st.session_state.chat_id = chat_id.strip()
                st.session_state.deadlines = []
                st.session_state.source_name = ""
                st.session_state.onboarded = True
                st.rerun()

    st.stop()



st.title("📅 Deadline Tracker")
st.caption(
    f"Logged in as {st.session_state.name} • Telegram reminders enabled"
)

uploaded = st.file_uploader(
    "Upload a syllabus, timetable, or assignment sheet",
    type=["jpg", "jpeg", "png", "pdf"],
    help="For the vision workflow, JPG/PNG images are recommended.",
)

if uploaded is not None:
    st.session_state.source_name = uploaded.name

    if uploaded.type.startswith("image/"):
        image_bytes = uploaded.getvalue()
        st.image(image_bytes, caption=uploaded.name, use_container_width=True)

        if st.button("🔎 Extract Deadlines", use_container_width=True):
            parts = [
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=uploaded.type,
                ),
                (
                    "Extract all deadlines, due dates, submission dates, "
                    "exam dates, and important scheduled dates from this image."
                ),
            ]

            with st.spinner("Reading the document and finding deadlines..."):
                raw = extract_deadlines(parts)
                result = parse_deadlines(raw)

            st.session_state.deadlines = result.get("deadlines", [])
            st.session_state.warnings = result.get("warnings", [])

    else:
        st.info(
            "PDF selected. For this project version, export the relevant page "
            "as JPG/PNG and upload the image so Gemini's vision workflow can read it."
        )

# Display results
if "deadlines" in st.session_state and st.session_state.deadlines:
    st.subheader("📋 Detected Deadlines")

    for item in st.session_state.deadlines:
        title = item.get("title", "Untitled")
        date = item.get("date", "Date not found")
        time = item.get("time", "")
        course = item.get("course", "")
        confidence = item.get("confidence", "unknown")

        with st.container(border=True):
            st.write(f"### {title}")
            st.write(f"**Date:** {date}")
            if time:
                st.write(f"**Time:** {time}")
            if course:
                st.write(f"**Course/Subject:** {course}")
            st.write(f"**Confidence:** {confidence}")

    if st.session_state.get("warnings"):
        for warning in st.session_state.warnings:
            st.warning(warning)

    st.divider()

    st.subheader("📲 Send Digest to Telegram")

    if st.button(
        "Send Upcoming Deadlines to Telegram",
        use_container_width=True,
    ):
        digest = make_telegram_digest(
            st.session_state.deadlines,
            st.session_state.get("source_name", "Uploaded document"),
        )

        with st.spinner("Sending your deadline digest..."):
            success, info = send_telegram(
                st.session_state.chat_id,
                digest,
            )

        if success:
            st.success("Sent! Check your Telegram bot. 📲")
        else:
            st.error(f"Couldn't send the Telegram message: {info}")

else:
    st.info(
        "Upload a document image and click **Extract Deadlines** to begin."
    )

st.divider()
st.caption(
    "AI-extracted dates should be checked against the original document before relying on them."
)
