"""CQ WPX CW plugin"""

# pylint: disable=invalid-name
import logging
from pathlib import Path

from PyQt5 import QtWidgets

logger = logging.getLogger("__main__")

name = "CQ WPX CW"
cabrillo_name = "CQ-WPX-CW"
mode = "CW"  # CW SSB BOTH RTTY

# 1 once per contest, 2 work each band, 3 each band/mode, 4 no dupe checking
dupe_type = 2


def init_contest(self):
    """setup plugin"""
    set_tab_next(self)
    set_tab_prev(self)
    interface(self)
    self.next_field = self.other_2


def interface(self):
    """Setup user interface"""
    self.field1.show()
    self.field2.show()
    self.field3.show()
    self.field4.show()
    label = self.field3.findChild(QtWidgets.QLabel)
    label.setText("SentNR")
    label = self.field4.findChild(QtWidgets.QLabel)
    label.setText("RcvNR")


def set_tab_next(self):
    """Set TAB Advances"""
    self.tab_next = {
        self.callsign: self.field1.findChild(QtWidgets.QLineEdit),
        self.field1.findChild(QtWidgets.QLineEdit): self.field2.findChild(
            QtWidgets.QLineEdit
        ),
        self.field2.findChild(QtWidgets.QLineEdit): self.field3.findChild(
            QtWidgets.QLineEdit
        ),
        self.field3.findChild(QtWidgets.QLineEdit): self.field4.findChild(
            QtWidgets.QLineEdit
        ),
        self.field4.findChild(QtWidgets.QLineEdit): self.callsign,
    }


def set_tab_prev(self):
    """Set TAB Advances"""
    self.tab_prev = {
        self.callsign: self.field4.findChild(QtWidgets.QLineEdit),
        self.field1.findChild(QtWidgets.QLineEdit): self.callsign,
        self.field2.findChild(QtWidgets.QLineEdit): self.field1.findChild(
            QtWidgets.QLineEdit
        ),
        self.field3.findChild(QtWidgets.QLineEdit): self.field2.findChild(
            QtWidgets.QLineEdit
        ),
        self.field4.findChild(QtWidgets.QLineEdit): self.field3.findChild(
            QtWidgets.QLineEdit
        ),
    }


def set_contact_vars(self):
    """Contest Specific"""
    self.contact["SNT"] = self.sent.text()
    self.contact["RCV"] = self.receive.text()
    self.contact["SentNr"] = self.other_1.text()
    self.contact["NR"] = self.other_2.text()
    if self.contact.get("WPXPrefix"):
        result = self.database.fetch_wpx_exists(self.contact.get("WPXPrefix", ""))
        if result.get("wpx_count"):
            self.contact["IsMultiplier1"] = 0
        else:
            self.contact["IsMultiplier1"] = 1


def prefill(self):
    """Fill SentNR"""
    result = self.database.get_serial()
    serial_nr = str(result.get("serial_nr", "1"))
    if serial_nr == "None":
        serial_nr = "1"
    field = self.field3.findChild(QtWidgets.QLineEdit)
    if len(field.text()) == 0:
        field.setText(serial_nr)


def points(self):
    """Calc point"""
    result = self.cty_lookup(self.pref.get("callsign", ""))
    if result:
        for item in result.items():
            mycountry = item[1].get("entity", "")
            mycontinent = item[1].get("continent", "")
    result = self.cty_lookup(self.contact.get("Call", ""))
    band = int(int(float(self.contact.get("Freq"))) / 1000)
    if result:
        for item in result.items():
            entity = item[1].get("entity", "")
            continent = item[1].get("continent", "")
            if mycountry.upper() == entity.upper():
                return 1
            if mycontinent and continent == "NA":
                if band in [28, 21, 14]:
                    return 2
                return 4
            if mycontinent == continent:
                if band in [28, 21, 14]:
                    return 1
                return 2
            if band in [28, 21, 14]:
                return 3
            return 6
    return 0


def show_mults(self):
    """Return display string for mults"""
    result = self.database.fetch_wpx_count()
    if result:
        return int(result.get("wpx_count", 0))
    return 0


def show_qso(self):
    """Return qso count"""
    result = self.database.fetch_qso_count()
    if result:
        return int(result.get("qsos", 0))
    return 0


def get_points(self):
    """Return raw points before mults"""
    result = self.database.fetch_points()
    if result:
        return int(result.get("Points", 0))
    return 0


def calc_score(self):
    """Return calculated score"""
    result = self.database.fetch_points()
    if result is not None:
        score = result.get("Points", "0")
        if score is None:
            score = "0"
        contest_points = int(score)
        result = self.database.fetch_wpx_count()
        mults = int(result.get("wpx_count", 0))
        return contest_points * mults
    return 0


def adif(self):
    """
    Creates an ADIF file of the contacts made.
    """
    filename = (
        str(Path.home())
        + "/"
        + f"{self.pref.get('callsign').upper()}_{cabrillo_name}.adi"
    )
    log = self.database.fetch_all_contacts_asc()
    try:
        with open(filename, "w", encoding="utf-8") as file_descriptor:
            print("<ADIF_VER:5>2.2.0", end="\r\n", file=file_descriptor)
            print("<EOH>", end="\r\n", file=file_descriptor)
            for contact in log:

                hiscall = contact.get("Call", "")
                the_date_and_time = contact.get("TS")
                band = contact.get("Band")
                themode = contact.get("Mode")
                frequency = str(contact.get("Freq", 0) / 1000)
                sentrst = contact.get("SNT", "")
                rcvrst = contact.get("RCV", "")
                sentnr = str(contact.get("SentNr", "59"))
                rcvnr = str(contact.get("NR", "59"))
                grid = contact.get("GridSquare", "")
                comment = contact.get("ContestName", "")
                loggeddate = the_date_and_time[:10]
                loggedtime = the_date_and_time[11:13] + the_date_and_time[14:16]
                print(
                    f"<QSO_DATE:{len(''.join(loggeddate.split('-')))}:d>"
                    f"{''.join(loggeddate.split('-'))}",
                    end="\r\n",
                    file=file_descriptor,
                )
                print(
                    f"<TIME_ON:{len(loggedtime)}>{loggedtime}",
                    end="\r\n",
                    file=file_descriptor,
                )
                print(
                    f"<CALL:{len(hiscall)}>{hiscall}",
                    end="\r\n",
                    file=file_descriptor,
                )
                print(
                    f"<MODE:{len(themode)}>{themode}", end="\r\n", file=file_descriptor
                )
                # print(
                #     f"<BAND:{len(band + 'M')}>{band + 'M'}",
                #     end="\r\n",
                #     file=file_descriptor,
                # )
                try:
                    print(
                        f"<FREQ:{len(frequency)}>{frequency}",
                        end="\r\n",
                        file=file_descriptor,
                    )
                except TypeError:
                    pass  # This is bad form... I can't remember why this is in a try block

                print(
                    f"<RST_SENT:{len(sentrst)}>{sentrst}",
                    end="\r\n",
                    file=file_descriptor,
                )
                print(
                    f"<RST_RCVD:{len(rcvrst)}>{rcvrst}",
                    end="\r\n",
                    file=file_descriptor,
                )

                print(
                    f"<STX_STRING:{len(sentnr)}>{sentnr}",
                    end="\r\n",
                    file=file_descriptor,
                )
                print(
                    f"<SRX_STRING:{len(rcvnr)}>{rcvnr}",
                    end="\r\n",
                    file=file_descriptor,
                )
                if len(grid) > 1:
                    print(
                        f"<GRIDSQUARE:{len(grid)}>{grid}",
                        end="\r\n",
                        file=file_descriptor,
                    )

                print(
                    f"<COMMENT:{len(comment)}>{comment}",
                    end="\r\n",
                    file=file_descriptor,
                )
                print("<EOR>", end="\r\n", file=file_descriptor)
                print("", end="\r\n", file=file_descriptor)
    except IOError:
        ...


def cabrillo(self):
    """Generates Cabrillo file. Maybe."""
    # https://www.cqwpx.com/cabrillo.htm
    logger.debug("******Cabrillo*****")
    filename = (
        str(Path.home())
        + "/"
        + f"{self.pref.get('callsign').upper()}_{cabrillo_name}.log"
    )
    logger.debug("%s", filename)
    log = self.database.fetch_all_contacts_asc()
    try:
        with open(filename, "w", encoding="ascii") as file_descriptor:
            print("START-OF-LOG: 3.0", end="\r\n", file=file_descriptor)
            print(
                f"CREATED-BY: Not1MM v{__version__}",
                end="\r\n",
                file=file_descriptor,
            )
            print(
                f"CONTEST: {cabrillo_name}",
                end="\r\n",
                file=file_descriptor,
            )
            print(
                f"CALLSIGN: {self.pref.get('callsign','')}",
                end="\r\n",
                file=file_descriptor,
            )
            print(
                f"LOCATION: {self.pref.get('section', '')}",
                end="\r\n",
                file=file_descriptor,
            )
            # print(
            #     f"ARRL-SECTION: {self.pref.get('section', '')}",
            #     end="\r\n",
            #     file=file_descriptor,
            # )
            # CATEGORY-OPERATOR: SINGLE-OP
            # CATEGORY-ASSISTED: NON-ASSISTED
            # CATEGORY-BAND: ALL
            # CATEGORY-MODE: SSB
            # CATEGORY-TRANSMITTER: ONE
            # CATEGORY-OVERLAY: CLASSIC
            # GRID-LOCATOR: DM13at
            print(
                f"CATEGORY: {None}",
                end="\r\n",
                file=file_descriptor,
            )
            print("CATEGORY-POWER: ", end="\r\n", file=file_descriptor)

            print(
                f"CLAIMED-SCORE: {calc_score(self)}",
                end="\r\n",
                file=file_descriptor,
            )
            print(
                "OPERATORS: ",
                end="\r\n",
                file=file_descriptor,
            )
            print(
                f"NAME: {self.pref.get('name', '')}",
                end="\r\n",
                file=file_descriptor,
            )
            print(
                f"ADDRESS: {self.pref.get('address1', '')}",
                end="\r\n",
                file=file_descriptor,
            )
            print(
                f"ADDRESS-CITY: {self.pref.get('city', '')}",
                end="\r\n",
                file=file_descriptor,
            )
            print(
                f"ADDRESS-STATE-PROVINCE: {self.pref.get('state', '')}",
                end="\r\n",
                file=file_descriptor,
            )
            print(
                f"ADDRESS-POSTALCODE: {self.pref.get('zip', '')}",
                end="\r\n",
                file=file_descriptor,
            )
            print(
                f"ADDRESS-COUNTRY: {self.pref.get('country', '')}",
                end="\r\n",
                file=file_descriptor,
            )
            print(
                f"EMAIL: {self.pref.get('email', '')}",
                end="\r\n",
                file=file_descriptor,
            )
            for contact in log:
                the_date_and_time = contact.get("TS", "")
                themode = contact.get("Mode", "")
                if themode == "LSB" or themode == "USB":
                    themode = "PH"
                frequency = str(int(contact.get("Freq", "0"))).rjust(5)

                loggeddate = the_date_and_time[:10]
                loggedtime = the_date_and_time[11:13] + the_date_and_time[14:16]
                print(
                    f"QSO: {frequency} {themode} {loggeddate} {loggedtime} "
                    f"{contact.get('StationPrefix', '').ljust(13)} "
                    f"{str(contact.get('SNT', '')).ljust(3)} "
                    f"{str(contact.get('SentNr', '')).ljust(6)} "
                    f"{contact.get('Call', '').ljust(13)} "
                    f"{str(contact.get('RCV', '')).ljust(3)} "
                    f"{str(contact.get('NR', '')).ljust(6)}",
                    end="\r\n",
                    file=file_descriptor,
                )
            print("END-OF-LOG:", end="\r\n", file=file_descriptor)
    except IOError as exception:
        logger.critical("cabrillo: IO error: %s, writing to %s", exception, filename)
        return