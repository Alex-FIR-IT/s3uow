from .has_data import HasDataAttributeProtocol
from .has_ext import HasExtensionPropertyProtocol


class HasDataAndExtensionAttrProtocol(
    HasDataAttributeProtocol,
    HasExtensionPropertyProtocol,
):
    pass
