"""
TODO(bootcamper): write the tests for ``src/waypoint_utils.py`` in here.

The example below covers files that parse fine: with and without ``home``,
and files with comments and blank lines in them. The rest is yours:

- Bad data: a file whose top level isn't a mapping, waypoints missing
  ``lat``, ``lon``, or ``alt``, values that aren't numbers, YAML that
  doesn't parse, and a file that isn't there.
- Out of range: latitudes past +/-90 and longitudes past +/-180 get
  rejected.
- Nothing to work with: an empty file, an empty ``waypoints`` list, and
  ``sort_clockwise_sweep`` given a list of 0 or 1 waypoints.
- ``east_north_coordinate_offset_m``: offsets you worked out yourself,
  compared with ``pytest.approx``. Never use ``==`` on meters.
- Ordering: with no ``home``, ``sort_clockwise_sweep`` goes clockwise
  starting from north.
- With a ``home``: the order starts in home's direction instead, and goes
  back to starting at north if home is right on top of the centroid.
- Two waypoints in the same direction: the closer one comes first.
- Parsing gives you frozen ``Coordinate`` objects that can't be changed.

Graded by ``warg run utils grade-tests``: pass on the real code, 90% branch
coverage, and fail on every broken copy in ``grader/mutants/``.
"""

import dataclasses
import math

import pytest

from src.constants import EARTH_RADIUS_M
from src.types import Coordinate
from src.waypoint_utils import (
    east_north_coordinate_offset_m,
    parse_waypoints_file,
    sort_clockwise_sweep,
)

# The helper and the test below are given to you.


def write_to_tmp_waypoints_file(tmp_path, text):
    """Write ``text`` to a YAML file and hand back its path.

    ``tmp_path`` is a pytest fixture: a fresh empty directory per test.
    """
    path = tmp_path / "waypoints.yaml"
    path.write_text(text)
    return path


# One test, three files. ``parametrize`` runs the test body once per
# ``(text, expected)`` pair, and ``ids`` names each run so a failure tells you
# which file broke.
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            """
            home: {lat: 1, lon: 2, alt: 3}
            waypoints:
              - {lat: 4, lon: 5, alt: 6}
            """,
            (Coordinate(1, 2, 3), [Coordinate(4, 5, 6)]),
        ),
        (
            """
            waypoints:
              - {lat: 4, lon: 5, alt: 6}
              - {lat: 7, lon: 8, alt: 9}
            """,
            (None, [Coordinate(4, 5, 6), Coordinate(7, 8, 9)]),
        ),
        (
            """
            # a lap

            home: {lat: 1, lon: 2, alt: 3}

            waypoints:
              # first leg
              - {lat: 4, lon: 5, alt: 6}
            """,
            (Coordinate(1, 2, 3), [Coordinate(4, 5, 6)]),
        ),
    ],
    ids=["home-and-waypoints", "no-home", "comments-and-blank-lines"],
)
def test_parse_waypoints_file_success(tmp_path, text, expected):
    path = write_to_tmp_waypoints_file(tmp_path, text)
    assert parse_waypoints_file(path) == expected


def test_east_north_coordinate_offset_m():
    east, north = east_north_coordinate_offset_m(from_lat = 5, from_lon = 5, to_lat = 5, to_lon = 5)
    assert east == 0
    assert north == 0  

    east, north = east_north_coordinate_offset_m(from_lat = 5, from_lon = 0, to_lat = 10, to_lon = 0)
    assert east == pytest.approx(0, abs=1e-6)
    assert north == pytest.approx((math.radians(5) * EARTH_RADIUS_M), abs = 1.0)

    east, north = east_north_coordinate_offset_m(from_lat = 0, from_lon = 5, to_lat = 0, to_lon = 10)
    assert east == pytest.approx((math.radians(5) * EARTH_RADIUS_M), abs = 1.0)
    assert north == pytest.approx(0, abs=1e-6) 

    east, north = east_north_coordinate_offset_m(from_lat = 45, from_lon = 0, to_lat = 45, to_lon = 5)
    assert north == pytest.approx(0, abs=1e-6)
    assert east == pytest.approx(math.radians(5) * math.cos(math.radians(45)) * EARTH_RADIUS_M, abs=1.0)

    assert callable(east_north_coordinate_offset_m)
    assert callable(parse_waypoints_file)
    assert callable(sort_clockwise_sweep)

def test_pwf_rejects_non_mapping_entry(tmp_path):   
  path = write_to_tmp_waypoints_file(tmp_path, text= """
  waypoints:
    - "amongus"
  """,
    )
  with pytest.raises(ValueError):
    parse_waypoints_file(path)
def test_pfw_rejects_non_numeric_value(tmp_path):
  path = write_to_tmp_waypoints_file(tmp_path, text = """
  waypoints:
    - lat: "amongus"
      lon: 10
      alt: 4
  """
  )
  with pytest.raises(ValueError):
    parse_waypoints_file(path)
def test_pfw_rejects_out_of_range_lat(tmp_path):
  path = write_to_tmp_waypoints_file(tmp_path, text = """
  waypoints:
    - lat: 91
      lon: 60
      alt: 20
  """
  )
  with pytest.raises(ValueError):
    parse_waypoints_file(path)
def test_pfw_rejects_out_of_range_lon(tmp_path):
  path = write_to_tmp_waypoints_file(tmp_path, text = """
  waypoints:
    - lat: 60
      lon: 181
      alt: 4
  """
  )
  with pytest.raises(ValueError):
    parse_waypoints_file(path)
def test_pfw_rejects_bad_YAML(tmp_path):
  path = write_to_tmp_waypoints_file(tmp_path, text = """
  waypoints:
  - lat: 'among
  """
  )
  with pytest.raises(ValueError):
    parse_waypoints_file(path)
def test_pfw_rejects_non_mapping_top_level(tmp_path):
  path = write_to_tmp_waypoints_file(tmp_path, text = """
  100
  """
  )
  with pytest.raises(ValueError):
    parse_waypoints_file(path)
def test_pfw_rejetcs_empty_file(tmp_path):
  path = write_to_tmp_waypoints_file(tmp_path, text = """
  """
  )
  assert parse_waypoints_file(path) == (None, [])
def test_pfw_rejects_missing_file(tmp_path):
  path = tmp_path / "waypoints.yaml"
  with pytest.raises(OSError):
    parse_waypoints_file(path)

def test_pfw_rejects_missing_alt(tmp_path):
  path = write_to_tmp_waypoints_file(tmp_path, text="""
  waypoints:
    - lat: 10
      lon: 10
      """
                                     )
  with pytest.raises(ValueError):
    parse_waypoints_file(path)

def test_coordinate_is_frozen():
    coordinate = Coordinate(lat=43.47, lon=-80.54, alt=15)
    with pytest.raises(dataclasses.FrozenInstanceError):
        coordinate.lat = 10

def test_scw_single_waypoint():
  coordinate = Coordinate(lat=43.47, lon=-80.54, alt=15)
  output = sort_clockwise_sweep([coordinate], None)
  assert output == [coordinate]

def test_scw_reject_empty_list():
  assert sort_clockwise_sweep([]) == []

def test_scw_coordinate_output_sort():
  assert sort_clockwise_sweep([Coordinate(lat=-10, lon=0, alt=10),
                              Coordinate(lat=0, lon=-10, alt=10),
                              Coordinate(lat=10, lon=0, alt=10), 
                              Coordinate(lat=0, lon=10, alt=10)]) == ([Coordinate(lat=10, lon=0,alt=10),
                                                                       Coordinate(lat=0, lon=10,alt=10),
                                                                       Coordinate(lat=-10, lon=0, alt=10),
                                                                       Coordinate(lat=0, lon=-10, alt=10)])

def test_scw_home_sweep_inthatdirection():
  assert sort_clockwise_sweep([Coordinate(lat=-10, lon=0, alt=10),
                              Coordinate(lat=0, lon=-10, alt=10),
                              Coordinate(lat=10, lon=0, alt=10), 
                              Coordinate(lat=0, lon=10, alt=10)],
                              home= Coordinate(lat=0, lon=10, alt=10)) == ([Coordinate(lat=0, lon=10,alt=10),
                                                                       Coordinate(lat=-10, lon=0, alt=10),
                                                                       Coordinate(lat=0, lon=-10, alt=10),
                                                                       Coordinate(lat=10, lon=0,alt=10)])

def test_scw_home_centroid():
  assert sort_clockwise_sweep([Coordinate(lat=-10, lon=0, alt=10),
                              Coordinate(lat=0, lon=-10, alt=10),
                              Coordinate(lat=10, lon=0, alt=10), 
                              Coordinate(lat=0, lon=10, alt=10)],
                              home= Coordinate(lat=0, lon=0, alt=10)) == ([Coordinate(lat=10, lon=0,alt=10),
                                                                       Coordinate(lat=0, lon=10,alt=10),
                                                                       Coordinate(lat=-10, lon=0, alt=10),
                                                                       Coordinate(lat=0, lon=-10, alt=10)])

def test_scw_tiebreak():
  assert sort_clockwise_sweep([Coordinate(lat=-10, lon=0, alt=10),
                                Coordinate(lat=0, lon=-10, alt=10),
                                Coordinate(lat=10, lon=0, alt=10), 
                                Coordinate(lat=0, lon=10, alt=10),
                                Coordinate(lat=100, lon=0, alt=10),
                                Coordinate(lat=-100, lon=0, alt=10)]) == ([Coordinate(lat=10, lon=0,alt=10),
                                                                       Coordinate(lat=100, lon=0, alt=10),
                                                                       Coordinate(lat=0, lon=10,alt=10),
                                                                       Coordinate(lat=-10, lon=0, alt=10),
                                                                       Coordinate(lat=-100, lon=0, alt=10),
                                                                       Coordinate(lat=0, lon=-10, alt=10)])