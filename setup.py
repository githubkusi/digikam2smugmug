from setuptools import setup, find_packages

setup(
    name="digikam2smugmug",
    version="0.0.1",
    author="Markus Leuthold",
    author_email="github@titlis.org",
    packages=find_packages(),
    install_requires=["iso8601", "wheel", "mysqlclient", "requests", "requests", "etaprogress", "pyyaml", "rauth @ git+https://github.com/githubkusi/rauth.git@binarydata"],
    url="https://github.com/adhawkins/smugmugv2py",
    license="GPL",
    description="Upload Digikam photos and metadata to Smugmug",
    long_description=open("README.md").read(),
    entry_points={"console_scripts": ["digikam2smugmug=smugmugv2py.digikam2smugmug:main"]} 
)
