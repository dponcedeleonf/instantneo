from setuptools import setup, find_packages

setup(
    name='instantneo',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'openai',
        'json',
        'inspect',
        'typing',
    ],
    author='Diego Ponce de León Franco',
    author_email='dponcedeleonf@gmail.com',
    description='',  # Puedes añadir una descripción en el futuro si lo deseas
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/dponcedeleonf/instantneo',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
    ],
    keywords='openai, agent, neo, matrix, wrapper',
    project_urls={
        'Bug Reports': 'https://github.com/dponcedeleonf/instantneo/issues', 
        'Source': 'https://github.com/dponcedeleonf/instantneo',  
    },
)
