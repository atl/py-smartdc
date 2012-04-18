from setuptools import setup, find_packages

setup(
    name='smartdc',
    version='0.1.0',
    description="SmartDataCenter CloudAPI connector",
    long_description="Joyent SmartDataCenter connection using http-signature authentication via kennethreitz's Requests",
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Boot",
        "Topic :: System :: Systems Administration",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        
    ],
    keywords='http,web,joyent,admin,operations',
    author='Adam T. Lindsay',
    author_email='a.lindsay+github@gmail.com',
    url='https://github.com/atl/py-smartdc',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['setuptools','requests','pycrypto'],
)
