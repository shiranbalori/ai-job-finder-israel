"""Realistic demo CV profile and Israeli AI/Data job listings."""

DEMO_CV = {
    "full_name": "Demo Candidate Profile",
    "email": "demo.candidate@example.com",
    "summary": (
        "Machine Learning Engineer with 5+ years building NLP pipelines, LLM applications, "
        "and production ML systems in Tel Aviv startups. Strong Python, PyTorch, and MLOps background."
    ),
    "years_experience": 5,
    "job_titles": ["Machine Learning Engineer", "NLP Engineer", "AI Engineer"],
    "skills": [
        "Python", "PyTorch", "TensorFlow", "NLP", "LLM", "LangChain",
        "Machine Learning", "Deep Learning", "SQL", "Spark",
    ],
    "tools": ["Docker", "Kubernetes", "Git", "Airflow", "MLflow", "Jupyter"],
    "technologies": ["AWS", "FastAPI", "PostgreSQL", "OpenAI API", "Hugging Face", "Redis"],
    "language": "en",
    "raw_text": "Demo CV — AI/Data candidate profile, ML Engineer, Tel Aviv",
    "source_filename": "demo_cv.pdf",
    "is_demo": True,
}

DEMO_JOBS = [
    {
        "title": "Senior Machine Learning Engineer",
        "company": "Monday.com",
        "location": "Tel Aviv, Israel",
        "description": (
            "Build and deploy ML models that power product recommendations and workflow automation. "
            "Work with a cross-functional team on scalable training pipelines and A/B testing."
        ),
        "requirements": ["5+ years ML", "Python", "PyTorch", "Production ML", "SQL"],
        "skills": ["Python", "PyTorch", "MLOps", "SQL", "AWS", "Machine Learning"],
        "category": "AI / ML",
        "employment_type": "Full-time",
        "salary_range": "₪45,000–₪60,000",
        "url": "https://example.com/jobs/monday-ml",
        "language": "en",
    },
    {
        "title": "NLP / LLM Engineer",
        "company": "AI21 Labs",
        "location": "Tel Aviv, Israel",
        "description": (
            "Develop large language model applications, fine-tuning workflows, and evaluation harnesses. "
            "Collaborate with research on Hebrew and multilingual NLP."
        ),
        "requirements": ["NLP", "LLM", "Python", "PyTorch", "Transformers"],
        "skills": ["NLP", "LLM", "Python", "PyTorch", "LangChain", "Hugging Face"],
        "category": "AI / NLP",
        "employment_type": "Full-time",
        "salary_range": "₪50,000–₪70,000",
        "url": "https://example.com/jobs/ai21-nlp",
        "language": "en",
    },
    {
        "title": "Data Scientist — Growth",
        "company": "Wix",
        "location": "Tel Aviv / Hybrid",
        "description": (
            "Analyze user behavior, design experiments, and build predictive models for growth funnels. "
            "Partner with product and engineering on data-driven decisions."
        ),
        "requirements": ["SQL", "Python", "Statistics", "A/B Testing", "3+ years"],
        "skills": ["Python", "SQL", "Machine Learning", "Statistics", "Tableau"],
        "category": "Data Science",
        "employment_type": "Full-time",
        "salary_range": "₪38,000–₪52,000",
        "url": "https://example.com/jobs/wix-ds",
        "language": "en",
    },
    {
        "title": "מהנדס/ת למידת מכונה",
        "company": "Mobileye",
        "location": "ירושלים, ישראל",
        "description": (
            "פיתוח מודלים לראייה ממוחשבת ולמערכות נהיגה אוטונומית. עבודה עם צוותי R&D "
            "על אימון מודלים בקנה מידה גדול ופריסה לרכב."
        ),
        "requirements": ["Python", "Deep Learning", "Computer Vision", "C++", "PyTorch"],
        "skills": ["Python", "PyTorch", "Computer Vision", "Deep Learning", "CUDA"],
        "category": "AI / CV",
        "employment_type": "משרה מלאה",
        "salary_range": "₪48,000–₪65,000",
        "url": "https://example.com/jobs/mobileye-ml-he",
        "language": "he",
    },
    {
        "title": "MLOps Engineer",
        "company": "Riskified",
        "location": "Tel Aviv, Israel",
        "description": (
            "Own CI/CD for ML models, feature stores, monitoring, and infrastructure on AWS. "
            "Enable data scientists to ship models safely to production."
        ),
        "requirements": ["Docker", "Kubernetes", "AWS", "Python", "MLflow"],
        "skills": ["MLOps", "Docker", "Kubernetes", "AWS", "Python", "Airflow"],
        "category": "MLOps",
        "employment_type": "Full-time",
        "salary_range": "₪42,000–₪58,000",
        "url": "https://example.com/jobs/riskified-mlops",
        "language": "en",
    },
    {
        "title": "Data Engineer",
        "company": "Fiverr",
        "location": "Tel Aviv, Israel",
        "description": (
            "Design batch and streaming pipelines with Spark and Airflow. Build reliable data "
            "warehouses that feed analytics and ML teams."
        ),
        "requirements": ["Spark", "SQL", "Python", "Airflow", "ETL"],
        "skills": ["Spark", "SQL", "Python", "Airflow", "AWS", "Data Engineering"],
        "category": "Data Engineering",
        "employment_type": "Full-time",
        "salary_range": "₪40,000–₪55,000",
        "url": "https://example.com/jobs/fiverr-de",
        "language": "en",
    },
    {
        "title": "AI Automation Specialist",
        "company": "NICE Ltd",
        "location": "Ra'anana, Israel",
        "description": (
            "Build intelligent automation workflows using LLMs, RPA integrations, and internal APIs. "
            "Reduce manual ops for enterprise customers."
        ),
        "requirements": ["Automation", "Python", "LLM", "APIs", "RPA"],
        "skills": ["Automation", "Python", "LLM", "LangChain", "FastAPI", "RPA"],
        "category": "Automation",
        "employment_type": "Full-time",
        "salary_range": "₪35,000–₪48,000",
        "url": "https://example.com/jobs/nice-automation",
        "language": "en",
    },
    {
        "title": "Research Scientist — Generative AI",
        "company": "Intel Habana",
        "location": "Haifa, Israel",
        "description": (
            "Research efficient training and inference for generative models on AI accelerators. "
            "Publish and prototype novel architectures."
        ),
        "requirements": ["PhD or MSc", "Deep Learning", "PyTorch", "Research"],
        "skills": ["Deep Learning", "PyTorch", "Research", "CUDA", "Python"],
        "category": "Research",
        "employment_type": "Full-time",
        "salary_range": "₪55,000–₪75,000",
        "url": "https://example.com/jobs/intel-genai",
        "language": "en",
    },
    {
        "title": "Analytics Engineer",
        "company": "Taboola",
        "location": "Netanya, Israel",
        "description": (
            "Model business metrics in dbt, maintain Snowflake pipelines, and support self-serve BI "
            "for revenue and content teams."
        ),
        "requirements": ["dbt", "SQL", "Snowflake", "Python", "Looker"],
        "skills": ["dbt", "SQL", "Python", "Snowflake", "Data Engineering"],
        "category": "Analytics",
        "employment_type": "Full-time",
        "salary_range": "₪36,000–₪50,000",
        "url": "https://example.com/jobs/taboola-ae",
        "language": "en",
    },
    {
        "title": "Computer Vision Engineer",
        "company": "Trigo",
        "location": "Tel Aviv, Israel",
        "description": (
            "Develop real-time vision models for retail checkout-free stores. Optimize inference "
            "on edge devices and cloud GPUs."
        ),
        "requirements": ["Computer Vision", "Python", "PyTorch", "ONNX", "Edge ML"],
        "skills": ["Computer Vision", "PyTorch", "Python", "Deep Learning", "Docker"],
        "category": "AI / CV",
        "employment_type": "Full-time",
        "salary_range": "₪44,000–₪62,000",
        "url": "https://example.com/jobs/trigo-cv",
        "language": "en",
    },
]

# Curated match scores for demo CV — stable, presentation-ready narratives (no API keys).
# Keyed by company name; applied when Demo Mode activates.
DEMO_CURATED_MATCHES: dict[str, dict] = {
    "AI21 Labs": {
        "match_score": 92,
        "match_reason": (
            "Strong overlap in NLP, LLM, Python, and PyTorch. Your LangChain experience aligns "
            "with AI21's product stack. 5 years of experience matches senior role seniority."
        ),
        "matched_skills": ["NLP", "LLM", "Python", "PyTorch", "LangChain"],
        "missing_skills": ["Transformers"],
    },
    "Monday.com": {
        "match_score": 88,
        "match_reason": (
            "Excellent Python and PyTorch fit for production ML at Monday.com. "
            "SQL and AWS skills match core requirements."
        ),
        "matched_skills": ["Python", "PyTorch", "Machine Learning", "SQL", "AWS"],
        "missing_skills": ["MLOps"],
    },
    "NICE Ltd": {
        "match_score": 85,
        "match_reason": (
            "LLM and LangChain experience map directly to intelligent automation workflows. "
            "FastAPI in your stack supports enterprise API integrations."
        ),
        "matched_skills": ["Python", "LLM", "LangChain", "FastAPI", "Automation"],
        "missing_skills": ["RPA"],
    },
    "Riskified": {
        "match_score": 82,
        "match_reason": (
            "Docker, Kubernetes, and Airflow align with MLOps at Riskified. "
            "Python and AWS are core platform requirements."
        ),
        "matched_skills": ["Docker", "Kubernetes", "Python", "AWS", "Airflow"],
        "missing_skills": ["MLflow"],
    },
    "Trigo": {
        "match_score": 78,
        "match_reason": (
            "PyTorch and deep learning background fit Trigo's computer vision team. "
            "Highlight edge deployment experience if available."
        ),
        "matched_skills": ["Computer Vision", "PyTorch", "Python", "Deep Learning", "Docker"],
        "missing_skills": ["ONNX", "Edge ML"],
    },
    "Mobileye": {
        "match_score": 76,
        "match_reason": (
            "Deep learning and PyTorch match Mobileye's autonomous driving ML team. "
            "Hebrew posting — strong local market fit."
        ),
        "matched_skills": ["Python", "PyTorch", "Deep Learning", "Computer Vision"],
        "missing_skills": ["C++", "CUDA"],
    },
    "Intel Habana": {
        "match_score": 74,
        "match_reason": (
            "Research-oriented generative AI role — your deep learning stack is relevant. "
            "PhD may be preferred for this seniority level."
        ),
        "matched_skills": ["Deep Learning", "PyTorch", "Python"],
        "missing_skills": ["Research publications"],
    },
    "Wix": {
        "match_score": 71,
        "match_reason": (
            "Solid Python, SQL, and ML foundation for growth data science at Wix. "
            "Emphasize A/B testing and statistics on your CV."
        ),
        "matched_skills": ["Python", "SQL", "Machine Learning"],
        "missing_skills": ["Tableau", "A/B Testing"],
    },
    "Fiverr": {
        "match_score": 68,
        "match_reason": (
            "Spark and Airflow overlap with your data engineering exposure. "
            "Strong SQL and Python foundation for pipeline work."
        ),
        "matched_skills": ["Spark", "SQL", "Python", "Airflow"],
        "missing_skills": ["ETL", "Data Engineering"],
    },
    "Taboola": {
        "match_score": 62,
        "match_reason": (
            "SQL and Python match analytics engineering at Taboola. "
            "dbt and Snowflake are quick upskill opportunities."
        ),
        "matched_skills": ["SQL", "Python"],
        "missing_skills": ["dbt", "Snowflake", "Looker"],
    },
}
