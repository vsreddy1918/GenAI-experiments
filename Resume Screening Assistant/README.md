
## 🧠 Resume Screening Assistant

An intelligent, AI-powered Streamlit app to **analyze**, **match**, and **compare** candidate resumes against job descriptions. Ideal for recruiters and hiring managers to streamline the shortlisting process using LLMs and semantic search.
![image](https://github.com/user-attachments/assets/bfadbaab-a328-4c4a-8873-a0c19114a7ad)



---

### 🚀 Features

✅ Upload and analyze multiple resumes (PDFs)  
✅ Ask HR-style questions about candidates  
✅ Match resumes to job descriptions using RAG (Retrieval-Augmented Generation)  
✅ Get structured insights like match percentage, missing skills, and recommendations  
✅ Compare multiple candidates side-by-side

---

### 🛠️ Tech Stack

- **Frontend**: Streamlit
- **LLM**: [Groq](https://console.groq.com) (supports Mixtral, Qwen, etc.)
- **Embeddings**: `sentence-transformers` (MiniLM)
- **Vector Store**: FAISS
- **Document Parsing**: LangChain, PyPDFLoader
- **Prompt Engineering**: LangChain Prompt Templates

---

### 📦 Installation

1. **Clone the repo**

```bash
git clone https://github.com/vsreddy1918/GenAI-experiments/Resume Screening Assistant.git
cd resume-screening-assistant
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Set your environment variable**

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Alternatively, Streamlit supports `st.secrets` if deployed.

4. **Run the app**

```bash
streamlit run app.py
```

---

### 📸 Screenshots

| Upload & Process | Resume QA | Job Match |
|------------------|-----------|-----------|
| ![upload](screens/upload.png) | ![qa](screens/qa.png) | ![match](screens/match.png) |
![image](https://github.com/user-attachments/assets/e4e66236-c717-40ba-afe9-58a8ea685345)
![image](https://github.com/user-attachments/assets/c1493e3b-acb7-47dd-8cf1-f3b60a72ee6c)
![image](https://github.com/user-attachments/assets/c153ebcd-957f-4447-9efa-56f8a1c33da1)


---

### 🧪 Example Prompts

- _“Which candidates have experience in Python and Machine Learning?”_  
- _“Compare the educational qualifications of all candidates.”_  
- _“Match candidates to the role of Senior Data Scientist.”_

---

### 🔐 API Access

You’ll need a valid **Groq API key** for LLM access. Get one from [https://console.groq.com](https://console.groq.com).

---

### 👨‍💻 Author

Built with ❤️ by [**Srinivasa Reddy**](https://www.linkedin.com/in/vsreddy1918)  
Let's connect on [LinkedIn](https://www.linkedin.com/in/vsreddy1918)

---

### 📄 License

MIT License
