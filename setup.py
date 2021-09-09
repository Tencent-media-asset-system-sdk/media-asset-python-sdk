import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="media-asset-python-sdk",
    version="1.0.0",
    author="maopengwang",
    author_email="maopengwang@tencent.com",
    description="Media AI Middle and Taiwan Media Management System SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.woa.com/xlab_dev/ai-media/media-asset-python-sdk.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
