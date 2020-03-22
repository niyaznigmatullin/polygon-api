import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="polygon-api",
    version="0.0.1",
    author="Niyaz Nigmatullin",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/niyaznigmatullin/polygon-api",
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
    install_requires=['requests']
)
