from datetime import datetime, timedelta
from typing import List, Union
from .checkers import UpstreamChecker
import re


class VersionInfo:
    def __init__(
        self,
        version: str,
        source: Union[str, UpstreamChecker],
        tags: set,
        updated: datetime = None,
        origin: bool = False,
    ):
        self._version: str = str(version)
        self._source: Union[str, UpstreamChecker] = source
        self._origin: bool = origin
        self._tags: set = tags
        self._updated: datetime = updated

    @property
    def version(self) -> str:
        """
        Returns version of the object. If it's containing information
        about possible upstream version, updates it if it's older than 1 hour.
        """
        if isinstance(self._source, UpstreamChecker):
            now = datetime.now()
            if not self._updated or not (
                now - timedelta(hours=1) <= self._updated <= now
            ):
                self._version = self._source.get_version()
                self._updated = now
                return self._version
            else:
                self._version = self._source.version
        return self._version

    @version.setter
    def version(self, version: Union[str, int, float]):
        if not version:
            raise ValueError("Cannot set empty value for version.")
        self._version = str(version)

    @property
    def provider(self) -> str:
        """Returns provider of upstream source, eg. GitHub """
        if isinstance(self._source, UpstreamChecker):
            return self._source.provider
        else:
            return self._source

    @property
    def docker_origin(self) -> bool:
        """
        Returns true if this upsream is used to install tool in
        corresponding dockerfile.
        """
        if isinstance(self._source, UpstreamChecker):
            return self._source.docker_origin
        else:
            return False

    @property
    def extra_info(self) -> str:
        """Returns possible added extra information."""
        if isinstance(self._source, UpstreamChecker):
            return self._source.extra_info
        else:
            return ""

    @property
    def source(self) -> UpstreamChecker:
        return self._source

    @source.setter
    def source(self, checker: Union[str, UpstreamChecker]):
        self._source = checker

    @property
    def origin(self) -> str:
        if isinstance(self._source, UpstreamChecker):
            self._origin = self._source.origin
        return self._origin

    @property
    def tags(self) -> set:
        return self._tags

    @property
    def updated(self) -> datetime:
        return self._updated

    @updated.setter
    def updated(self, dt: datetime):
        if not isinstance(dt, datetime):
            raise ValueError("Given time is not 'datetime' object.")
        self._updated = dt

    def _normalize(self, value: str) -> Union[str, List]:
        if any(char.isdigit() for char in value):
            # Git uses SHA-1 hash currently, length 40 characters
            # Commit hash maybe
            if re.findall(r"(^[a-fA-F0-9]{40}$)", value):
                return value
            # In future, SHA-256 will be used for commit hash, length is 64 chars
            elif re.findall(r"(^[a-fA-F0-9]{64}$)", value):
                return value
            else:
                # Subtract else than numbers and '.' and '_'
                sub = re.sub(r"[^0-9._]+", "", value)
                # Replace dash with dot, seems to be commonly used with similar purpose
                rep = sub.replace("_", ".")
                split_by_dot = re.split(r'[._]', rep)
                first = None
                second = None
                # Get slice from list, which is expected to contain version information
                # NOTE not 100% working, but maybe 99%
                for i, val in enumerate(split_by_dot):
                    if not val and not first:
                        first = i + 1
                        continue
                    if val == "" and first:
                        second = i
                        break
                return list(map(int, split_by_dot[first:second]))
        else:
            return value

    def get_normalized_ver(self) -> List:
        return self._normalize(self.version)

    def __eq__(self, value: Union[str, "VersionInfo"]) -> bool:
        """
        Support comparison between strings or other VersionInfo objects
        """
        if isinstance(value, str):
            if self.get_normalized_ver() == self._normalize(value):
                return True
            else:
                return False
        elif not isinstance(value, VersionInfo):
            raise ValueError(
                f"Unable to compare '=' type {type(value)} and type {type(VersionInfo)}"
            )
        else:
            if self.get_normalized_ver() == value.get_normalized_ver():
                return True
            else:
                return False

    def __str__(self) -> str:
        return str(self.version)

    def __format__(self, value):
        return self.version.__format__(value)

    def __iter__(self):
        yield "version", self.version,
        yield "source", self.source if isinstance(self.source, str) else dict(
            self.source
        ),
        yield "tags", sorted(list(self.tags)),
        yield "updated", str(self.updated),
        yield "origin", self.origin,