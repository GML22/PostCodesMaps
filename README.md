# PostCodesMaps

<p align="justify">
PostCodesMaps is an application written in Python that creates postcode maps of regions in Poland based on a set of address points from the Polish National Register of Boundaries Database (also known as the PRG database). As part of PostCodeMaps, a website has been created that allows visualisation of the generated postcodes maps.
</p>

<p align="justify">
PostCodesMaps creates SQL database containing all address points in Poland by parsing files in Geography Markup Language format into SQL tables. The main data source of GeocoderPL is The National Register of Boundaries Database (also known as PRG database) - state-maintained reference database of all address points in Poland (including administrative division of the country):

- https://dane.gov.pl/pl/dataset/726,panstwowy-rejestr-granic-i-powierzchni-jednostek-podziaow-terytorialnych-kraju/resource/29538

- https://dane.gov.pl/pl/dataset/726,panstwowy-rejestr-granic-i-powierzchni-jednostek-podziaow-terytorialnych-kraju/resource/29515
</p>

<p align="justify">
The resulting database was used to generate postcode maps of Poland (in .shp and .geojson formats), which were then overlaid on Google Maps for visualisation purposes.
</p>

<p align="left">
The technical documentation of PostCodesMaps is available at:
  
- https://github.com/GML22/PostCodesMaps/blob/a743c3c1afd7012df322a8925db6330ec6d8aeb8/docs/PostCodesMaps%20-%20technical%20documentation.pdf
</p>
