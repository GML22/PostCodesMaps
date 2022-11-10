""" __init_.py module """
import sqlalchemy as sa

from prg_db import BASE
from prg_parser import PRGDataParser
from utilities import *

# Tworzymy domyślny obiekt loggera
create_logger('pcm_logger')


@time_decorator
def main() -> None:
    """ Main function """

    # Sprawdzamy w bazie czy tablica 'PRG_TABLE' istnieje, jeżeli nie istnieje to ja tworzymy na podstawie bazy PRG
    if not sa.inspect(SQL_ENGINE).has_table("PRG_TABLE"):
        # Tworzymy domyslne obiekt tabeli PRG
        BASE.metadata.create_all(SQL_ENGINE)

        # Tworzymy tabelę SQL z punktami adresowymi PRG
        PRGDataParser(os.path.join(os.environ["PARENT_PATH"], os.environ['PRG_PATH']),
                      tuple(os.environ['PRG_TAGS'].split(";")), 'end')

    # Tworzymy shapefile obszarów kodów pocztowych
    create_postal_codes_shps()


if __name__ == "__main__":
    s_time = time.time()
    main()
    logging.getLogger('root').info("Łączny czas wykonywania programu - {:.2f} sekundy.".format(time.time() - s_time))
