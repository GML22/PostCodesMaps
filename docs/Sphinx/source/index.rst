PostCodesMaps
=============

PostCodesMaps is an application written in Python that creates postcode maps of regions in Poland based on a set of address points from the Polish National Register of Boundaries Database (also known as the PRG database). As part of PostCodeMaps, a website has been created that allows visualisation of the generated postcodes maps.

PostCodesMaps creates SQL database containing all address points and buildings in Poland by parsing files in Geography Markup Language format into SQL tables. The main data source of GeocoderPL is The National Register of Boundaries Database (also known as PRG database) - state-maintained reference database of all address points in Poland (including administrative division of the country):

- https://dane.gov.pl/pl/dataset/726,panstwowy-rejestr-granic-i-powierzchni-jednostek-podziaow-terytorialnych-kraju/resource/29538

- https://dane.gov.pl/pl/dataset/726,panstwowy-rejestr-granic-i-powierzchni-jednostek-podziaow-terytorialnych-kraju/resource/29515

The resulting database was used to generate postcode maps of Poland (in .shp and .geojson formats), which were then overlaid on Leaflet JS maps for visualisation purposes.

.. toctree::
   :maxdepth: 4
   :caption: Contents:

   pcm_db
   pcm_parser
   pcm_utilities

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
