import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="da4py",
    version="0.0.3",
    author="Boltenhagen Mathilde",
    author_email="boltenhagen@lsv.fr",
    description="da4py implements state-of-the-art Process Mining methods over SAT encoding. An Ocaml version is Darksider.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BoltMaud/da4py",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)