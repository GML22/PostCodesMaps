""" PostCodesMaps setup file """

import setuptools

setuptools.setup(
    name='postcodesmaps',
    version='1.0',
    description='PostCodesMaps is a Python-written application that creates post code maps of regions in Poland ' +
                'based on a set of address points from the Polish National Register of Boundaries Database ' +
                ' (a.k.a. PRG database). As part of PostCodeMaps, a website was created that enables the ' +
                'visualization of the generated post codes by overlaying them on Google maps.',
    author='Mateusz Gomulski',
    author_email='mateusz.gomulski@gmail.com',
    license="MIT License",
    keywords="post codes maps Poland python numpy javascript leafletjs search-engine sqlalchemy gdal-python",
    url="https://github.com/GML22/PostCodesMaps",
    python_requires='>=3.8',
    packages=setuptools.find_packages(include=['postcodesmaps']),
    install_requires=['numpy~=1.20.1',
                      'unidecode~=1.3.2',
                      'lxml~=4.6.3',
                      'pandas~=1.2.4',
                      'matplotlib~=3.5.0',
                      'setuptools>=52.0.0',
                      'sqlalchemy>=1.4.7',
                      'python-dotenv>=0.19.2',
                      'fiona~=1.8.20',
                      'shapely~=1.7.1',
                      'tqdm~=4.64.0',
                      'scipy~=1.6.2'],
)
