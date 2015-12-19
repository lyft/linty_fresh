from setuptools import find_packages, setup


def get_version(file_name='linty_fresh/__init__.py'):
    with open(file_name) as f:
        for line in f.read().splitlines():
            if line.startswith('__version__'):
                return line.split('=')[-1].strip(" '")

setup(
    name='linty-fresh',
    version=get_version(),
    license='apache',
    description='''
        This package reports style violations for a Github PR as comments.
    ''',
    author='Roy Williams',
    author_email='rwilliams@lyft.com',
    url='https://github.com/lyft/linty-fresh',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    setup_requires=[
        'flake8>=2.2.3',
        'flake8-blind-except>=0.1.0',
        'flake8-debugger>=1.4.0',
        'flake8-import-order>=0.6.1',
        'flake8-quotes>=0.1.1',
        'pep8==1.5.7',
        'pep8-naming>=0.3.3',
    ],
    install_requires=[
        'aiohttp>=0.19.0',
        'typing>=3.5.0.1',
    ],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Quality Assurance',
    ],
    entry_points={
        'console_scripts': ['linty_fresh = linty_fresh.main:main'],
    },
    tests_require=[
        'nose>=1.3.3',
        'mock>=1.0.1',
    ],
    test_suite='nose.collector',
)
