from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings # Import Gemini Embeddings
import re
import PyPDF2
import io
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from concurrent.futures import ThreadPoolExecutor
import tempfile
import os
import json

google_api_key="########"

class ResumeAnalysisAgent:
    def __init__(self, api_key, cutoff_score=75):
        self.api_key = api_key
        self.cutoff_score = cutoff_score
        self.resume_text = None
        self.rag_vectorstore = None
        self.analysis_result = None
        self.jd_text = None
        self.extracted_skills = None
        self.resume_weaknesses = []
        self.resume_strengths = []
        self.improvement_suggestions = {}

    def extract_text_from_pdf(self, pdf_file):
        """Extract text from a PDF file"""
        try:
            if hasattr(pdf_file, 'getvalue'): 
                pdf_data = pdf_file.getvalue()
                pdf_file_like = io.BytesIO(pdf_data)
                reader = PyPDF2.PdfReader(pdf_file_like)
            else: 
                reader = PyPDF2.PdfReader(pdf_file)
                
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    def extract_text_from_txt(self, txt_file):
        """Extract text from a text file"""
        try:
            if hasattr(txt_file, 'getvalue'):  
                return txt_file.getvalue().decode('utf-8')
            else: 
                with open(txt_file, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"Error extracting text from text file: {e}")
            return ""

    def extract_text_from_file(self, file):
        """Extract text from a file (PDF or TXT)"""
        if hasattr(file, 'name'):
            file_extension = file.name.split('.')[-1].lower()
        else:
            file_extension = file.split('.')[-1].lower()
            
        if file_extension == 'pdf':
            return self.extract_text_from_pdf(file)
        elif file_extension == 'txt':
            return self.extract_text_from_txt(file)
        else:
            print(f"Unsupported file extension: {file_extension}")
            return ""
        

    def create_rag_vector_store(self, text):
        """Create a vector store for RAG"""
   
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)
        
   
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=google_api_key
        )
        vectorstore = FAISS.from_texts(chunks, embeddings)
        return vectorstore
    


    def create_vector_store(self, text):
        """Create a simpler vector store for skill analysis"""
     
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=google_api_key
        )
        vectorstore = FAISS.from_texts([text], embeddings)
        return vectorstore

    def analyze_skill(self, qa_chain, skill):
        """Analyze a skill in the resume"""
        query = f"On a scale of 0-10, how clearly does the candidate mention proficiency in {skill}? Provide a numeric rating first, followed by reasoning."
        response = qa_chain.run(query)
        match = re.search(r"(\d{1,2})", response)
        score = int(match.group(1)) if match else 0
        

        reasoning = response.split('.', 1)[1].strip() if '.' in response and len(response.split('.')) > 1 else ""
        
    
        return skill, min(score, 10), reasoning
    


    def analyze_resume_weaknesses(self):
        """Analyze specific weaknesses in the resume based on missing skills"""
        if not self.resume_text or not self.extracted_skills or not self.analysis_result:
            return []
        
        weaknesses = []
        
        for skill in self.analysis_result.get("missing_skills", []):

            llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite", # Recommended model
    google_api_key=google_api_key, # Can often be omitted if env var is set
    temperature=0.2, # Example parameter
    convert_system_message_to_human=True # Often helpful for Gemini compatibility
)
            prompt = f"""
            Analyze why the resume is weak in demonstrating proficiency in "{skill}".
            
            For your analysis, consider:
            1. What's missing from the resume regarding this skill?
            2. How could it be improved with specific examples?
            3. What specific action items would make this skill stand out?
            
            Resume Content:
            {self.resume_text[:3000]}...
            
            Provide your response in this JSON format:
            {{
                "weakness": "A concise description of what's missing or problematic (1-2 sentences)",
                "improvement_suggestions": [
                    "Specific suggestion 1",
                    "Specific suggestion 2",
                    "Specific suggestion 3"
                ],
                "example_addition": "A specific bullet point that could be added to showcase this skill"
            }}
            
            Return only valid JSON, no other text.
            """
            
            response = llm.invoke(prompt)
            weakness_content = response.content.strip()
            
    
            try:
                weakness_data = json.loads(weakness_content)
                
                weakness_detail = {
                    "skill": skill,
                    "score": self.analysis_result.get("skill_scores", {}).get(skill, 0),
                    "detail": weakness_data.get("weakness", "No specific details provided."),
                    "suggestions": weakness_data.get("improvement_suggestions", []),
                    "example": weakness_data.get("example_addition", "")
                }
                
                weaknesses.append(weakness_detail)

                self.improvement_suggestions[skill] = {
                    "suggestions": weakness_data.get("improvement_suggestions", []),
                    "example": weakness_data.get("example_addition", "")
                }
            except json.JSONDecodeError:
             
                weaknesses.append({
                    "skill": skill,
                    "score": self.analysis_result.get("skill_scores", {}).get(skill, 0),
                    "detail": weakness_content[:200]  # Truncate if it's not proper JSON
                })
            
        self.resume_weaknesses = weaknesses
        return weaknesses
    



    def extract_skills_from_jd(self, jd_text):
        """Extract skills from a job description"""
        try:
 
            llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite", # Recommended model
    google_api_key=google_api_key, # Can often be omitted if env var is set
    temperature=0.2, # Example parameter
    convert_system_message_to_human=True # Often helpful for Gemini compatibility
)
            prompt = f"""
            Extract a comprehensive list of technical skills, technologies, and competencies required from this job description. 
            Format the output as a Python list of strings. Only include the list, nothing else.
            
            Job Description:
            {jd_text}
            """
            
            response = llm.invoke(prompt)
            skills_text = response.content
            
      
            match = re.search(r'\[(.*?)\]', skills_text, re.DOTALL)
            if match:
                skills_text = match.group(0)
            

            try:
                skills_list = eval(skills_text)
                if isinstance(skills_list, list):
                    return skills_list
            except:
                pass
            
         
            skills = []
            for line in skills_text.split('\n'):
                line = line.strip()
                if line.startswith('- ') or line.startswith('* '):
                    skill = line[2:].strip()
                    if skill:
                        skills.append(skill)
                elif line.startswith('"') and line.endswith('"'):
                    skill = line.strip('"')
                    if skill:
                        skills.append(skill)
            
            return skills
        except Exception as e:
            print(f"Error extracting skills from job description: {e}")
            return []
        

    def semantic_skill_analysis(self, resume_text, skills):
        """Analyze skills semantically"""
        vectorstore = self.create_vector_store(resume_text)
        retriever = vectorstore.as_retriever()
        qa_chain = RetrievalQA.from_chain_type(
            llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite", # Recommended model
    google_api_key=google_api_key, # Can often be omitted if env var is set
    temperature=0.2, # Example parameter
    convert_system_message_to_human=True # Often helpful for Gemini compatibility
),
            retriever=retriever,
            return_source_documents=False
        )

        skill_scores = {}
        skill_reasoning = {}
        missing_skills = []
        total_score = 0

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda skill: self.analyze_skill(qa_chain, skill), skills))

        for skill, score, reasoning in results:
            skill_scores[skill] = score
            skill_reasoning[skill] = reasoning
            total_score += score
            if score <= 5:
                missing_skills.append(skill)

        overall_score = int((total_score / (10 * len(skills))) * 100)
        selected = overall_score >= self.cutoff_score

        reasoning = "Candidate evaluated based on explicit resume content using semantic similarity and clear numeric scoring."
        strengths = [skill for skill, score in skill_scores.items() if score >= 7]
        improvement_areas = missing_skills if not selected else []
        

        self.resume_strengths = strengths

        return {
            "overall_score": overall_score,
            "skill_scores": skill_scores,
            "skill_reasoning": skill_reasoning,
            "selected": selected,
            "reasoning": reasoning,
            "missing_skills": missing_skills,
            "strengths": strengths,
            "improvement_areas": improvement_areas
        }


    def analyze_resume(self, resume_file, role_requirements=None, custom_jd=None):
        """Analyze a resume against role requirements or a custom JD"""
        self.resume_text = self.extract_text_from_file(resume_file)
        
       
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8') as tmp:
            tmp.write(self.resume_text)
            self.resume_file_path = tmp.name
     
        self.rag_vectorstore = self.create_rag_vector_store(self.resume_text)
        
   
        if custom_jd:
            self.jd_text = self.extract_text_from_file(custom_jd)
            self.extracted_skills = self.extract_skills_from_jd(self.jd_text)
            
        
            self.analysis_result = self.semantic_skill_analysis(self.resume_text, self.extracted_skills)
    
        elif role_requirements:
            self.extracted_skills = role_requirements
            
 
            self.analysis_result = self.semantic_skill_analysis(self.resume_text, role_requirements)
            
    
        if self.analysis_result and "missing_skills" in self.analysis_result and self.analysis_result["missing_skills"]:
            self.analyze_resume_weaknesses()
     
            self.analysis_result["detailed_weaknesses"] = self.resume_weaknesses
        
        return self.analysis_result

    def ask_question(self, question):
        """Ask a question about the resume"""
        if not self.rag_vectorstore or not self.resume_text:
            return "Please analyze a resume first."
        
        retriever = self.rag_vectorstore.as_retriever(
            search_kwargs={"k": 3}  
        )
        
        qa_chain = RetrievalQA.from_chain_type(
            llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite", # Recommended model
    google_api_key=google_api_key, # Can often be omitted if env var is set
    temperature=0.2, # Example parameter
    convert_system_message_to_human=True # Often helpful for Gemini compatibility
),
            chain_type="stuff",  
            retriever=retriever,
            return_source_documents=False,
        )
        
        response = qa_chain.run(question)
        return response
    

    def generate_interview_questions(self, question_types, difficulty, num_questions):
        """Generate interview questions based on the resume"""
        if not self.resume_text or not self.extracted_skills:
            return []
        
        try:
            llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite", # Recommended model
    google_api_key=google_api_key, # Can often be omitted if env var is set
    temperature=0.2, # Example parameter
    convert_system_message_to_human=True # Often helpful for Gemini compatibility
)
            
        
            context = f"""
            Resume Content:
            {self.resume_text[:2000]}...
            
            Skills to focus on: {', '.join(self.extracted_skills)}
            
            Strengths: {', '.join(self.analysis_result.get('strengths', []))}
            
            Areas for improvement: {', '.join(self.analysis_result.get('missing_skills', []))}
            """
            
            prompt = f"""
            Generate {num_questions} personalized {difficulty.lower()} level interview questions for this candidate 
            based on their resume and skills. Include only the following question types: {', '.join(question_types)}.
            
            For each question:
            1. Clearly label the question type
            2. Make the question specific to their background and skills
            3. For coding questions, include a clear problem statement
            
            {context}
            
            Format the response as a list of tuples with the question type and the question itself.
            Each tuple should be in the format: ("Question Type", "Full Question Text")
            """
            
            response = llm.invoke(prompt)
            questions_text = response.content
            
      
            questions = []
            pattern = r'[("]([^"]+)[",)\s]+[(",\s]+([^"]+)[")\s]+'
            matches = re.findall(pattern, questions_text, re.DOTALL)
            
            for match in matches:
                if len(match) >= 2:
                    question_type = match[0].strip()
                    question = match[1].strip()
                    
     
                    for requested_type in question_types:
                        if requested_type.lower() in question_type.lower():
                            questions.append((requested_type, question))
                            break
            

            if not questions:
                lines = questions_text.split('\n')
                current_type = None
                current_question = ""
                
                for line in lines:
                    line = line.strip()
                    if any(t.lower() in line.lower() for t in question_types) and not current_question:
                        current_type = next((t for t in question_types if t.lower() in line.lower()), None)
                        if ":" in line:
                            current_question = line.split(":", 1)[1].strip()
                    elif current_type and line:
                        current_question += " " + line
                    elif current_type and current_question:
                        questions.append((current_type, current_question))
                        current_type = None
                        current_question = ""

            questions = questions[:num_questions]
            
            return questions
        
        except Exception as e:
            print(f"Error generating interview questions: {e}")
            return []
        
    

    def cleanup(self):
        """Clean up temporary files"""
        try:
            if hasattr(self, 'resume_file_path') and os.path.exists(self.resume_file_path):
                os.unlink(self.resume_file_path)
            
            if hasattr(self, 'improved_resume_path') and os.path.exists(self.improved_resume_path):
                os.unlink(self.improved_resume_path)
        except Exception as e:
            print(f"Error cleaning up temporary files: {e}")