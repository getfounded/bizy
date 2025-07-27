#!/usr/bin/env python
"""
Setup script for behave-ai-orchestration

A Behave plugin that provides step definitions and patterns for testing
AI framework coordination and business logic orchestration.
"""

from setuptools import setup, find_packages
import os

# Read README file
current_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(current_dir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open(os.path.join(current_dir, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='bizy-behave',
    version='0.1.0',
    description='Behave plugin for testing Bizy AI framework coordination',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Bizy Team',
    author_email='team@bizy.work',
    url='https://github.com/getfounded/bizy',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'behave_ai_orchestration': [
            'templates/*.feature',
            'examples/*.feature',
            'fixtures/*.json',
        ],
    },
    install_requires=requirements,
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Testing :: BDD',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
    keywords='behave bdd ai testing orchestration bizy langchain temporal semantic-kernel mcp',
    entry_points={
        'console_scripts': [
            'behave-ai-demo=behave_ai_orchestration.cli:demo_command',
            'behave-ai-validate=behave_ai_orchestration.cli:validate_command',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/getfounded/bizy/issues',
        'Source': 'https://github.com/getfounded/bizy',
        'Documentation': 'https://docs.bizy.work/behave',
    },
)
