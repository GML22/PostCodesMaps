""" Module that defines SQL database class in the PostCodesMaps project """

import os

import sqlalchemy as sa
from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base

# Tworzymy bazowy schemat dla tabel
BASE = declarative_base()

# Wczytujemy zmienne środowiskowe projektu
parent_path = os.path.join(os.getcwd()[:os.getcwd().index("PostCodesMaps")], "PostCodesMaps")
load_dotenv(os.path.join(parent_path, ".env"))
os.environ["PARENT_PATH"] = parent_path

# Deklarujemy obiekt reprezentujący silnik SQL
SQL_ENGINE = sa.create_engine("sqlite:///" + os.path.join(os.environ["PARENT_PATH"], os.environ["DB_PATH"]))


class PRG(BASE):
    """ Class that defines columns of "PRG_TABLE" """

    # Defniujemy nazwę tabeli
    __tablename__ = "PRG_TABLE"

    # Definiujemy kolumny tabeli
    prg_point_id = sa.Column('PRG_POINT_ID', sa.Integer, primary_key=True)
    kod_teryt = sa.Column('KOD_TERYT', sa.String, nullable=False, index=True)
    kod_pocztowy = sa.Column('KOD_POCZTOWY', sa.String, nullable=False, index=True)
    szerokosc = sa.Column('SZEROKOSC', sa.Integer, nullable=False)
    dlugosc = sa.Column('DLUGOSC', sa.Integer, nullable=False)

    def __init__(self, kod_teryt: str, kod_pocztowy: str, szerokosc: float, dlugosc: float) -> None:
        """
        Method that creates objects from a class "PRG"

        :param kod_teryt: TERYT code of the region in which the address point is located
        :param kod_pocztowy: Postcode where the address point is located
        :param szerokosc: Longitude of a given address point
        :param dlugosc: Latitude of a given address point
        :return: The method does not return any values
        """

        self.kod_teryt = kod_teryt
        self.kod_pocztowy = kod_pocztowy
        self.szerokosc = szerokosc
        self.dlugosc = dlugosc

    def __repr__(self) -> str:
        """
        Method that represents an objects in a class "PRG" as a string

        :return: String that represents objects of the class "PRG"
        """

        print_str = "<PRG('%s', '%s', '%s', '%s')>"
        return print_str % (self.kod_teryt, self.kod_pocztowy, self.szerokosc, self.dlugosc)
