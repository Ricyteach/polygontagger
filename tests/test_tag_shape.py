import pytest

from polygontagger.main import tag_shapes, ContainmentError

_LEN = 10


@pytest.fixture
def objs():
    return [x for x in range(_LEN)]


@pytest.fixture
def tags():
    return [str(x) for x in range(_LEN)]


@pytest.fixture
def containers():
    return [_TestContainer(x) for x in range(_LEN)]


class _TestContainer(int):
    def contains(self, other):
        return self == other


def test_tag_shapes_basic(objs, tags, containers):
    shape_tags_gen = tag_shapes(objs, tags, containers)
    first_tag = next(shape_tags_gen)
    assert first_tag == "0"
    with pytest.raises(ContainmentError):
        next(shape_tags_gen)
