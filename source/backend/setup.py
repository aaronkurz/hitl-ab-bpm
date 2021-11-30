from setuptools import find_packages, setup

setup(
    name='bprl',
    version='1.0.0',
    packages=find_packages(),
    #include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask==2.0.2',
        'requests==2.26.0',
        'Flask-SQLAlchemy==2.5.1',
        'psycopg2-binary==2.9.2',
        'python-dotenv==0.19.2'
    ],
)