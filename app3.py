import streamlit as st
import pandas as pd
from pathlib import Path

# ------------------- CONFIG -------------------
st.set_page_config(page_title="Model 2 Image Review", layout="wide")

IMAGES_FOLDER = Path("images")
OUTPUT_CSV = "final_reviews.csv"

# ------------------- LOAD IMAGES -------------------
images = sorted([p for p in IMAGES_FOLDER.glob("*") if p.suffix.lower() in [".jpg", ".jpeg", ".png"]])

# Create CSV if not exists
if not Path(OUTPUT_CSV).exists():
    df_init = pd.DataFrame({"ImageName": [img.name for img in images],
                            "Review": [""] * len(images)})
    df_init.to_csv(OUTPUT_CSV, index=False)

df = pd.read_csv(OUTPUT_CSV)

# ------------------- SIDEBAR -------------------
st.sidebar.title("Navigation")
mode = st.sidebar.radio("Select Mode:", ["Review New", "Edit Reviews", "Download CSV", "View All Images"])

# ------------------- MODE: REVIEW NEW -------------------
if mode == "Review New":
    st.header("📝 Review New Images")

    pending = df[df["Review"] == ""]
    if len(pending) == 0:
        st.success("All images have been reviewed.")
        st.stop()

    row = pending.iloc[0]
    img_name = row["ImageName"]

    st.subheader(f"Reviewing: {img_name}")
    img_path = IMAGES_FOLDER / img_name

    st.image(str(img_path), use_container_width=True)

    review = st.radio("Select Review:", ["Infection", "Normal", "Not Sure"], horizontal=True)

    if st.button("Submit Review"):
        df.loc[df.ImageName == img_name, "Review"] = review
        df.to_csv(OUTPUT_CSV, index=False)
        st.success("Saved! Refresh or click Next to continue.")

# ------------------- MODE: EDIT REVIEWS -------------------
elif mode == "Edit Reviews":
    st.header("✏️ Edit Existing Reviews")

    for i, row in df.iterrows():
        with st.expander(row["ImageName"]):
            img_path = IMAGES_FOLDER / row["ImageName"]
            st.image(str(img_path), use_container_width=True)

            new_review = st.radio(
                "Update Review:",
                ["Infection", "Normal", "Not Sure"],
                index=["Infection", "Normal", "Not Sure"].index(row["Review"]),
                key=row["ImageName"]
            )
            df.loc[i, "Review"] = new_review

    if st.button("Save All Changes"):
        df.to_csv(OUTPUT_CSV, index=False)
        st.success("All changes saved!")

# ------------------- MODE: DOWNLOAD CSV -------------------
elif mode == "Download CSV":
    st.header("📥 Download Final CSV")

    st.dataframe(df)

    st.download_button(
        label="Download CSV",
        data=df.to_csv(index=False),
        file_name="final_reviews.csv",
        mime="text/csv"
    )

# ------------------- MODE: VIEW ALL IMAGES (NO ZOOM) -------------------
elif mode == "View All Images":
    st.header("🖼️ All Images Preview")

    if len(images) == 0:
        st.info("No images found in the images/ folder.")
        st.stop()

    cols = st.columns(5)  # 5 images per row
    col_idx = 0

    for img in images:
        with cols[col_idx]:
            try:
                st.image(str(img), caption=img.name, use_container_width=True)
            except Exception as e:
                st.error(f"Error loading {img.name}: {e}")

        col_idx += 1
        if col_idx == 5:
            cols = st.columns(5)
            col_idx = 0
