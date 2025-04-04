# Import required libraries
import os
import tempfile
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
from langchain_community.embeddings import SentenceTransformerEmbeddings
from typing import List, Dict, Any

# Set page configuration
st.set_page_config(page_title="Resume Screening Assistant", layout="wide")

# Initialize components
def initialize_components():
    """Initialize embedding model and LLM"""
    # Use environment variables for API keys
    groq_api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
    
    # Initialize embedding model - using a simpler approach that doesn't require auth
    try:
        # Use a simpler embedding model that doesn't require auth
        embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    except Exception as e:
        st.error(f"Error initializing embeddings: {str(e)}")
        # Fallback to even simpler embeddings
        from langchain_community.embeddings import TensorflowHubEmbeddings
        try:
            embeddings = TensorflowHubEmbeddings()
        except:
            # Last resort fallback
            from langchain_community.embeddings import FakeEmbeddings
            embeddings = FakeEmbeddings(size=384)
    
    # Initialize Groq LLM - using Mixtral for good performance
    llm = ChatGroq(
        temperature=0, 
        model_name="deepseek-r1-distill-qwen-32b", 
        api_key=groq_api_key
    )
    
    return embeddings, llm

# Document processing pipeline
def process_resumes(uploaded_files, applicant_ids):
    """Process uploaded resume PDFs and return documents with metadata"""
    all_docs = []
    
    # Process each resume
    for i, pdf_file in enumerate(uploaded_files):
        # Check file size (10MB limit)
        if pdf_file.size > 10 * 1024 * 1024:  # 10MB in bytes
            st.error(f"Error processing {pdf_file.name}: File exceeds 10MB size limit.")
            continue
            
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(pdf_file.getbuffer())
            temp_path = temp_file.name
        
        try:
            # Use PyPDFLoader for PDF processing
            loader = PyPDFLoader(temp_path)
            documents = loader.load()
            
            # Add metadata to each document
            for doc in documents:
                doc.metadata["applicant_id"] = applicant_ids[i].strip()
                doc.metadata["applicant_name"] = f"Applicant {i+1}"  # Could extract from resume
                doc.metadata["source"] = pdf_file.name
            
            all_docs.extend(documents)
        except Exception as e:
            st.error(f"Error processing {pdf_file.name}: {str(e)}")
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
    
    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    
    split_docs = text_splitter.split_documents(all_docs)
    
    return split_docs

# Custom retriever class
class ResumeRetriever:
    """Custom retriever for resume documents with hybrid search capabilities"""
    
    def __init__(self, vector_store):
        self.vector_store = vector_store
    
    def get_relevant_documents(self, query, k=5):
        """Retrieve documents based on semantic similarity"""
        return self.vector_store.similarity_search(query, k=k)
    
    def filter_by_applicant_id(self, applicant_ids):
        """Filter documents by applicant ID"""
        if not self.vector_store:
            return []
        
        # Use metadata filtering in FAISS
        results = []
        for applicant_id in applicant_ids:
            docs = self.vector_store.similarity_search(
                "", 
                k=100,  # Get more to ensure we have enough
                filter={"applicant_id": applicant_id.strip()}
            )
            results.extend(docs)
        
        return results

# RAG chain for resume analysis
def create_rag_chain(retriever, llm):
    """Create a RAG chain for resume analysis"""
    
    # Create a prompt template
    template = """
    You are an expert HR recruiter and resume analyst. 
    
    Use the following resume information to answer the question.
    
    Resume information:
    {context}
    
    Question: {question}
    
    Provide a detailed and professional analysis. If the information isn't available in the resumes, 
    clearly state that you don't have enough information to answer accurately.
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    
    # Format context to extract text from documents
    def format_docs(docs):
        return "\n\n".join([doc.page_content for doc in docs])
    
    # Create the RAG chain
    rag_chain = (
        {"context": lambda query: format_docs(retriever.get_relevant_documents(query)), 
         "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain
groq_api_key = os.environ.get("GROQ_API_KEY")
# Job matching chain
def create_job_matching_chain(retriever, llm):
    """Create a chain for matching resumes to job descriptions"""
    
    template = """
    You are an expert HR recruiter specializing in matching candidates to job requirements.
    consider mba as master degree
    
    Job Description:
    {job_description}
    
    Resume information:
    {context}
    
    Task: Analyze how well the candidate's qualifications match the job requirements.
    
    Provide a detailed analysis including:
    1. Overall match score (0-100%)
    2. Key matching qualifications
    3. Notable gaps or missing requirements
    4. Recommendation (Highly Recommended, Recommended, Consider, Not Recommended)
    5.Give candidate and match percentage as table format
    "Candidate	Overall Match Score"
    
    Format your response clearly with these sections.
    


    At last , Give me the candidates who are recommended

    """
    
    prompt = ChatPromptTemplate.from_template(template)
    
    # Format context to extract text from documents
    def format_docs(docs):
        return "\n\n".join([doc.page_content for doc in docs])
    
    # Create the job matching chain
    job_matching_chain = (
        {"context": lambda x: format_docs(retriever.get_relevant_documents(x["job_description"], k=10)), 
         "job_description": lambda x: x["job_description"]}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return job_matching_chain

# Streamlit UI
def main():
    st.title("🧠 Resume Screening Assistant")
    st.markdown("Upload resumes, analyze candidates, and match them to job descriptions.")
    
    # API key input in sidebar
    with st.sidebar:
        # st.subheader("API Configuration")
        # groq_api_key = st.text_input("Enter Groq API Key:", type="password", 
        #                              help="Get your API key from https://console.groq.com/")
        if groq_api_key:
            os.environ["GROQ_API_KEY"] = groq_api_key
    
    # Initialize session state
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None
    if "retriever" not in st.session_state:
        st.session_state.retriever = None
    if "processed_applicants" not in st.session_state:
        st.session_state.processed_applicants = []
    
    # Sidebar for resume upload
    with st.sidebar:
        st.header("📄 Upload Resumes")
        uploaded_files = st.file_uploader(
            "Choose PDF files (max 10MB each)", 
            type="pdf", 
            accept_multiple_files=True,
            help="Upload candidate resumes in PDF format. Maximum file size: 10MB"
        )
        
        applicant_ids_input = st.text_area(
            "Enter applicant IDs (one per line)", 
            help="Enter one ID per resume, in the same order as the uploaded files"
        )
        
        applicant_ids = applicant_ids_input.split("\n") if applicant_ids_input else []
        
        process_button = st.button(
            "Process Resumes", 
            disabled=not (uploaded_files and applicant_ids and len(uploaded_files) == len(applicant_ids) and groq_api_key)
        )
        
        if process_button:
            with st.spinner("Processing resumes..."):
                try:
                    # Process documents
                    documents = process_resumes(uploaded_files, applicant_ids)
                    
                    if documents:
                        # Initialize embedding model
                        embeddings, _ = initialize_components()
                        
                        # Create vector store
                        st.session_state.vector_store = FAISS.from_documents(documents, embeddings)
                        
                        # Create retriever
                        st.session_state.retriever = ResumeRetriever(st.session_state.vector_store)
                        
                        # Store processed applicant IDs
                        st.session_state.processed_applicants = applicant_ids
                        
                        st.success(f"✅ Successfully processed {len(uploaded_files)} resumes!")
                    else:
                        st.error("No documents were extracted from the resumes.")
                except Exception as e:
                    st.error(f"Error during processing: {str(e)}")
        
        # Display processed applicants
        if st.session_state.processed_applicants:
            st.subheader("Processed Applicants")
            for i, app_id in enumerate(st.session_state.processed_applicants):
                st.write(f"{i+1}. {app_id}")
    
    # Main content area with tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Resume Analysis", "🎯 Job Matching", "📊 Comparison"])
    
    # Tab 1: Resume Analysis
    with tab1:
        st.header("Resume Analysis")
        
        if st.session_state.retriever:
            # Query interface
            query = st.text_area("Ask a question about the candidates:", 
                                height=100,
                                placeholder="Example: What skills do the candidates have? Who has experience with Python?")
            
            if query and st.button("Analyze", key="analyze_btn"):
                if not groq_api_key:
                    st.error("Please enter your Groq API key in the sidebar.")
                else:
                    with st.spinner("Analyzing resumes..."):
                        try:
                            # Initialize LLM
                            _, llm = initialize_components()
                            
                            # Create RAG chain
                            rag_chain = create_rag_chain(st.session_state.retriever, llm)
                            
                            # Get response
                            response = rag_chain.invoke(query)
                            
                            # Display response
                            st.markdown("### Analysis Results")
                            st.markdown(response)
                        except Exception as e:
                            st.error(f"Error during analysis: {str(e)}")
        else:
            st.info("Please upload and process resumes first.")
    
    # Tab 2: Job Matching
    with tab2:
        st.header("Job Description Matching")
        
        if st.session_state.retriever:
            # Job description input
            job_description = st.text_area(
                "Enter job description:", 
                height=200,
                placeholder="Paste the job description here to match candidates against it..."
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                selected_applicants = st.multiselect(
                    "Select applicants to match (optional):",
                    options=st.session_state.processed_applicants,
                    default=st.session_state.processed_applicants
                )
            
            with col2:
                match_button = st.button("Match Candidates", key="match_btn")
            
            if job_description and match_button:
                if not groq_api_key:
                    st.error("Please enter your Groq API key in the sidebar.")
                else:
                    with st.spinner("Matching candidates to job description..."):
                        try:
                            # Initialize LLM
                            _, llm = initialize_components()
                            
                            # Filter retriever by selected applicants if needed
                            if selected_applicants and selected_applicants != st.session_state.processed_applicants:
                                filtered_docs = st.session_state.retriever.filter_by_applicant_id(selected_applicants)
                                temp_retriever = ResumeRetriever(
                                    FAISS.from_documents(filtered_docs, SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2"))
                                )
                            else:
                                temp_retriever = st.session_state.retriever
                            
                            # Create job matching chain
                            job_chain = create_job_matching_chain(temp_retriever, llm)
                            
                            # Get response
                            response = job_chain.invoke({"job_description": job_description})
                            
                            # Display response
                            st.markdown("### Matching Results")
                            st.markdown(response)
                        except Exception as e:
                            st.error(f"Error during matching: {str(e)}")
        else:
            st.info("Please upload and process resumes first.")
    
    # Tab 3: Comparison
    with tab3:
        st.header("Candidate Comparison")
        
        if st.session_state.retriever and len(st.session_state.processed_applicants) > 1:
            # Comparison criteria
            comparison_criteria = st.text_area(
                "Enter comparison criteria:", 
                height=100,
                placeholder="Example: technical skills, years of experience, education level"
            )
            
            selected_applicants = st.multiselect(
                "Select applicants to compare:",
                options=st.session_state.processed_applicants,
                default=st.session_state.processed_applicants[:min(5, len(st.session_state.processed_applicants))]
            )
            
            if comparison_criteria and selected_applicants and st.button("Compare", key="compare_btn"):
                if not groq_api_key:
                    st.error("Please enter your Groq API key in the sidebar.")
                else:
                    with st.spinner("Comparing candidates..."):
                        try:
                            # Initialize LLM
                            _, llm = initialize_components()
                            
                            # Get documents for selected applicants
                            docs = st.session_state.retriever.filter_by_applicant_id(selected_applicants)
                            
                            # Format context
                            context = "\n\n".join([doc.page_content for doc in docs])
                            
                            # Create comparison prompt
                            template = """
                            You are an expert HR recruiter comparing multiple candidates.
                            
                            Resume information for multiple candidates:
                            {context}
                            
                            Compare these candidates based on the following criteria:
                            {criteria}
                            
                            Provide a detailed comparison in a table format, with candidates as columns and criteria as rows.
                            After the table, provide a summary of strengths and weaknesses for each candidate.
                            """
                            
                            prompt = ChatPromptTemplate.from_template(template)
                            
                            # Create comparison chain - FIXED VERSION
                            comparison_chain = (
                                {"context": lambda _: context, "criteria": lambda _: comparison_criteria}
                                | prompt
                                | llm
                                | StrOutputParser()
                            )
                            
                            # Get response
                            response = comparison_chain.invoke({})
                            
                            # Display response
                            st.markdown("### Comparison Results")
                            st.markdown(response)
                        except Exception as e:
                            st.error(f"Error during comparison: {str(e)}")
        else:
            st.info("Please upload at least 2 resumes to use the comparison feature.")
    
    # Footer
    st.markdown("---")
    st.markdown("Made with ❤️ By Srinivasa Reddy")

if __name__ == "__main__":
    main()

