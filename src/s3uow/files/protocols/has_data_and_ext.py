from .has_ext import HasExtensionPropertyProtocol
from .has_data import HasDataAttributeProtocol



class HasDataAndExtensionAttrProtocol(HasDataAttributeProtocol, HasExtensionPropertyProtocol,):
    pass