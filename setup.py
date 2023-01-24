import setuptools


def readme():
    with open("README.md", "r") as f:
        return f.read()


setuptools.setup(
    name="shopihq_library_package",
    version="1.0.0",
    author="Burkay",
    author_email="burkay.ubuntu@gmail.com",
    description="",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/burkayelbek/shopihq_library_package",
    packages=setuptools.find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "tests/"]),
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        'Programming Language :: Python',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True
)
