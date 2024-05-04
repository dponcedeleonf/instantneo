from setuptools import setup, find_packages

setup(
    name='instantneo',
    version='0.2.0-dev',
    packages=find_packages() + ['adapters'],  # Agrega 'adapters' a la lista de paquetes
    install_requires=[
        'openai',
        'typing',
        'anthropic'
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
