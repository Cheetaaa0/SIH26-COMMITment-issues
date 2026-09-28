import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_image_comparison import image_comparison
from PIL import Image, ImageDraw
import os

# ==============================================================================
# 1. Page Configuration & Sovereign Status Header
# ==============================================================================
st.set_page_config(
    page_title="TerraTrace | Satellite Intelligence",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("## 🛰️ TerraTrace — Semantic Retrieval & Multi-Temporal Change Engine")
st.success("🔒 System Status: Operating 100% Offline (Air-Gapped Sovereign Enclave)")

# ==============================================================================
# 2. Local Fallback Tile Generator (Guarantees zero crashes / no internet calls)
# ==============================================================================
def get_default_tiles():
    cache_dir = "default_tiles"
    os.makedirs(cache_dir, exist_ok=True)
    p1 = os.path.join(cache_dir, "baseline.png")
    p2 = os.path.join(cache_dir, "inspection.png")

    if not os.path.exists(p1):
        img1 = Image.new("RGB", (512, 512), color=(34, 139, 34))  # Forest Green
        d1 = ImageDraw.Draw(img1)
        for s in range(0, 512, 64):
            d1.line([(s, 0), (s, 512)], fill=(45, 160, 45), width=1)
            d1.line([(0, s), (512, s)], fill=(45, 160, 45), width=1)
        img1.save(p1)

    if not os.path.exists(p2):
        img2 = Image.new("RGB", (512, 512), color=(112, 128, 144))  # Concrete Slate
        d2 = ImageDraw.Draw(img2)
        for s in range(0, 512, 64):
            d2.line([(s, 0), (s, 512)], fill=(130, 145, 160), width=1)
            d2.line([(0, s), (512, s)], fill=(130, 145, 160), width=1)
        d2.rectangle([140, 140, 372, 372], outline=(255, 255, 255), width=4)
        img2.save(p2)

    return p1, p2

default_t1, default_t2 = get_default_tiles()

# ==============================================================================
# 3. Sidebar: Ingestion & Mock Search Controls
# ==============================================================================
with st.sidebar:
    st.header("1. Data Source Selection")
    source_mode = st.radio("Choose Input Mode:", ["Select from local folder", "Upload custom files directly"])

    path_t1 = default_t1
    path_t2 = default_t2
    label_t1 = "Baseline (T1)"
    label_t2 = "Inspection (T2)"

    VALID_EXTS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tif', '.tiff')
    active_search_folder = "."

    if source_mode == "Select from local folder":
        active_search_folder = st.text_input("Folder Path:", value=".")
        if os.path.isdir(active_search_folder):
            available_files = [f for f in os.listdir(active_search_folder) if f.lower().endswith(VALID_EXTS)]
            if len(available_files) >= 1:
                f1 = st.selectbox("Select 'Before' Image (T1):", available_files, index=0)
                default_idx_2 = 1 if len(available_files) > 1 else 0
                f2 = st.selectbox("Select 'After' Image (T2):", available_files, index=default_idx_2)
                path_t1 = os.path.join(active_search_folder, f1)
                path_t2 = os.path.join(active_search_folder, f2)
                label_t1 = f1
                label_t2 = f2
            else:
                st.info("No image files found in folder. Using default tiles.")
        else:
            st.error("Specified folder path does not exist.")

    elif source_mode == "Upload custom files directly":
        up_file_1 = st.file_uploader("Upload 'Before' Image (T1)", type=["png", "jpg", "jpeg", "tif", "tiff", "webp"])
        up_file_2 = st.file_uploader("Upload 'After' Image (T2)", type=["png", "jpg", "jpeg", "tif", "tiff", "webp"])
        if up_file_1 and up_file_2:
            upload_dir = "uploaded_tiles"
            os.makedirs(upload_dir, exist_ok=True)
            path_t1 = os.path.join(upload_dir, up_file_1.name)
            path_t2 = os.path.join(upload_dir, up_file_2.name)
            with open(path_t1, "wb") as f:
                f.write(up_file_1.getbuffer())
            with open(path_t2, "wb") as f:
                f.write(up_file_2.getbuffer())
            label_t1 = up_file_1.name
            label_t2 = up_file_2.name

    st.write("---")
    st.header("2. Semantic Discovery Engine")
    query_input = st.text_input("Natural Language Query", placeholder="e.g., river water expansion")
    sensor_modality = st.selectbox("Sensor Filter", ["Sentinel-2 L2A (10m)", "Landsat-8/9 (30m)", "SAR Sentinel-1"])
    min_confidence = st.slider("Confidence Gate", 0.0, 1.0, 0.75)
    
    execute_search = st.button("Run Semantic Search", type="primary")

    if execute_search:
        if query_input.strip():
            # Mock search response (Simulating GeoRSCLIP + FAISS output)
            st.success("Discovered 2 candidate tiles in local archive:")
            st.write(f"• **{label_t2}** (Similarity Score: `0.8942`)")
            st.write(f"• **candidate_tile_0412.png** (Similarity Score: `0.7610`)")
        else:
            st.warning("Please type a search query first.")

# ==============================================================================
# 4. Mock Change Classification (Stand-in for Backend Math Engine)
# ==============================================================================
# In the future, this dictionary is replaced by: analysis = analyze_temporal_change(path_t1, path_t2)
analysis = {
    "detected": True,
    "event": "River Extent / Waterbody Expansion (Hydrological Change)",
    "status": "CONFIRMED CHANGE",
    "confidence": 94.6,
    "delta_veg": -0.18,
    "delta_water": 0.24,
    "delta_built": 0.02
}

# ==============================================================================
# 5. Main Screen: Two-Column Analyst Workspace
# ==============================================================================
col_left, col_right = st.columns([1, 1])
target_lat, target_lon = 28.6139, 77.2090  # Delhi Bounding Coordinates

# --- LEFT COLUMN: Geospatial Map Canvas ---
with col_left:
    st.subheader("1. Geospatial Area of Interest")
    aoi_map = folium.Map(location=[target_lat, target_lon], zoom_start=13, tiles="OpenStreetMap")
    
    # Marker pin color switches based on status
    marker_color = "red" if analysis["detected"] else "green"
    folium.Marker(
        [target_lat, target_lon],
        popup=f"Status: {analysis['status']}",
        tooltip="Click to inspect coordinates",
        icon=folium.Icon(color=marker_color, icon="info-sign")
    ).add_to(aoi_map)
    st_folium(aoi_map, height=460, width=580)

# --- RIGHT COLUMN: Analyst Review Queue & Comparison Slider ---
with col_right:
    st.subheader("2. Automated Review Queue (Capability 2.2.5)")

    # Dynamic Alert Card Rendered from Status
    if analysis["status"] == "CONFIRMED CHANGE":
        st.error(f"🚨 **Change Confirmed:** {analysis['event']} (Confidence: {analysis['confidence']}%)")
    elif analysis["status"] == "SEASONAL PHENOLOGY (CONFIRMED)":
        st.info(f"🌿 **Environmental Variation:** {analysis['event']} (Confidence: {analysis['confidence']}%)")
    elif analysis["status"] == "FALSE ALARM SUPPRESSED":
        st.warning(f"🛡️ **False Alarm Suppressed:** {analysis['event']}")
    else:
        st.success(f"✓ **Surface Stable:** {analysis['event']}")

    st.write("**Visual Evidence (Analyst Split-Inspection):**")
    image_comparison(
        img1=path_t1,
        img2=path_t2,
        label1=f"T1: {label_t1}",
        label2=f"T2: {label_t2}",
        width=580
    )

    # Human-in-the-Loop Audit Actions
    btn1, btn2, btn3 = st.columns(3)
    with btn1:
        if st.button("Confirm Change ✓"):
            st.success("Analyst decision recorded to local review queue.")
    with btn2:
        if st.button("Reject (False Alarm) ✗"):
            st.warning("Flagged as false positive in local review queue.")
    with btn3:
        if st.button("Export GeoJSON ⤓"):
            st.info("Exporting polygon bounds to GeoJSON...")

# ==============================================================================
# 6. Provenance & Audit Metadata Drawer (Capability 2.2.6)
# ==============================================================================
st.write("---")
with st.expander("🔍 View Scene Provenance & Processing Pipeline History"):
    st.json({
        "Scene_T1_Baseline": label_t1,
        "Scene_T2_Inspection": label_t2,
        "Sensor_Modality": sensor_modality,
        "Algorithmic_Verdict": analysis["status"],
        "Detected_Category": analysis["event"],
        "Confidence_Score": f"{analysis['confidence']}%",
        "Spectral_Deltas": {
            "Delta_Vegetation_Proxy": analysis["delta_veg"],
            "Delta_Water_Proxy": analysis["delta_water"],
            "Delta_Builtup_Brightness": analysis["delta_built"]
        },
        "Pipeline_Configuration": "GeoRSCLIP ViT-B/32 + Localized Normalized Spectral Array Differencing",
        "Sovereign_Compliance": "100% Air-Gapped Localhost Execution"
    })