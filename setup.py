from setuptools import setup, find_namespace_packages

setup(
    name="solana-orca-bot",
    version="0.1",
    packages=find_namespace_packages(include=['src*']),
    package_dir={'': '.'},
    python_requires='>=3.9',
    install_requires=[
        'solana==0.30.2',
        'solders==0.18.1',
        'anchorpy==0.18.0',
        'whirlpool-essentials==0.1.0',
        'pandas',
        'rich',
        'base58',
        'python-dotenv'
    ]
) 