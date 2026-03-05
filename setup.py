from setuptools import setup, find_packages

setup(
    name='phone_extractor',
    version='3.0.0',
    description='GUI application for extracting and processing phone numbers from text',
    py_modules=['phone_extractor'],
    python_requires='>=3.9',
    install_requires=[
        'tkinterdnd2>=0.3',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0',
            'flake8>=6.0',
            'pyinstaller>=5.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'phone-extractor=phone_extractor:main',
        ],
    },
)
