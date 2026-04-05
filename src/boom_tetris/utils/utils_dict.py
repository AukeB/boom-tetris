"""Helpers for YAML-friendly dict structures and attribute-style dict access."""

from typing import Any, Union

from ruamel.yaml.comments import CommentedMap, CommentedSeq


def format_for_writing_to_yaml_file(
    obj: Union[dict[Any, Any], list[Any], Any],
    path: list[str | int] | None = None,
) -> Union[CommentedMap, CommentedSeq, Any]:
    """
    Build ruamel structures with optional path-based formatting hints.

    Args:
        obj: Plain dict, list, or scalar to wrap for YAML output.
        path: Key path from the root for special cases (e.g. ALL_SHAPES).

    Returns:
        ``CommentedMap``, ``CommentedSeq``, or the original scalar.
    """
    path = path or []

    if isinstance(obj, dict):
        new_map = CommentedMap()

        for k, v in obj.items():
            new_map[k] = format_for_writing_to_yaml_file(v, path + [k])

        if not path:
            keys = list(new_map.keys())
            for k in keys[1:]:
                new_map.yaml_set_comment_before_after_key(k, before="\n")

        return new_map

    elif isinstance(obj, list):
        # Special case for POLYOMINO.ALL_SHAPES:
        if path == ["POLYOMINO", "ALL_SHAPES"]:
            outer = CommentedSeq()
            for shape in obj:
                inner = CommentedSeq()
                inner.fa.set_flow_style()  # force inline for each 2D shape
                for point in shape:
                    inner.append(point)
                outer.append(inner)
            return outer

        seq = CommentedSeq()
        for item in obj:
            seq.append(format_for_writing_to_yaml_file(item, path))
        seq.fa.set_flow_style()  # Force inline.
        return seq

    else:
        return obj


class DotDict(dict[Any, Any]):
    """``dict`` subclass with attribute access for nested configuration."""

    def __init__(self, data: dict[Any, Any] | None = None) -> None:
        """
        Populate from a mapping, wrapping nested dicts as ``DotDict``.

        Args:
            data: Source mapping, or empty if ``None``.
        """
        super().__init__()
        data = data or {}

        for key, value in data.items():
            self[key] = self._wrap(value)

    def __getattr__(self, attr: str) -> Any:
        """
        Return a key as an attribute, mirroring ``dict`` lookup.

        Args:
            attr: Key name.

        Returns:
            The stored value.

        Raises:
            AttributeError: If the key is missing.
        """
        try:
            return self[attr]
        except KeyError as e:
            raise AttributeError(f"'DotDict' object has no attribute '{attr}'") from e

    def __setattr__(self, key: str, value: Any) -> None:
        """
        Store a value under ``key``, wrapping dicts as ``DotDict``.

        Args:
            key: Attribute and dict key name.
            value: Value to store (dicts are wrapped recursively).
        """
        self[key] = self._wrap(value)

    def __delattr__(self, key: str) -> None:
        """
        Delete a key by attribute syntax.

        Args:
            key: Key to remove.

        Raises:
            AttributeError: If the key is missing.
        """
        try:
            del self[key]
        except KeyError as e:
            raise AttributeError(f"'DotDict' object has no attribute '{key}'") from e

    def _wrap(self, value: Any) -> Any:
        """
        Recursively wrap dicts as ``DotDict`` and lists element-wise.

        Args:
            value: Arbitrary nested structure.

        Returns:
            Wrapped structure or the original scalar.
        """
        if isinstance(value, dict):
            return DotDict(value)
        elif isinstance(value, list):
            return [self._wrap(v) for v in value]

        return value

    def to_dict(self) -> dict[Any, Any]:
        """
        Convert this tree to plain dicts and lists (no ``DotDict`` nodes).

        Returns:
            A JSON-serializable plain ``dict`` representation.
        """
        result: dict[Any, Any] = {}

        for key, value in self.items():
            if isinstance(value, DotDict):
                result[key] = value.to_dict()
            elif isinstance(value, list):
                result[key] = [
                    item.to_dict() if isinstance(item, DotDict) else item
                    for item in value
                ]
            else:
                result[key] = value

        return result
