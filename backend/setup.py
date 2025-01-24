from setuptools import setup, find_packages

setup(
    name="pdf-rag-agent",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.12",
    install_requires=[
        "fastapi",
        "pydantic",
        "pydantic-settings",
        "pydantic-ai[logfire]",
        "uvicorn",
        "python-multipart",
        "python-dotenv",
        "logfire",
        "openai",
        "httpx",
        "numpy",
        "tiktoken",
        "PyMuPDF",
        "pdfplumber",
        "pandas"
    ]
)
