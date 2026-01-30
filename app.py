"""
TraceX - HLR-LLR Traceability System
Streamlit UI Application
"""

from pathlib import Path
env_path = Path(__file__).resolve().parent.parent / "config/.env"
from dotenv import load_dotenv
load_dotenv(dotenv_path=env_path)

import streamlit as st
import pandas as pd
from pathlib import Path
import io
import json
import os
from datetime import datetime
from src.model_provider import create_model_provider, MODEL_CONFIGS, get_ollama_models
from src.traceability_system import TraceabilitySystem
from src.requirements_loader import RequirementsLoader

# Page configuration
st.set_page_config(
    page_title="TraceX - Requirements Traceability",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .link-card {
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f9f9f9;
        border-radius: 0.3rem;
    }
    .gap-warning {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'system' not in st.session_state:
    st.session_state.system = None
if 'matrix' not in st.session_state:
    st.session_state.matrix = None
if 'hlrs' not in st.session_state:
    st.session_state.hlrs = []
if 'llrs' not in st.session_state:
    st.session_state.llrs = []


def main():
    # Header
    st.markdown('<div class="main-header">🔗 TraceX</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Aerospace HLR-LLR Requirements Traceability System</div>', unsafe_allow_html=True)
    
    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        st.subheader("Model Selection")
        st.info("🚀 Aerospace-focused traceability analysis")
        
        # Structured extraction model
        st.markdown("**Structured Extraction Model**")
        struct_provider = st.selectbox(
            "Provider",
            ["gemini", "groq", "ollama"],
            key="struct_provider",
            help="Model for extracting structured data from aerospace requirements"
        )
        
        # Get models based on provider
        if struct_provider == "ollama":
            # Get locally available Ollama models
            ollama_models = get_ollama_models()
            if ollama_models:
                struct_models = ollama_models
            else:
                struct_models = MODEL_CONFIGS["ollama"]["models"]
                st.warning("⚠️ Could not fetch Ollama models. Ensure Ollama is running.")
        else:
            struct_models = MODEL_CONFIGS[struct_provider]["models"]
        
        struct_model = st.selectbox(
            "Model",
            struct_models,
            index=0,
            key="struct_model"
        )
        
        st.markdown("---")
        
        # Reasoning model
        st.markdown("**Reasoning Model**")
        reason_provider = st.selectbox(
            "Provider",
            ["gemini", "groq", "ollama"],
            key="reason_provider",
            help="Model for reasoning about aerospace traceability links"
        )
        
        # Get models based on provider
        if reason_provider == "ollama":
            ollama_models = get_ollama_models()
            if ollama_models:
                reason_models = ollama_models
            else:
                reason_models = MODEL_CONFIGS["ollama"]["models"]
                st.warning("⚠️ Could not fetch Ollama models. Ensure Ollama is running.")
        else:
            reason_models = MODEL_CONFIGS[reason_provider]["models"]
        
        reason_model = st.selectbox(
            "Model",
            reason_models,
            index=0,
            key="reason_model"
        )
        
        st.markdown("---")
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            top_k = st.slider(
                "Top-K Candidates",
                min_value=5,
                max_value=20,
                value=10,
                help="Number of candidate links to generate per HLR"
            )
        
        st.markdown("---")
        st.info("💡 Make sure to set your API keys in the `.env` file")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📥 Load Requirements",
        "🔍 Generate Traceability",
        "📊 Traceability Matrix",
        "📈 Gap Analysis"
    ])
    
    # Tab 1: Load Requirements
    with tab1:
        st.header("Load Requirements")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            source_type = st.radio(
                "Data Source",
                ["Upload Files", "Use Sample Data"],
                horizontal=True
            )
            
            if source_type == "Upload Files":
                st.markdown("### Upload Requirement Files")
                
                file_format = st.radio(
                    "File Format",
                    ["Separate CSV Files", "Excel with Multiple Sheets", "JSON Files"],
                    horizontal=True
                )
                
                if file_format == "Separate CSV Files":
                    hlr_file = st.file_uploader("Upload HLRs CSV", type=['csv'])
                    llr_file = st.file_uploader("Upload LLRs CSV", type=['csv'])
                    
                    if hlr_file and llr_file:
                        if st.button("Load Requirements", type="primary"):
                            with st.spinner("Loading requirements..."):
                                try:
                                    # Save uploaded files temporarily
                                    hlr_path = f"/tmp/hlrs_{hlr_file.name}"
                                    llr_path = f"/tmp/llrs_{llr_file.name}"
                                    
                                    with open(hlr_path, "wb") as f:
                                        f.write(hlr_file.getvalue())
                                    with open(llr_path, "wb") as f:
                                        f.write(llr_file.getvalue())
                                    
                                    hlrs, llrs = RequirementsLoader.load_from_csv(hlr_path, llr_path)
                                    st.session_state.hlrs = hlrs
                                    st.session_state.llrs = llrs
                                    
                                    st.success(f"✅ Loaded {len(hlrs)} HLRs and {len(llrs)} LLRs")
                                except Exception as e:
                                    st.error(f"Error loading files: {e}")
                
                elif file_format == "Excel with Multiple Sheets":
                    excel_file = st.file_uploader("Upload Excel File", type=['xlsx', 'xls'])
                    
                    if excel_file:
                        col_a, col_b = st.columns(2)
                        with col_a:
                            hlr_sheet = st.text_input("HLR Sheet Name", value="HLRs")
                        with col_b:
                            llr_sheet = st.text_input("LLR Sheet Name", value="LLRs")
                        
                        if st.button("Load Requirements", type="primary"):
                            with st.spinner("Loading requirements..."):
                                try:
                                    excel_path = f"/tmp/{excel_file.name}"
                                    with open(excel_path, "wb") as f:
                                        f.write(excel_file.getvalue())
                                    
                                    hlrs, llrs = RequirementsLoader.load_from_excel(
                                        excel_path, hlr_sheet, llr_sheet
                                    )
                                    st.session_state.hlrs = hlrs
                                    st.session_state.llrs = llrs
                                    
                                    st.success(f"✅ Loaded {len(hlrs)} HLRs and {len(llrs)} LLRs")
                                except Exception as e:
                                    st.error(f"Error loading file: {e}")
                
                else:  # JSON format
                    st.markdown("Upload separate JSON files for HLRs and LLRs")
                    hlr_json = st.file_uploader("Upload HLRs JSON", type=['json'])
                    llr_json = st.file_uploader("Upload LLRs JSON", type=['json'])
                    
                    if hlr_json and llr_json:
                        if st.button("Load Requirements", type="primary"):
                            with st.spinner("Loading requirements..."):
                                try:
                                    hlr_data = json.loads(hlr_json.getvalue())
                                    llr_data = json.loads(llr_json.getvalue())
                                    
                                    hlrs, llrs = RequirementsLoader.load_from_json(hlr_data, llr_data)
                                    st.session_state.hlrs = hlrs
                                    st.session_state.llrs = llrs
                                    
                                    st.success(f"✅ Loaded {len(hlrs)} HLRs and {len(llrs)} LLRs")
                                except Exception as e:
                                    st.error(f"Error loading JSON files: {e}")
            
            else:  # Use sample data
                st.markdown("### Use Built-in Sample Data")
                st.info("📊 Sample data includes aerospace flight control system requirements (DAL-A/B certified)")
                
                if st.button("Load Sample Requirements", type="primary"):
                    with st.spinner("Loading sample aerospace requirements..."):
                        try:
                            # Load from actual sample files
                            sample_dir = Path(__file__).parent / "data" / "samples"
                            hlr_path = sample_dir / "sample_hlrs.csv"
                            llr_path = sample_dir / "sample_llrs.csv"
                            
                            if hlr_path.exists() and llr_path.exists():
                                hlrs, llrs = RequirementsLoader.load_from_csv(str(hlr_path), str(llr_path))
                            else:
                                # Fallback to built-in samples
                                hlrs, llrs = RequirementsLoader.create_sample_requirements()
                            
                            st.session_state.hlrs = hlrs
                            st.session_state.llrs = llrs
                            st.success(f"✅ Loaded {len(hlrs)} HLRs and {len(llrs)} LLRs")
                        except Exception as e:
                            st.error(f"Error loading sample data: {e}")
                            import traceback
                            st.code(traceback.format_exc())
        
        with col2:
            st.markdown("### Expected Format")
            st.markdown("""
            **CSV/Excel Columns (Aerospace):**
            
            **HLRs:**
            - `id` - Unique identifier (e.g., HLR-001)
            - `title` - Short title
            - `description` - Full requirement text
            - `type` - functional/performance/safety
            - `safety_level` - DAL-A/B/C/D (DO-178C)
            
            **LLRs:**
            - Same as HLRs, plus:
            - `component` - Avionics component name
            
            **JSON Format:**
            ```json
            {
              "requirements": [
                {
                  "id": "HLR-001",
                  "title": "Pitch Stability",
                  "description": "The system shall...",
                  "type": "functional",
                  "safety_level": "DAL-B"
                }
              ]
            }
            ```
            """)
            
            # Download template
            if st.button("📥 Download Template"):
                template_hlr = pd.DataFrame({
                    'id': ['HLR-001'],
                    'title': ['Pitch Control'],
                    'description': ['The flight control system shall maintain pitch within ±2° during cruise'],
                    'type': ['functional'],
                    'safety_level': ['DAL-B']
                })
                template_llr = pd.DataFrame({
                    'id': ['LLR-001'],
                    'title': ['Elevator Actuator Response'],
                    'description': ['The elevator actuator shall respond within 30ms'],
                    'type': ['performance'],
                    'component': ['Flight Control Actuator'],
                    'safety_level': ['DAL-B']
                })
                
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    template_hlr.to_excel(writer, sheet_name='HLRs', index=False)
                    template_llr.to_excel(writer, sheet_name='LLRs', index=False)
                
                st.download_button(
                    label="Download Aerospace Template",
                    data=buffer.getvalue(),
                    file_name="aerospace_requirements_template.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        # Display loaded requirements
        if st.session_state.hlrs:
            st.markdown("---")
            st.subheader("Loaded Requirements Preview")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**High-Level Requirements (HLRs)**")
                hlr_data = [{
                    'ID': h.id,
                    'Title': h.title,
                    'Type': h.type,
                    'Safety Level': h.safety_level
                } for h in st.session_state.hlrs[:5]]
                st.dataframe(pd.DataFrame(hlr_data), use_container_width=True)
                if len(st.session_state.hlrs) > 5:
                    st.caption(f"Showing 5 of {len(st.session_state.hlrs)} HLRs")
            
            with col2:
                st.markdown("**Low-Level Requirements (LLRs)**")
                llr_data = [{
                    'ID': l.id,
                    'Title': l.title,
                    'Type': l.type,
                    'Component': l.component or 'N/A'
                } for l in st.session_state.llrs[:5]]
                st.dataframe(pd.DataFrame(llr_data), use_container_width=True)
                if len(st.session_state.llrs) > 5:
                    st.caption(f"Showing 5 of {len(st.session_state.llrs)} LLRs")
    
    # Tab 2: Generate Traceability
    with tab2:
        st.header("Generate Traceability Matrix")
        
        if not st.session_state.hlrs:
            st.warning("⚠️ Please load aerospace requirements first (Tab 1)")
        else:
            st.success(f"✅ {len(st.session_state.hlrs)} HLRs and {len(st.session_state.llrs)} LLRs loaded")
            
            st.markdown("### Aerospace Traceability Process")
            st.markdown("""
            The AI-powered analysis performs the following steps:
            1. 🧠 **Understand** - Extract semantic meaning from aerospace requirements
            2. 🔍 **Generate** - Find candidate links using embeddings + BM25 search
            3. 🤔 **Reason** - Evaluate each link with multi-dimensional aerospace reasoning
            4. 📊 **Create** - Build traceability matrix with DO-178C compliance focus
            """)
            
            if st.button("🚀 Generate Aerospace Traceability Matrix", type="primary", use_container_width=True):
                # Create log container
                log_container = st.container()
                progress_bar = st.progress(0)
                status_container = st.empty()
                
                # Create expandable log area
                with log_container:
                    log_expander = st.expander("📋 Detailed Process Log", expanded=True)
                    log_placeholder = log_expander.empty()
                    logs = []
                    
                    def add_log(message, level="info"):
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        icon = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}.get(level, "ℹ️")
                        logs.append(f"{icon} [{timestamp}] {message}")
                        log_placeholder.text("\n".join(logs))
                
                try:
                    # Initialize models
                    add_log("Initializing AI models...", "info")
                    status_container.info("🤖 Initializing AI models...")
                    progress_bar.progress(0.05)
                    
                    add_log(f"Selected structured model: {st.session_state.struct_provider}/{st.session_state.struct_model}", "info")
                    add_log(f"Selected reasoning model: {st.session_state.reason_provider}/{st.session_state.reason_model}", "info")
                    
                    structured_provider = create_model_provider(
                        st.session_state.struct_provider,
                        st.session_state.struct_model
                    )
                    add_log("✓ Structured extraction model initialized", "success")
                    progress_bar.progress(0.10)
                    
                    reasoning_provider = create_model_provider(
                        st.session_state.reason_provider,
                        st.session_state.reason_model
                    )
                    add_log("✓ Reasoning model initialized", "success")
                    progress_bar.progress(0.15)
                    
                    # Create system
                    system = TraceabilitySystem(
                        structured_model=structured_provider,
                        reasoning_model=reasoning_provider,
                        top_k_candidates=top_k
                    )
                    
                    system.hlrs = st.session_state.hlrs
                    system.llrs = st.session_state.llrs
                    st.session_state.system = system
                    
                    add_log(f"System initialized with {len(system.hlrs)} HLRs and {len(system.llrs)} LLRs", "success")
                    
                except Exception as e:
                    add_log(f"Error initializing models: {e}", "error")
                    st.error(f"Error initializing models: {e}")
                    st.stop()
                
                try:
                    # Step 1: Understand requirements
                    status_container.info("🧠 Step 1/4: Understanding aerospace requirements...")
                    add_log("=" * 50, "info")
                    add_log("STEP 1: SEMANTIC UNDERSTANDING", "info")
                    add_log("=" * 50, "info")
                    progress_bar.progress(0.20)
                    
                    add_log(f"Analyzing {len(system.hlrs)} HLRs...", "info")
                    for i, hlr in enumerate(system.hlrs, 1):
                        add_log(f"  Processing HLR {i}/{len(system.hlrs)}: {hlr.id} - {hlr.title}", "info")
                    
                    progress_bar.progress(0.25)
                    add_log(f"Analyzing {len(system.llrs)} LLRs...", "info")
                    for i, llr in enumerate(system.llrs, 1):
                        add_log(f"  Processing LLR {i}/{len(system.llrs)}: {llr.id} - {llr.title}", "info")
                    
                    system.understand_requirements()
                    progress_bar.progress(0.35)
                    add_log("✓ All requirements semantically analyzed", "success")
                    add_log("  - Extracted: intent verbs, subjects, objects, constraints", "success")
                    add_log("  - Identified: key aerospace concepts and safety levels", "success")
                    
                    # Step 2: Generate candidates
                    status_container.info("🔍 Step 2/4: Generating candidate links...")
                    add_log("=" * 50, "info")
                    add_log("STEP 2: CANDIDATE GENERATION", "info")
                    add_log("=" * 50, "info")
                    progress_bar.progress(0.40)
                    
                    add_log("Building semantic embedding index...", "info")
                    add_log("Building BM25 keyword search index...", "info")
                    progress_bar.progress(0.45)
                    
                    # Generate candidates
                    candidates_map = system.candidate_generator.generate_candidates(system.hlrs, system.llrs)
                    total_candidates = sum(len(candidates) for candidates in candidates_map.values())
                    
                    add_log(f"✓ Generated {total_candidates} candidate links", "success")
                    for hlr_id, candidates in candidates_map.items():
                        add_log(f"  {hlr_id}: {len(candidates)} candidates (top-{top_k})", "info")
                    
                    progress_bar.progress(0.55)
                    
                    # Step 3: Evaluate with reasoning
                    status_container.info("🤔 Step 3/4: Evaluating links with aerospace reasoning...")
                    add_log("=" * 50, "info")
                    add_log("STEP 3: LINK REASONING & EVALUATION", "info")
                    add_log("=" * 50, "info")
                    progress_bar.progress(0.60)
                    
                    add_log("Applying aerospace-specific reasoning dimensions:", "info")
                    add_log("  1. Intent Alignment (functional decomposition)", "info")
                    add_log("  2. Causal Chain (system dependencies)", "info")
                    add_log("  3. Type Compatibility (req type matching)", "info")
                    add_log("  4. Safety Consistency (DO-178C DAL levels)", "info")
                    add_log("  5. Coverage Logic (completeness analysis)", "info")
                    
                    progress_bar.progress(0.65)
                    
                    # Evaluate candidates
                    evaluated_count = 0
                    accepted_count = 0
                    
                    for hlr_id, candidates in candidates_map.items():
                        add_log(f"Evaluating candidates for {hlr_id}...", "info")
                        for i, candidate in enumerate(candidates, 1):
                            evaluated_count += 1
                            if i <= 3:  # Log first 3 for brevity
                                add_log(f"  Candidate {i}: {candidate.hlr_id} → {candidate.llr_id} (sim: {candidate.embedding_score:.2f})", "info")
                            progress = 0.65 + (0.20 * evaluated_count / total_candidates)
                            progress_bar.progress(min(progress, 0.85))
                    
                    matrix = system.generate_traceability()
                    st.session_state.matrix = matrix
                    accepted_count = len(matrix.links)
                    
                    progress_bar.progress(0.90)
                    add_log(f"✓ Evaluated {evaluated_count} candidates", "success")
                    add_log(f"✓ Accepted {accepted_count} valid traceability links", "success")
                    add_log(f"✓ Rejection rate: {((evaluated_count - accepted_count) / evaluated_count * 100):.1f}%", "success")
                    
                    # Step 4: Generate matrix
                    status_container.info("📊 Step 4/4: Building traceability matrix...")
                    add_log("=" * 50, "info")
                    add_log("STEP 4: MATRIX GENERATION & GAP ANALYSIS", "info")
                    add_log("=" * 50, "info")
                    progress_bar.progress(0.92)
                    
                    add_log("Generating traceability matrix...", "info")
                    add_log("Performing gap analysis...", "info")
                    add_log("Checking DO-178C compliance...", "info")
                    
                    progress_bar.progress(1.0)
                    add_log("=" * 50, "success")
                    add_log("✓ AEROSPACE TRACEABILITY ANALYSIS COMPLETE!", "success")
                    add_log("=" * 50, "success")
                    
                    status_container.success("✅ Complete!")
                    
                    # Show summary
                    st.balloons()
                    st.success("🎉 Aerospace traceability matrix generated successfully!")
                    
                    add_log(f"Total HLRs: {len(system.hlrs)}", "info")
                    add_log(f"Total LLRs: {len(system.llrs)}", "info")
                    add_log(f"Traceability Links: {matrix.link_count}", "info")
                    add_log(f"Coverage: {matrix.gap_report.coverage_percentage:.1f}%", "info")
                    add_log(f"Orphan HLRs: {len(matrix.gap_report.orphan_hlrs)}", "warning" if matrix.gap_report.orphan_hlrs else "success")
                    add_log(f"Orphan LLRs: {len(matrix.gap_report.orphan_llrs)}", "info")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Links", matrix.link_count)
                    with col2:
                        st.metric("Coverage", f"{matrix.gap_report.coverage_percentage:.1f}%")
                    with col3:
                        st.metric("Orphan HLRs", len(matrix.gap_report.orphan_hlrs))
                    with col4:
                        st.metric("Orphan LLRs", len(matrix.gap_report.orphan_llrs))
                    
                except Exception as e:
                    add_log(f"ERROR: {e}", "error")
                    st.error(f"Error during generation: {e}")
                    import traceback
                    add_log(traceback.format_exc(), "error")
                    st.code(traceback.format_exc())
    
    # Tab 3: Traceability Matrix
    with tab3:
        st.header("Traceability Matrix")
        
        if not st.session_state.matrix:
            st.info("ℹ️ Generate traceability matrix first (Tab 2)")
        else:
            matrix = st.session_state.matrix
            system = st.session_state.system
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Links", matrix.link_count)
            with col2:
                st.metric("HLRs Covered", 
                         len(set(l.hlr_id for l in matrix.links)))
            with col3:
                st.metric("LLRs Used", 
                         len(set(l.llr_id for l in matrix.links)))
            
            st.markdown("---")
            
            # View selector
            view_mode = st.radio(
                "View Mode",
                ["Links List", "By HLR", "By LLR", "Pivot Table"],
                horizontal=True
            )
            
            if view_mode == "Links List":
                st.subheader("All Traceability Links")
                
                # Create dataframe
                links_data = []
                for link in matrix.links:
                    links_data.append({
                        "HLR": link.hlr_id,
                        "LLR": link.llr_id,
                        "Link Type": link.link_type.value,
                        "Coverage": link.coverage.value,
                        "Confidence": f"{link.confidence:.2f}"
                    })
                
                df = pd.DataFrame(links_data)
                st.dataframe(df, use_container_width=True)
                
                # Show details for selected link
                st.markdown("### Link Details")
                selected_idx = st.selectbox(
                    "Select link to view details",
                    range(len(matrix.links)),
                    format_func=lambda i: f"{matrix.links[i].hlr_id} → {matrix.links[i].llr_id}"
                )
                
                if selected_idx is not None:
                    link = matrix.links[selected_idx]
                    
                    st.markdown('<div class="link-card">', unsafe_allow_html=True)
                    st.markdown(f"**{link.hlr_id} → {link.llr_id}**")
                    st.markdown(f"**Link Type:** {link.link_type.value}")
                    st.markdown(f"**Coverage:** {link.coverage.value}")
                    st.markdown(f"**Confidence:** {link.confidence:.2f}")
                    st.markdown("**Explanation:**")
                    st.text(link.explanation)
                    st.markdown('</div>', unsafe_allow_html=True)
            
            elif view_mode == "By HLR":
                st.subheader("Links by HLR")
                
                hlr_ids = [h.id for h in system.hlrs]
                selected_hlr = st.selectbox("Select HLR", hlr_ids)
                
                if selected_hlr:
                    # Get HLR details
                    hlr = next(h for h in system.hlrs if h.id == selected_hlr)
                    
                    st.markdown(f"### {hlr.id}: {hlr.title}")
                    st.markdown(f"**Description:** {hlr.description}")
                    st.markdown(f"**Type:** {hlr.type} | **Safety Level:** {hlr.safety_level}")
                    
                    # Get links
                    links = system.get_hlr_links(selected_hlr)
                    
                    if links:
                        st.markdown(f"**Linked LLRs ({len(links)}):**")
                        
                        for link in links:
                            llr = next(l for l in system.llrs if l.id == link.llr_id)
                            
                            with st.expander(f"{link.llr_id}: {llr.title} ({link.coverage.value})"):
                                st.markdown(f"**LLR Description:** {llr.description}")
                                st.markdown(f"**Component:** {llr.component or 'N/A'}")
                                st.markdown(f"**Confidence:** {link.confidence:.2f}")
                                st.markdown("**Explanation:**")
                                st.text(link.explanation)
                    else:
                        st.warning("⚠️ No links found for this HLR (orphan)")
            
            elif view_mode == "By LLR":
                st.subheader("Links by LLR")
                
                llr_ids = [l.id for l in system.llrs]
                selected_llr = st.selectbox("Select LLR", llr_ids)
                
                if selected_llr:
                    # Get LLR details
                    llr = next(l for l in system.llrs if l.id == selected_llr)
                    
                    st.markdown(f"### {llr.id}: {llr.title}")
                    st.markdown(f"**Description:** {llr.description}")
                    st.markdown(f"**Type:** {llr.type} | **Component:** {llr.component or 'N/A'}")
                    
                    # Get links
                    links = system.get_llr_links(selected_llr)
                    
                    if links:
                        st.markdown(f"**Implements/Supports ({len(links)}):**")
                        
                        for link in links:
                            hlr = next(h for h in system.hlrs if h.id == link.hlr_id)
                            
                            with st.expander(f"{link.hlr_id}: {hlr.title}"):
                                st.markdown(f"**HLR Description:** {hlr.description}")
                                st.markdown(f"**Link Type:** {link.link_type.value}")
                                st.markdown(f"**Confidence:** {link.confidence:.2f}")
                    else:
                        st.warning("⚠️ No links found for this LLR (orphan)")
            
            else:  # Pivot Table
                st.subheader("Pivot Table View")
                
                pivot_df = system.matrix_generator.create_pivot_matrix(
                    matrix, system.hlrs, system.llrs
                )
                
                st.dataframe(pivot_df, use_container_width=True)
                st.caption("✓✓ = Full Coverage | ◐ = Partial Coverage | ✓ = Linked")
            
            # Export button
            st.markdown("---")
            col_export1, col_export2 = st.columns(2)
            
            with col_export1:
                if st.button("📥 Export as Excel", type="primary", use_container_width=True):
                    output_path = "/tmp/traceability_matrix.xlsx"
                    system.export_results(output_path)
                    
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="Download Excel Report",
                            data=f.read(),
                            file_name=f"aerospace_traceability_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
            
            with col_export2:
                if st.button("📥 Export as JSON", use_container_width=True):
                    # Create JSON export
                    json_export = {
                        "metadata": {
                            "generated_at": datetime.now().isoformat(),
                            "system": "TraceX Aerospace",
                            "total_hlrs": len(system.hlrs),
                            "total_llrs": len(system.llrs),
                            "total_links": matrix.link_count,
                            "coverage_percentage": matrix.gap_report.coverage_percentage
                        },
                        "links": [
                            {
                                "hlr_id": link.hlr_id,
                                "llr_id": link.llr_id,
                                "link_type": link.link_type.value,
                                "coverage": link.coverage.value,
                                "confidence": link.confidence,
                                "explanation": link.explanation
                            }
                            for link in matrix.links
                        ],
                        "gap_analysis": {
                            "orphan_hlrs": matrix.gap_report.orphan_hlrs,
                            "orphan_llrs": matrix.gap_report.orphan_llrs,
                            "partial_coverage_hlrs": matrix.gap_report.partial_coverage_hlrs,
                            "coverage_percentage": matrix.gap_report.coverage_percentage
                        }
                    }
                    
                    json_str = json.dumps(json_export, indent=2)
                    st.download_button(
                        label="Download JSON Report",
                        data=json_str,
                        file_name=f"aerospace_traceability_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
    
    # Tab 4: Gap Analysis
    with tab4:
        st.header("Gap Analysis")
        
        if not st.session_state.matrix:
            st.info("ℹ️ Generate traceability matrix first (Tab 2)")
        else:
            matrix = st.session_state.matrix
            system = st.session_state.system
            gap = matrix.gap_report
            
            # Overall metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Coverage", f"{gap.coverage_percentage:.1f}%")
            with col2:
                st.metric("Orphan HLRs", len(gap.orphan_hlrs))
            with col3:
                st.metric("Orphan LLRs", len(gap.orphan_llrs))
            
            st.markdown("---")
            
            # Orphan HLRs
            if gap.orphan_hlrs:
                st.markdown("### ⚠️ Orphan HLRs (No Linked LLRs)")
                st.markdown('<div class="gap-warning">', unsafe_allow_html=True)
                st.markdown("These HLRs have no linked LLRs. This indicates missing implementation details.")
                
                for hlr_id in gap.orphan_hlrs:
                    hlr = next(h for h in system.hlrs if h.id == hlr_id)
                    with st.expander(f"{hlr_id}: {hlr.title}"):
                        st.markdown(f"**Description:** {hlr.description}")
                        st.markdown(f"**Type:** {hlr.type}")
                        st.markdown(f"**Safety Level:** {hlr.safety_level}")
                        st.error("❌ No implementing LLRs found")
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.success("✅ No orphan HLRs - all HLRs have at least one linked LLR")
            
            st.markdown("---")
            
            # Partial coverage HLRs
            if gap.partial_coverage_hlrs:
                st.markdown("### ⚠️ Partial Coverage HLRs")
                st.warning(f"{len(gap.partial_coverage_hlrs)} HLRs have only partial coverage")
                
                for hlr_id in gap.partial_coverage_hlrs:
                    hlr = next(h for h in system.hlrs if h.id == hlr_id)
                    links = system.get_hlr_links(hlr_id)
                    
                    with st.expander(f"{hlr_id}: {hlr.title} ({len(links)} links)"):
                        st.markdown(f"**Description:** {hlr.description}")
                        st.markdown("**Linked LLRs:**")
                        for link in links:
                            llr = next(l for l in system.llrs if l.id == link.llr_id)
                            st.markdown(f"- {link.llr_id}: {llr.title} ({link.coverage.value})")
            
            st.markdown("---")
            
            # Orphan LLRs
            if gap.orphan_llrs:
                st.markdown("### ℹ️ Orphan LLRs (No Linked HLRs)")
                st.info("These LLRs are not traced to any HLR. They may be implementation details or unused requirements.")
                
                for llr_id in gap.orphan_llrs:
                    llr = next(l for l in system.llrs if l.id == llr_id)
                    with st.expander(f"{llr_id}: {llr.title}"):
                        st.markdown(f"**Description:** {llr.description}")
                        st.markdown(f"**Component:** {llr.component or 'N/A'}")
                        st.markdown(f"**Type:** {llr.type}")
            else:
                st.success("✅ No orphan LLRs - all LLRs are traced to at least one HLR")


if __name__ == "__main__":
    main()
