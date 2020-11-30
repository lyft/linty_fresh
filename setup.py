from setuptools import find_packages, setup


setup(
    name='linty-fresh',
    version='0.7.0',
    license='apache',
    description="""
        This package reports style violations for a Github PR as comments.
    """,
    author='Roy Williams',
    author_email='rwilliams@lyft.com',
    url='https://github.com/lyft/linty_fresh',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    setup_requires=[
        'flake8>=2.2.3, <3.0.0',
        'flake8-blind-except==0.1.1',
        'flake8-debugger>=1.4.0, <4.0.0',
        'flake8-import-order>=0.10, <0.19',
        'flake8-quotes>=0.8.1, <3.2.0',
        'pycodestyle>=2.0.0, <2.1.0',
    ],
    install_requires=[
        'aiohttp>=3.6.2, <4.0.0',
        'typing>=3.5.0.1, <4.0.0;python_version<"3.7"',
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
)
