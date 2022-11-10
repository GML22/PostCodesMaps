""" Module that parses data from PRG database """

from abc import ABC
from functools import lru_cache

from utilities import *


class PRGDataParser(ABC):
    """ Class that parses adress points from PRG database to SQLAlchemy database """

    def __init__(self, xml_path: str, tags_tuple: tuple, event_type: str) -> None:
        self.xml_path = xml_path
        self.tags_tuple = tags_tuple
        self.event_type = event_type
        self.woj_teryt_dict = {}
        self.pow_teryt_dict = {}
        self.teryt_dict = {}
        self.check_path()
        self.create_teryt_dict()
        self.parse_xml()

    def check_path(self) -> None:
        """" Method that checks if path to file is valid """
        if not os.path.isfile(self.xml_path):
            raise Exception("Pod adresem: '" + self.xml_path + "' nie ma pliku '" + os.environ['PRG_NAME'] +
                            "'. Pobierz ten plik ze strony: '" + os.environ['PRG_LINK'] +
                            "' i uruchom program ponownie!")

    @time_decorator
    def create_teryt_dict(self) -> None:
        """ Method that creates TERYT dictionary """

        # Wczytujemy slowniki TERYT z dysku
        self.woj_teryt_dict = csv_to_dict(os.path.join(os.environ["PARENT_PATH"], os.environ['TERYT_WOJ_PATH']))
        self.pow_teryt_dict = csv_to_dict(os.path.join(os.environ["PARENT_PATH"], os.environ['TERYT_POW_PATH']))
        gmn_teryt_dict = csv_to_dict(os.path.join(os.environ["PARENT_PATH"], os.environ['TERYT_GMN_PATH']))
        self.teryt_dict = {woj_code: {} for woj_code in self.woj_teryt_dict.keys()}

        for pow_code in self.pow_teryt_dict.keys():
            self.teryt_dict[pow_code[:2]][pow_code] = {}

        # Tworzymy finalny slownik
        for gmn_code, gmn_name in gmn_teryt_dict.items():
            if gmn_name not in self.teryt_dict[gmn_code[:2]][gmn_code[:4]]:
                self.teryt_dict[gmn_code[:2]][gmn_code[:4]][gmn_name] = {gmn_code[-1]: gmn_code}
            else:
                self.teryt_dict[gmn_code[:2]][gmn_code[:4]][gmn_name].update({gmn_code[-1]: gmn_code})

    @time_decorator
    def parse_xml(self) -> None:
        """ Method that parses xml file and saves data to SQL database """

        # Definiujemy podstawowe parametry
        x_path, x_filename = os.path.split(self.xml_path)
        os.chdir(x_path)

        with zipfile.ZipFile(x_filename, "r") as zfile:
            for woj_name in tqdm(zfile.namelist()):
                with zfile.open(woj_name) as my_file:
                    xml_contex = etree.iterparse(my_file, events=(self.event_type,), tag=self.tags_tuple[:-1],
                                                 recover=True)

                    # Tworzymy listę punktów adresowych PRG i zapisujemy je w bazie
                    self.create_points_list(xml_contex)

    def create_points_list(self, xml_contex: etree.iterparse) -> None:
        """ Creating list of data points """

        # Definiujemy podstawowe parametry
        c_ind = 0
        c_row = [''] * 4
        c_miejsc = ''
        points_list = []
        all_tags = self.tags_tuple

        for _, curr_node in xml_contex:
            c_val = curr_node.text
            c_tag = curr_node.tag

            if c_tag == all_tags[0] and c_val != "Polska":
                c_row[c_ind] = unidecode(c_val).upper()
                c_ind += 1
            elif c_tag == all_tags[1] and c_val is not None:
                c_miejsc = unidecode(c_val).upper()
            elif c_tag == all_tags[2]:
                c_val = c_val if c_val is not None else ""
                c_row[3] = c_val
                c_ind = 0
            elif c_tag == all_tags[3] or c_tag == all_tags[4]:
                c_val = c_val.split()

                if c_row[0] != '' and c_row[1] != '' and c_row[2] != '' and c_row[3] != '':
                    # Ustalamy kod TERYT gminy, w ktorej jest dany punkt adresowy
                    woj_code = [key for key, val in self.woj_teryt_dict.items() if val == c_row[0]][0]
                    pow_name = get_corr_reg_name(c_row[1])
                    pow_code = [key for key, val in self.pow_teryt_dict.items() if val == pow_name and
                                key[:2] == woj_code][0]
                    gmn_name = get_corr_reg_name(c_row[2])
                    gmn_codes = self.teryt_dict[woj_code][pow_code][gmn_name]

                    if len(gmn_codes) == 1:
                        fin_teryt_code = next(iter(gmn_codes.values()))
                    elif c_miejsc is not None and gmn_name == c_miejsc:
                        fin_teryt_code = gmn_codes["1"]
                    else:
                        fin_teryt_code = gmn_codes["2"]

                    # Dodajemy punkt do listy punktow
                    points_list.append(PRG(fin_teryt_code, c_row[3], int(float(c_val[0])), int(float(c_val[1]))))

                c_ind = 0
                c_row = [''] * 4

            # Czyscimy przetworzone obiekty wezlow XML z pamieci
            clear_xml_node(curr_node)

        # Dodajemy punkty do bazy
        with Session(SQL_ENGINE) as db_session:
            db_session.bulk_save_objects(points_list)
            db_session.commit()


@lru_cache
def get_corr_reg_name(curr_name: str) -> str:
    """ Function that corrects wrong regions names """

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
