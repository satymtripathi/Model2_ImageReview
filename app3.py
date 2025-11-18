import streamlit as st
import pandas as pd
from pathlib import Path
from PIL import Image
import time

# ---------------- CONFIG ----------------
IMAGE_FOLDER = Path("images")
DATA_FOLDER = Path("data")
MASTER_FILE = DATA_FOLDER / "reviews_master.csv"
DATA_FOLDER.mkdir(exist_ok=True)

st.set_page_config(page_title="🩺 Corneal Image Review", layout="wide")

# ---------------- HEADER ----------------
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.title("🩺 Corneal Image Review System")
with col2:
    st.image("https://cdn-icons-png.flaticon.com/512/3843/3843492.png", width=80)

# ---------------- Reviewer ----------------
reviewer = st.text_input("👩‍⚕️ Enter your name or ID:")
if not reviewer:
    st.warning("Please enter your name or ID to begin.")
    st.stop()

# Reviewer-specific file
REVIEWER_FILE = DATA_FOLDER / f"reviews_{reviewer}.csv"

# ---------------- Load Images ----------------
images = list(IMAGE_FOLDER.glob("*.*"))
images.sort()

# ---------------- Load Previous Reviews Safely ----------------
if REVIEWER_FILE.exists():
    try:
        reviewed = pd.read_csv(REVIEWER_FILE)
        if reviewed.empty or "ImageName" not in reviewed.columns:
            reviewed = pd.DataFrame(columns=["Reviewer", "ImageName", "Condition", "MarginOfErrorNote", "Feedback"])
    except Exception as e:
        st.warning(f"⚠️ Could not read your previous file. Starting fresh.\n\nError: {e}")
        reviewed = pd.DataFrame(columns=["Reviewer", "ImageName", "Condition", "MarginOfErrorNote", "Feedback"])
else:
    reviewed = pd.DataFrame(columns=["Reviewer", "ImageName", "Condition", "MarginOfErrorNote", "Feedback"])

reviewed_images = reviewed["ImageName"].tolist()
remaining_images = [img for img in images if img.name not in reviewed_images]
total_images = len(images)
completed = len(reviewed_images)
remaining = len(remaining_images)

# ---------------- Sidebar Compact ----------------
with st.sidebar:
    st.header("🔍 Quick Actions")
    mode = st.radio("Mode:", ["Review New", "Edit Reviews", "Download CSV"], horizontal=False)
    st.markdown("---")
    st.write(f"👩‍⚕️ **Reviewer:** `{reviewer}`")
    st.progress(completed / total_images if total_images > 0 else 0)
    st.caption(f"✅ Completed: {completed} / {total_images}")
    st.caption(f"🕒 Remaining: {remaining}")

# ---------------- Review New Images ----------------
if mode == "Review New":
    if not remaining_images:
        st.success("🎉 All images reviewed! You can switch to *Edit Reviews* or *Download CSV*.")
        st.stop()

    current_image = remaining_images[0]

    c1, c2 = st.columns([0.55, 0.45])
    with c1:
        st.image(Image.open(current_image), caption=current_image.name, use_container_width=True)
        st.markdown(f"**Progress:** {completed + 1} / {total_images}")
    with c2:
        with st.form(key=f"review_form_{current_image.name}", border=True):
            st.markdown(f"### 🖼️ Reviewing: `{current_image.name}`")
            
            # Condition resets to "Normal" each time
            condition = st.radio(
                "Select Condition:", 
                ["Normal", "Scar", "Edema", "Infection", "Others", "Not Sure"],
                horizontal=True,
                index=0,
                key=f"condition_{current_image.name}"
            )

            # Notes and Feedback reset to blank for each new image
            margin_note = st.text_area(
                "Notes (if any):", 
                value="", 
                placeholder="Example: 'Scar with mild edema – acceptable if labeled as Edema or Scar.'",
                height=60,
                key=f"note_{current_image.name}"
            )

            feedback = st.text_area(
                "Feedback (optional):", 
                value="", 
                placeholder="Example: 'Slightly blurred – visibility reduced.'", 
                height=60,
                key=f"feedback_{current_image.name}"
            )

            submit = st.form_submit_button("✅ Submit Review", use_container_width=True)

            if submit:
                new_data = {
                    "Reviewer": reviewer,
                    "ImageName": current_image.name,
                    "Condition": condition,
                    "MarginOfErrorNote": margin_note.strip() if margin_note else "",
                    "Feedback": feedback.strip() if feedback else ""
                }

                df_new = pd.DataFrame([new_data])
                df_new.to_csv(REVIEWER_FILE, mode='a', header=not REVIEWER_FILE.exists(), index=False)
                df_new.to_csv(MASTER_FILE, mode='a', header=not MASTER_FILE.exists(), index=False)

                st.success(f"✅ Review for `{current_image.name}` saved!")
                st.toast("Saved successfully — loading next image...", icon="✅")
                time.sleep(2)
                st.rerun()

# ---------------- Edit Previous Reviews ----------------
elif mode == "Edit Reviews":
    if reviewed.empty:
        st.info("No reviews found yet. Please review some images first.")
        st.stop()

    c1, c2 = st.columns([0.4, 0.6])
    with c1:
        selected_image = st.selectbox("Select image:", reviewed["ImageName"].tolist())
        st.image(Image.open(IMAGE_FOLDER / selected_image), caption=selected_image, use_container_width=True)
    with c2:
        prev = reviewed[reviewed["ImageName"] == selected_image].iloc[0]
        with st.form(key=f"edit_form_{selected_image}", border=True):
            st.markdown(f"### ✏️ Edit Review for `{selected_image}`")
            condition = st.radio(
                "Condition:",
                ["Normal", "Scar", "Edema", "Infection", "Others", "Not Sure"],
                horizontal=True,
                index=["Normal", "Scar", "Edema", "Infection", "Others", "Not Sure"].index(prev["Condition"]),
                key=f"edit_condition_{selected_image}"
            )
            margin_note = st.text_area("Margin of error / clinical note:", value=prev.get("MarginOfErrorNote", ""), height=60, key=f"edit_note_{selected_image}")
            feedback = st.text_area("Feedback / comments:", value=prev.get("Feedback", ""), height=60, key=f"edit_feedback_{selected_image}")
            update = st.form_submit_button("💾 Update Review", use_container_width=True)

            if update:
                idx = reviewed[reviewed["ImageName"] == selected_image].index[0]
                reviewed.loc[idx, ["Condition", "MarginOfErrorNote", "Feedback"]] = [
                    condition, margin_note.strip(), feedback.strip()
                ]
                reviewed.to_csv(REVIEWER_FILE, index=False)

                all_files = list(DATA_FOLDER.glob("reviews_*.csv"))
                merged = pd.concat(
                    [pd.read_csv(f) for f in all_files if f.name != "reviews_master.csv"],
                    ignore_index=True
                )
                merged.to_csv(MASTER_FILE, index=False)
                st.success(f"✅ Updated review for `{selected_image}`!")
                st.toast("Review updated — refreshing...", icon="🔄")
                time.sleep(2)
                st.rerun()

# ---------------- Download CSV ----------------
else:
    if not REVIEWER_FILE.exists():
        st.info("No reviews available yet.")
        st.stop()

    c1, c2 = st.columns([0.6, 0.4])
    with c1:
        st.markdown("### 📥 My Review Summary")
        df = pd.read_csv(REVIEWER_FILE)
        st.dataframe(df, height=300, use_container_width=True)
    with c2:
        st.markdown("### ⬇️ Download")
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download My Reviews (CSV)", csv_data, f"{reviewer}_reviews.csv", "text/csv", use_container_width=True)
        st.success("✅ You can share this file with the project lead.")
