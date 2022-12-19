from setuptools import setup

setup(
    name='postcodesmaps',
    version='1.0',
    description='PostCodesMaps is a Python-written application that creates post code maps of regions in Poland based' +
                ' on a set of address points from the Polish National Register of Boundaries Database (a.k.a. PRG ' +
                'database). As part of PostCodeMaps, a website was created that enables the visualization of the ' +
                'generated post codes by overlaying them on Google maps.',
    author='Mateusz Gomulski',
    author_email='mateusz.gomulski@gmail.com',
    license="MIT License",
    keywords="postal codes maps Poland python numpy javascript leafletjs search-engine sqlalchemy gdal-python",
    url="https://github.com/GML22/PostCodesMaps",
    packages=['postcodesmaps'],
    install_requires=['setuptools', 'sqlalchemy', 'python-dotenv', 'fiona', 'numpy', 'pandas', 'lxml', 'matplotlib',
                      'scipy', 'shapely', 'tqdm', 'unidecode'],
)
