from setuptools import find_packages, setup

setup(
    name="house_price_pipeline",
    version="1.0.0",
    description="End-to-end MLOps pipeline for real-estate price prediction",
    packages=find_packages(include=["src", "src.*"]),
    python_requires=">=3.10",
)
