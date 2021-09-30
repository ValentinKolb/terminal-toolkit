import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='terminal-toolkit',
    version='0.0.1',
    author='Valentin Kolb',
    description="Small library for writing terminal app's",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir="src",
    url='https://github.com/ValentinKolb/terminal-toolkit',
    license='MIT',
    packages=['terminal-toolkit'],
    python_requires=">=3.9",
    platforms="unix, linux, osx",
    install_requires=[
        'dacite==1.6.0',
        'webcolors==1.11.1'
    ]
)