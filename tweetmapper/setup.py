from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))


version = '0.1'

install_requires = [
    # List your project dependencies here.
    # For more details, see:
    # http://packages.python.org/distribute/setuptools.html#declaring-dependencies
]


setup(name='tweetmapper',
    version=version,
    description="Flask based API to return geolocated tweets",
    classifiers=[
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    ],
    keywords='twitter Flask',
    author='Bryan Wilson',
    author_email='bryanlandia@gmail.com',
    url='github.com/bryanlandia',
    license='GPL',
    packages=find_packages('src'),
    package_dir = {'': 'src'},include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    entry_points={
        'console_scripts':
            ['tweetmapper=tweetmapper:main']
    }
)
