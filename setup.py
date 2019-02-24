from setuptools import setup, find_packages

with open('./requirements.txt') as reqs:
    requirements = [line.rstrip() for line in reqs if 'git' not in line]

setup(name="satellite-czml-propagator",
      version='0.1',
      author='Jeff Albrecht',
      author_email='geospatialjeff@gmail.com',
      packages=find_packages(),
      install_requires = requirements,
      include_package_data=True
      )