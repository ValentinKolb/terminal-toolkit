import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='terminal',
    version='0.0.3',
    author='Valentin Kolb',
    description="Small library for writing terminal app's",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/ValentinKolb/terminal-toolkit',
    license='MIT',
    packages=["terminal"],
    python_requires=">=3.9",
    platforms="unix",
    install_requires=[
        'webcolors==1.11.1'
    ]
)
