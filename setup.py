import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Fairy_WeChat-0.0.1",
    version="0.0.1",
    author="Qier LU",
    author_email="lvqier@gmail.com",
    description="Yet another implemention of WeChat Python SDK for Flask",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lvqier/Fairy-WeChat",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL-3.0 License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    python_requires='>=3.5',
    install_requires=[
        "pycrypto"
    ]
)
