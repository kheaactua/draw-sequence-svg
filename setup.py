from setuptools import setup
from setuptools import find_packages

setup(name='funniest',
    version='0.1',
    description='Rudimentary module to generate sequence diagrams',
    url='https://github.com/kheaactua/draw-sequence-svg',
    author='Matthew Russell',
    author_email='matthew.g.russell@gmail.com',
    license='MIT',
    packages=find_packages(),
    entry_points = {
      'console_scripts': [
          'generateSequenceDiag = dsd.generateSequenceDiag:main',
          'generateWireSharkDisplayFilters = dsd.generateWireSharkDisplayFilters:main',
      ]
    },
    zip_safe=False
)