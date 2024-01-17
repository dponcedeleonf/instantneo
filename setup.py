from setuptools import setup, find_packages

setup(
    name='instantneo',
    version='1.1.0',
    packages=find_packages(),
    install_requires=[
        'openai',
        'typing',
    ],
    author='Diego Ponce de León Franco',
    author_email='dponcedeleonf@gmail.com',
    description='', 
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/dponcedeleonf/instantneo',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
    ],
    keywords='openai, agent, wrapper',
    project_urls={
        'Bug Reports': 'https://github.com/dponcedeleonf/instantneo/issues', 
        'Source': 'https://github.com/dponcedeleonf/instantneo',  
    },
)
