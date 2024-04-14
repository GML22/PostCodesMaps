# PostCodesMaps
[This project was completed in April 2024]

<p align="justify">
PostCodesMaps is an application written in Python that creates postcode maps of regions in Poland based on a set of address points from the Polish National Register of Boundaries Database (also known as the PRG database). As part of PostCodeMaps, a website has been created that allows visualisation of the generated postcodes maps:
https://gml22.github.io/PostCodesMaps
</p>

<p align="center">
  <img width=75% height=75% src="/imgs/post_codes_maps_1.gif"/>
</p>

<p align="justify">
PostCodesMaps creates SQL database containing all address points in Poland by parsing files in Geography Markup Language format into SQL tables. The main data source of PostCodesMaps is The National Register of Boundaries Database (also known as PRG database) - state-maintained reference database of all address points in Poland (including administrative division of the country):

- https://dane.gov.pl/pl/dataset/726,panstwowy-rejestr-granic-i-powierzchni-jednostek-podziaow-terytorialnych-kraju/resource/29538

- https://dane.gov.pl/pl/dataset/726,panstwowy-rejestr-granic-i-powierzchni-jednostek-podziaow-terytorialnych-kraju/resource/29515
</p>

<p align="center">
  <img width=75% height=75% src="/imgs/post_codes_maps_2.gif"/>
</p>

<p align="justify">
The resulting database was used to generate postcode maps of Poland (in .shp and .geojson formats), which were then overlaid on OpenStreetMap for visualisation purposes.
</p>

<p align="center">
  <img width=75% height=75% src="/imgs/post_codes_maps_3.gif"/>
</p>

<p align="left">
The technical documentation of PostCodesMaps is available at:
  
- https://github.com/GML22/PostCodesMaps/blob/dc1ef989bcafd5bbf93876a6aeceb2905ab0cc58/docs/PostCodesMaps%20-%20technical%20documentation.pdf
</p>
