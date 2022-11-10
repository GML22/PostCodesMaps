""" Module that defines SQL database classes """

import os

import sqlalchemy as sa
from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base

# Tworzymy bazowy schemat dla tabel
BASE = declarative_base()

# Wczytujemy zmienne środowiskowe projektu
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
os.environ["PARENT_PATH"] = os.path.abspath(os.path.join(os.path.join(os.getcwd(), os.pardir), os.pardir))

# Deklarujemy silnik SQL
SQL_ENGINE = sa.create_engine("sqlite:///" + os.path.join(os.environ["PARENT_PATH"], os.environ["DB_PATH"]))


class PRG(BASE):
    """ Class that defines columns of 'PRG_TABLE' """

    # Defniujemy nazwę tabeli
    __tablename__ = "PRG_TABLE"

    # Definiujemy kolumny tabeli
    prg_point_id = sa.Column('PRG_POINT_ID', sa.Integer, primary_key=True)
    kod_teryt = sa.Column('KOD_TERYT', sa.String, nullable=False, index=True)
    kod_pocztowy = sa.Column('KOD_POCZTOWY', sa.String, nullable=False)
    szerokosc = sa.Column('SZEROKOSC', sa.Integer, nullable=False)
    dlugosc = sa.Column('DLUGOSC', sa.Integer, nullable=False)

    def __init__(self, kod_teryt: str, kod_pocztowy: str, szerokosc: float, dlugosc: float) -> None:
        self.kod_teryt = kod_teryt
        self.kod_pocztowy = kod_pocztowy
        self.szerokosc = szerokosc
        self.dlugosc = dlugosc

    def __repr__(self) -> str:
        print_str = "<PRG('%s', '%s', '%s', '%s')>"
        return print_str % (self.kod_teryt, self.kod_pocztowy, self.szerokosc, self.dlugosc)
