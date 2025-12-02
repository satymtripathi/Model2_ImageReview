# ---------------- View All Images (Review from any point) ----------------
elif mode == "View All Images":
    st.header("🖼️ All Images — Review from Any Point")

    if len(images) == 0:
        st.info("No images found in the images/ folder.")
        st.stop()

    cols = st.columns(5)  # 5 images per row
    col_idx = 0

    for img in images:
        img_name = img.name

        with cols[col_idx]:
            st.image(str(img), caption=img_name, use_container_width=True)

            # Load previous review if exists
            prev_row = reviewed[reviewed["ImageName"] == img_name]
            if not prev_row.empty:
                prev_condition = prev_row.iloc[0]["Condition"]
                prev_note = prev_row.iloc[0]["DiagnosticNote"]
                prev_feedback = prev_row.iloc[0]["Feedback"]
            else:
                prev_condition = "Bacterial"
                prev_note = ""
                prev_feedback = ""

            with st.form(key=f"quick_review_{img_name}"):
                condition = st.radio(
                    "Condition:",
                    ["Bacterial", "Fungal", "Others", "Not Sure"],
                    horizontal=False,
                    index=["Bacterial", "Fungal", "Others", "Not Sure"].index(prev_condition)
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

                submit_btn = st.form_submit_button("Save", use_container_width=True)

                if submit_btn:
                    # Remove existing entry if any
                    reviewed = reviewed[reviewed["ImageName"] != img_name]

                    # Add updated review
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

                    # Update master file
                    all_files = list(DATA_FOLDER.glob("reviews_*.csv"))
                    merged = pd.concat(
                        [pd.read_csv(f) for f in all_files if f.name != "reviews_master.csv"],
                        ignore_index=True
                    )
                    merged.to_csv(MASTER_FILE, index=False)

                    st.success(f"Saved review for {img_name}")
                    st.rerun()

        col_idx += 1
        if col_idx == 5:
            cols = st.columns(5)
            col_idx = 0
