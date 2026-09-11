import streamlit as st
import re
from datetime import date
from io import BytesIO
from docxtpl import DocxTemplate

st.set_page_config(page_title="Cover Sheet Generator", page_icon="📝", layout="centered")

# Collapsible guide at the top of the UI
with st.expander("▶️ Watch: How to Copy from Arbor & Generate a Cover Sheet", expanded=False):
    try:
        with open("Cover Form Filler inner.mp4", "rb") as video_file:
            video_bytes = video_file.read()
        st.video(video_bytes)
    except FileNotFoundError:
        st.info("Walkthrough video is currently unavailable.")
        
PERIOD_MAP = {
    "08:30": "am",
    "08:55": "p1",
    "09:55": "p2",
    "11:15": "p3",
    "12:15": "p4",
    "14:00": "p5",
    "15:00": "pm"
}

def parse_calendar_paste(text: str, only_cover_arranged: bool = False) -> dict:
    """
    Extracts room, subject, and group per period slot.
    - If only_cover_arranged is True, matches only lines with '[Cover Arranged]'.
    - If False, matches all lesson lines regardless of prefix.
    """
    data = {}
    for prefix in PERIOD_MAP.values():
        data[f"{prefix}_room"] = ""
        data[f"{prefix}_group"] = ""
        if prefix not in ("am", "pm"):
            data[f"{prefix}_subject"] = ""

    # Conditionally enforce or allow optional '[Cover Arranged]'
    cover_tag_pattern = r"\[Cover Arranged\]\s*" if only_cover_arranged else r"(?:\[Cover Arranged\]\s*)?"

    pattern = re.compile(
        r"(?P<start>\d{2}:\d{2})\s*[-–]\s*(?P<end>\d{2}:\d{2})\s*\|\s*Location:\s*(?P<room>[^\n\r]+)[\r\n]+"
        + cover_tag_pattern +
        r"(?P<subject>[^:\n\r]+):\s*(?P<year>[^:\n\r]+):\s*(?P<group>[^\n\r]+)"
    )

    for match in pattern.finditer(text):
        m = match.groupdict()
        start = m["start"]
        prefix = PERIOD_MAP.get(start)
        if prefix:
            data[f"{prefix}_room"] = m["room"].strip()
            data[f"{prefix}_group"] = m["group"].strip()
            if prefix not in ("am", "pm"):
                data[f"{prefix}_subject"] = m["subject"].strip()

    return data

# --- Streamlit UI ---
st.title("Cover Work Sheet Auto-Filler")

col1, col2 = st.columns(2)
with col1:
    teacher = st.text_input("Teacher Initials / Name", value="")
with col2:
    cover_date = st.date_input("Date", value=date.today())

# Checkbox toggle for filtering cover
only_cover = st.checkbox("Only include [Cover Arranged]", value=False)

raw_paste = st.text_area(
    "Paste Calendar Data Here (From Arbor DAY view)",
    height=240,
    placeholder="09:55 - 10:55 | Location: S8\nScience: Year 8: 8S/Sc2\n..."
)

if st.button("Generate Cover Sheet", type="primary"):
    if not raw_paste.strip():
        st.warning("Please paste some calendar text first.")
    else:
        context = parse_calendar_paste(raw_paste, only_cover_arranged=only_cover)
        context["teacher"] = teacher.strip()
        context["date"] = cover_date.strftime("%-d/%-m/%y")

        # Load and render template
        doc = DocxTemplate("Cover_Work_Sheet_Template.docx")
        doc.render(context)

        # Buffer for browser download
        output = BytesIO()
        doc.save(output)
        output.seek(0)

        filename = f"Cover Work Sheet {teacher} {cover_date.strftime('%d %b %Y')}.docx"
        st.success("Cover sheet generated successfully!")
        st.download_button(
            label="📥 Download Completed Proforma",
            data=output,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
