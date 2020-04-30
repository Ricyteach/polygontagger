from __future__ import annotations
from dataclasses import dataclass
from typing import (
    Optional,
    Callable,
    Any,
    TypeVar,
    List,
    Mapping,
    NamedTuple,
    Iterator,
    Generic,
    Sequence,
    NewType,
    overload,
    Iterable,
)

from shapely import geometry as geo


class ContainmentError(Exception):
    ...


class IndexerError(Exception):
    ...


# types
Idx = NewType("Idx", int)
ContainerGeo = TypeVar("ContainerGeo", bound=geo.base.BaseGeometry)
ContainedGeo = TypeVar("ContainedGeo", bound=geo.base.BaseGeometry)
ContainerSeq = Sequence[ContainerGeo]
ContainFunc = Callable[[ContainerGeo, ContainedGeo], bool]
KeyFunc = Callable[[Any], ContainedGeo]


def _default_key(obj):
    """Default key function."""
    return obj


def _contains_default(container: ContainerGeo, contained: ContainedGeo):
    """Default contains function."""
    return container.contains(contained)


class ContainsTuple(NamedTuple, Generic[ContainedGeo, ContainerGeo]):
    """An `obj, contained, container, f` tuple where contained is inside container using f."""

    obj: Any
    contained: ContainedGeo
    container: ContainerGeo
    f: ContainFunc[ContainerGeo, ContainedGeo] = _contains_default


def gen_container_tuples(
    obj: Any,
    containers: ContainerSeq,
    *,
    contain_f: Optional[ContainFunc] = None,
    key: Optional[KeyFunc] = None
) -> Iterator[ContainsTuple]:
    """Checks containment of the obj geometry by each container and returns a ContainsTuple
    each time there is containment."""

    if key is None:
        key = _default_key
    key: KeyFunc
    contains = _contains_default if contain_f is None else contain_f
    contained = key(obj)
    for i, container in enumerate(containers):
        if contains(container, contained):
            yield ContainsTuple(
                obj, contained, container
            ) if contain_f is None else ContainsTuple(
                obj, contained, container, contain_f
            )


@dataclass
class PolygonIndexer(Generic[ContainedGeo, ContainerGeo]):
    """Used to gather the indexes for object geometries depending on whether they are contained in the containers.

    An optional key function argument can be provided to get the object geometry from the object.
    """

    containers: ContainerSeq[ContainerGeo]
    contain_f: ContainFunc[ContainerGeo, ContainedGeo] = _contains_default
    key: KeyFunc[ContainedGeo] = _default_key

    def gen_indexes(self, obj: Any) -> Iterator[Idx]:
        yield from (
            Idx(idx)
            for idx, _ in enumerate(
                gen_container_tuples(
                    obj, self.containers, contain_f=self.contain_f, key=self.key
                )
            )
        )

    def idx_list(self, obj: Any) -> List[Idx]:
        return list(self.gen_indexes(obj))

    def idx(self, obj: Any) -> Idx:
        try:
            return next(self[0].gen_indexes(obj))
        except StopIteration:
            raise ContainmentError()
        except IndexError as err:
            raise IndexerError from err

    @overload
    def __getitem__(self, i: int) -> PolygonIndexer[ContainedGeo, ContainerGeo]:
        ...

    @overload
    def __getitem__(self, s: slice) -> PolygonIndexer[ContainedGeo, ContainerGeo]:
        ...

    def __getitem__(self, i):
        containers = self.containers[i] if isinstance(i, slice) else [self.containers[i]]
        return type(self)(containers, self.contain_f, self.key)


def index_shapes(
    objs: Iterable[Any],
    containers: ContainerSeq,
    contain_f: ContainFunc[ContainerGeo, ContainedGeo] = _contains_default,
    key: KeyFunc[ContainedGeo] = _default_key,
) -> Iterator[Idx]:

    indexer = PolygonIndexer(containers, contain_f, key)[0]
    yield from (indexer.idx(obj) for obj in objs)


def tag_shapes(
    objs: Iterable[Any],
    tags: Sequence[Any],
    containers: ContainerSeq,
    contain_f: ContainFunc[ContainerGeo, ContainedGeo] = _contains_default,
    key: KeyFunc[ContainedGeo] = _default_key,
) -> Iterator[Any]:
    yield from (tags[idx] for idx in index_shapes(objs, containers, contain_f, key))
