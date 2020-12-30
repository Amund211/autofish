from functools import total_ordering

from minecraft import RELEASE_MINECRAFT_VERSIONS, SUPPORTED_MINECRAFT_VERSIONS

LATEST_VERSION = next(reversed(RELEASE_MINECRAFT_VERSIONS))
LATEST_RELEASE_VERSION = next(reversed(SUPPORTED_MINECRAFT_VERSIONS))


def is_supported(version):
    return version in SUPPORTED_MINECRAFT_VERSIONS


@total_ordering
class Version:
    """
    Class that implements a total ordering on minecraft versions
    using the chronological order defined in pyCraft.
    """

    def __init__(self, version):
        self.version = version

    @property
    def protocol(self):
        return SUPPORTED_MINECRAFT_VERSIONS[self.version]

    @property
    def _index(self):
        return next(
            i
            for i, version in enumerate(SUPPORTED_MINECRAFT_VERSIONS)
            if version == self.version
        )

    def __lt__(self, other):
        return self._index < other._index

    def __eq__(self, other):
        return self.version == other.version
