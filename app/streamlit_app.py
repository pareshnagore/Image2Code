import streamlit as st
st.set_page_config(
    page_title="Image2Code",
    layout="wide"
)
import os
import uuid
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from core.pipeline import CodeExtractionPipeline
from streamlit_sortables import sort_items

# ------------------------------------
# CONFIG
# ------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
OUTPUT_DIR = STORAGE_DIR / "outputs"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

st.markdown("""
<style>
div[data-testid="column"] {
    padding: 5px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------
# GLOBAL RESTART (NEW)
# ------------------------------------

if st.sidebar.button("🔁 Restart Session"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# ------------------------------------
# SESSION STATE INIT
# ------------------------------------

if "stage" not in st.session_state:
    st.session_state.stage = "UPLOAD"

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "saved_paths" not in st.session_state:
    st.session_state.saved_paths = []

if "auto_blocks" not in st.session_state:
    st.session_state.auto_blocks = None

if "ordered_filenames" not in st.session_state:
    st.session_state.ordered_filenames = None

if "result" not in st.session_state:
    st.session_state.result = None

# ------------------------------------
# TITLE
# ------------------------------------

st.title("Image2Code")

# ------------------------------------
# STAGE 1: UPLOAD
# ------------------------------------

if st.session_state.stage == "UPLOAD":
    st.header("Upload Code Images and Get Code Files")
    uploaded_files = st.file_uploader(
        "Upload one or more images for single code reconstruction",
        accept_multiple_files=True,
        type=["png", "jpg", "jpeg", "webp"],
    )
    if not uploaded_files:
        st.info("General guidelines for best results:\n"
        "- First thing first, click as much as crisp photos. Blury images may give suboptimal outputs (garbage in, garbage out lol)\n"
        "- Enable line number visibility in your IDE (vscode, cursor, notepad++, etc). It helps ordering and validation.\n"
        "- Include tab name or file name in image, so that AI can can output original filename as it is \n"
        "- Make sure no lines are missed across images. i.e. image 1 ends at 50 and image 2 starts at 60, then those 10 lines are gone. Overlap is fine, in fact little overlap is good to have. It helps ordering and validation.\n"
        "- Try to click the images sequencially from top to bottom. Image timestamps is one of the fallback logic.\n"
        "- If possible, click photos in light theme. Contrast detection and OCR is better. Dark theme may work but results may be suboptimal.\n")
    if uploaded_files:
        session_upload_dir = UPLOAD_DIR / st.session_state.session_id
        session_upload_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = []
        for file in uploaded_files:
            save_path = session_upload_dir / file.name
            with open(save_path, "wb") as f:
                f.write(file.read())
            saved_paths.append(str(save_path))

        st.session_state.saved_paths = saved_paths
        st.success(f"{len(saved_paths)} images uploaded.")

        if st.button("Read Image Contents"):
            try:
                pipeline = CodeExtractionPipeline(debug=False)
                # 🔥 STATUS PANEL ADDED
                with st.status("Processing images...", expanded=True) as status:
                    status.update(label="Feeding images to AI...", state="running")
                    blocks = pipeline.extract_blocks(st.session_state.saved_paths)

                    status.update(label="Extracting structure & metadata...", state="running")
                    ordered_blocks = pipeline.order_blocks(blocks)

                    status.update(label="Finalizing order...", state="running")
                    status.update(label="Ordering complete!", state="complete")

                # blocks = pipeline.extract_blocks(st.session_state.saved_paths)
                # ordered_blocks = pipeline.order_blocks(blocks)
                st.session_state.auto_blocks = ordered_blocks
                st.session_state.ordered_filenames = [
                    os.path.basename(block.image_path)
                    for block in ordered_blocks
                ]
                st.session_state.stage = "ORDER_REVIEW"
                st.rerun()
            except Exception as e:
                st.error(f"Error during ordering: {e}")

# ------------------------------------
# STAGE 2: ORDER REVIEW
# ------------------------------------

elif st.session_state.stage == "ORDER_REVIEW":
    st.header("Review & Adjust Order of Images")
    st.subheader("Drag image names (not thumbnail) to reorder images if needed, then confirm to reconstruct code")

    reordered = sort_items(
        st.session_state.ordered_filenames or [],
        direction="horizontal",
    )
    st.session_state.ordered_filenames = reordered
    st.markdown("---")

    st.subheader("Preview (Current Order)")

    cols = st.columns(max(1,len(st.session_state.ordered_filenames)))

    for col, filename in zip(cols, st.session_state.ordered_filenames):
        block = next(
            (b for b in st.session_state.auto_blocks or [] if os.path.basename(b.image_path) == filename),
            None
        )

        with col:
            if block:
                st.image(block.image_path, width=300)
                st.caption(f"📄 {filename}")
                st.caption(f"Lang: {block.language}")
                if block.start_line and block.end_line:
                    st.caption(f"Lines: {block.start_line}-{block.end_line}")

    if st.button("Confirm & Reconstruct"):
        try:
            # Map filename -> block
            block_map = {
                os.path.basename(block.image_path): block
                for block in st.session_state.auto_blocks or []
            }
            final_blocks = [
                block_map[name]
                for name in st.session_state.ordered_filenames
            ]
            pipeline = CodeExtractionPipeline(debug=False)
            result = pipeline.reconstruct(final_blocks)
            st.session_state.result = result
            st.session_state.stage = "RECONSTRUCTED"
            st.rerun()

        except Exception as e:
            st.error(f"Reconstruction error: {e}")

# ------------------------------------
# STAGE 3: OUTPUT
# ------------------------------------

elif st.session_state.stage == "RECONSTRUCTED":
    st.header("Reconstruction Complete")
    result = st.session_state.result
    st.subheader("Preview")
    if result["format"] == "ipynb":
        import json
        st.json(result["content"])
    else:
        st.code(result["content"])

    # Save output file
    session_output_dir = OUTPUT_DIR / st.session_state.session_id
    session_output_dir.mkdir(parents=True, exist_ok=True)

    filename = result["filename"] or f"reconstructed.{result['format']}"
    output_path = session_output_dir / filename

    if result["format"] == "ipynb":
        import json
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result["content"], f, indent=2)
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result["content"])

    with open(output_path, "rb") as f:
        st.download_button(
            label="Download File",
            data=f,
            file_name=filename,
        )

    st.markdown("---")
    if st.button("Start New Session"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()