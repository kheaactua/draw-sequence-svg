from setuptools import setup
from setuptools import find_packages

setup(
    name='dsd',
    version='0.2',
    description='Rudimentary module to generate sequence diagrams',
    url='https://github.com/kheaactua/draw-sequence-svg',
    author='Matthew Russell',
    author_email='matthew.russell@comtechtel.com',
    license='MIT',
    packages=find_packages(),
    install_requires=['aenum', 'pyshark'],
    python_requires='>=3',
    package_data={'': ['data/template.svg']},
    include_package_data=True,
    entry_points = {
      'console_scripts': [
          'generateSequenceDiag = dsd.generateSequenceDiag:main',
          'generateWireSharkDisplayFilters = dsd.generateWireSharkDisplayFilters:main',
          'queryCaptureLogs = dsd.queryLogs:main',
      ]
    },
    zip_safe=False
)
