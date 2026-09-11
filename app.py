import streamlit as st
import re
from datetime import date
from io import BytesIO
from docxtpl import DocxTemplate

st.set_page_config(page_title="Cover Sheet Generator", page_icon="📝", layout="centered")

# Map calendar start times to template variable prefixes
PERIOD_MAP = {
    "08:30": "am",
    "08:55": "p1",
    "09:55": "p2",
    "11:15": "p3",
    "12:15": "p4",
    "14:00": "p5",
    "15:00": "pm"
}

def parse_calendar_paste(text: str) -> dict:
    """Extracts room, subject, and group per period slot."""
    # Pattern handles standard time windows, location lines, and cover lines
    pattern = re.compile(
        r"(?P<start>\d{2}:\d{2})\s*[-–]\s*(?P<end>\d{2}:\d{2})\s*\|\s*Location:\s*(?P<room>[^\n]+)\n"
        r"\[Cover Arranged\]\s*(?P<subject>[^:]+):\s*(?P<year>[^:]+):\s*(?P<group>[^\n]+)"
    )
    
    # Initialize all slots to empty strings so unused tags resolve to blank
    data = {}
    for prefix in PERIOD_MAP.values():
        data[f"{prefix}_room"] = ""
        data[f"{prefix}_group"] = ""
        if prefix not in ("am", "pm"):
            data[f"{prefix}_subject"] = ""

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

# Streamlit UI
st.title("Cover Work Sheet Auto-Filler")

col1, col2 = st.columns(2)
with col1:
    teacher = st.text_input("Teacher Initials / Name", value="SH")
with col2:
    cover_date = st.date_input("Date", value=date.today())

raw_paste = st.text_area(
    "Paste Calendar Data Here",
    height=220,
    placeholder="09:55 - 10:55 | Location: S8\n[Cover Arranged] Science: Year 8: 8S/Sc2\n..."
)

if st.button("Generate Cover Sheet", type="primary"):
    if not raw_paste.strip():
        st.warning("Please paste some calendar text first.")
    else:
        # Build rendering dictionary
        context = parse_calendar_paste(raw_paste)
        context["teacher"] = teacher.strip()
        context["date"] = cover_date.strftime("%-d/%-m/%y")

        # Render docx template
        doc = DocxTemplate("Cover_Work_Sheet_Template.docx")
        doc.render(context)

        # Output to memory buffer for browser download
        output = BytesIO()
        doc.save(output)
        output.seek(0)

        filename = f"Cover Work Sheet {teacher} {cover_date.strftime('%d %b %Y')}.docx"
        st.success("Cover sheet populated successfully!")
        st.download_button(
            label="📥 Download Completed Proforma",
            data=output,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
