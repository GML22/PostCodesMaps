from setuptools import setup

setup(
    name='postcodesmaps',
    version='1.0',
    description='GeocoderPL is an application written in Python, which can be used for geocoding address points in ' +
                'Poland along with the possibility to display basic information about a given address point and the ' +
                'building assigned to this address. GeocoderPL has a form of search engine with three map layers: ' +
                'OpenStreetMap, Google Maps and Stamens Map.',
    author='Mateusz Gomulski',
    author_email='mateusz.gomulski@gmail.com',
    license="MIT License",
    keywords="search-engine geocoding numpy pyqt5 geospatial sqlite3 gdal-python superpermutation folium-maps",
    url="https://github.com/GML22/GeocoderPL",
    packages=['postcodesmaps'],
    install_requires=['folium', 'numpy', 'pyqt5', 'unidecode', 'pyproj', 'lxml', 'geocoder', 'pandas', 'matplotlib',
                      'setuptools', 'sqlalchemy', 'python-dotenv'],
)
