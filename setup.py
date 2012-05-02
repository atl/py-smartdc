from setuptools import setup, find_packages
import versioneer

versioneer.versionfile_source = 'smartdc/_version.py'
versioneer.versionfile_build = 'smartdc/_version.py'
versioneer.tag_prefix = 'v' # tags are like 1.2.0
versioneer.parentdir_prefix = 'smartdc-' # dirname like 'myproject-1.2.0'

with open('README.rst') as file:
    long_description = file.read()
with open('CHANGES.rst') as file:
    long_description += '\n\n' + file.read()

setup(
    name='smartdc',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Joyent SmartDataCenter CloudAPI connector using http-signature authentication via Requests",
    long_description=long_description,
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
        "Development Status :: 3 - Alpha",
    ],
    keywords='http,web,joyent,admin,operations',
    author='Adam T. Lindsay',
    author_email='a.lindsay+github@gmail.com',
    url='https://github.com/atl/py-smartdc',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,
    install_requires=['requests','http-signature'],
)
