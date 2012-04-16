from setuptools import setup, find_packages

setup(
    name='smartdc',
    version='0.1.0',
    description="SmartDataCenter CloudAPI connector",
    long_description="Joyent SmartDataCenter connection using http-signature authentication via kennethreitz's Requests",
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Environment :: Web Environment",
    ],
    keywords='http,web,joyent,admin,operations',
    author='Adam Lindsay',
    author_email='a.lindsay+github@gmail.com',
    url='http://github.com/atl/py-smartdc',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['setuptools','requests','pycrypto'],
)
