import streamlit as st
import pandas as pd
import base64
import io
import matplotlib.pyplot as plt

google_api_key="#########"

def setup_page():
    """Apply custom CSS and setup page (without setting page config)"""
    # Apply custom CSS only
    #apply_custom_css()
    
    # Add local logo handling via JavaScript
    st.markdown("""
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Try to load the logo, if it fails, show fallback text
            var logoImg = document.querySelector('.logo-image');
            if (logoImg) {
                logoImg.onerror = function() {
                    var logoContainer = document.querySelector('.logo-container');
                    if (logoContainer) {
                        logoContainer.innerHTML = '<div style="font-size: 40px;">🚀</div>';
                    }
                };
            }
        });
    </script>
    """, unsafe_allow_html=True)

def display_header():

    try:
        with open("res.jpg", "rb") as img_file:
            logo_base64 = base64.b64encode(img_file.read()).decode()
            logo_html = f'<img src="data:image/jpeg;base64,{logo_base64}" alt="res Logo" class="logo-image" style="max-height: 100px;">'
    except:
      
        logo_html = '<div style="font-size: 50px; text-align: center;">🚀</div>'

    st.markdown(f"""
    <div class="main-header">
        <div class="header-container">
            <div class="logo-container" style="text-align: center; margin-bottom: 20px;">
                {logo_html}
            </div>
            <div class="title-container" style="text-align: center;">
                <h1>Recruitment Agent</h1>
                <p>Smart Resume Analysis & Interview Preparation System</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def setup_sidebar():
    with st.sidebar:
        st.header("Configuration")
        
        st.subheader("API Keys")
        google_api_key = st.text_input("Google API Key", type="password")
        
        st.markdown("---")
        
        
        st.subheader("Theme")
        theme_color = st.color_picker("Accent Color", "#d32f2f")
        st.markdown(f"""
        <style>
        .stButton button, .main-header, .stTabs [aria-selected="true"] {{
            background-color: {theme_color} !important;
            border-color: {theme_color} !important;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("""
        <div style="text-align: center; margin-top: 20px;">
            <p>🚀 Recruitment Agent</p>
            <p style="font-size: 0.8rem; color: #666;">v1.0.0</p>
        </div>
        """, unsafe_allow_html=True)
        
        return {
            "google_api_key": google_api_key,
            "theme_color": theme_color
        }




def role_selection_section(role_requirements):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        role = st.selectbox("Select the role you're applying for:", list(role_requirements.keys()))
    
    with col2:
        upload_jd = st.checkbox("Upload custom job description instead")
    
    custom_jd = None
    if upload_jd:
        custom_jd_file = st.file_uploader("Upload job description (PDF or TXT)", type=["pdf", "txt"])
        if custom_jd_file:
            st.success("Custom job description uploaded!")
            custom_jd = custom_jd_file
    
    if not upload_jd:
        st.info(f"Required skills: {', '.join(role_requirements[role])}")
        st.markdown(f"<p>Cutoff Score for selection: <b>{75}/100</b></p>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return role, custom_jd



def resume_upload_section():
    st.markdown("""
    <div class="card">
        <h3>📄 Upload Your Resume</h3>
        <p>Supported format: PDF</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_resume = st.file_uploader("", type=["pdf"], label_visibility="collapsed")
    
    return uploaded_resume



def create_score_pie_chart(score):
    """Create a professional pie chart for the score visualization"""
    fig, ax = plt.subplots(figsize=(4, 4), facecolor='#111111')
    
    # Data
    sizes = [score, 100 - score]
    labels = ['', '']  # We'll use annotation instead
    colors = ["#d32f2f", "#333333"]
    explode = (0.05, 0)  # explode the 1st slice (Score)
    
    # Plot
    wedges, texts = ax.pie(
        sizes, 
        labels=labels, 
        colors=colors,
        explode=explode, 
        startangle=90,
        wedgeprops={'width': 0.5, 'edgecolor': 'black', 'linewidth': 1}
    )
    
    # Draw a circle in the center to make it a donut chart
    centre_circle = plt.Circle((0, 0), 0.25, fc='#111111')
    ax.add_artist(centre_circle)
    
    # Equal aspect ratio ensures that pie is drawn as a circle
    ax.set_aspect('equal')
    
    # Add score text in the center
    ax.text(0, 0, f"{score}%", 
            ha='center', va='center', 
            fontsize=24, fontweight='bold', 
            color='white')
    
    # Add pass/fail indicator
    status = "PASS" if score >= 75 else "FAIL"
    status_color = "#4CAF50" if score >= 75 else "#d32f2f"
    ax.text(0, -0.15, status, 
            ha='center', va='center', 
            fontsize=14, fontweight='bold', 
            color=status_color)
    
    # Set the background color
    ax.set_facecolor('#111111')
    
    return fig




def display_analysis_results(analysis_result):
    if not analysis_result:
        return

    overall_score = analysis_result.get('overall_score', 0)
    selected = analysis_result.get("selected", False)
    skill_scores = analysis_result.get("skill_scores", {})
    detailed_weaknesses = analysis_result.get("detailed_weaknesses", [])

    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown(
        '<div style="text-align: right; font-size: 0.8rem; color: #888; margin-bottom: 10px;">Powered by Recruitment</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        st.metric("Overall Score", f"{overall_score}/100")
        fig = create_score_pie_chart(overall_score)
        st.pyplot(fig)

    with col2:
        if selected:
            st.markdown("<h2 style='color:#4CAF50;'>✅ Congratulations! You have been shortlisted.</h2>", unsafe_allow_html=True)
        else:
            st.markdown("<h2 style='color:#d32f2f;'>❌ Unfortunately, you were not selected.</h2>", unsafe_allow_html=True)
        st.write(analysis_result.get('reasoning', ''))

    st.markdown('<hr>', unsafe_allow_html=True)

    st.markdown('<div class="strengths-improvements">', unsafe_allow_html=True)

    # Strengths
    st.markdown('<div>', unsafe_allow_html=True)
    st.subheader("🌟 Strengths")
    strengths = analysis_result.get("strengths", [])
    if strengths:
        for skill in strengths:
            st.markdown(f'<div class="skill-tag">{skill} ({skill_scores.get(skill, "N/A")}/10)</div>', unsafe_allow_html=True)
    else:
        st.write("No notable strengths identified.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Weaknesses
    
    st.markdown('<div>', unsafe_allow_html=True)
    st.subheader("🚩 Areas for Improvement")
    missing_skills = analysis_result.get("missing_skills", [])
    if missing_skills:
        for skill in missing_skills:
            st.markdown(f'<div class="skill-tag missing">{skill} ({skill_scores.get(skill, "N/A")}/10)</div>', unsafe_allow_html=True)
    else:
        st.write("No significant areas for improvement.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    
    # Detailed weaknesses section
    if detailed_weaknesses:
        st.markdown('<hr>', unsafe_allow_html=True)
        st.subheader("📊 Detailed Weakness Analysis")
        
        for weakness in detailed_weaknesses:
            skill_name = weakness.get('skill', '')
            score = weakness.get('score', 0)
            
            with st.expander(f"{skill_name} (Score: {score}/10)"):
                # Clean detail display
                detail = weakness.get('detail', 'No specific details provided.')
                # Clean JSON formatting if it appears in the text
                if detail.startswith('```json') or '{' in detail:
                    detail = "The resume lacks examples of this skill."
                
                st.markdown(f'<div class="weakness-detail"><strong>Issue:</strong> {detail}</div>', 
                           unsafe_allow_html=True)
                
                # Display improvement suggestions if available
                if 'suggestions' in weakness and weakness['suggestions']:
                    st.markdown("<strong>How to improve:</strong>", unsafe_allow_html=True)
                    for i, suggestion in enumerate(weakness['suggestions']):
                        st.markdown(f'<div class="solution-detail">{i+1}. {suggestion}</div>', 
                                   unsafe_allow_html=True)
                
                # Display example if available
                if 'example' in weakness and weakness['example']:
                    st.markdown("<strong>Example addition:</strong>", unsafe_allow_html=True)
                    st.markdown(f'<div class="example-detail">{weakness["example"]}</div>', 
                               unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        report_content = f"""
# Resume Analysis Report

## Overall Score: {overall_score}/100

Status: {"✅ Shortlisted" if selected else "❌ Not Selected"}

## Analysis Reasoning
{analysis_result.get('reasoning', 'No reasoning provided.')}

## Strengths
{", ".join(strengths if strengths else ["None identified"])}

## Areas for Improvement
{", ".join(missing_skills if missing_skills else ["None identified"])}

## Detailed Weakness Analysis
"""
        # Add detailed weaknesses to report
        for weakness in detailed_weaknesses:
            skill_name = weakness.get('skill', '')
            score = weakness.get('score', 0)
            detail = weakness.get('detail', 'No specific details provided.')
            
            # Clean JSON formatting if it appears in the text
            if detail.startswith('```json') or '{' in detail:
                detail = "The resume lacks examples of this skill."
                
            report_content += f"\n### {skill_name} (Score: {score}/10)\n"
            report_content += f"Issue: {detail}\n"
            
            # Add suggestions to report
            if 'suggestions' in weakness and weakness['suggestions']:
                report_content += "\nImprovement suggestions:\n"
                for i, sugg in enumerate(weakness['suggestions']):
                    report_content += f"- {sugg}\n"
            
            # Add example to report
            if 'example' in weakness and weakness['example']:
                report_content += f"\nExample: {weakness['example']}\n"
            
        report_content += "\n---\nAnalysis provided by Recruitment Agent"
        
        report_b64 = base64.b64encode(report_content.encode()).decode()
        href = f'<a class="download-btn" href="data:text/plain;base64,{report_b64}" download="resume_analysis.txt">📊 Download Analysis Report</a>'
        st.markdown(href, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)






def resume_qa_section(has_resume, ask_question_func=None):
    if not has_resume:
        st.warning("Please upload and analyze a resume first.")
        return
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    st.subheader("Ask Questions About the Resume")
    user_question = st.text_input("Enter your question about the resume:", placeholder="What is the candidate's most recent experience?")
    
    if user_question and ask_question_func:
        with st.spinner("Searching resume and generating response..."):
            response = ask_question_func(user_question)
            
            st.markdown('<div style="background-color: #111122; padding: 15px; border-radius: 5px; border-left: 5px solid #d32f2f;">', unsafe_allow_html=True)
            st.write(response)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Add example questions
    with st.expander("Example Questions"):
        example_questions = [
            "What is the candidate's most recent role?",
            "How many years of experience does the candidate have with Python?",
            "What educational qualifications does the candidate have?",
            "What are the candidate's key achievements?",
            "Has the candidate managed teams before?",
            "What projects has the candidate worked on?",
            "Does the candidate have experience with cloud technologies?"
        ]
        
        for question in example_questions:
            if st.button(question, key=f"q_{question}"):
                st.session_state.current_question = question
                st.experimental_rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def interview_questions_section(has_resume, generate_questions_func=None):
    if not has_resume:
        st.warning("Please upload and analyze a resume first.")
        return
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        question_types = st.multiselect(
            "Select question types:",
            ["Basic", "Technical", "Experience", "Scenario", "Coding", "Behavioral"],
            default=["Basic", "Technical"]
        )
    
    with col2:
        difficulty = st.select_slider(
            "Question difficulty:",
            options=["Easy", "Medium", "Hard"],
            value="Medium"
        )
    
    num_questions = st.slider("Number of questions:", 3, 15, 5)
    
    if st.button("Generate Interview Questions"):
        if generate_questions_func:
            with st.spinner("Generating personalized interview questions..."):
                questions = generate_questions_func(question_types, difficulty, num_questions)
                
                # Create content for download
                download_content = f"# Recruitment - Interview Questions\n\n"
                download_content += f"Difficulty: {difficulty}\n"
                download_content += f"Types: {', '.join(question_types)}\n\n"
                
                for i, (q_type, question) in enumerate(questions):
                    with st.expander(f"{q_type}: {question[:50]}..."):
                        st.write(question)
                        
                        # For coding questions, add code editor
                        if q_type == "Coding":
                            st.code("# Write your solution here", language="python")
                    
                    # Add to download content
                    download_content += f"## {i+1}. {q_type} Question\n\n"
                    download_content += f"{question}\n\n"
                    if q_type == "Coding":
                        download_content += "```python\n# Write your solution here\n```\n\n"
                
                # Add branding to download content
                download_content += "\n---\nQuestions generated by Recruitment Agent"
                
                # Add download button
                if questions:
                    st.markdown("---")
                    questions_bytes = download_content.encode()
                    b64 = base64.b64encode(questions_bytes).decode()
                    href = f'<a class="download-btn" href="data:text/markdown;base64,{b64}" download="interview_questions.md">📝 Download All Questions</a>'
                    st.markdown(href, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)




    
def create_tabs():
    return st.tabs([
        "Resume Analysis", 
        "Resume Q&A", 
        "Interview Questions"
    ])