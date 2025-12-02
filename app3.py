import streamlit as st
import pandas as pd
from pathlib import Path
from PIL import Image
import time

# ---------------- CONFIG ----------------
IMAGE_FOLDER = Path("images")
DATA_FOLDER = Path("data")
DATA_FOLDER.mkdir(exist_ok=True)

MASTER_FILE = DATA_FOLDER / "reviews_master.csv"

st.set_page_config(page_title="🦠 Corneal Bacterial vs Fungal Review System", layout="wide")

# ---------------- HEADER ----------------
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.title("🦠 Corneal Bacterial vs Fungal Review System")
with col2:
    st.image("https://cdn-icons-png.flaticon.com/512/3843/3843492.png", width=80)

# ---------------- Reviewer ----------------
reviewer = st.text_input("👩‍⚕️ Enter your name or ID:")
if not reviewer:
    st.warning("Please enter your name or ID to begin.")
    st.stop()

REVIEWER_FILE = DATA_FOLDER / f"reviews_{reviewer}.csv"

# ---------------- Load Images ----------------
images = sorted([p for p in IMAGE_FOLDER.glob("*") if p.suffix.lower() in [".jpg", ".jpeg", ".png"]])
image_names = [p.name for p in images]

# ---------------- Load Previous Reviews Safely (Reviewer file) ----------------
if REVIEWER_FILE.exists():
    try:
        reviewed = pd.read_csv(REVIEWER_FILE)
        # Ensure required columns exist
        expected_cols = ["Reviewer", "ImageName", "Condition", "DiagnosticNote", "Feedback"]
        if not set(expected_cols).issubset(set(reviewed.columns)):
            reviewed = pd.DataFrame(columns=expected_cols)
    except Exception as e:
        st.warning(f"⚠️ Could not read your previous file. Starting fresh.\n\nError: {e}")
        reviewed = pd.DataFrame(columns=["Reviewer", "ImageName", "Condition", "DiagnosticNote", "Feedback"])
else:
    reviewed = pd.DataFrame(columns=["Reviewer", "ImageName", "Condition", "DiagnosticNote", "Feedback"])

# ---------------- Filter Bad Entries ----------------
# If reviewer file has image names that no longer exist, drop them and save
if not reviewed.empty:
    missing_files = [img for img in reviewed["ImageName"].tolist() if img not in image_names]
    if missing_files:
        st.warning("⚠️ These reviewed images do NOT exist in your images/ folder (removed from your reviewer file):")
        st.code("\n".join(missing_files))
        reviewed = reviewed[~reviewed["ImageName"].isin(missing_files)]
        reviewed.to_csv(REVIEWER_FILE, index=False)

# Prepare remaining images for sequential review
remaining_images = [img for img in images if img.name not in reviewed["ImageName"].tolist()]
total_images = len(images)
completed = len(reviewed)
remaining = len(remaining_images)

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("🔍 Quick Actions")
    mode = st.radio(
        "Mode:",
        [
            "Review New",
            "View All Images (Review Anytime)",
            "Edit Reviews",
            "Download CSV"
        ],
        index=0
    )
    st.markdown("---")
    st.write(f"👩‍⚕️ **Reviewer:** `{reviewer}`")
    st.progress(completed / total_images if total_images > 0 else 0)
    st.caption(f"✅ Completed: {completed} / {total_images}")
    st.caption(f"🕒 Remaining: {remaining}")

# ---------------- Helper: update master ----------------
def update_master_file():
    """
    Merge all reviews_*.csv (except the master file) and write MASTER_FILE.
    """
    all_files = list(DATA_FOLDER.glob("reviews_*.csv"))
    # If no reviewer files exist, remove master if exists
    if not all_files:
        if MASTER_FILE.exists():
            MASTER_FILE.unlink()
        return
    dfs = []
    for f in all_files:
        if f.name == MASTER_FILE.name:
            continue
        try:
            dfs.append(pd.read_csv(f))
        except:
            # skip corrupted files
            continue
    if dfs:
        merged = pd.concat(dfs, ignore_index=True)
        merged.to_csv(MASTER_FILE, index=False)

# ---------------- MODE: REVIEW NEW ----------------
if mode == "Review New":
    if not remaining_images:
        st.success("🎉 All images reviewed! You can switch to *Edit Reviews* or *Download CSV*.")
        st.stop()

    current_image = remaining_images[0]

    c1, c2 = st.columns([0.55, 0.45])

    with c1:
        try:
            st.image(Image.open(current_image), caption=current_image.name, use_container_width=True)
        except Exception as e:
            st.error(f"❌ Cannot open image: {current_image.name}\n{e}")
            st.stop()

        st.markdown(f"**Progress:** {completed + 1} / {total_images}")

    with c2:
        with st.form(key=f"review_form_{current_image.name}", clear_on_submit=False):
            st.markdown(f"### 🖼️ Reviewing: `{current_image.name}`")

            condition = st.radio(
                "Select Condition:", 
                ["Bacterial", "Fungal", "Others", "Not Sure"],
                horizontal=True,
                index=0
            )

            margin_note = st.text_area(
                "Diagnostic Notes (if any):", 
                value="", 
                placeholder="Example: 'Satellite lesions — suggests Fungal.'",
                height=60
            )

            feedback = st.text_area(
                "Feedback (optional):", 
                value="", 
                placeholder="Example: 'Image slightly blurred.'", 
                height=60
            )

            submit = st.form_submit_button("✅ Submit Review", use_container_width=True)

            if submit:
                # Remove existing entry for this image (if any)
                reviewed = reviewed[reviewed["ImageName"] != current_image.name]

                new_data = {
                    "Reviewer": reviewer,
                    "ImageName": current_image.name,
                    "Condition": condition,
                    "DiagnosticNote": margin_note.strip(),
                    "Feedback": feedback.strip()
                }

                df_new = pd.DataFrame([new_data])
                # Append to reviewer file
                df_new.to_csv(REVIEWER_FILE, mode='a', header=not REVIEWER_FILE.exists(), index=False)
                # Also append to master
                df_new.to_csv(MASTER_FILE, mode='a', header=not MASTER_FILE.exists(), index=False)

                # Update in-memory reviewed dataframe and remaining_images
                reviewed = pd.concat([reviewed, df_new], ignore_index=True)
                remaining_images = [img for img in images if img.name not in reviewed["ImageName"].tolist()]

                st.success(f"✅ Review for `{current_image.name}` saved!")
                time.sleep(1.2)
                st.experimental_rerun()

# ---------------- MODE: VIEW ALL IMAGES (Review from any point) ----------------
elif mode == "View All Images (Review Anytime)":
    st.header("🖼️ All Images — Review from Any Point")

    if len(images) == 0:
        st.info("No images found in your images/ folder.")
        st.stop()

    cols = st.columns(5)  # 5 images per row
    col_idx = 0

    # We'll keep a flag to know if anything changed during this page render.
    any_saved = False

    for img in images:
        img_name = img.name

        with cols[col_idx]:
            try:
                st.image(str(img), caption=img_name, use_container_width=True)
            except Exception as e:
                st.error(f"Error loading {img_name}: {e}")
                continue

            # Load previous review values if present
            prev_row = reviewed[reviewed["ImageName"] == img_name]
            if not prev_row.empty:
                prev_condition = prev_row.iloc[0].get("Condition", "Bacterial")
                prev_note = prev_row.iloc[0].get("DiagnosticNote", "")
                prev_feedback = prev_row.iloc[0].get("Feedback", "")
            else:
                prev_condition = "Bacterial"
                prev_note = ""
                prev_feedback = ""

            # Unique form per-image
            with st.form(key=f"quick_review_{img_name}", clear_on_submit=False):
                condition = st.radio(
                    "Condition:",
                    ["Bacterial", "Fungal", "Others", "Not Sure"],
                    index=["Bacterial", "Fungal", "Others", "Not Sure"].index(prev_condition),
                    horizontal=False
                )

                diagnostic = st.text_area(
                    "Diagnostic Note:",
                    value=prev_note,
                    height=60
                )

                feedback = st.text_area(
                    "Feedback:",
                    value=prev_feedback,
                    height=60
                )

                save_btn = st.form_submit_button("Save", use_container_width=True)

                if save_btn:
                    # remove previous entry for this image (if any)
                    reviewed = reviewed[reviewed["ImageName"] != img_name]

                    new_entry = {
                        "Reviewer": reviewer,
                        "ImageName": img_name,
                        "Condition": condition,
                        "DiagnosticNote": diagnostic.strip(),
                        "Feedback": feedback.strip()
                    }

                    reviewed = pd.concat([reviewed, pd.DataFrame([new_entry])], ignore_index=True)
                    # Save reviewer file
                    reviewed.to_csv(REVIEWER_FILE, index=False)

                    # Rebuild master from all reviewer files
                    update_master_file()

                    st.success(f"Saved review for {img_name}")
                    any_saved = True
                    # short sleep to give user feedback then rerun to refresh forms
                    time.sleep(0.6)
                    st.rerun()

        col_idx += 1
        if col_idx == 5:
            cols = st.columns(5)
            col_idx = 0

    if not any_saved:
        st.info("Tip: You can review any image directly here. Click 'Save' under any image to store the review for that image.")

# ---------------- MODE: EDIT REVIEWS ----------------
elif mode == "Edit Reviews":
    st.header("✏️ Edit Existing Reviews")

    if reviewed.empty:
        st.info("No reviews found yet. Please review some images first.")
        st.stop()

    c1, c2 = st.columns([0.4, 0.6])

    with c1:
        selected_image = st.selectbox("Select image:", reviewed["ImageName"].tolist())
        img_path = IMAGE_FOLDER / selected_image

        if img_path.exists():
            try:
                st.image(Image.open(img_path), caption=selected_image, use_container_width=True)
            except Exception as e:
                st.error(f"Cannot open image: {e}")
        else:
            st.error(f"❌ Image not found: {selected_image}")
            st.stop()

    with c2:
        prev = reviewed[reviewed["ImageName"] == selected_image].iloc[0]

        with st.form(key=f"edit_form_{selected_image}", clear_on_submit=False):
            st.markdown(f"### ✏️ Edit Review for `{selected_image}`")

            condition = st.radio(
                "Condition:",
                ["Bacterial", "Fungal", "Others", "Not Sure"],
                horizontal=True,
                index=["Bacterial", "Fungal", "Others", "Not Sure"].index(prev.get("Condition", "Bacterial"))
            )

            margin_note = st.text_area(
                "Diagnostic Notes:",
                value=prev.get("DiagnosticNote", ""),
                height=60
            )

            feedback = st.text_area(
                "Feedback / comments:",
                value=prev.get("Feedback", ""),
                height=60
            )

            update = st.form_submit_button("💾 Update Review", use_container_width=True)

            if update:
                idx = reviewed[reviewed["ImageName"] == selected_image].index[0]
                reviewed.loc[idx, ["Condition", "DiagnosticNote", "Feedback"]] = [
                    condition, margin_note.strip(), feedback.strip()
                ]
                reviewed.to_csv(REVIEWER_FILE, index=False)

                # Rebuild master
                update_master_file()

                st.success(f"✅ Updated review for `{selected_image}`!")
                time.sleep(0.8)
                st.experimental_rerun()

# ---------------- MODE: DOWNLOAD CSV ----------------
elif mode == "Download CSV":
    st.header("📥 Download Final CSV")

    # If master exists show it; else show reviewer file for that reviewer
    if MASTER_FILE.exists():
        df_display = pd.read_csv(MASTER_FILE)
        st.markdown("**Master file (all reviewers)**")
    else:
        df_display = reviewed.copy()
        st.markdown("**Your reviewer file (master not available yet)**")

    st.dataframe(df_display, height=400, use_container_width=True)

    csv_data = df_display.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download CSV",
        csv_data,
        file_name=f"reviews_{reviewer}.csv",
        mime="text/csv",
        use_container_width=True
    )
