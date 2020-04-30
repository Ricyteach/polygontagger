# polygontagger
A tool for tagging indexed objects based on shapely polygons.

TODO: improve awful API.

```python
from polygontagger.main import tag_shapes

# containers is a sequence of shapely objects to test for containment in

indexer = PolygonIndexer(containers)

# obj is a shapely object, or any kind of object with a key argument

indexes = indexer.idx_list(obj, key=lambda x: x.get_shapely_object(x))
```
