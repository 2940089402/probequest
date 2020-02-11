"""
Unit tests written with the 'unittest' module.
"""

# pylint: disable=import-error
# pylint: disable=unused-variable

from re import compile as rcompile, IGNORECASE
import unittest
import pylint.lint
from netaddr.core import AddrFormatError

from scapy.layers.dot11 import RadioTap, Dot11, Dot11ProbeReq, Dot11Elt
from scapy.packet import fuzz

from probequest.config import Config
from probequest.probe_request import ProbeRequest
from probequest.probe_request_parser import ProbeRequestParser


class TestProbeRequest(unittest.TestCase):
    """
    Unit tests for the 'ProbeRequest' class.
    """

    def test_without_parameters(self):
        """
        Initialises a 'ProbeRequest' object without any parameter.
        """

        # pylint: disable=no-value-for-parameter

        with self.assertRaises(TypeError):
            probe_req = ProbeRequest()  # noqa: F841

    def test_with_only_one_parameter(self):
        """
        Initialises a 'ProbeRequest' object with only one parameter.
        """

        # pylint: disable=no-value-for-parameter

        timestamp = 1517872027.0

        with self.assertRaises(TypeError):
            probe_req = ProbeRequest(timestamp)  # noqa: F841

    def test_with_only_two_parameters(self):
        """
        Initialises a 'ProbeRequest' object with only two parameters.
        """

        # pylint: disable=no-value-for-parameter

        timestamp = 1517872027.0
        s_mac = "aa:bb:cc:dd:ee:ff"

        with self.assertRaises(TypeError):
            probe_req = ProbeRequest(timestamp, s_mac)  # noqa: F841

    def test_create_a_probe_request(self):
        """
        Creates a new 'ProbeRequest' with all the required parameters.
        """

        # pylint: disable=no-self-use

        timestamp = 1517872027.0
        s_mac = "aa:bb:cc:dd:ee:ff"
        essid = "Test ESSID"

        probe_req = ProbeRequest(timestamp, s_mac, essid)  # noqa: F841

    def test_bad_mac_address(self):
        """
        Initialises a 'ProbeRequest' object with a malformed MAC address.
        """

        timestamp = 1517872027.0
        s_mac = "aa:bb:cc:dd:ee"
        essid = "Test ESSID"

        with self.assertRaises(AddrFormatError):
            probe_req = ProbeRequest(timestamp, s_mac, essid)  # noqa: F841

    def test_print_a_probe_request(self):
        """
        Initialises a 'ProbeRequest' object and prints it.
        """

        timestamp = 1517872027.0
        s_mac = "aa:bb:cc:dd:ee:ff"
        essid = "Test ESSID"

        probe_req = ProbeRequest(timestamp, s_mac, essid)

        self.assertNotEqual(
            str(probe_req).find("Mon, 05 Feb 2018 23:07:07"),
            -1
        )
        self.assertNotEqual(
            str(probe_req).find("aa:bb:cc:dd:ee:ff (None) -> Test ESSID"),
            -1
        )


class TestConfig(unittest.TestCase):
    """
    Unit tests for the 'Config' class.
    """

    def test_default_frame_filter(self):
        """
        Tests the default frame filter.
        """

        config = Config()
        frame_filter = config.generate_frame_filter()

        self.assertEqual(
            frame_filter,
            "type mgt subtype probe-req"
        )

    def test_frame_filter_with_mac_filtering(self):
        """
        Tests the frame filter when some MAC addresses need to be filtered.
        """

        config = Config()
        config.mac_filters = ["a4:77:33:9a:73:5c", "b0:05:94:5d:5a:4d"]
        frame_filter = config.generate_frame_filter()

        self.assertEqual(
            frame_filter,
            "type mgt subtype probe-req" +
            " and (ether src host a4:77:33:9a:73:5c" +
            "|| ether src host b0:05:94:5d:5a:4d)"
        )

    def test_frame_filter_with_mac_exclusion(self):
        """
        Tests the frame filter when some MAC addresses need to be excluded.
        """

        config = Config()
        config.mac_exclusions = ["a4:77:33:9a:73:5c", "b0:05:94:5d:5a:4d"]
        frame_filter = config.generate_frame_filter()

        self.assertEqual(
            frame_filter,
            "type mgt subtype probe-req" +
            " and not (ether src host a4:77:33:9a:73:5c" +
            "|| ether src host b0:05:94:5d:5a:4d)"
        )

    def test_compile_essid_regex_with_an_empty_regex(self):
        """
        Tests 'complile_essid_regex' with an empty regex.
        """

        config = Config()
        compiled_regex = config.complile_essid_regex()

        self.assertEqual(compiled_regex, None)

    def test_compile_essid_regex_with_a_case_sensitive_regex(self):
        """
        Tests 'complile_essid_regex' with a case-sensitive regex.
        """

        config = Config()
        config.essid_regex = "Free Wi-Fi"
        compiled_regex = config.complile_essid_regex()

        self.assertEqual(compiled_regex, rcompile(config.essid_regex))

    def test_compile_essid_regex_with_a_case_insensitive_regex(self):
        """
        Tests 'complile_essid_regex' with a case-insensitive regex.
        """

        config = Config()
        config.essid_regex = "Free Wi-Fi"
        config.ignore_case = True
        compiled_regex = config.complile_essid_regex()

        self.assertEqual(compiled_regex, rcompile(
            config.essid_regex, IGNORECASE))


class TestProbeRequestParser(unittest.TestCase):
    """
    Unit tests for the 'ProbeRequestParser' class.
    """

    def test_no_probe_request_layer(self):
        """
        Creates a non-probe-request Wi-Fi packet and parses it with the
        'ProbeRequestParser.parse()' function.
        """

        # pylint: disable=no-self-use

        packet = RadioTap() \
            / Dot11(
                addr1="ff:ff:ff:ff:ff:ff",
                addr2="aa:bb:cc:11:22:33",
                addr3="dd:ee:ff:11:22:33"
            )

        with self.assertRaises(TypeError):
            ProbeRequestParser.parse(packet)

    def test_empty_essid(self):
        """
        Creates a probe request packet with an empty ESSID field and parses
        it with the 'ProbeRequestParser.parse()' function.
        """

        # pylint: disable=no-self-use

        packet = RadioTap() \
            / Dot11(
                addr1="ff:ff:ff:ff:ff:ff",
                addr2="aa:bb:cc:11:22:33",
                addr3="dd:ee:ff:11:22:33"
            ) \
            / Dot11ProbeReq() \
            / Dot11Elt(
                info=""
            )

        ProbeRequestParser.parse(packet)

    def test_fuzz_packets(self):
        """
        Parses 1000 randomly-generated probe requests with the
        'ProbeRequestParser.parse()' function.
        """

        # pylint: disable=no-self-use

        for i in range(0, 1000):
            with self.subTest():
                try:
                    packet = RadioTap() / \
                        fuzz(Dot11()/Dot11ProbeReq()/Dot11Elt())
                    ProbeRequestParser.parse(packet)
                except TypeError:
                    # Expected behaviour.
                    pass


class TestLinter(unittest.TestCase):
    """
    Unit tests for Python linters.
    """

    # Some linting errors will be fixed while
    # refactoring the code.
    @unittest.expectedFailure
    def test_pylint(self):
        """
        Executes Pylint.
        """

        # pylint: disable=no-self-use

        pylint.lint.Run([
            "probequest",
            "test"
        ])
