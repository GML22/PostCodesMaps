""" Module that collects variety utility functions for geospatial programming """

import functools
import glob
import json
import logging
import math
import os
import pickle
import re
import time
import zipfile
from functools import lru_cache
from itertools import groupby
from typing import Dict, List, Any, Callable

import fiona
import numpy as np
import ogr2ogr
import pandas as pd
import pyproj
import shapely
from fiona.crs import from_epsg
from lxml import etree
from matplotlib import path
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from scipy.spatial import distance
from scipy.spatial.distance import pdist, squareform
from shapely import wkt
from shapely.geometry import mapping, shape, Polygon, MultiPolygon
from shapely.ops import unary_union, transform
from sqlalchemy.orm import Session
from tqdm import tqdm
from unidecode import unidecode

from pcm_db import PRG, SQL_ENGINE


def create_logger(name: str) -> logging.Logger:
    """
    Function that creates logging file

    :param name: Name of logger
    :return: Logger object
    """

    # Deklaracja najwazniejszych sciezek
    parent_path = os.path.join(os.getcwd()[:os.getcwd().index("PostCodesMaps")], "PostCodesMaps")

    # Tworzymy plik loggera
    logging.basicConfig(filename=os.path.join(parent_path, "files\\logs_pcm.log"), level=logging.DEBUG,
                        format='%(asctime)s %(name)s[%(process)d] %(levelname)s: %(message)s',
                        datefmt='%H:%M:%S', filemode="a")

    # Podstawowe funkcje
    handler = logging.StreamHandler()
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    # Wyłączamy logowanie z określonych modułów
    disable_loggers = ['fiona.env', 'fiona.ogrext', 'fiona._env', 'fiona.collection', 'fiona._shim', 'fiona._crs',
                       'shapely.geos']

    for logger_name in disable_loggers:
        logger = logging.getLogger(logger_name)
        logger.disabled = True

    return logger


def time_decorator(func) -> Callable:
    """
    Decorator that logs information about time of function execution

    :param func: Function call that should be wrapped
    :return: Time wrapper function call
    """

    @functools.wraps(func)
    def time_wrapper(*args, **kwargs):
        """
        Wrapper that calculates function execution time

        :param args: First set of arguments of wrapped function
        :param kwargs: Second set of arguments of wrapped function
        :return: Values returned by a wrapped function
        """

        start_time = time.time()
        logger = logging.getLogger('root')
        logger.info("0. Rozpoczęcie wykonywania funkcji '" + func.__name__ + "'")

        # Wykonujemy główną fukcję
        ret_vals = func(*args, **kwargs)
        time_passed = time.time() - start_time
        logger.info("1. Łączny czas wykonywania funkcji '" + func.__name__ + "' - {:.2f} sekundy".format(time_passed))

        return ret_vals

    return time_wrapper


def clear_xml_node(curr_node: etree.Element) -> None:
    """
    Function that clears unnecessary XML nodes from RAM memory

    :param curr_node: Current XML node
    :return: Function does not return any values
    """

    curr_node.clear()

    for ancestor in curr_node.xpath('ancestor-or-self::*'):
        while ancestor.getprevious() is not None:
            del ancestor.getparent()[0]


def csv_to_dict(c_path: str, pl_names_dict: Dict[str, str]) -> Dict[str, str]:
    """
    Function that imports CSV file and creates dictionairy from first two columns of that file

    :param c_path: Path of the CSV file that should be read to dictionary
    :param  pl_names_dict: Dictionary containing Polish names of regions
    :return: Dictionary read from CSV file and corrected using "pl_names_dict" dictionairy
    """

    try:
        x_kod = pd.read_csv(c_path, sep=";", dtype=str, engine='c', header=None, low_memory=False,
                            encoding='cp1250').values
    except FileNotFoundError:
        raise Exception("Pod adresem: '" + c_path + "' nie ma pliku potrzebnego pliku. Uzupełnij ten plik i  uruchom " +
                        "program ponownie!")

    fin_dict = {}

    for row in x_kod:
        c_name = row[1]
        undc_name = unidecode(row[1]).upper()
        pl_names_dict[undc_name] = c_name
        fin_dict[row[0]] = undc_name

    return fin_dict


@time_decorator
def create_postal_codes_shps() -> None:
    """
    Function that creates shapefiles of postal codes zones

    :return: Function does not return any values
    """

    # Wczytujemy słownik kodów teryt i kodów pocztowych
    with open(os.path.join(os.environ["PARENT_PATH"], os.environ['TERYT_PC_PATH']), 'rb') as f:
        teryt_pc_dict = pickle.load(f)

    # Wczytujemy słownik kodów pocztowych i sciezek granic gmin
    shp_fold = os.path.join(os.environ["PARENT_PATH"], os.environ['GMN_SHP_FOLD'])
    prg_cols = [PRG.kod_pocztowy, PRG.dlugosc, PRG.szerokosc]
    teryt_gmn_paths_dict = create_geom_refs_dict()
    wod_pow_shape = read_wod_pow_shapes()
    curr_pc = [1]

    # Finalne atrybuty zapisywanych plikow SHP
    fin_schema = {'geometry': 'Polygon', 'properties': {'Value': 'int', 'Name': 'str', "PC_NUM": 'int', "Gmina": 'str',
                                                        'TERYT': 'str'}}

    # Tworzymy folder 'SHAPES'
    if not os.path.exists(shp_fold):
        os.mkdir(shp_fold)

    # Ustalamy listę już wygenerowanych mapek
    c_teryts = [file1[(file1.rindex("\\") + 1):file1.index("_")] for file1 in
                glob.glob(os.path.join(shp_fold, "*.shp")) if "" in file1]

    for teryt_code, paths_list in tqdm(teryt_gmn_paths_dict.items(), desc='Generating postcodes shapefiles: '):
        # Jeżeli mapa została już wcześniej wygenerowana to przechodzimy do kolejnego kodu teryt
        if teryt_code in c_teryts:
            continue

        # Lista oczekiwanych kodów pocztowych dla danego kodu TERYT
        c_post_cods = teryt_pc_dict[teryt_code]

        if len(c_post_cods) < 2:
            sngl_pc_zone_shp(teryt_code, paths_list, c_post_cods, shp_fold)
        else:
            mult_pc_zones_shps(teryt_code, paths_list, c_post_cods, prg_cols, shp_fold)

    # Laczymy wielokaty kodow pocztowych po wojewodztwach i zapisujemy je na dysku twardym
    save_merged_shps(shp_fold, wod_pow_shape, teryt_gmn_paths_dict, fin_schema, curr_pc)


@time_decorator
def save_merged_shps(shp_fold: str, wod_pow_shape: shapely.geometry.Polygon, teryt_gmn_paths_dict: Dict[str, List[Any]],
                     fin_schema: Dict[str, Any], curr_pc: List[int]) -> None:
    """
    Function that merges postcodes shapefiles by provinces and save them to the hard disk

    :param shp_fold: The path to the folder where the shapefiles will be saved
    :param wod_pow_shape: Polygons representing surface water shapes
    :param teryt_gmn_paths_dict: Dictionairy with TERYT codes and boundary paths of municipalities
    :param fin_schema: Dictionairy containing final parameters of SHP files
    :param curr_pc: List for counting address points for a given postcode
    :return: Function does not return any values
    """

    # Tworzymy ściezke do wielokatow kodow pocztowych wv formacie TXT
    txt_fold = os.path.join(os.environ["PARENT_PATH"], os.environ['PC_TXT_FOLD'])

    if not os.path.exists(txt_fold):
        os.mkdir(txt_fold)

    # Wczytujemy słowniki kodów TERYT województw i gmin
    pl_names_dict = {}
    woj_teryt_dict = csv_to_dict(os.path.join(os.environ["PARENT_PATH"], os.environ['TERYT_WOJ_PATH']), pl_names_dict)
    pow_teryt_dict = csv_to_dict(os.path.join(os.environ["PARENT_PATH"], os.environ['TERYT_POW_PATH']), pl_names_dict)
    gmn_teryt_dict = csv_to_dict(os.path.join(os.environ["PARENT_PATH"], os.environ['TERYT_GMN_PATH']), pl_names_dict)

    with open(os.path.join(txt_fold, "PL_NAMES.txt"), 'w') as file:
        file.write(json.dumps(pl_names_dict))

    # Z folderu z shapefile'ami wybieramy tylko pliki kończące sie na ".shp"
    shp_list = glob.glob(os.path.join(shp_fold, "*.shp"))

    # Tworzymy ściezke do finalnych map
    fin_maps_path = os.path.join(os.environ["PARENT_PATH"], "fin_maps")

    # Transformacje układów współrzędnych
    curr_srs = 'EPSG:' + os.environ['PL_CRDS']
    fin_srs = 'EPSG:' + os.environ['WORLD_CRDS']
    coords_prec = "COORDINATE_PRECISION=" + os.environ['COORDS_PREC']
    reproject_srs = pyproj.Transformer.from_crs(curr_srs, fin_srs, always_xy=True).transform

    # Tworzymy słownik z finalnymi wielokatami dla calej Polski oraz z liczbami punktów adresowych
    all_pl_pc_dict = {}
    add_pts_nums = {}

    if not os.path.exists(fin_maps_path):
        os.mkdir(fin_maps_path)

    for teryt, woj_name in woj_teryt_dict.items():
        print("\n" + woj_name)
        teryt_arr = np.asarray([(t_pth, os.path.basename(t_pth)[:7]) for t_pth in shp_list if "\\" + teryt in t_pth])

        if len(teryt_arr) == 0:
            continue

        # Jeżeli dany folder istnieje to przechodzimy do kolejnego wojewodztwa
        if not os.path.exists(os.path.join(fin_maps_path, teryt + "_" + woj_name)):
            os.mkdir(os.path.join(fin_maps_path, teryt + "_" + woj_name))
        else:
            continue

        # Tworzymy pomocnicze słowniki
        fin_geom_dict = {}
        pc_dict = {}

        # Finalna nazwa plikow i sciezki
        maps_name = teryt + "_" + woj_name + "\\" + teryt + "_" + woj_name + "_ALL_PC_"
        mrgd_plg_path_shp = os.path.join(fin_maps_path, maps_name + os.environ['PL_CRDS'] + ".shp")
        mrgd_plg_path_geoj = os.path.join(fin_maps_path, maps_name + os.environ['WORLD_CRDS'] + ".geojson")

        # Przechodzimy przez wszystkie wielokaty dla danego wojewodztwa i dodajemy je do slownika 'fin_geom_dict'
        create_geom_dict(fin_geom_dict, teryt_arr, teryt_gmn_paths_dict, gmn_teryt_dict)

        # Przechodzimy przez wszystkie regiony w slowniku 'fin_geom_dict' i pozbywamy się małych polygonow pokrywajacych
        # sie w calosic z innymi polygonami
        rmv_sml_ovrlp_polygs(fin_geom_dict)

        # Wyznaczamy finalny slownik kształtow regionow kodow pocztowych
        prepare_merging(fin_geom_dict, wod_pow_shape, pc_dict, curr_pc)

        # Zapisujemy ksztalty regionow kodow pocztowych do lacznego pliku SHP
        merge_all_shps_save(mrgd_plg_path_shp, mrgd_plg_path_geoj, pc_dict, all_pl_pc_dict, fin_schema, fin_srs,
                            coords_prec, add_pts_nums)

    # Zapisujemy laczny plik SHP dla wszystkich wielokatow kodow pocztowych
    if all_pl_pc_dict:
        print("\nPOLSKA")

        if not os.path.exists(os.path.join(fin_maps_path, "00_POLSKA")):
            os.mkdir(os.path.join(fin_maps_path, "00_POLSKA"))

        gmn_pow_nms_dict = {}
        all_pl_shps_path = os.path.join(fin_maps_path, "00_POLSKA\\00_POLSKA_ALL_PC_" + os.environ['PL_CRDS'] + ".shp")

        # Zapisujemy wielokaty do SHP
        with fiona.open(all_pl_shps_path, mode='w', crs=from_epsg(int(os.environ['PL_CRDS'])), driver='ESRI Shapefile',
                        schema=fin_schema) as output:
            for pc_reg, pc_dict in tqdm(all_pl_pc_dict.items(), desc='Saving post codes areas of whole country: '):

                all_pc_dict = {}

                for pc_code, vals_pc in pc_dict.items():
                    for v_pc in vals_pc:
                        # Zapisujemy wielokat do pliku
                        gmn_name = v_pc[2]
                        teryt_code = v_pc[3]
                        c_pow = v_pc[1].area
                        jnd_pow = add_pts_nums[pc_code + "_" + gmn_name]["JOIN_POW"]
                        c_share = c_pow / jnd_pow
                        c_pc_num = math.ceil(add_pts_nums[pc_code + "_" + gmn_name]["ALL"] * c_share)
                        output.write({'geometry': mapping(v_pc[1]),
                                      'properties': {'Value': v_pc[0], "Name": pc_code, "PC_NUM": c_pc_num,
                                                     "Gmina": gmn_name, "TERYT": teryt_code}})

                        # Zmianiemy uklad wspolrzednych geograficznych i zaokraglamy koordynaty wspolrzednych
                        fin_geom_rpj = transform(reproject_srs, v_pc[1])
                        fin_geom_red_prec = wkt.loads(wkt.dumps(fin_geom_rpj,
                                                                rounding_precision=os.environ['COORDS_PREC']))

                        # Ustalamy finalne wartości słownika
                        pc_key = pc_code + "_" + gmn_name
                        pc_dict = {"Gmina": gmn_name, "PC_NUM": c_pc_num, "Polygon": fin_geom_red_prec.wkt}

                        # Dodajemy informacje do słownika kodow pocztowych
                        if pc_key not in all_pc_dict:
                            all_pc_dict[pc_key] = [pc_dict]
                        else:
                            all_pc_dict[pc_key].append(pc_dict)

                        # Dodajemy informacje do slownika nazw gmin i powiatow
                        pow_name = pow_teryt_dict[teryt_code[:4]]
                        woj_name = woj_teryt_dict[teryt_code[:2]]
                        gmn_key = gmn_name + "_" + pow_name + "_" + woj_name
                        pow_key = pow_name + "_" + woj_name

                        if gmn_key not in gmn_pow_nms_dict:
                            gmn_pow_nms_dict[gmn_key] = [pc_key]
                        elif gmn_key in gmn_pow_nms_dict and pc_key not in gmn_pow_nms_dict[gmn_key]:
                            gmn_pow_nms_dict[gmn_key] += [pc_key]

                        if pow_key not in gmn_pow_nms_dict:
                            gmn_pow_nms_dict[pow_key] = [pc_key]
                        elif pow_key in gmn_pow_nms_dict and pc_key not in gmn_pow_nms_dict[pow_key]:
                            gmn_pow_nms_dict[pow_key] += [pc_key]

                # Zapisujemy słownik wielokatow dla biezacego regionu kodow do pliku TXT
                with open(os.path.join(txt_fold, "PC_" + pc_reg + ".txt"), 'w') as file:
                    file.write(json.dumps(all_pc_dict))

        # Zapisujemy słowniki nazw gmin i powiatow
        with open(os.path.join(txt_fold, "GMN_POW_NMS.txt"), 'w') as file:
            file.write(json.dumps(gmn_pow_nms_dict))

        # Konwertujemy zbiorczy plik SHP do formstu GEOJSON
        fin_geojson_path = os.path.join(fin_maps_path, "00_POLSKA\\00_POLSKA_ALL_PC_" + os.environ['WORLD_CRDS'] +
                                        ".geojson")
        fin_name = os.path.basename(fin_geojson_path)[:-8]
        ogr2ogr.main(["", "-f", "GeoJSON", fin_geojson_path, all_pl_shps_path, "-lco", "RFC7946=YES", "-t_srs",
                      fin_srs, "-lco", coords_prec, '-nln', fin_name])


def merge_all_shps_save(mrgd_plg_path_shp: str, mrgd_plg_path_geoj: str, pc_dict: Dict[str, List[Any]],
                        all_pl_pc_dict: Dict[str, Dict[Any, Any]], fin_schema: Dict[str, Any], fin_srs: str,
                        coords_prec: str, add_pts_nums: Dict[str, Dict[Any, Any]]) -> None:
    """
    Function that merges all polygons of post codes areas and saves them to files .shp and .geojson

    :param mrgd_plg_path_shp: SHP path under which merged polygon files are to be saved
    :param mrgd_plg_path_geoj: GEOJSON path under which merged polygon files are to be saved
    :param pc_dict: Dictionary of current polygons
    :param all_pl_pc_dict: Dictionary of all polygons
    :param fin_schema: Dictionairy containing final parameters of SHP files
    :param fin_srs: String containing the name of the final coordinate system
    :param coords_prec: String containing final precison of coordinates
    :param add_pts_nums: Dictionary containing the number of address points and the area of a given municipality
    :return: Function does not return any values
    """

    tq_desc = 'Merging postcodes shapes and saving them to the hard drive: '
    fin_polygs_list = []

    for pc_code, gms_l in tqdm(pc_dict.items(), desc=tq_desc):
        # Laczymy wielokaty
        for geom_info in gms_l:
            # Nazwa gminy
            gmn_name = geom_info[2]
            teryt_kod = geom_info[3]
            pc_gmn_key = pc_code + "_" + gmn_name

            # Ustalamy liczbe punktow adresowych dla danego kodu pocztowego
            with Session(SQL_ENGINE) as db_session:
                # Pobieramy z bazy PRG kody pocztowe i wspolrzedne geograficzne dla danego kodu TERYT
                pc_codes_num = db_session.query(PRG.kod_pocztowy).filter((PRG.kod_pocztowy == pc_code) &
                                                                         (PRG.kod_teryt == teryt_kod)).count()

                if pc_gmn_key not in add_pts_nums:
                    add_pts_nums[pc_gmn_key] = {"ALL": pc_codes_num, "JOIN_POW": 0.0}

            # Ustalamy finalne parametry warstwy
            prop_dict = {'Value': geom_info[0], "Name": pc_code, "PC_NUM": pc_codes_num, "Gmina": gmn_name,
                         "TERYT": teryt_kod}

            # Tworzymy nowy wielokat bez wewnetrznych dziur
            fin_un_geom = Polygon(geom_info[1].exterior.coords) if geom_info[1].type == "Polygon" else \
                MultiPolygon([Polygon(c_plg.exterior.coords) for c_plg in geom_info[1]])

            # Kumulujemy laczna powierzchnie dla danego kodu / gminy
            add_pts_nums[pc_gmn_key]["JOIN_POW"] += fin_un_geom.area

            # Dodajemy multipolygon do słownika wszystkich wielokatow
            if pc_code[:2] not in all_pl_pc_dict:
                all_pl_pc_dict[pc_code[:2]] = {pc_code: [[geom_info[0], fin_un_geom, gmn_name, teryt_kod]]}
            elif pc_code[:2] in all_pl_pc_dict and pc_code not in all_pl_pc_dict[pc_code[:2]]:
                all_pl_pc_dict[pc_code[:2]][pc_code] = [[geom_info[0], fin_un_geom, gmn_name, teryt_kod]]
            elif pc_code[:2] in all_pl_pc_dict and pc_code in all_pl_pc_dict[pc_code[:2]]:
                all_pl_pc_dict[pc_code[:2]][pc_code].append([geom_info[0], fin_un_geom, gmn_name, teryt_kod])

            # Zapisujemy polygony i ich parametry na liście
            fin_polygs_list.append([pc_gmn_key, prop_dict, fin_un_geom])

    # Zapisujemy wielokaty do SHP
    with fiona.open(mrgd_plg_path_shp, mode='w', crs=from_epsg(int(os.environ['PL_CRDS'])), driver='ESRI Shapefile',
                    schema=fin_schema) as output:
        for c_row in fin_polygs_list:
            c_polyg = c_row[-1]
            c_dict = c_row[-2]
            c_pow = c_polyg.area
            jnd_pow = add_pts_nums[c_row[0]]["JOIN_POW"]

            # Przeliczamy proporcjonalnie liczbę adresów do powierzchni danego polygonu
            if c_pow != jnd_pow:
                c_share = c_pow / jnd_pow
                fin_nums = math.ceil(add_pts_nums[c_row[0]]["ALL"] * c_share)
                c_dict["PC_NUM"] = fin_nums

            # Zapisujemy bieżący polygon na dysku
            output.write({'geometry': mapping(c_polyg), 'properties': c_dict})

    # Konwertujemy zbiorczy plik SHP do formatu GEOJSON
    fin_name = os.path.basename(mrgd_plg_path_geoj)[:-8]
    ogr2ogr.main(["", "-f", "GeoJSON", mrgd_plg_path_geoj, mrgd_plg_path_shp, "-lco", "RFC7946=YES", "-t_srs", fin_srs,
                  "-lco", coords_prec, '-nln', fin_name])
    # Opcja "RFC7946=YES" - właściwy format pliku GEOJSON (dobrze interporetowalny przez mapy Google)
    # Opcja "COORDINATE_PRECISION=5" - redukujemy dokladnosc koordynatów do 5 miejsc po przecinku (do okolo 1 metra)


def prepare_merging(fin_geom_dict: Dict[str, Dict[Any, Any]], wod_pow_shape: shapely.geometry.Polygon,
                    pc_dict: Dict[str, List[Any]], curr_pc: List[int]) -> None:
    """
    Function that prepares postcodes polygons for merging

    :param fin_geom_dict: Dictionary with basic parameters for a given region
    :param wod_pow_shape: Polygons representing surface water shapes
    :param pc_dict: Dictionary of current polygons
    :param curr_pc: List for counting address points for a given postcode
    :return: Function does not return any values
    """

    # Pattern walidujacy kod pocztowy
    pc_pattern = re.compile(r"\d{2}-\d{3}")

    for teryt_code, teryt_dict in tqdm(fin_geom_dict.items(), desc='Preparing postcodes shapes for merging: '):
        if teryt_dict["NUM_PC"] > 1:

            fin_geom_arr = teryt_dict["GEOM_LIST"]

            for j, c_geom in enumerate(fin_geom_arr):
                # Kod pocztowy
                fin_pc = c_geom[2]

                # Jeżeli dany kod nie pasuje do patternu kodów pocztowych to pomijamy jego wielokat
                if not pc_pattern.match(fin_pc):
                    continue

                if c_geom[3]:
                    c_geom_mrr = c_geom[1].buffer(int(os.environ['BUFF_SIZE']))
                    gmn_poly = teryt_dict["GMN_SHP"]

                    # Wycinamy fragment tylko dotyczacy danej gminy
                    try:
                        gmn_shape_polyg = c_geom_mrr.intersection(gmn_poly)
                    except (Exception,):
                        if not c_geom_mrr.is_valid:
                            c_geom_mrr = c_geom_mrr.buffer(0)

                        if not gmn_poly.is_valid:
                            gmn_poly = gmn_poly.buffer(0)

                        gmn_shape_polyg = c_geom_mrr.intersection(gmn_poly)

                    # Upewniamy się, że finalne mapy nie będą obejmowały Zalewu Szczecińskiego, Zatoki Gdańskiej
                    # i Zalewu Wiślanego
                    fin_polyg = gmn_shape_polyg.intersection(wod_pow_shape)

                    for c_ind in c_geom[3]:
                        if c_ind in fin_geom_arr[:, 0]:
                            fin_row = np.where(fin_geom_arr[:, 0] == c_ind)[0][0]
                            clst_geo = fin_geom_arr[fin_row, 1]

                            # Wyliczamy różnicę tylko gdy nie ma błędu
                            if not fin_polyg.contains(clst_geo):
                                try:
                                    fin_polyg = fin_polyg.difference(clst_geo)
                                except (Exception,):
                                    if not fin_polyg.is_valid:
                                        fin_polyg = fin_polyg.buffer(0)

                                    if not clst_geo.is_valid:
                                        clst_geo = clst_geo.buffer(0)

                                    fin_polyg = fin_polyg.difference(clst_geo)

                    if fin_polyg.type == "MultiPolygon" or fin_polyg.type == "GeometryCollection":
                        fin_geom = unary_union([fin_p for fin_p in fin_polyg if fin_p.area >
                                                int(os.environ['SML_POLYG_DOWN'])])
                    else:
                        fin_geom = fin_polyg if fin_polyg.area > \
                                                int(os.environ['SML_POLYG_DOWN']) else Polygon([])
                else:
                    # Wycinamy fragment tylko dotyczacy danej gminy
                    gmn_shape_polyg = c_geom[1].intersection(teryt_dict["GMN_SHP"])

                    # Upewniamy się, że finalne mapy nie będą obejmowały Zalewu Szczecińskiego, Zatoki Gdańskiej
                    # i Zalewu Wiślanego
                    fin_geom = gmn_shape_polyg.intersection(wod_pow_shape)

                if not fin_geom.is_empty and (fin_geom.type == "MultiPolygon" or fin_geom.type == "Polygon"):
                    fin_geom_arr[j, 1] = fin_geom

                    if fin_pc in pc_dict:
                        pc_dict[fin_pc].append([curr_pc[0], fin_geom, teryt_dict["GMN_NAME"], teryt_code])
                    else:
                        pc_dict[fin_pc] = [[curr_pc[0], fin_geom, teryt_dict["GMN_NAME"], teryt_code]]

                    curr_pc[0] += 1
                else:
                    fin_geom_arr[j, 1] = Polygon([])
        else:
            # Finalny kod pocztowy
            fin_pc = teryt_dict["GEOM_LIST"][0]

            # Jeżeli dany kod nie pasuje do patternu kodów pocztowych to pomijamy jego wielokat
            if not pc_pattern.match(fin_pc):
                continue

            # Upewniamy się, że finalne mapy nie będą obejmowały Zalewu Szczecińskiego, Zatoki Gdańskiej
            # i Zalewu Wiślanego
            shape_gm = teryt_dict["GMN_SHP"]

            try:
                fin_geom = shape_gm.intersection(wod_pow_shape)
            except (Exception,):
                if not shape_gm.is_valid:
                    shape_gm = shape_gm.buffer(0)
                if not wod_pow_shape.is_valid:
                    wod_pow_shape = wod_pow_shape.buffer(0)

                fin_geom = shape_gm.intersection(wod_pow_shape)

            # Dodajemy wielokaty do słownika
            if fin_pc in pc_dict:
                pc_dict[fin_pc].append([curr_pc[0], fin_geom, teryt_dict["GMN_NAME"], teryt_code])
            else:
                pc_dict[fin_pc] = [[curr_pc[0], fin_geom, teryt_dict["GMN_NAME"], teryt_code]]

            curr_pc[0] += 1


def rmv_sml_ovrlp_polygs(fin_geom_dict: Dict[str, Dict[Any, Any]]) -> None:
    """
    Function that removes too small and overlapping polygons from dictionary "fin_geom_dict"

    :param fin_geom_dict: Dictionary with basic parameters for a given region
    :return: Function does not return any values
    """

    for teryt_code, teryt_dict in tqdm(fin_geom_dict.items(), desc='Removing too small, overlapping shapes: '):
        if teryt_dict["NUM_PC"] > 1:
            geom_arr = np.asarray(teryt_dict["GEOM_LIST"], dtype=object)
            rmv_mask = np.ones(len(geom_arr), dtype=bool)

            for i, c_geom in enumerate(geom_arr):
                # Wielkosc biezacego wielokata
                buff_geom = c_geom[1].buffer(int(os.environ['BUFF_SIZE']))
                c_area = buff_geom.area
                ovlp_percs = np.asarray([buff_geom.intersection(c_g[1]).area / c_area if
                                         c_geom[0] != c_g[0] and c_area != 0.0 else 0.0 for c_g in geom_arr])
                ovly_mask = np.logical_and(ovlp_percs > 0.0, ovlp_percs <= 1.0)

                if any(ovly_mask):
                    geom_arr[i, 3] = geom_arr[ovly_mask, 0].tolist()

                if c_area <= int(os.environ['SML_POLYG_UP']) and len(ovlp_percs) > 0 and np.max(ovlp_percs) > \
                        float(os.environ['SML_POLYG_OVRL']):
                    rmv_mask[i] = False

            teryt_dict["GEOM_LIST"] = geom_arr[rmv_mask, :]


def create_geom_dict(fin_geom_dict: Dict[str, Dict[Any, Any]], teryt_arr: np.ndarray,
                     teryt_gmn_paths_dict: Dict[str, List[Any]], gmn_teryt_dict: Dict[str, str]) -> None:
    """
    Function that creates dictionairy of all polygons in current province

    :param fin_geom_dict: Dictionary with basic parameters for a given region
    :param teryt_arr: Numpy array cotaining paths of shapefiles
    :param teryt_gmn_paths_dict: Dictionairy with TERYT codes and border points paths of municipalities
    :param gmn_teryt_dict: Dictionary with TERYT codes and names of municipalities
    :return: Function does not return any values
    """

    for shp_path, teryt_code in tqdm(teryt_arr, desc='Creating dictionairy of shapefiles for current province: '):
        # Bieżący kod pocztowy
        curr_code = shp_path[-10:-4]
        gmn_name = gmn_teryt_dict[teryt_code]
        count_teryt = np.sum(teryt_arr[:, 1] == teryt_code)

        if teryt_code not in fin_geom_dict:
            gmn_points = teryt_gmn_paths_dict[teryt_code]

            if len(gmn_points) < 2:
                gmn_shape = Polygon(gmn_points[0])
            else:
                gmn_shape = MultiPolygon([Polygon(g_points) for g_points in gmn_points])

            fin_geom_dict[teryt_code] = {'NUM_PC': count_teryt, "GEOM_LIST": list(), "GMN_SHP": gmn_shape,
                                         "GEOM_ID": 0, "GMN_NAME": gmn_name}

        if count_teryt > 1:
            geoms_list = [shape(features['geometry']) for features in fiona.open(shp_path)
                          if features['properties']['Value'] == 1]

            for c_geom in geoms_list:
                # Pobieramy granice z Polygonu
                c_bound = c_geom.boundary
                polys_list = [c_geom] if c_bound.type == 'LineString' else [Polygon(c_line) for c_line in c_bound]

                for c_poly in polys_list:
                    if c_poly.area > int(os.environ['SML_POLYG_DOWN']) and c_poly.is_valid:
                        c_poly_simp = c_poly.simplify(7.0, preserve_topology=False)
                        fin_geom_dict[teryt_code]["GEOM_LIST"] += [(fin_geom_dict[teryt_code]["GEOM_ID"],
                                                                    c_poly_simp, curr_code, list())]
                        fin_geom_dict[teryt_code]["GEOM_ID"] += 1
        else:
            fin_geom_dict[teryt_code]["GEOM_LIST"] = [curr_code]


def sngl_pc_zone_shp(teryt_code: str, paths_list: List[Any], c_post_cods: List[str], shp_fold: str) -> None:
    """
    Function that creates single shapefile of postal codes zones for single municipality

    :param teryt_code: TERYT code of the region
    :param paths_list: List of points representing the boundaries of the region
    :param c_post_cods: List of expected postcodes for giving region
    :param shp_fold: Path where the Shapefile will be saved
    :return: Function does not return any values
    """

    # Zapisujemy nowy plik Shapefile na dysku
    c_schema = {'geometry': 'Polygon', 'properties': {'Value': 'int', 'Name': 'str'}}

    with fiona.open(os.path.join(shp_fold, teryt_code + "_0_" + c_post_cods[0] + ".shp"), mode='w',
                    crs=from_epsg(int(os.environ['PL_CRDS'])), driver='ESRI Shapefile', schema=c_schema) as c:
        for c_points in paths_list:
            geom = Polygon(c_points)
            c.write({'geometry': mapping(geom), 'properties': {'Value': 1, "Name": c_post_cods[0]}})


def mult_pc_zones_shps(teryt_code: str, paths_list: List[Any], c_post_cods: List[str], prg_cols: List[Any],
                       shp_fold: str) -> None:
    """
    Function that creates multiple shapefiles of postcodes zones for single municipality

    :param teryt_code: TERYT code of the region
    :param paths_list: List of points representing the boundaries of the region
    :param c_post_cods: List of expected postcodes for giving region
    :param prg_cols: List with postcode, latitude and longitude of a given address point
    :param shp_fold: Path where the Shapefile will be saved
    :return: Function does not return any values
    """

    # Lista punktów adresowych z bazy PRG dla danego kodu TERYT
    with Session(SQL_ENGINE) as db_session:
        # Pobieramy z bazy PRG kody pocztowe i wspolrzedne geograficzne dla danego kodu TERYT
        c_prg_pts = db_session.query(*prg_cols).filter(PRG.kod_teryt == teryt_code).all()

    # Grupujemy pobrane z bazy PRG wspolrzedne geograficzne po przypisanych do nich kodach pocztowych
    grp_prg_pts = {k: np.array(list(gr))[:, 1:].astype(float)
                   for k, gr in groupby(sorted(c_prg_pts), key=lambda x: x[0]) if k in c_post_cods}

    # Dla każdego kodu pocztowego usuwamy odstajace punkty
    grp_prg_pts = rmv_prg_outlyrs(grp_prg_pts)

    for path_num, c_points in enumerate(paths_list):
        # Koordynaty prawego górego rogu bounding boxa sciezki przesuniete o 100 metrow
        c_path = path.Path(c_points, readonly=True, closed=True)
        ur_coords = np.asarray(c_path.get_extents().corners()[1] - (100, -100), dtype=np.int32)
        a_width = int((c_path.get_extents().width + 200) / 10)
        a_height = int((c_path.get_extents().height + 200) / 10)

        # Docelowa macierz z oznaczeniami kodów pocztowych
        fin_pc_arr = np.ones((a_width, a_height), dtype=np.int16) * -1
        c_inds = np.indices((a_width, a_height), dtype=float).transpose(1, 2, 0).reshape(a_width * a_height, 2)
        coords_arr = (10, -10) * c_inds.astype(int) + (ur_coords + (5, -5))
        in_flags = c_path.contains_points(coords_arr)
        in_flags_ids = c_inds[in_flags, :].astype(int)
        fin_pc_arr[in_flags_ids[:, 0], in_flags_ids[:, 1]] = 0

        for i, prg_pts in enumerate(grp_prg_pts.items()):
            prg_inds = np.asarray((prg_pts[1] - ur_coords) / 10, dtype=int) * (1, -1) + 1
            neg_vals_mask_x = np.logical_and(prg_inds[:, 0] > 0, prg_inds[:, 0] < a_width)
            neg_vals_mask_y = np.logical_and(prg_inds[:, 1] > 0, prg_inds[:, 1] < a_height)
            prg_inds_pos = prg_inds[np.logical_and(neg_vals_mask_x, neg_vals_mask_y)]
            fin_pc_arr[prg_inds_pos[:, 0], prg_inds_pos[:, 1]] = i + 1

        if fin_pc_arr.max() > 0:
            find_min_ids = c_inds[fin_pc_arr.reshape(a_width * a_height) == 0, :]
            fmin_len = len(find_min_ids)
            prg_pts_ids = c_inds[fin_pc_arr.reshape(a_width * a_height) > 0, :]
            prg_len = len(prg_pts_ids)
            const_div = int(int(os.environ['DIV_CONST']) / prg_len)

            for i in range(int(fmin_len / const_div) + 1):
                start_ind = i * const_div
                end_ind = (i + 1) * const_div if (i + 1) * const_div < fmin_len else fmin_len
                c_min_ids = find_min_ids[start_ind:end_ind, :]

                # Wyliczamy odleglosc euklidesowa pomiedzy punktami PRG a punktami, dla których szukamy kodow
                # pocztowych. Macierze 'c_min_ids' i 'prg_pts_ids' musza miec typ float, bo wtedy cdist nie musi ich
                # kopiowac przy wywolywaniu funkcji w C
                manh_dists = distance.cdist(c_min_ids, prg_pts_ids, 'euclidean')

                # Wyznaczamy indeksy najbliższych punktów PRG
                min_dist_ids = prg_pts_ids[np.argmin(manh_dists, axis=1)].astype(int)
                c_min_ids = c_min_ids.astype(int)
                prg_pts_ids = prg_pts_ids.astype(int)

                # Oznaczamy w finalnej macierzy zerowe komórki indeksami kodów pocztowych
                fin_pc_arr[c_min_ids[:, 0], c_min_ids[:, 1]] = fin_pc_arr[min_dist_ids[:, 0], min_dist_ids[:, 1]]

            # Pozbywamy się izolowanych wysp kodów pocztowych wewnatrz obszarów innych kodów pocztowych
            rmv_isl_pc(fin_pc_arr, prg_pts_ids)

            # Tworzymy pliki Shapefile dla poszczególnych kodów pocztowych
            create_pc_shps(grp_prg_pts, a_width, a_height, fin_pc_arr, shp_fold, ur_coords, teryt_code, path_num)
        else:
            codes_lengths = np.array([(key, len(prg_pts)) for key, prg_pts in grp_prg_pts.items()])
            curr_code = codes_lengths[np.argmax(codes_lengths[:, 1].astype(float)), 0] if len(codes_lengths) > 0 \
                else c_post_cods
            sngl_pc_zone_shp(teryt_code, [c_points], curr_code, shp_fold)


def rmv_isl_pc(fin_pc_arr: np.ndarray, prg_pts_ids: np.ndarray) -> None:
    """
    Function that removes isolated postal codes from the area of other postal codes

    :param fin_pc_arr: TERYT code of the region
    :param prg_pts_ids: List of points representing the boundaries of the region
    :return: Function does not return any values
    """

    # Podstawowe parametry
    wind_s = int(os.environ['ISS_WINDOW_SIZE'])
    chng_perc = float(os.environ['ISS_PERC'])
    x_max, y_max = fin_pc_arr.shape

    for p_inds in prg_pts_ids:
        c_val = fin_pc_arr[p_inds[0], p_inds[1]]
        x_0 = p_inds[0] - wind_s if p_inds[0] >= wind_s else 0
        x_1 = p_inds[0] + wind_s if p_inds[0] + wind_s < x_max else x_max - 1
        y_0 = p_inds[1] - wind_s if p_inds[1] >= wind_s else 0
        y_1 = p_inds[1] + wind_s if p_inds[1] + wind_s < y_max else y_max - 1
        test_wind = fin_pc_arr[x_0:x_1, y_0:y_1]
        test_wind_data = test_wind[test_wind != -1]
        unique, counts = np.unique(test_wind_data, return_counts=True)

        if len(unique) > 1:
            freq_perc = counts / counts.sum()
            max_ind = np.argmax(freq_perc)
            max_val = unique[max_ind]

            if max_val != c_val and freq_perc[max_ind] > chng_perc:
                test_wind[test_wind == c_val] = max_val
                fin_pc_arr[x_0:x_1, y_0:y_1] = test_wind


def rmv_prg_outlyrs(grp_prg_pts: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """
    Function that removes from list of address points potentially incorrect zip codes

    :param grp_prg_pts: Dictionary containing geographical coordinates grouped by postal code
    :return: Corrected dictionary of geographical coordinates grouped by postcode
    """

    new_grp_prg_pts = {}

    for pc_code, pts_arr in grp_prg_pts.items():
        eukl_dists = squareform(pdist(pts_arr, metric='euclidean'))

        # Wypełniamy przekatna macierzy duzymi wartościami, żeby mozna bylo szybko znalezc wartosc minimalna
        np.fill_diagonal(eukl_dists, 10000)
        top_num = int(os.environ["TOP_NUM"])

        if len(pts_arr) > top_num:
            eukl_dists_top_mins = np.partition(eukl_dists, kth=(top_num - 1), axis=1)[:, top_num - 1]

            # Wycinamy wszystkie punkty PRG, które maja odleglosc od najblizszego innego punktu wieksza niz 500 metrow
            in_mask = eukl_dists_top_mins <= int(os.environ['OUTLAY_THRES'])
            new_grp_prg_pts[pc_code] = pts_arr[in_mask]
        else:
            new_grp_prg_pts[pc_code] = pts_arr

    return new_grp_prg_pts


def create_pc_shps(grp_prg_pts: Dict[str, np.ndarray], a_width: int, a_height: int, fin_pc_arr: np.ndarray,
                   shp_fold: str, ur_coords: np.ndarray, teryt_code: str, path_num: int) -> None:
    """
    Function that creates shapefiles of postcodes zones

    :param grp_prg_pts: Dictionary containing geographical coordinates grouped by postal code
    :param a_width: Width of path bounding box
    :param a_height: Height of path bounding box
    :param fin_pc_arr: TERYT code of the region
    :param shp_fold: Path where the Shapefile will be saved
    :param ur_coords: Coordinates of the upper right vertex of the path bounding box
    :param teryt_code: TERYT code of the region
    :param path_num: Path number
    :return: Function does not return any values
    """

    # Tworzymy plik rastrowy dla każdego kodu pocztowego
    for i, prg_pts in enumerate(grp_prg_pts.items()):
        # Dla każdego kodu pocztowego tworzmy raster zawierajacy informacje gdzie dany kod pocztowy wystepuje
        c_arr = np.zeros((a_width, a_height), dtype=np.uint8)
        c_arr[fin_pc_arr == i + 1] = 1
        c_arr = c_arr.T
        driver = gdal.GetDriverByName("GTiff")
        [rows, cols] = c_arr.shape
        dst_ds = driver.Create(os.path.join(shp_fold, "temp.tif"), cols, rows, 1, gdal.GDT_Byte,
                               options=['COMPRESS=LZW'])
        dst_ds.SetGeoTransform([ur_coords[0], 10, 0, ur_coords[1], 0, -10])
        sr = osr.SpatialReference()
        sr.ImportFromEPSG(int(os.environ['PL_CRDS']))
        dst_ds.SetProjection(sr.ExportToWkt())
        dst_ds.GetRasterBand(1).WriteArray(c_arr)
        dst_ds.GetRasterBand(1).SetNoDataValue(0)
        dst_ds.FlushCache()

        # Otwieramy nowoutworzony raster i zapisujemy go jako shapefile pzy pomocy polecenia gdal.Polygonize
        src_ds = gdal.Open(os.path.join(shp_fold, "temp.tif"))
        srcband = src_ds.GetRasterBand(1)
        dst_layername = 'Post_Code'
        drv = ogr.GetDriverByName("ESRI Shapefile")
        shp_name = os.path.join(shp_fold, teryt_code + "_" + str(path_num) + "_" + prg_pts[0] + ".shp")
        dst_ds = drv.CreateDataSource(shp_name)
        sp_ref = osr.SpatialReference()
        sp_ref.ImportFromEPSG(int(os.environ['PL_CRDS']))
        dst_layer = dst_ds.CreateLayer(dst_layername, srs=sp_ref)
        fld = ogr.FieldDefn("Value", ogr.OFTInteger)
        dst_layer.CreateField(fld)
        dst_field = dst_layer.GetLayerDefn().GetFieldIndex("Value")

        # Przetwarzamy wartstwe z formatu rastrowego do formatu wielokatowego
        gdal.Polygonize(srcband, None, dst_layer, dst_field, [], callback=None)

        # Usuwamy niepotrzebne obiekty, żeby mieć pewność, że wszystko zapisało się na dysku jak trzeba
        del src_ds
        del dst_ds

        # Usuwamy plik TIFF, bo nie jest już nam potrzebny
        os.remove(os.path.join(shp_fold, "temp.tif"))

        # Otwieramy nowoutworzony shapefile i dodajemy mu pole z nazwą kodu pocztowego
        src_ds2 = ogr.Open(shp_name, 1)
        lyr = src_ds2.GetLayer(0)
        field_defn = ogr.FieldDefn("Name", ogr.OFTString)
        lyr.CreateField(field_defn)

        for feat in lyr:
            lyr.SetFeature(feat)
            feat.SetField("Name", prg_pts[0])
            lyr.SetFeature(feat)

        src_ds2.FlushCache()
        del src_ds2


def read_wod_pow_shapes() -> shapely.geometry.Polygon:
    """
    Function that reads shapes of surface waters in Poland

    :return: Shape of surface waters in Poland
    """

    # Sciezka do pliku z wodami powierzchniowymi
    wod_pow_path = os.path.join(os.environ["PARENT_PATH"], os.environ['WOD_POW_PATH'])

    try:
        with zipfile.ZipFile(wod_pow_path, "r") as zfile:
            for name in zfile.namelist():
                if name == "JCWPd.shp":
                    wod_pow_shp = unary_union([shape(features['geometry']) for features in
                                               fiona.open(r'/vsizip/' + wod_pow_path + '/' + name)])
                    break

    except FileNotFoundError:
        raise Exception("Pod podanym adresem: '" + wod_pow_path + "' nie ma pliku 'SHPaPGW.zip'. Pobierz ten plik ze " +
                        "strony: 'https://dane.gov.pl/pl/dataset/599/resource/672,wektorowe-warstwy-tematyczne-apgw' "
                        "i uruchom program ponownie!")

    return wod_pow_shp


def create_geom_refs_dict() -> Dict[str, List[Any]]:
    """
    Funtion that creates dictionairy with TERYT codes and border points paths of municipalities

    :return: Dictionairy with TERYT codes and border points paths of municipalities
    """

    # Scieżka do pliku z jednostkami administracyjnymi
    ja_path = os.path.join(os.environ["PARENT_PATH"], os.environ['JA_PATH'])

    try:
        with zipfile.ZipFile(ja_path, "r") as zfile:
            for name in zfile.namelist():
                if name[-4:] == ".shp" and "_gmin" in name:
                    gmin_shapes = ogr.Open(r'/vsizip/' + ja_path + '/' + name)

    except FileNotFoundError:
        raise Exception("Pod podanym adresem: '" + ja_path + "' nie ma pliku '00_jednostki_administracyjne.zip'. " +
                        "Pobierz ten plik ze strony: 'https://dane.gov.pl/pl/dataset/726,panstwowy-rejestr-granic-i-" +
                        "powierzchni-jednostek-podziaow-terytorialnych-kraju/resource/29515' i uruchom program " +
                        "ponownie!")

    # Transformujemy wspolrzednie do ukladu 4326 (przy okazji korygujemy kolejność współrzędnych)
    curr_epsg = int(gmin_shapes.GetLayer(0).GetSpatialRef().GetAttrValue("AUTHORITY", 1))
    pl_wrld_trans = create_coords_transform(curr_epsg, int(os.environ['PL_CRDS']), True)
    teryt_gmn_paths_dict = {}

    for feature in gmin_shapes.GetLayer(0):
        feat_itms = feature.items()
        teryt = feat_itms['JPT_KOD_JE']
        geom = feature.geometry()
        geom.Transform(pl_wrld_trans)

        if geom.GetGeometryName() == "POLYGON":
            geom_points = [geom.GetGeometryRef(0).GetPoints()]
        else:
            geom_points = [geom.GetGeometryRef(i).GetGeometryRef(0).GetPoints() for i in range(geom.GetGeometryCount())]

        if teryt not in teryt_gmn_paths_dict:
            teryt_gmn_paths_dict[teryt] = geom_points
        else:
            teryt_gmn_paths_dict[teryt] += geom_points

    return teryt_gmn_paths_dict


def create_coords_transform(in_epsg: int, out_epsg: int, change_map_strateg: bool = False) -> \
        osr.CoordinateTransformation:
    """
    Function that creates object that transforms geographical coordinates

    :param in_epsg: Number of input EPSG coordinates system
    :param out_epsg: Number of output EPSG coordinates system
    :param change_map_strateg: Flag indicating if map strategy should be changed
    :return: Coordinates transformation that transforms spatial references from input EPSG system to output EPSG system
    """

    # Zmieniamy system koordynatow dla gmin
    in_sp_ref = osr.SpatialReference()
    in_sp_ref.ImportFromEPSG(in_epsg)

    # Zmieniamy mapping strategy, bo koordynaty dla gmin podawane sa w odwrotnej kolejnosc tzw. "starej"
    if change_map_strateg:
        in_sp_ref.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

    out_sp_ref = osr.SpatialReference()
    out_sp_ref.ImportFromEPSG(out_epsg)

    # Zmieniamy mapping strategy, bo k0ordynaty dla gmin podawane sa w odwrotnej kolejnosc tzw. "starej"
    if change_map_strateg:
        out_sp_ref.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

    return osr.CoordinateTransformation(in_sp_ref, out_sp_ref)


@lru_cache
def get_corr_reg_name(curr_name: str) -> str:
    """
    Function that corrects wrong regions names

    :param curr_name: Current region name
    :return: Corrected region name
    """

    # Specjalny wyjatek, bo w danych PRG występuje czasem powiat "JELENIOGORSKI", a od 2021 roku powiat ten nazywa sie
    # "KARKONOSKI", wiec trzeba to poprawic
    if curr_name == "JELENIOGORSKI":
        return "KARKONOSKI"

    # Kolejny wyjatek, bo w danych PRG występuje czasem gmina "SITKOWKA-NOWINY", a od 2021 roku gmina ta nazywa sie
    # "NOWINY", wiec trzeba to poprawic
    elif curr_name == "SITKOWKA-NOWINY":
        return "NOWINY"

    # Kolejny wyjatek, bo w danych PRG występuje czasem gmina "SLUPIA (KONECKA)", a od 2018 roku gmina ta nazywa sie
    # "SLUPIA KONECKA", wiec trzeba to poprawic
    elif curr_name == "SLUPIA (KONECKA)":
        return "SLUPIA KONECKA"

    # Kolejny wyjatek, bo w danych PRG występuje czasem gmina "SLUPIA (JEDRZEJOWSKA)", a oficjalna nazwa tej gminy,
    # według kodów TERYT, to "SLUPIA", wiec trzeba to poprawic
    elif curr_name == "SLUPIA (JEDRZEJOWSKA)":
        return "SLUPIA"

    else:
        return curr_name
