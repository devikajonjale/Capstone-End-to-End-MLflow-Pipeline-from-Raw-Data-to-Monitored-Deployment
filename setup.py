from setuptools import setup, find_packages

setup(
    name="house_price_pipeline",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy",
        "scikit-learn",
        "mlflow",
        "prefect",
        "pyyaml",
        "pytest",
        "evidently",
        "fastapi",
        "uvicorn",
        "prometheus-client",
        "requests",
        "dvc",
        "pydantic"
    ],
    author="Devika Jonjale & Saachi Shinde",
    description="Real-estate price prediction pipeline MLOps project",
)
