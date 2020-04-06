import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
     name='backtraderbd',  
     version='0.0.1',
     author="Raisul Islam",
     author_email="raisul.exe@gmail.com",
     description="A backtrader utility for dse",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/rochi88/backtraderbd",
     packages=setuptools.find_packages(),
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
     python_requires='>=3.6',
 )
