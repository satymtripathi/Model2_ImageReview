import streamlit as st
import pandas as pd
from pathlib import Path

# -------------------- CONFIG --------------------
DATA_FOLDER = Path("reviews")
IMAGES_FOLDER = Path("images")
IMAGES_FOLDER.mkdir(exist_ok=True)
DATA_FOLDER.mkdir(exist_ok=True)

# Dropdown of reviewers
reviewer = st.sidebar.selectbox("Select Reviewer", ["Reviewer1", "Reviewer2", "Reviewer3"])
REVIEWER_FILE = DATA_FOLDER / f"reviews_{reviewer}.csv"

# If reviewer file doesn't exist, create it
if not REVIEWER_FILE.exists():
    pd.DataFrame(columns=["Reviewer", "ImageName", "Condition", "DiagnosticNote", "Feedback"]).to_csv(REVIEWER_FILE, index=False)

reviewed = pd.read_csv(REVIEWER_FILE)

# Sidebar menu (Option B)
menu = st.sidebar.radio(
    "Navigation",
    ["Review New", "View All Images (Review Anytime)", "Edit Reviews", "Download CSV"]
)


images = list(IMAGES_FOLDER.glob("*.*"))
images = [img for img in images if img.suffix.lower() in [".jpg", ".jpeg", ".png"]]


# ============================================================
#                   MODE 1 : REVIEW NEW
# ============================================================
if menu == "Review New":
    st.header("📝 Review New Images")

    reviewed_names = set(reviewed["ImageName"])
    pending = [img for img in images if img.name not in reviewed_names]

    if len(pending) == 0:
        st.success("🎉 All images reviewed!")
        st.stop()

    img = pending[0]
    st.image(str(img), caption=img.name, use_container_width=True)

    with st.form("review_form"):
        condition = st.radio("Condition:", ["Bacterial", "Fungal", "Others", "Not Sure"])
        diagnostic = st.text_area("Diagnostic Note:", "")
        feedback = st.text_area("Feedback:", "")
        submit = st.form_submit_button("Save Review")

        if submit:
            new_entry = {
                "Reviewer": reviewer,
                "ImageName": img.name,
                "Condition": condition,
                "DiagnosticNote": diagnostic.strip(),
                "Feedback": feedback.strip()
            }

            reviewed = pd.concat([reviewed, pd.DataFrame([new_entry])], ignore_index=True)
            reviewed.to_csv(REVIEWER_FILE, index=False)

            st.success("Saved!")
            st.rerun()


# ============================================================
#           MODE 2 : VIEW ALL IMAGES (REVIEW ANYTIME)
# ============================================================
elif menu == "View All Images (Review Anytime)":
    st.header("🖼️ View All Images — Review Anytime")

    if len(images) == 0:
        st.info("No images found.")
        st.stop()

    cols = st.columns(5)
    col_idx = 0

    for img in images:
        img_name = img.name

        # Fetch previous review if exists
        prev_row = reviewed[reviewed["ImageName"] == img_name]
        if not prev_row.empty:
            prev_condition = prev_row.iloc[0]["Condition"]
            prev_note = prev_row.iloc[0]["DiagnosticNote"]
            prev_feedback = prev_row.iloc[0]["Feedback"]
        else:
            prev_condition = "Bacterial"
            prev_note = ""
            prev_feedback = ""

        with cols[col_idx]:
            st.image(str(img), caption=img_name, use_container_width=True)

            with st.form(key=f"form_{img_name}"):
                condition = st.radio(
                    "Condition:",
                    ["Bacterial", "Fungal", "Others", "Not Sure"],
                    index=["Bacterial", "Fungal", "Others", "Not Sure"].index(prev_condition)
                )

                diagnostic = st.text_area("Diagnostic Note:", prev_note, height=60)
                feedback = st.text_area("Feedback:", prev_feedback, height=60)

                save_btn = st.form_submit_button("Save", use_container_width=True)

                if save_btn:
                    reviewed = reviewed[reviewed["ImageName"] != img_name]

                    new_entry = {
                        "Reviewer": reviewer,
                        "ImageName": img_name,
                        "Condition": condition,
                        "DiagnosticNote": diagnostic.strip(),
                        "Feedback": feedback.strip()
                    }

                    reviewed = pd.concat([reviewed, pd.DataFrame([new_entry])], ignore_index=True)
                    reviewed.to_csv(REVIEWER_FILE, index=False)

                    st.success(f"Saved review for {img_name}")
                    st.rerun()

        col_idx += 1
        if col_idx == 5:
            cols = st.columns(5)
            col_idx = 0


# ============================================================
#                   MODE 3 : EDIT REVIEWS  
# ============================================================
elif menu == "Edit Reviews":
    st.header("✏️ Edit Existing Reviews")

    if len(reviewed) == 0:
        st.info("No reviews yet.")
        st.stop()

    img_list = reviewed["ImageName"].tolist()
    img_name = st.selectbox("Select Image to Edit", img_list)

    row = reviewed[reviewed["ImageName"] == img_name].iloc[0]

    st.image(str(IMAGES_FOLDER / img_name), caption=img_name, use_container_width=True)

    with st.form("edit_form"):
        condition = st.radio(
            "Condition:",
            ["Bacterial", "Fungal", "Others", "Not Sure"],
            index=["Bacterial", "Fungal", "Others", "Not Sure"].index(row["Condition"])
        )
        diagnostic = st.text_area("Diagnostic Note:", row["DiagnosticNote"])
        feedback = st.text_area("Feedback:", row["Feedback"])

        update_btn = st.form_submit_button("Update")

        if update_btn:
            reviewed = reviewed[reviewed["ImageName"] != img_name]

            updated = {
                "Reviewer": reviewer,
                "ImageName": img_name,
                "Condition": condition,
                "DiagnosticNote": diagnostic.strip(),
                "Feedback": feedback.strip()
            }

            reviewed = pd.concat([reviewed, pd.DataFrame([updated])], ignore_index=True)
            reviewed.to_csv(REVIEWER_FILE, index=False)

            st.success("Updated successfully!")
            st.rerun()


# ============================================================
#               MODE 4 : DOWNLOAD CSV  
# ============================================================
elif menu == "Download CSV":
    st.header("⬇️ Download Your Reviews")
    st.download_button(
        "Download CSV",
        data=reviewed.to_csv(index=False),
        file_name=f"{reviewer}_reviews.csv",
        mime="text/csv"
    )
